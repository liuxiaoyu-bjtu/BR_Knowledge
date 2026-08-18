"""
深度图测距标定探针（U4 单元核心验证脚本）

【源码确认的结论】
  完整 boosteros 包搜索 `distance_m` 仅命中 `types/vision_data.py` 一处定义：
      distance_m: Optional[float] = None  # 距离（如果结合了深度相机）
  且 `Detection.detect()` 在所有构造 DetectionResult 处都不传该字段，
  `to_dict()` 也不输出它。结论：标准检测**不出距离**，distance_m 永远是 None。

  真正的测距要自己读深度图（K1 = 双目深度相机）：
      depth = robot.get_image(img_type="depth")   # AnyImage
      depth_np = depth.to_numpy()                  # (H, W)，uint16(毫米) 或 float32(米)
      region = depth_np[y:y+h, x:x+w]              # 裁剪检测框区域
      valid = region[(region > 0) & np.isfinite(region)]
      dist = float(np.median(valid))              # 深度中位数

【仿真环境是否可用？—— 源码确认：可用】
  SDK 内置两套相机配置，按机型自动切换（booster_robot.py:212）：
    - 实体机器人 : _DEFAULT_CAMERA_CFG  → depth 话题 /boostercamera/head/depth
    - 虚拟/仿真  : _VIRTUAL_ROBOT_CAMERA_CFG → depth 话题 rgbd_camera/depth/image_raw
      判定方式：loco_client.has_simulation_type()（robot_info 含 "Simulation Type"）
  即仿真里同样发布深度图，get_image(img_type="depth") 在 Booster Studio 仿真中可直接取到。
  实测深度图为 uint16，数值范围约 219~5111，单位**毫米**（219mm≈0.22m，5111mm≈5.1m）。
  本脚本对 uint16(毫米) 与 float32(米) 两种 dtype 都做了兼容换算（uint16 自动 /1000）。

用法（把目标放在机器人正前方已知距离）：
    python probe_depth_distance.py default 1.0     # 球，真实距离 1 米
    python probe_depth_distance.py person 1.2      # 人，真实距离 1.2 米

输出：
    - 环境标识（仿真 / 实体机）+ 深度图 encoding/dtype/范围
    - 多帧（默认 20 帧）自算距离的中位数、离散度（验证稳定性）
    - 每个目标的 to_dict()、检测框、深度中位数、换算成米的距离
    - 一行 CALIBRATION ROW，复制贴回即可用于标定
"""
import sys
import json

import numpy as np

# 注意：顶层 boosteros/__init__.py 为空，BoosterRobot 只能从子模块导入
# （from boosteros import BoosterRobot 会 ImportError）
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection


def median_depth_in_box(depth_np, box, depth_h, depth_w, rgb_w, rgb_h):
    """在检测框区域内取深度中位数（过滤无效值 0 / 无穷）。
    若 depth 与 rgb 分辨率不同，按比例把 bbox 映射到 depth 坐标。"""
    x, y, w, h = box.x, box.y, box.width, box.height
    if (depth_w, depth_h) != (rgb_w, rgb_h):
        sx, sy = depth_w / rgb_w, depth_h / rgb_h
        x, y, w, h = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
    x2, y2 = min(x + w, depth_w), min(y + h, depth_h)
    x, y = max(x, 0), max(y, 0)
    region = depth_np[y:y2, x:x2]
    valid = region[(region > 0) & np.isfinite(region)]
    if valid.size == 0:
        return None, 0
    return float(np.median(valid)), int(valid.size)


def detect_env(robot):
    """尽量判定当前是仿真还是实体机（仅用于打印提示）。"""
    for fn in ("_is_virtual_robot", "is_virtual_robot"):
        if hasattr(robot, fn):
            try:
                return "仿真(虚拟机器人)" if getattr(robot, fn)() else "实体机器人"
            except Exception:
                pass
    return "未知（无法自动识别）"


