"""K1 足球单目几何坐标测试；沿用工训课 chapter12 的射线与地面求交。

OS SDK 负责 RGB、检测、内参和 TF；本文件负责像素到米的几何计算。
默认姿态来源是相机到 trunk 的完整 TF，须输入当前镜头中心离地高度。
只读取数据，不创建 SoccerKickManager 或发送运动命令。
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import shutil
import threading
import time
import traceback
import zipfile

import numpy as np

VERSION = "0.2.0-geometry"
_ROBOT = None
_DETECTOR = None

# 原工训课 ball_localization_utils.DEFAULT_T_CAM_TO_HEAD，数值原样保留。
# 仅在显式提供旧头部位姿时使用；完整 optical→trunk TF 已含相机外参。
LEGACY_T_CAM_TO_HEAD = np.array([
    [0.0204047617, 0.00377522805, 0.999784708, -0.00454888586],
    [-0.999754429, -0.00857020356, 0.0204365067, 0.0473468825],
    [0.00864551123, -0.999956131, 0.00359942787, -0.00659073936],
    [0.0, 0.0, 0.0, 1.0],
])


def rigid_matrix(value):
    matrix = np.asarray(value, dtype=float)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise ValueError("姿态须为有限的4×4矩阵")
    rotation = matrix[:3, :3]
    if (not np.allclose(matrix[3], [0, 0, 0, 1], atol=1e-6)
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(rotation), 1, atol=1e-4)):
        raise ValueError("姿态不是刚体变换")
    return matrix.copy()


def choose_ball_pixel(bbox, *, bottom_offset_ratio=0.10):
    """SDK 框为(x,y,width,height)；沿用旧版底部向上10%的取点规则。"""
    x, y, width, height = map(float, bbox)
    if not np.isfinite([x, y, width, height, bottom_offset_ratio]).all():
        raise ValueError("检测框或取点比例含非有限数")
    if width <= 0 or height <= 0 or not 0 <= bottom_offset_ratio <= 1:
        raise ValueError("检测框宽高须为正，取点比例须在0到1之间")
    return x + width / 2, y + height - bottom_offset_ratio * max(1.0, height)


def pixel_to_ray_camera(u, v, k, *, distortion=(), distortion_model="plumb_bob"):
    """无畸变时与旧版针孔射线相同；非零畸变先用实际内参去畸变。"""
    k = np.asarray(k, dtype=float).reshape(3, 3)
    if (not np.isfinite(k).all() or k[0, 0] <= 0 or k[1, 1] <= 0
            or not np.allclose(k[2], [0, 0, 1]) or abs(k[0, 1]) > 1e-8
            or abs(k[1, 0]) > 1e-8 or not np.isfinite([u, v]).all()):
        raise ValueError("像素或相机内参无效；需标准针孔K矩阵")
    d = np.asarray(distortion, dtype=float).ravel()
    if not np.isfinite(d).all():
        raise ValueError("畸变参数无效")
    if d.size and np.any(np.abs(d) > 1e-10):
        import cv2
        uv = np.array([[[u, v]]], dtype=float)
        if distortion_model in ("plumb_bob", "rational_polynomial"):
            xy = cv2.undistortPoints(uv, k, d).reshape(2)
        elif distortion_model == "equidistant" and d.size == 4:
            xy = cv2.fisheye.undistortPoints(uv, k, d).reshape(2)
        else:
            raise ValueError("不支持的非零畸变模型：" + str(distortion_model))
        ray = np.r_[xy, 1.0]
    else:
        ray = np.array([(u - k[0, 2]) / k[0, 0], (v - k[1, 2]) / k[1, 1], 1.0])
    if not np.isfinite(ray).all():
        raise ValueError("反投影射线无效")
    return ray / (np.linalg.norm(ray) + 1e-9)


def ray_to_ground_base(u, v, *, k, T_base_camera, distortion=(),
                       distortion_model="plumb_bob"):
    """沿用旧版算法：P=O+sD，s=-O.z/D.z，地面为 base 中的 z=0。

    base 的 x前/y左/z上，原点在地面。身体原点若在躯干，须先补齐地面高度。
    输出接地附近像素对应的地面位置估计，不是深度球面拟合球心。
    """
    matrix = rigid_matrix(T_base_camera)
    ray = pixel_to_ray_camera(u, v, k, distortion=distortion, distortion_model=distortion_model)
    origin = matrix[:3, 3]
    direction = matrix[:3, :3] @ ray
    direction /= np.linalg.norm(direction) + 1e-9
    if origin[2] <= 0:
        raise ValueError("相机高度必须位于地面之上")
    if abs(direction[2]) < 1e-6:
        raise ValueError("射线近似平行地面")
    scale = -origin[2] / direction[2]
    if scale <= 0:
        raise ValueError("射线朝向地面上方，交点不在相机前方")
    point = origin + scale * direction
    if not np.isfinite(point).all():
        raise ValueError("求交结果无效")
    return {"point_base_m": point.tolist(), "ray_camera": ray.tolist(),
            "camera_origin_base_m": origin.tolist(), "direction_base": direction.tolist(),
            "ray_length_m": float(scale), "distance_xy_m": float(np.linalg.norm(point[:2])),
            "bearing_rad": math.atan2(point[1], point[0])}


def legacy_camera_pose(T_head_to_base, *, T_cam_to_head=None, T_compensation=None):
    """原版组合顺序原样保留；head_to_base 须与旧相机外参使用同一头部帧。"""
    return (rigid_matrix(T_head_to_base)
            @ rigid_matrix(np.eye(4) if T_compensation is None else T_compensation)
            @ rigid_matrix(LEGACY_T_CAM_TO_HEAD if T_cam_to_head is None else T_cam_to_head))


def ground_pose_from_body_tf(T_body_camera, camera_height_m):
    """静止直立、身体z轴竖直时，将身体TF的z原点平移到地面；x/y原点保持。

    camera_height_m 是镜头光心离地垂直高度，不是整机身高。头部转动已包含在TF。
    """
    if not math.isfinite(camera_height_m) or camera_height_m <= 0:
        raise ValueError("请填写当前姿态下镜头中心到地面的垂直高度（米）")
    matrix = rigid_matrix(T_body_camera)
    body_origin_height_m = camera_height_m - matrix[2, 3]
    matrix[2, 3] += body_origin_height_m
    return matrix, float(body_origin_height_m)


def _timestamp(obj):
    value = getattr(obj, "timestamp", None)
    if value is None:
        value = getattr(getattr(obj, "header", None), "timestamp", None)
    return float(value) if value is not None and math.isfinite(float(value)) else None


def _rgb_snapshot(robot, camera_id, timeout_s):
    event, received = threading.Event(), []
    def callback(image):
        if not event.is_set():
            received.append((image, time.monotonic()))
            event.set()
    subscription = robot.subscribe_image(callback, camera_id=camera_id, img_type="rgb",
                                         queue_size=1, overflow="drop_oldest")
    try:
        if not event.wait(timeout_s):
            raise TimeoutError("等待一张新RGB图像超时")
        return received[0]
    finally:
        subscription.unsubscribe()


def _clean(value):
    if isinstance(value, np.ndarray):
        return _clean(value.tolist())
    if isinstance(value, np.generic):
        return _clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    return value


def run_geometry_probe(robot=None, detector=None, *, camera_height_m=None,
                       head_to_ground=None, T_cam_to_head=None, T_compensation=None,
                       camera_id="head", target_frame="trunk", confidence=0.5,
                       bottom_offset_ratio=0.10, known_xy=None, note="",
                       output_root="足球几何坐标测试结果", timeout_s=6.0):
    """一次静止快照。常用调用：run_geometry_probe(camera_height_m=实测镜头高度)。

    若显式传入 head_to_ground，则使用旧版头部位姿与外参组合，绕过身体TF查询。
    此矩阵须由已有可信数据提供；不能用单位阵冒充头部相对身体的姿态。
    known_xy 仅供比较，绝不用于修改高度、姿态或计算结果。
    """
    global _ROBOT, _DETECTOR
    if head_to_ground is None:
        if camera_height_m is None:
            raise ValueError("请先设置 camera_height_m：当前镜头中心到地面的垂直高度，单位米")
        if T_cam_to_head is not None or T_compensation is not None:
            raise ValueError("完整相机→身体TF已含外参，不应重复添加旧相机外参或补偿")
        ground_pose_from_body_tf(np.eye(4), camera_height_m)
    else:
        if camera_height_m is not None:
            raise ValueError("head_to_ground已含离地高度；请勿同时填写camera_height_m")
        legacy_camera_pose(head_to_ground, T_cam_to_head=T_cam_to_head, T_compensation=T_compensation)
    if (not math.isfinite(timeout_s) or not 0 < timeout_s <= 30
            or not math.isfinite(confidence) or not 0 <= confidence <= 1
            or not math.isfinite(bottom_offset_ratio) or not 0 <= bottom_offset_ratio <= 1):
        raise ValueError("超时须在0—30秒，置信度及取点比例须在0—1")
    if known_xy is not None and (np.asarray(known_xy).shape != (2,) or not np.isfinite(known_xy).all()):
        raise ValueError("known_xy须为相同原点/轴向下的(x,y)，单位米")
    folder = Path(output_root).resolve() / datetime.now().strftime("几何球位_%Y%m%d_%H%M%S_%f")
    folder.mkdir(parents=True, exist_ok=False)
    report = {"version": VERSION, "created_at": datetime.now().astimezone().isoformat(),
              "status": "started", "note": note, "output_dir": str(folder),
              "method": "legacy_pixel_ray_ground", "control_input_verified": False,
              "kick_input_preview": None, "warnings": [], "known_xy_m": known_xy,
              "assumptions": ["机器人、头部与球在取图和姿态查询期间静止",
                              "平整地面；身体z轴竖直，x向前、y向左",
                              "框底向上10%附近像素近似接地点；该近似待现场核对"],
              "bottom_offset_ratio": bottom_offset_ratio}
    print("单目几何静态测试：像素→射线→地面；不发送动作。", flush=True)
    try:
        if robot is None:
            if _ROBOT is None:
                from boosteros.robots.booster import BoosterRobot
                _ROBOT = BoosterRobot()
            robot = _ROBOT
        if detector is None:
            if _DETECTOR is None:
                from boosteros.brain import Detection
                _DETECTOR = Detection(model="soccer")
            detector = _DETECTOR
        image, receipt_time = _rgb_snapshot(robot, camera_id, timeout_s)
        rgb = np.array(image.to_numpy(), copy=True)
        np.save(folder / "rgb_raw.npy", rgb)
        image.save(str(folder / "rgb.png"))
        source = image.header.frame_id
        report["rgb"] = {"frame_id": source, "width": image.width, "height": image.height,
                         "timestamp": _timestamp(image), "encoding": getattr(image, "encoding", None)}
        info = robot.get_camera_info(camera_id=camera_id)
        report["camera_info"] = {"frame_id": info.header.frame_id, "width": info.width,
            "height": info.height, "k": np.asarray(info.k), "d": list(info.d),
            "distortion_model": getattr(info, "distortion_model", "plumb_bob")}
        if ((info.width, info.height) != (image.width, image.height) or info.header.frame_id != source):
            raise ValueError("内参尺寸/帧与RGB不一致；不能直接套用或按比例猜测")
        if head_to_ground is None:
            report["list_frames"] = list(robot.list_frames())
            report["requested_transform"] = {"target": target_frame, "source": source}
            if target_frame not in report["list_frames"] or source not in report["list_frames"]:
                raise ValueError("当前帧列表缺少身体目标帧或图像光学帧；头部帧间TF不足以确定身体姿态。"
                                 "可在取得可信的旧head_to_ground位姿后显式传入，不能编造身体TF。")
            tf = robot.get_transform(target_frame=target_frame, source_frame=source)
            body_camera = rigid_matrix(tf.to_matrix())
            ground_camera, body_height = ground_pose_from_body_tf(body_camera, camera_height_m)
            report["pose"] = {"source": "sdk_optical_to_body_tf", "body_frame": target_frame,
                "T_body_camera": body_camera, "T_ground_camera": ground_camera,
                "camera_height_m": camera_height_m, "body_origin_height_m": body_height,
                "timestamp": _timestamp(tf), "returned_source_label": getattr(tf, "source_frame", None),
                "returned_target_label": getattr(tf, "target_frame", None)}
            if _timestamp(tf) is not None and _timestamp(image) is not None:
                report["pose"]["tf_minus_rgb_s"] = _timestamp(tf) - _timestamp(image)
            # 按请求方向使用矩阵；现场旧版本返回的source/target标签可能与请求相反。
        else:
            ground_camera = legacy_camera_pose(head_to_ground, T_cam_to_head=T_cam_to_head,
                                               T_compensation=T_compensation)
            report["pose"] = {"source": "explicit_legacy_head_to_ground", "T_ground_camera": ground_camera,
                "T_head_to_ground": head_to_ground,
                "T_cam_to_head": LEGACY_T_CAM_TO_HEAD if T_cam_to_head is None else T_cam_to_head,
                "T_compensation": np.eye(4) if T_compensation is None else T_compensation}
        started = time.monotonic()
        results = list(detector.detect(rgb, confidence=confidence))
        report["detection_elapsed_s"] = time.monotonic() - started
        report["detections"] = [{"class_name": r.class_name, "confidence": float(r.confidence),
            "bbox": [r.bbox.x, r.bbox.y, r.bbox.width, r.bbox.height]} for r in results]
        balls = [(index, item) for index, item in enumerate(report["detections"])
                 if item["class_name"] == "Ball" and math.isfinite(item["confidence"])
                 and item["confidence"] >= confidence]
        if not balls:
            report["status"] = "no_ball"
        else:
            index, ball = max(balls, key=lambda pair: pair[1]["confidence"])
            report["selected_ball"] = ball
            if len(balls) > 1:
                report["warnings"].append("多球时本测试按置信度选球，请检查标注图")
            x, y, width, height = ball["bbox"]
            if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
                raise ValueError("检测框超出原图；拒绝计算")
            u, v = choose_ball_pixel(ball["bbox"], bottom_offset_ratio=bottom_offset_ratio)
            report["pixel_uv"] = [u, v]
            geometry = ray_to_ground_base(u, v, k=info.k, T_base_camera=ground_camera,
                distortion=info.d, distortion_model=report["camera_info"]["distortion_model"])
            report["geometry"] = geometry
            px, py, pz = geometry["point_base_m"]
            # 沿用旧程序范围；这是异常值筛查，不代表测量精度或控制验证。
            if not (0 <= px <= 10 and abs(py) <= 5):
                report["status"] = "out_of_legacy_range"
            else:
                report["status"] = "geometry_candidate"
                report["kick_input_preview"] = {"x": px, "y": py}
                if head_to_ground is None:
                    report["point_body_m"] = [px, py, pz - body_height]
                if known_xy is not None:
                    error = np.array([px, py]) - known_xy
                    report["measurement_comparison"] = {"error_xy_m": error,
                                                         "planar_error_m": float(np.linalg.norm(error))}
            try:
                detector.plot(rgb, [results[index]], as_image=True).save(str(folder / "selected_ball.png"))
                from PIL import Image, ImageDraw
                marked = Image.open(folder / "selected_ball.png").convert("RGB")
                draw = ImageDraw.Draw(marked)
                draw.ellipse((u - 3, v - 3, u + 3, v + 3), outline="red", width=1)
                marked.save(folder / "selected_ball.png")
            except Exception as exc:
                report["warnings"].append("标注图保存失败：" + str(exc))
            print(f"取点(u,v)=({u:.2f},{v:.2f})；候选x={px:+.3f}m，y={py:+.3f}m", flush=True)
        report["snapshot_receipt_age_at_result_s"] = time.monotonic() - receipt_time
        report["warnings"].append("静态计算成功不代表动态取数同步或踢球管理器原点已确认")
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    except Exception as exc:
        report["status"], report["error"] = "error", f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print(report["error"], flush=True)
    finally:
        report = _clean(report)
        shutil.copyfile(__file__, folder / "测试脚本.py")
        (folder / "原始记录.json").write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                                       allow_nan=False), encoding="utf-8")
        lines = ["# K1单目几何坐标测试", "", f"状态：{report['status']}",
                 f"备注：{note}", f"踢球参数预览：{report['kick_input_preview']}",
                 f"卷尺输入xy：{known_xy}", f"比较：{report.get('measurement_comparison')}",
                 f"异常：{report.get('error')}", "",
                 "沿用工训课底部取点、针孔射线、地面求交；OS SDK取数，未发送运动命令。",
                 "x/y为所选身体原点的地面投影参考，尚未确认与踢球管理器原点一致。", "",
                 *["- " + warning for warning in report["warnings"]]]
        (folder / "采集汇总.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
        archive = folder.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
            for path in sorted(folder.iterdir()):
                if path.is_file():
                    package.write(path, folder.name + "/" + path.name)
        print(f"结果目录：{folder}\n结果ZIP：{archive}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description="工训课单目几何→OS SDK静态只读测试")
    parser.add_argument("--camera-height", type=float, required=True, help="镜头光心离地垂直高度，米")
    parser.add_argument("--target", default="trunk")
    parser.add_argument("--known-xy", type=float, nargs=2, help="同原点/轴向的实测地面xy，仅供比较")
    parser.add_argument("--note", default="")
    parser.add_argument("--output", default="足球几何坐标测试结果")
    args = parser.parse_args()
    run_geometry_probe(camera_height_m=args.camera_height, target_frame=args.target,
                       known_xy=args.known_xy, note=args.note, output_root=args.output)


if __name__ == "__main__":
    main()
