"""离线复算用户已采集的快照并画诊断图；不调用机器人。"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BASE = ROOT / "04-shared/sdk-tests/足球坐标只读测试"
RAW = BASE / "K1足球坐标_测试工具包/足球坐标测试结果/球位_20261103_113057_624030"
OUT = BASE / "结果回读"
OUT.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("probe_review", BASE / "probe_ball_coordinates.py")
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)

report = json.loads((RAW / "原始记录.json").read_text(encoding="utf-8"))
depth, rgb = np.load(RAW / "depth_raw.npy"), np.load(RAW / "rgb_raw.npy")
box = report["selected_ball"]["bbox"]
width, height = report["rgb"]["width"], report["rgb"]["height"]
info = report["camera_info"]
fit = probe.sphere_from_depth(depth, (width, height), box, info["k"], info["d"], info["distortion_model"], .001)
matrix = np.array(report["transform"]["matrix"])
diagnostic = probe.transform_point(matrix, fit["center_camera_m"])
np.testing.assert_allclose(diagnostic, report["candidate_center_target_m"], atol=1e-10)
np.testing.assert_allclose(fit["sphere_rms_m"], report["sphere_fit"]["sphere_rms_m"], atol=1e-10)
reasons = probe.sphere_quality(fit)
assert reasons and probe.VERSION == "0.1.1"

x, y, w, h = box
u, v = np.meshgrid(np.arange(x, x + w), np.arange(y, y + h))
mask = ((u - x - w / 2) / (.35 * w)) ** 2 + ((v - y - h / 2) / (.35 * h)) ** 2 <= 1
z = depth[v[mask], u[mask]] * .001
normal_target = matrix[:3, :3] @ np.array(fit["plane_normal_camera"])
if normal_target[2] < 0:
    normal_target = -normal_target
diagnostics = {
    "source": str(RAW.relative_to(ROOT)).replace("\\", "/"),
    "record_sha256": hashlib.sha256((RAW / "原始记录.json").read_bytes()).hexdigest(),
    "depth_sha256": hashlib.sha256((RAW / "depth_raw.npy").read_bytes()).hexdigest(),
    "offline_replay_matches_original": True,
    "original_candidate_target_m": report["candidate_center_target_m"],
    "original_status": report["status"], "new_quality_status": "fit_rejected",
    "rejection_reasons": reasons, "sphere_fit": fit,
    "plane_normal_target_up": normal_target.tolist(),
    "depth_quantiles_m": dict(zip(["min", "p05", "p25", "median", "p75", "p95", "max"],
                                  map(float, np.percentile(z, [0, 5, 25, 50, 75, 95, 100])))),
    "robot_run_by_assistant": False,
    "user_field_reference": {"source": "2026-11-03本对话补充", "feet_to_ball_distance_m_approx": 2.5,
        "ball_diameter_m_approx": .20, "robot_height_m": .90,
        "camera_height_not_measured": True, "trunk_to_feet_offset_not_measured": True,
        "ball_reference_point_not_specified": True},
    "different_reference_numeric_difference_m_not_localization_error": float(diagnostic[0] - 2.5),
    "fitted_camera_optical_Z_m": fit["center_camera_m"][2],
    "fitted_camera_slant_range_m": float(np.linalg.norm(fit["center_camera_m"])),
    "illustrative_slant_range_m_if_horizontal_center_distance_2_5_and_camera_height_0_9": float(np.hypot(2.5, .9 - .1)),
    "fitted_diameter_m": 2 * fit["fitted_radius_m"],
    "fitted_to_actual_diameter_ratio_approx": 2 * fit["fitted_radius_m"] / .20,
}
(OUT / "球位_20261103_113057_624030_复算.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")

plt.rcParams.update({"font.family": "Microsoft YaHei", "axes.unicode_minus": False, "font.size": 10})
fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
fig.suptitle("K1静态足球坐标：首份快照回读（2026-11-03）", fontsize=17, fontweight="bold")
pad = 28
x0, x1, y0, y1 = x - pad, x + w + pad, y - pad, y + h + pad
rgb_show = rgb[..., ::-1] if report["rgb"]["encoding"] == "bgr8" else rgb
axes[0, 0].imshow(rgb_show, extent=(0, width, height, 0))
axes[0, 0].set(xlim=(x0, x1), ylim=(y1, y0), title="RGB：选中了足球，检测框19×18像素", xlabel="图像u（像素）", ylabel="图像v（像素）")
axes[0, 0].add_patch(Rectangle((x, y), w, h, fill=False, ec="#ff4747", lw=2))

masked = np.ma.masked_where((depth == 0) | (depth == 65535), depth * .001)
cmap = plt.get_cmap("viridis").copy()
cmap.set_bad("#dddddd")
im = axes[0, 1].imshow(masked, cmap=cmap, vmin=2.4, vmax=4.1, extent=(0, width, height, 0))
axes[0, 1].set(xlim=(x0, x1), ylim=(y1, y0), title="同像素深度：框内存在明显上下梯度", xlabel="图像u（像素）", ylabel="图像v（像素）")
axes[0, 1].add_patch(Rectangle((x, y), w, h, fill=False, ec="#ff4747", lw=2))
axes[0, 1].add_patch(Ellipse((x + w / 2, y + h / 2), .7 * w, .7 * h, fill=False, ec="white", lw=1.5))
fig.colorbar(im, ax=axes[0, 1], label="按0.001比例解释的光轴Z（米）", extend="both")

axes[1, 0].scatter(v[mask], z, s=18, alpha=.65, color="#236e9b", label="中心椭圆134个深度样本")
axes[1, 0].set(title="取样跨度2.530—3.601米", xlabel="图像v（像素）", ylabel="按0.001比例解释的Z（米）")
axes[1, 0].grid(alpha=.2)
axes[1, 0].legend(loc="best", fontsize=9)

values = [fit["sphere_rms_m"] * 100, fit["plane_rms_m"] * 100]
bars = axes[1, 1].bar(["球面拟合", "平面拟合（诊断对照）"], values, color=["#d2664a", "#408c83"], width=.55)
axes[1, 1].set(title="同一批点更接近平面；不能认定为可靠球心", ylabel="点到拟合面的RMS（厘米）", ylim=(0, 14))
for bar, value in zip(bars, values):
    axes[1, 1].text(bar.get_x() + bar.get_width() / 2, value + .3, f"{value:.2f} cm", ha="center", fontsize=12)
axes[1, 1].text(.5, .95, "残差小不证明深度单位或配准正确\n平面对照也不自动证明采到的是地面", transform=axes[1, 1].transAxes, ha="center", va="top", fontsize=9, color="#555555")
fig.savefig(OUT / "球位_20261103_113057_624030_诊断图.png", dpi=160)
plt.close(fig)
print(json.dumps({"replayed_target": diagnostic.tolist(), "sphere_rms_m": fit["sphere_rms_m"],
                  "plane_rms_m": fit["plane_rms_m"], "new_status": "fit_rejected"}, ensure_ascii=False))
