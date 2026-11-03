"""K1静态足球坐标诊断。只使用公开OS SDK取数，不发送运动或踢球命令。

测试假设：RGB/深度同像素配准、深度值表示光轴Z、比例由depth_scale_m指定。
这些假设不会因计算成功而自动成立。结果是目标TF帧下的候选球心。
Python >=3.10，numpy；真实运行另需已有BoosterOS SDK视觉环境。
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime
import importlib.metadata
import inspect
import json
import math
from pathlib import Path
import shutil
import threading
import time
import traceback
import zipfile

import numpy as np

_SESSION_ROBOT = None
_SESSION_DETECTOR = None
VERSION = "0.1.0"


def timestamp(obj):
    value = getattr(obj, "timestamp", None)
    if value is None:
        value = getattr(getattr(obj, "header", None), "timestamp", None)
    if value is None or not math.isfinite(float(value)):
        raise ValueError("缺少有限的传感器时间戳")
    return float(value)


def transform_point(matrix, point):
    """M按get_transform(target, source)请求方向使用；不根据返回标签自行求逆。"""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise ValueError("TF不是有限4×4矩阵")
    r = matrix[:3, :3]
    if (not np.allclose(matrix[3], [0, 0, 0, 1])
            or not np.allclose(r.T @ r, np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(r), 1, atol=1e-4)):
        raise ValueError("TF不是刚体变换")
    point = np.asarray(point, dtype=float)
    if point.shape != (3,) or not np.isfinite(point).all():
        raise ValueError("三维点无效")
    return (matrix @ np.r_[point, 1.0])[:3]


def sphere_from_depth(depth, rgb_size, bbox, k, distortion, distortion_model, scale_m):
    """框内中心椭圆取点→相机三维点→球面拟合；不把可见表面当球心。"""
    if not math.isfinite(scale_m) or scale_m <= 0:
        raise ValueError("深度比例必须为正且有限")
    depth = np.asarray(depth)
    width, height = rgb_size
    if depth.ndim != 2 or depth.shape != (height, width):
        raise ValueError("RGB与深度尺寸不同；本工具不按比例缩框冒充配准")
    k = np.asarray(k, dtype=float).reshape(3, 3)
    if not np.isfinite(k).all() or k[0, 0] <= 0 or k[1, 1] <= 0:
        raise ValueError("相机内参无效")
    x, y, w, h = map(float, bbox)
    if (not np.isfinite([x, y, w, h]).all() or x < 0 or y < 0 or w <= 2 or h <= 2
            or x + w > width or y + h > height):
        raise ValueError("检测框越界或太小")
    u, v = np.meshgrid(np.arange(math.ceil(x), math.floor(x + w)),
                       np.arange(math.ceil(y), math.floor(y + h)))
    raw = depth[v, u].astype(float)
    ellipse = ((u - x - w / 2) / (0.35 * w)) ** 2 + ((v - y - h / 2) / (0.35 * h)) ** 2 <= 1
    valid = ellipse & np.isfinite(raw) & (raw > 0) & (raw != 65535)
    u, v, raw = u[valid], v[valid], raw[valid]
    stats = {"ellipse_pixels": int(ellipse.sum()), "valid_points": int(raw.size),
             "invalid_raw_hypothesis": [0, 65535]}
    if raw.size < 30:
        raise ValueError("足球框内有效深度不足30点")
    stats.update(raw_median=float(np.median(raw)), raw_min=float(raw.min()), raw_max=float(raw.max()))
    # 限制计算量；保持各点原来的像素和深度对应。
    ids = np.linspace(0, raw.size - 1, min(raw.size, 12000)).astype(int)
    uv = np.column_stack([u[ids], v[ids]]).astype(float)
    d = np.asarray(distortion, dtype=float).ravel()
    if not np.isfinite(d).all():
        raise ValueError("畸变参数无效")
    if d.size and np.any(np.abs(d) > 1e-10):
        import cv2
        if distortion_model in ("plumb_bob", "rational_polynomial"):
            xy = cv2.undistortPoints(uv[:, None, :], k, d).reshape(-1, 2)
        elif distortion_model == "equidistant" and d.size == 4:
            xy = cv2.fisheye.undistortPoints(uv[:, None, :], k, d).reshape(-1, 2)
        else:
            raise ValueError("不支持的非零畸变模型：" + str(distortion_model))
        rays = np.column_stack([xy, np.ones(len(xy))])
    else:
        rays = np.column_stack([uv, np.ones(len(uv))]) @ np.linalg.inv(k).T
        rays /= rays[:, 2:3]
    # 本次假设原始深度是光轴Z；若为沿射线量程，此式需要修改。
    points = rays * (raw[ids] * scale_m)[:, None]
    surface = np.median(points, axis=0)
    # 平移到点云附近后拟合，减少数值尺度的影响。
    local = points - surface
    a = np.column_stack([2 * local, np.ones(len(local))])
    solution, _, rank, singular = np.linalg.lstsq(a, (local ** 2).sum(axis=1), rcond=None)
    if rank < 4:
        stats.update(center_camera_m=None, surface_sample_median_camera_m=surface.tolist(),
                     sphere_error="点云退化，无法拟合球心；可能取到了平面")
        return stats
    radius2 = float(solution[3] + solution[:3] @ solution[:3])
    if radius2 <= 0:
        raise ValueError("球面拟合半径无效")
    center, radius = solution[:3] + surface, math.sqrt(radius2)
    residual = np.linalg.norm(points - center, axis=1) - radius
    if not np.isfinite(center).all() or not math.isfinite(radius):
        raise ValueError("球面拟合产生非有限结果")
    stats.update(center_camera_m=center.tolist(), fitted_radius_m=radius,
                 sphere_rms_m=float(np.sqrt(np.mean(residual ** 2))),
                 surface_sample_median_camera_m=surface.tolist(),
                 sampled_points=int(len(points)), singular_values=singular.tolist())
    return stats


def _capture_pair(robot, camera_id, timeout_s):
    """先取RGB/深度再推理；订阅仅用于此次快照，退出前取消。"""
    buffers = {"rgb": deque(maxlen=32), "depth": deque(maxlen=32)}
    condition, subscriptions, errors = threading.Condition(), [], []

    def callback(kind, image):
        try:
            item = (timestamp(image), time.monotonic(), image)
            with condition:
                buffers[kind].append(item)
                condition.notify_all()
        except Exception as exc:
            with condition:
                if len(errors) < 20:
                    errors.append(f"{kind}: {exc}")

    rgb, depth = None, None
    try:
        for kind in buffers:
            subscriptions.append(robot.subscribe_image(lambda image, kind=kind: callback(kind, image),
                camera_id=camera_id, img_type=kind, queue_size=1, overflow="drop_oldest"))
        deadline = time.monotonic() + timeout_s
        with condition:
            while time.monotonic() < deadline:
                rgb = buffers["rgb"][-1] if buffers["rgb"] else None
                depth = min(buffers["depth"], key=lambda item: abs(item[0] - rgb[0]), default=None) if rgb else None
                if rgb and depth and abs(rgb[0] - depth[0]) <= 0.12:
                    break
                condition.wait(min(0.1, max(0, deadline - time.monotonic())))
    finally:
        for subscription in subscriptions:
            try:
                subscription.unsubscribe()
            except Exception as exc:
                errors.append("unsubscribe: " + str(exc))
    if rgb is None:
        raise RuntimeError("等待RGB超时；回调记录：" + repr(errors))
    return rgb, depth, errors


def _meta(image):
    return {"timestamp": timestamp(image), "frame_id": image.header.frame_id,
            "width": image.width, "height": image.height,
            "encoding": getattr(image, "encoding", None)}


def _clean(value):
    if isinstance(value, np.ndarray):
        return _clean(value.tolist())
    if isinstance(value, np.generic):
        return _clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def run_probe(robot=None, detector=None, *, camera_id="head", target_frame="trunk",
              depth_scale_m=0.001, known_xy=None, ball_radius_m=None, note="",
              output_root="足球坐标测试结果", timeout_s=6.0):
    """一次静态快照诊断；返回报告，自动保存原始数据和ZIP。无教师JSON要求。"""
    global _SESSION_ROBOT, _SESSION_DETECTOR
    if not math.isfinite(depth_scale_m) or depth_scale_m <= 0 or not 0 < timeout_s <= 30:
        raise ValueError("depth_scale_m必须为正有限数，timeout_s须为0到30秒")
    if known_xy is not None and (len(known_xy) != 2 or not np.isfinite(known_xy).all()):
        raise ValueError("known_xy须为有限的(x,y)，单位米")
    if ball_radius_m is not None and (not math.isfinite(ball_radius_m) or ball_radius_m <= 0):
        raise ValueError("球半径须为正有限数")
    folder = Path(output_root).resolve() / datetime.now().strftime("球位_%Y%m%d_%H%M%S_%f")
    folder.mkdir(parents=True, exist_ok=False)
    report = {"version": VERSION, "created_at": datetime.now().astimezone().isoformat(),
              "note": note, "status": "started", "output_dir": str(folder), "control_input_verified": False,
              "assumptions": {"robot_head_ball_static": True, "rgb_depth_same_pixel_hypothesis": True,
                  "depth_is_optical_Z_hypothesis": True, "depth_scale_m_hypothesis": depth_scale_m,
                  "target_frame": target_frame, "camera_id": camera_id},
              "known_xy_m": known_xy, "measured_ball_radius_m": ball_radius_m,
              "candidate_center_target_m": None, "warnings": [], "stages": []}
    print("静态只读测试：不发送动作。深度比例、同像素配准及光轴Z均按假设记录。", flush=True)
    try:
        if robot is None:
            if _SESSION_ROBOT is None:
                from boosteros.robots.booster import BoosterRobot
                _SESSION_ROBOT = BoosterRobot()
            robot = _SESSION_ROBOT
        if detector is None:
            if _SESSION_DETECTOR is None:
                from boosteros.brain import Detection
                _SESSION_DETECTOR = Detection(model="soccer")
            detector = _SESSION_DETECTOR
        try:
            report["sdk_version"] = importlib.metadata.version("boosteros")
        except importlib.metadata.PackageNotFoundError:
            report["sdk_version"] = "unknown"
        report["stages"].append("capture")
        rgb, depth, errors = _capture_pair(robot, camera_id, timeout_s)
        report["warnings"].extend(errors)
        image = rgb[2]
        report["rgb"] = _meta(image)
        rgb_np = np.array(image.to_numpy(), copy=True)
        np.save(folder / "rgb_raw.npy", rgb_np)
        image.save(str(folder / "rgb.png"))
        if depth:
            dep = np.array(depth[2].to_numpy(), copy=True)
            np.save(folder / "depth_raw.npy", dep)
            report["depth"] = {**_meta(depth[2]), "dtype": str(dep.dtype),
                               "shape": list(dep.shape), "receipt_gap_s": depth[1] - rgb[1]}
            finite = dep[np.isfinite(dep)]
            report["depth"].update(raw_min=float(finite.min()) if finite.size else None,
                                   raw_max=float(finite.max()) if finite.size else None)
            report["rgb_depth_skew_s"] = depth[0] - rgb[0]
            if abs(depth[0] - rgb[0]) > 0.12:
                report["warnings"].append("RGB/深度时间差超过0.12秒；本次仅静态诊断，不能据此用于运动")
            if depth[2].header.frame_id != image.header.frame_id:
                report["warnings"].append("RGB/深度帧名不同；同像素配准假设尤其需要核对")
        else:
            dep = None
            report["warnings"].append("本次未收到深度，仍保存检测与TF")
        report["stages"].append("camera_info_and_tf_before_detection")
        info = robot.get_camera_info(camera_id=camera_id)
        report["camera_info"] = {"frame_id": info.header.frame_id, "width": info.width,
            "height": info.height, "k": np.asarray(info.k).tolist(), "d": list(info.d),
            "distortion_model": getattr(info, "distortion_model", "plumb_bob")}
        source = image.header.frame_id
        tf = robot.get_transform(target_frame=target_frame, source_frame=source)
        matrix = np.asarray(tf.to_matrix(), dtype=float)
        transform_point(matrix, [0, 0, 0])  # 检查矩阵，但不验证其物理方向。
        report["transform"] = {"requested_source": source, "requested_target": target_frame,
            "returned_source_label": getattr(tf, "source_frame", None),
            "returned_target_label": getattr(tf, "target_frame", None), "matrix": matrix,
            "timestamp": timestamp(tf), "tf_minus_rgb_s": timestamp(tf) - rgb[0],
            "camera_origin_in_target_m": matrix[:3, 3], "camera_axes_in_target": matrix[:3, :3]}
        if abs(timestamp(tf) - rgb[0]) > 0.12:
            report["warnings"].append("TF与RGB时间差超过0.12秒；保持静止核对，不能延伸为运动时有效")
        print("TF请求：", source, "→", target_frame, "\n", matrix, flush=True)
        try:
            reverse = robot.get_transform(target_frame=source, source_frame=target_frame)
            report["reverse_transform"] = {"matrix": reverse.to_matrix(), "timestamp": timestamp(reverse),
                "roundtrip_max_error": float(np.max(np.abs(np.asarray(reverse.to_matrix()) @ matrix - np.eye(4))))}
        except Exception as exc:
            report["warnings"].append("反向TF查询失败，不影响保留正向查询：" + str(exc))
        try:
            definitions = inspect.getsource(robot.get_transform) + "\n" + inspect.getsource(type(tf))
            (folder / "TF本机公开实现.txt").write_text(definitions, encoding="utf-8")
        except (OSError, TypeError):
            pass
        report["stages"].append("detection")
        started = time.monotonic()
        results = detector.detect(rgb_np, confidence=0.4)
        report["detection_elapsed_s"] = time.monotonic() - started
        report["detections"] = [dict(class_name=r.class_name, confidence=float(r.confidence),
            bbox=[r.bbox.x, r.bbox.y, r.bbox.width, r.bbox.height], distance_m=getattr(r, "distance_m", None))
            for r in results]
        balls = [(i, r) for i, r in enumerate(report["detections"]) if r["class_name"] == "Ball"
                 and math.isfinite(r["confidence"]) and r["confidence"] >= 0.4]
        if not balls:
            report["status"] = "no_ball"
        else:
            selected, ball = max(balls, key=lambda pair: pair[1]["confidence"])
            report["selected_detection_index"] = selected
            report["selected_ball"] = ball
            if len(balls) > 1:
                report["warnings"].append("有多颗球；本次按置信度选球，请核对原图中的选中序号")
            try:
                detector.plot(rgb_np, [results[selected]], as_image=True).save(str(folder / "selected_ball.png"))
            except Exception as exc:
                report["warnings"].append("检测标注图保存失败：" + str(exc))
            print("检测：", ball, flush=True)
            report["stages"].append("metric_localization")
            if dep is None:
                raise ValueError("缺少深度，2D框＋TF不能得到米制球位")
            if ((info.width, info.height) != (image.width, image.height)
                    or info.header.frame_id != source):
                raise ValueError("内参尺寸/帧与RGB不一致")
            fit = sphere_from_depth(dep, (image.width, image.height), ball["bbox"], info.k, info.d,
                                    report["camera_info"]["distortion_model"], depth_scale_m)
            report["sphere_fit"] = fit
            report["surface_sample_median_target_m"] = transform_point(matrix, fit["surface_sample_median_camera_m"])
            if fit["center_camera_m"] is None:
                raise ValueError(fit["sphere_error"] + "；仅保留表面点，不冒充球心")
            center = transform_point(matrix, fit["center_camera_m"])
            report["candidate_center_target_m"] = center
            report["status"] = "candidate_only"
            report["snapshot_receipt_age_at_result_s"] = time.monotonic() - rgb[1]
            if known_xy is not None:
                error = center[:2] - np.asarray(known_xy)
                report["measurement_comparison"] = {"error_xy_m": error,
                                                      "planar_error_m": float(np.linalg.norm(error))}
            if ball_radius_m is not None:
                report["sphere_fit"]["radius_error_m"] = fit["fitted_radius_m"] - ball_radius_m
            if not 0.02 <= fit["fitted_radius_m"] <= 0.25 or fit["sphere_rms_m"] > 0.02:
                report["warnings"].append("球面半径或残差异常；候选值可能取到背景，须检查原图与深度")
            print(f"候选球心[{target_frame}]：x={center[0]:+.3f}, y={center[1]:+.3f}, z={center[2]:+.3f} m", flush=True)
            print(f"拟合半径={fit['fitted_radius_m']:.3f} m，球面RMS={fit['sphere_rms_m']:.4f} m", flush=True)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    except Exception as exc:
        report["status"], report["error"] = "error", f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print(report["error"], flush=True)
    finally:
        report = _clean(report)
        shutil.copyfile(Path(__file__), folder / "测试脚本.py")
        (folder / "原始记录.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        lines = ["# 足球坐标静态诊断", "", f"状态：{report['status']}", f"备注：{note}",
                 f"目标帧：{target_frame}", f"深度比例假设：{depth_scale_m}米/原始单位", "",
                 "本次仅查询数据，未调用SoccerKickManager、头部、速度或模式控制。",
                 "候选坐标仍待深度单位/配准、TF物理方向和控制原点核对。", "",
                 f"候选球心：{report['candidate_center_target_m']}",
                 f"卷尺输入xy：{report['known_xy_m']}",
                 f"误差：{report.get('measurement_comparison')}",
                 f"异常：{report.get('error')}", "", "提示：", *["- " + w for w in report["warnings"]]]
        (folder / "采集汇总.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
        archive = folder.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(folder.iterdir()):
                if path.is_file():
                    z.write(path, folder.name + "/" + path.name)
        print("记录目录：", folder, "\n结果ZIP：", archive, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description="K1静态检测→深度三维球心→TF候选坐标，只读")
    parser.add_argument("--depth-scale", type=float, default=0.001, help="比例假设；默认0.001，不按dtype猜单位")
    parser.add_argument("--known-xy", type=float, nargs=2, help="卷尺量得的目标帧xy，单位米")
    parser.add_argument("--ball-radius", type=float, help="实测球半径，单位米，用于比较")
    parser.add_argument("--camera", default="head")
    parser.add_argument("--target", default="trunk")
    parser.add_argument("--note", default="")
    parser.add_argument("--output", default="足球坐标测试结果")
    args = parser.parse_args()
    run_probe(camera_id=args.camera, target_frame=args.target, depth_scale_m=args.depth_scale,
              known_xy=args.known_xy, ball_radius_m=args.ball_radius, note=args.note, output_root=args.output)


if __name__ == "__main__":
    main()
