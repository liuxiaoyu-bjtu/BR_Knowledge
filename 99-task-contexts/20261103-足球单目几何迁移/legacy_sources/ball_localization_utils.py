#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter 12 足球空间定位公共工具。

本文件只服务于 Chapter 12，不依赖其他章节目录。它把空间定位中容易重复
使用的基础函数集中起来：
- 解析 JSON 话题消息；
- 将头部位姿 Pose 转为 4x4 变换矩阵；
- 将像素点反投影为相机坐标系下的一条射线；
- 计算射线与地面的交点；
- 解码深度图；
- 对深度点做球面拟合。

坐标系约定：
- 图像坐标系：原点在图像左上角，x 向右，y 向下。
- 相机坐标系：z 指向相机前方，x/y 由相机模型决定。
- 机器人基座坐标系：x 指向机器人前方，y 指向机器人左侧，z 指向上方。
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import yaml
from geometry_msgs.msg import Pose
from scipy.spatial.transform import Rotation as R
from sensor_msgs.msg import Image


DEFAULT_BALL_DET_TOPIC = "/vision_detection/ball"
DEFAULT_HEAD_POSE_TOPIC = "/head_pose"
DEFAULT_DEPTH_TOPIC = "/boostercamera/head/depth"
DEFAULT_CAMERA_INFO_TOPIC = "/boostercamera/head/rgb/camera_info"
DEFAULT_BASE_POS_TOPIC = "/vision/ball_position_base"


DEFAULT_T_CAM_TO_HEAD = np.array(
    [
        [0.0204047617, 0.00377522805, 0.999784708, -0.00454888586],
        [-0.999754429, -0.00857020356, 0.0204365067, 0.0473468825],
        [0.00864551123, -0.999956131, 0.00359942787, -0.00659073936],
        [0.0, 0.0, 0.0, 1.0],
    ],
    dtype=float,
)


@dataclass
class CameraModel:
    """相机内参与相机到头部坐标系的外参。"""

    fx: float = 203.921692
    fy: float = 203.921692
    cx: float = 254.567642
    cy: float = 214.381866
    T_cam_to_head: np.ndarray = None

    def __post_init__(self) -> None:
        if self.T_cam_to_head is None:
            self.T_cam_to_head = DEFAULT_T_CAM_TO_HEAD.copy()


def clamp01(value: float) -> float:
    """将数值限制到 [0, 1]，常用于滤波系数。"""

    return max(0.0, min(1.0, float(value)))


def parse_json_message(text: str) -> Optional[Dict[str, Any]]:
    """解析 ROS2 String 中的 JSON 字符串。

    有些调试工具会把 JSON 放在外层 ``data`` 字段中，本函数也兼容这种格式。
    """

    try:
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("data"), str):
            data = json.loads(data["data"])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def pose_to_matrix(pose: Pose) -> np.ndarray:
    """将 geometry_msgs/Pose 转换为 4x4 齐次变换矩阵。

    前 3x3 是旋转，最后一列前三个数是平移。这个矩阵可以把点从一个坐标系
    转换到另一个坐标系。
    """

    q = pose.orientation
    t = pose.position
    T = np.eye(4)
    T[:3, :3] = R.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
    T[:3, 3] = [t.x, t.y, t.z]
    return T


def build_compensation_matrix(
    pitch_compensation_deg: float,
    yaw_compensation_deg: float,
    z_compensation: float,
) -> np.ndarray:
    """构造相机安装误差补偿矩阵。

    pitch/yaw 用角度输入，内部转换为弧度。z_compensation 用米表示。
    """

    rotation = R.from_euler(
        "zy",
        [
            math.radians(float(yaw_compensation_deg)),
            math.radians(float(pitch_compensation_deg)),
        ],
    ).as_matrix()
    T = np.eye(4)
    T[:3, :3] = rotation
    T[2, 3] = float(z_compensation)
    return T


def load_camera_model_from_yaml(
    model: CameraModel,
    yaml_path: str,
) -> CameraModel:
    """尽量从 K1 视觉标定 YAML 中读取相机内参和外参。

    不同系统中的 YAML 结构可能略有差异，因此这里做了兼容读取。如果文件不存在
    或字段不匹配，直接返回传入的默认模型。
    """

    if not yaml_path or not os.path.exists(yaml_path):
        return model

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    intr = None
    extr = None
    if isinstance(data, dict):
        for key in ["camera", "Camera", "front_camera", "head_camera", "vision"]:
            obj = data.get(key)
            if isinstance(obj, dict):
                intr = (
                    obj.get("intrinsics")
                    or obj.get("intrinsic")
                    or obj.get("intrin")
                    or intr
                )
                extr = (
                    obj.get("extrin")
                    or obj.get("extrinsic")
                    or obj.get("extrinsics")
                    or extr
                )

        intr = data.get("intrinsics") or data.get("intrinsic") or data.get("intrin") or intr
        extr = data.get("extrin") or data.get("extrinsic") or data.get("extrinsics") or extr

    if isinstance(intr, dict):
        model.fx = float(intr.get("fx", model.fx))
        model.fy = float(intr.get("fy", model.fy))
        model.cx = float(intr.get("cx", model.cx))
        model.cy = float(intr.get("cy", model.cy))
    elif isinstance(intr, (list, tuple)) and len(intr) >= 4:
        model.fx, model.fy, model.cx, model.cy = map(float, intr[:4])

    if isinstance(extr, (list, tuple)):
        arr = np.array(extr, dtype=float)
        if arr.size == 16:
            model.T_cam_to_head = arr.reshape(4, 4)
    elif isinstance(extr, dict):
        mat = extr.get("matrix") or extr.get("T")
        if mat is not None:
            arr = np.array(mat, dtype=float)
            if arr.size == 16:
                model.T_cam_to_head = arr.reshape(4, 4)

    return model