def main():
    model_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    real_m = float(sys.argv[2]) if len(sys.argv) > 2 else None
    n_frames = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    robot = BoosterRobot()
    detector = Detection(model=model_id)

    print(f"\n=== probe_depth_distance | model={model_id} | real_m={real_m} | frames={n_frames} ===")
    print("环境：", detect_env(robot))

    # 先取一帧确认深度图可用与基本规格
    rgb = robot.get_image(img_type="rgb")
    depth = robot.get_image(img_type="depth")
    rgb_np = rgb.to_numpy()
    depth_np = depth.to_numpy()
    rgb_h, rgb_w = rgb_np.shape[:2]
    depth_h, depth_w = depth_np.shape[:2]
    print(f"RGB  : encoding={getattr(rgb,'encoding','?')} size={rgb_w}x{rgb_h} dtype={rgb_np.dtype}")
    print(f"DEPTH: encoding={getattr(depth,'encoding','?')} size={depth_w}x{depth_h} "
          f"dtype={depth_np.dtype} value范围={depth_np.min()}..{depth_np.max()}")
    if (depth_w, depth_h) != (rgb_w, rgb_h):
        print("[注意] depth 与 rgb 分辨率不同，已按比例映射 bbox 坐标。")

    # 多帧采集：对每一帧检测 + 取深度中位数，最后跨帧取中位数与离散度
    per_target_series = {}  # (class_name, idx) -> [dist_m, ...]
    last_results = []
    for _ in range(n_frames):
        rgb = robot.get_image(img_type="rgb")
        depth = robot.get_image(img_type="depth")
        rgb_np = rgb.to_numpy()
        depth_np = depth.to_numpy()
        results = detector.detect(rgb_np, confidence=0.3, iou_threshold=0.45)
        if not results:
            continue
        last_results = results
        for j, r in enumerate(results):
            med, _ = median_depth_in_box(depth_np, r.bbox, depth_h, depth_w, rgb_w, rgb_h)
            if med is None:
                continue
            if depth_np.dtype == np.uint16:
                d_m = med / 1000.0
            elif depth_np.dtype == np.float32:
                d_m = float(med)
            else:
                d_m = float(med)
            per_target_series.setdefault((r.class_name, j), []).append(d_m)

    if not last_results:
        print("\n[结果] 多帧均未检测到任何目标。请确认目标在视野内、距离合适、模型正确。")
        return

    print(f"\n多帧平均自算距离（{n_frames} 帧）：")
    for (cls, j), series in per_target_series.items():
        arr = np.array(series)
        print(f"  目标[{j}] {cls}: median={arr.median():.3f} m  mean={arr.mean():.3f} m  "
              f"min={arr.min():.3f} max={arr.max():.3f} (n={len(arr)})")

    print("\n--- 最后一帧目标详情 ---")
    for i, r in enumerate(last_results, 1):
        med, n = median_depth_in_box(depth_np, r.bbox, depth_h, depth_w, rgb_w, rgb_h)
        if depth_np.dtype == np.uint16:
            dist_m = med / 1000.0 if med is not None else None
            unit_note = "uint16(假定毫米)/1000"
        elif depth_np.dtype == np.float32:
            dist_m = med if med is not None else None
            unit_note = "float32(假定米)"
        else:
            dist_m = med
            unit_note = "未知 dtype，未换算"
        print(f"\n--- 目标 {i} 的 to_dict() ---")
        print(json.dumps(r.to_dict(), indent=2, default=str))
        print(f"  深度中位数(原始)={med}  自算距离={dist_m} m  ({unit_note})  有效像素={n}")
        print(f"CALIBRATION ROW | model={model_id} | real_m={real_m} | "
              f"class={r.class_name} | conf={r.confidence:.3f} | "
              f"self_dist_m={dist_m} | bbox=({r.bbox.width}x{r.bbox.height}) | "
              f"area={r.bbox.area} | depth_dtype={depth_np.dtype}")

    try:
        detector.plot(rgb_np, last_results).save("probe_depth_distance_result.jpg")
        print("\n已保存 detect 结果图：probe_depth_distance_result.jpg")
    except Exception as e:
        print(f"\n[提示] 结果图保存失败（不影响标定）：{e}")


if __name__ == "__main__":
    main()
