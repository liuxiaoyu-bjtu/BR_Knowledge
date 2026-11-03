#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter 12 单目几何足球定位节点。

本节点订阅 Chapter 12 本目录内检测节点发布的 ``/vision_detection/ball``，
再结合 K1 头部位姿 ``/head_pose``，把足球像素位置估计为机器人基座坐标系
下的 ``x/y/z``。

这个节点只使用单目几何，不读取深度图。它适合用来理解坐标转换公式：
像素点 -> 相机射线 -> 机器人基座坐标系 -> 与地面 z=0 求交。
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import numpy as np
import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from rclpy.node import Node
from std_msgs.msg import String

from ball_localization_utils import (
    CameraModel,
    DEFAULT_BALL_DET_TOPIC,
    DEFAULT_BASE_POS_TOPIC,
    DEFAULT_HEAD_POSE_TOPIC,
    build_compensation_matrix,
    choose_ball_pixel,
    format_ball_position_summary,
    load_camera_model_from_yaml,
    parse_json_message,
    pose_to_matrix,
    ray_to_ground_base,
)


class BallPositionGeometryNode(Node):
    """像素坐标到机器人基座坐标的单目几何转换节点。"""

    def __init__(self) -> None:
        super().__init__("ball_position_geometry_node")

        self.declare_parameter("ball_det_topic", DEFAULT_BALL_DET_TOPIC)
        self.declare_parameter("head_pose_topic", DEFAULT_HEAD_POSE_TOPIC)
        self.declare_parameter("base_pos_topic", DEFAULT_BASE_POS_TOPIC)
        self.declare_parameter("publish_rate_hz", 20.0)

        # 相机内参。实机优先从 /opt/booster/vision.yaml 或 camera_info 中确认。
        self.declare_parameter("fx", 203.921692)
        self.declare_parameter("fy", 203.921692)
        self.declare_parameter("cx", 254.567642)
        self.declare_parameter("cy", 214.381866)
        self.declare_parameter("use_yaml_camera", True)
        self.declare_parameter("vision_yaml_path", "/opt/booster/vision.yaml")

        # 安装补偿。调试时可微调，但每次只改一个参数。
        self.declare_parameter("pitch_compensation_deg", 0.0)
        self.declare_parameter("yaw_compensation_deg", 0.0)
        self.declare_parameter("z_compensation", 0.0)

        # 单目几何常用检测框底部中心附近的点，近似足球接地点。
        self.declare_parameter("use_bottom_center", True)
        self.declare_parameter("bbox_bottom_offset_ratio", 0.10)
        self.declare_parameter("ball_timeout_sec", 0.5)
        self.declare_parameter("min_conf", 0.5)

        # 安全输出范围，防止明显错误坐标进入后续控制。
        self.declare_parameter("min_x", 0.0)
        self.declare_parameter("max_x", 10.0)
        self.declare_parameter("max_abs_y", 5.0)

        # 简单低通滤波，减少轻微抖动。
        self.declare_parameter("enable_filter", False)
        self.declare_parameter("filter_alpha", 0.35)
        self.declare_parameter("debug", False)

        g = lambda name: self.get_parameter(name).value
        self.ball_det_topic = str(g("ball_det_topic"))
        self.head_pose_topic = str(g("head_pose_topic"))
        self.base_pos_topic = str(g("base_pos_topic"))
        self.publish_rate_hz = float(g("publish_rate_hz"))

        self.camera_model = CameraModel(
            fx=float(g("fx")),
            fy=float(g("fy")),
            cx=float(g("cx")),
            cy=float(g("cy")),
        )
        if bool(g("use_yaml_camera")):
            try:
                self.camera_model = load_camera_model_from_yaml(
                    self.camera_model,
                    str(g("vision_yaml_path")),
                )
            except Exception as exc:  # noqa: BLE001
                self.get_logger().warning(f"读取相机 YAML 失败，使用默认参数：{exc}")

        self.T_compensation = build_compensation_matrix(
            float(g("pitch_compensation_deg")),
            float(g("yaw_compensation_deg")),
            float(g("z_compensation")),
        )

        self.use_bottom_center = bool(g("use_bottom_center"))
        self.bbox_bottom_offset_ratio = float(g("bbox_bottom_offset_ratio"))
        self.ball_timeout_sec = float(g("ball_timeout_sec"))
        self.min_conf = float(g("min_conf"))
        self.min_x = float(g("min_x"))
        self.max_x = float(g("max_x"))
        self.max_abs_y = float(g("max_abs_y"))
        self.enable_filter = bool(g("enable_filter"))
        self.filter_alpha = max(0.0, min(1.0, float(g("filter_alpha"))))
        self.debug = bool(g("debug"))

        self.T_head_to_base: Optional[np.ndarray] = None
        self.last_ball_payload: Optional[Dict[str, Any]] = None
        self.last_ball_time = 0.0
        self.filtered_xy: Optional[Tuple[float, float]] = None
        self.last_log_time = 0.0

        self.create_subscription(String, self.ball_det_topic, self.on_ball_detection, 10)
        self.create_subscription(Pose, self.head_pose_topic, self.on_head_pose, 10)
        self.create_subscription(
            PoseStamped,
            self.head_pose_topic + "_stamped",
            self.on_head_pose_stamped,
            10,
        )
        self.base_pub = self.create_publisher(String, self.base_pos_topic, 10)
        self.timer = self.create_timer(
            1.0 / max(1e-6, self.publish_rate_hz),
            self.on_timer,
        )

        self.get_logger().info("Chapter 12 单目几何足球定位节点已启动。")
        self.get_logger().info(f"订阅检测话题：{self.ball_det_topic}")
        self.get_logger().info(
            f"订阅头部位姿：{self.head_pose_topic} 或 {self.head_pose_topic}_stamped"
        )
        self.get_logger().info(f"发布基座坐标：{self.base_pos_topic}")
        self.get_logger().info(
            "相机内参："
            f"fx={self.camera_model.fx:.3f}, fy={self.camera_model.fy:.3f}, "
            f"cx={self.camera_model.cx:.3f}, cy={self.camera_model.cy:.3f}"
        )

    def on_ball_detection(self, msg: String) -> None:
        """保存最新足球检测结果。"""

        payload = parse_json_message(msg.data)
        if payload is None:
            return
        self.last_ball_payload = payload
        self.last_ball_time = time.time()

    def on_head_pose(self, msg: Pose) -> None:
        """保存最新头部到基座的位姿矩阵。"""

        self.T_head_to_base = pose_to_matrix(msg)

    def on_head_pose_stamped(self, msg: PoseStamped) -> None:
        """兼容 PoseStamped 形式的头部位姿。"""

        self.T_head_to_base = pose_to_matrix(msg.pose)

    def on_timer(self) -> None:
        """固定频率计算并发布足球基座坐标。"""

        if self.last_ball_payload is None:
            self.publish_invalid("no_ball_payload")
            return

        if time.time() - self.last_ball_time > self.ball_timeout_sec:
            self.publish_invalid("ball_timeout")
            return

        payload = self.last_ball_payload
        if not bool(payload.get("detected", False)):
            self.publish_invalid("not_detected")
            return

        if float(payload.get("conf", 0.0)) < self.min_conf:
            self.publish_invalid("low_conf")
            return

        if self.T_head_to_base is None:
            self.publish_invalid("no_head_pose")
            return

        u, v = choose_ball_pixel(
            payload,
            use_bottom_center=self.use_bottom_center,
            bbox_bottom_offset_ratio=self.bbox_bottom_offset_ratio,
            fallback_cx=self.camera_model.cx,
            fallback_cy=self.camera_model.cy,
        )

        point = ray_to_ground_base(
            u,
            v,
            camera_model=self.camera_model,
            T_head_to_base=self.T_head_to_base,
            T_compensation=self.T_compensation,
        )
        if point is None:
            self.publish_invalid("ray_ground_intersection_failed")
            return

        x, y, z = point
        if not self.in_safe_range(x, y):
            self.publish_invalid("out_of_safe_range")
            return

        x, y = self.filter_xy(x, y)
        self.publish_valid(x, y, z, payload, u, v)

    def in_safe_range(self, x: float, y: float) -> bool:
        """过滤明显不合理的位置结果。"""

        return self.min_x <= x <= self.max_x and abs(y) <= self.max_abs_y

    def filter_xy(self, x: float, y: float) -> Tuple[float, float]:
        """对 x/y 做一阶低通滤波。"""

        if not self.enable_filter:
            return x, y

        if self.filtered_xy is None:
            self.filtered_xy = (x, y)
        else:
            px, py = self.filtered_xy
            a = self.filter_alpha
            self.filtered_xy = (a * x + (1.0 - a) * px, a * y + (1.0 - a) * py)
        return self.filtered_xy

    def publish_valid(
        self,
        x: float,
        y: float,
        z: float,
        payload: Dict[str, Any],
        pixel_u: float,
        pixel_v: float,
    ) -> None:
        """发布有效足球基座坐标。"""

        out = {
            "valid": True,
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "z": round(float(z), 3),
            "distance": round(float(math.hypot(x, y)), 3),
            "angle": round(float(math.atan2(y, x)), 3),
            "pixel_u": round(float(pixel_u), 1),
            "pixel_v": round(float(pixel_v), 1),
            "method": "geometry",
            "conf": float(payload.get("conf", 0.0)),
            "detected": bool(payload.get("detected", False)),
            "stamp": time.time(),
        }
        self.base_pub.publish(String(data=json.dumps(out, ensure_ascii=False)))

        if self.debug or time.time() - self.last_log_time >= 0.5:
            self.get_logger().info(format_ball_position_summary(out))
            self.last_log_time = time.time()

    def publish_invalid(self, reason: str) -> None:
        """发布无效定位状态，便于后续节点知道当前不能控制。"""

        out = {"valid": False, "reason": reason, "stamp": time.time()}
        self.base_pub.publish(String(data=json.dumps(out, ensure_ascii=False)))
        if self.debug and time.time() - self.last_log_time >= 0.5:
            self.get_logger().info(format_ball_position_summary(out))
            self.last_log_time = time.time()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BallPositionGeometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Chapter 12 单目几何足球定位节点停止。")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