def choose_ball_pixel(
    payload: Dict[str, Any],
    *,
    use_bottom_center: bool,
    bbox_bottom_offset_ratio: float,
    fallback_cx: float,
    fallback_cy: float,
) -> Tuple[float, float]:
    """选择用于空间定位的图像像素点。

    单目几何定位常用检测框底部中心附近的点，因为它更接近足球与地面接触的位置。
    深度定位常用检测框中心或框内深度点。
    """

    if use_bottom_center and "bbox_xyxy" in payload:
        try:
            x1, y1, x2, y2 = [float(v) for v in payload["bbox_xyxy"]]
            u = (x1 + x2) / 2.0
            height = max(1.0, y2 - y1)
            v = y2 - float(bbox_bottom_offset_ratio) * height
            return u, v
        except Exception:
            pass

    return float(payload.get("x", fallback_cx)), float(payload.get("y", fallback_cy))


def pixel_to_ray_camera(u: float, v: float, model: CameraModel) -> np.ndarray:
    """将像素点反投影为相机坐标系下的一条方向射线。

    这里用到的核心公式是：

    x_norm = (u - cx) / fx
    y_norm = (v - cy) / fy

    可以理解为：先算像素点距离图像中心有多远，再除以焦距，把像素单位换成
    相机前方的一条方向。
    """

    x_norm = (float(u) - model.cx) / model.fx
    y_norm = (float(v) - model.cy) / model.fy
    ray = np.array([x_norm, y_norm, 1.0], dtype=float)
    return ray / (np.linalg.norm(ray) + 1e-9)


def ray_to_ground_base(
    u: float,
    v: float,
    *,
    camera_model: CameraModel,
    T_head_to_base: np.ndarray,
    T_compensation: np.ndarray,
) -> Optional[Tuple[float, float, float]]:
    """计算像素射线与机器人基座坐标系地面 z=0 的交点。

    这是一种单目几何定位方法。它假设足球接触地面，通过“从相机出发的一条
    射线”和“地面平面”的交点估计足球位置。
    """

    ray_camera = pixel_to_ray_camera(u, v, camera_model)
    T_base_camera = T_head_to_base @ T_compensation @ camera_model.T_cam_to_head

    origin_base = T_base_camera[:3, 3]
    direction_base = T_base_camera[:3, :3] @ ray_camera
    direction_base = direction_base / (np.linalg.norm(direction_base) + 1e-9)

    dz = direction_base[2]
    if abs(dz) < 1e-6:
        return None

    scale = -origin_base[2] / dz
    if scale <= 0:
        return None

    point = origin_base + scale * direction_base
    return float(point[0]), float(point[1]), float(point[2])


def decode_depth_image(msg: Image) -> Optional[np.ndarray]:
    """将 ROS2 深度图消息解码为单位为米的 float32 数组。"""

    encoding = (msg.encoding or "").lower()
    height = int(msg.height)
    width = int(msg.width)
    buffer = bytes(msg.data)

    try:
        if encoding in ("16uc1", "mono16", "z16", ""):
            cols = int(msg.step // 2) if msg.step else width
            arr = np.frombuffer(buffer, dtype=np.uint16).reshape(height, cols)[:, :width]
            return arr.astype(np.float32) * 0.001

        if encoding == "32fc1":
            cols = int(msg.step // 4) if msg.step else width
            arr = np.frombuffer(buffer, dtype=np.float32).reshape(height, cols)[:, :width]
            return np.array(arr, dtype=np.float32)
    except Exception:
        return None

    return None


def fit_sphere(points: np.ndarray) -> Tuple[np.ndarray, float]:
    """对三维点做最小二乘球面拟合。

    球面方程可以写成：

    x^2 + y^2 + z^2 + D*x + E*y + F*z + G = 0

    程序求出 D/E/F/G 后，就能得到球心和半径。学习者不需要先掌握最小二乘
    的完整推导，只要理解：用很多个深度点共同估计一个最像足球的球面。
    """

    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    A = np.column_stack([x, y, z, np.ones(len(points))])
    b = -(x * x + y * y + z * z)
    solution, *_ = np.linalg.lstsq(A, b, rcond=None)
    D, E, F, G = solution

    center = np.array([-D / 2.0, -E / 2.0, -F / 2.0])
    radius_squared = center.dot(center) - G
    radius = math.sqrt(radius_squared) if radius_squared > 0 else 0.0
    return center, radius


def format_ball_position_summary(payload: Dict[str, Any]) -> str:
    """生成便于终端阅读的足球基座坐标摘要。"""

    if not bool(payload.get("valid", False)):
        return f"invalid reason={payload.get('reason', 'unknown')}"

    return (
        f"x={float(payload.get('x', 0.0)):.3f}m "
        f"y={float(payload.get('y', 0.0)):.3f}m "
        f"z={float(payload.get('z', 0.0)):.3f}m "
        f"distance={float(payload.get('distance', 0.0)):.3f}m "
        f"angle={float(payload.get('angle', 0.0)):.3f}rad "
        f"method={payload.get('method', 'unknown')}"
    )
