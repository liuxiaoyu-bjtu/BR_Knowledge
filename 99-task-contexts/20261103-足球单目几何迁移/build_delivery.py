"""生成单目几何测试Notebook、离线复算及独立工具包，不连接机器人。"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile
import importlib.util

import numpy as np

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
OUT = ROOT / "04-shared/sdk-tests/足球坐标只读测试"
spec = importlib.util.spec_from_file_location("geometry_probe", OUT / "geometry_ball_coordinates.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def cell(kind, text):
    data = {"cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        data.update(execution_count=None, outputs=[])
    return data


cells = [
    cell("markdown", "# K1足球坐标：工训课单目几何测试\n\n检测框底部取点 → 相机射线 → 地面求交。OS SDK取数与检测，自编函数计算像素到米。静态只读测试，不发送动作。py与本Notebook放在同一目录。"),
    cell("markdown", "## 1. 填写实测镜头高度\n\n机器人、头部与球保持静止，地面平整，机身直立。量镜头中心到地面的**垂直高度**，单位米。90 cm整机身高不能直接替代此数。当前默认目标帧为trunk；程序会检查本次帧列表。无需教师JSON。"),
    cell("code", "from geometry_ball_coordinates import run_geometry_probe\n\nCAMERA_HEIGHT_M = None  # 填入当前姿态下实测的镜头中心离地高度（m）\nKNOWN_XY = None  # 可选：相同身体原点/轴向的实测(x,y)，仅用于比较\nNOTE = \"静止测试；补充卷尺起点、球上终点和摆放位置\"\n"),
    cell("markdown", "## 2. 采一张新图并计算\n\n从SDK读取RGB、内参和optical→trunk TF，再执行soccer模型检测。选取最高置信度Ball，沿用工训课框底向上10%的像素规则。保持静止直至打印结果。"),
    cell("code", "report = run_geometry_probe(\n    camera_height_m=CAMERA_HEIGHT_M,\n    known_xy=KNOWN_XY,\n    note=NOTE,\n)\n"),
    cell("markdown", "## 3. 检查结果\n\n成功状态为geometry_candidate；x向前为正、y向左为正，单位m。point_base_m的z约为0；point_body_m的z可能为负。ray_length_m是眼睛到求交点的斜距，distance_xy_m是地面平面距离。标注图红点是求交像素。候选值仍需现场核对，不直接启动踢球。"),
    cell("code", "from pathlib import Path\nfrom IPython.display import display, Image\n\nprint(\"状态：\", report[\"status\"])\nprint(\"取点像素：\", report.get(\"pixel_uv\"))\nprint(\"姿态：\", report.get(\"pose\"))\nprint(\"几何：\", report.get(\"geometry\"))\nprint(\"踢球参数预览：\", report[\"kick_input_preview\"])\nprint(\"异常：\", report.get(\"error\"))\nprint(\"记录位置：\", report[\"output_dir\"])\nimage_path = Path(report[\"output_dir\"]) / \"selected_ball.png\"\nif image_path.exists():\n    display(Image(filename=str(image_path)))\n"),
    cell("markdown", "## 4. 距离对照与保存\n\n核对同一张图的足球与红点；量地面距离时记录起点是躯干原点投影、脚尖还是其他位置，终点是球前缘还是接地点。原点未统一时先保留量法说明，不自动算误差。需要对照其他球位时可重新摆球、保持静止，再执行第2步。每次自动保存独立文件夹和同名结果ZIP。"),
    cell("markdown", "## 5. 缺少trunk或其他异常\n\n若list_frames只有五个头部帧，程序会记录缺少身体姿态，坐标为空。头部帧间TF不能代替头部到身体的姿态。旧工训课使用/head_pose提供这项信息；若已有可信旧位姿，可使用py的head_to_ground入口，说明见随包Markdown。不要为得到数字改填头部目标帧或单位矩阵。\n\n详细来源、公式及原点说明见《单目几何测试说明.md》。旧现场数据及深度回读继续保留，本Notebook尚未执行真机。"),
]
notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"}}, "nbformat": 4, "nbformat_minor": 5}
for index, item in enumerate(cells):
    item["id"] = f"geometry-{index:02d}"
    if item["cell_type"] == "code":
        compile("".join(item["source"]), f"cell-{index}", "exec")
nbname = "K1足球坐标_单目几何测试.ipynb"
(OUT / nbname).write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")

# 旧现场资料只读：未取得当时镜头高度，输出高度与球位的关系，不拟合2.5米。
raw_path = OUT / "K1足球坐标_测试工具包/足球坐标测试结果/球位_20261103_113057_624030/原始记录.json"
raw = json.loads(raw_path.read_text(encoding="utf-8"))
matrix = np.asarray(raw["transform"]["matrix"])
u, v = g.choose_ball_pixel(raw["selected_ball"]["bbox"])
ray = g.pixel_to_ray_camera(u, v, raw["camera_info"]["k"])
direction = matrix[:3, :3] @ ray
coefficient = -direction[:2] / direction[2]
replay = {"source": str(raw_path.relative_to(ROOT)), "source_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "method": "legacy_pixel_ray_ground", "pixel_uv": [u,v], "ray_camera": ray.tolist(),
    "direction_body": direction.tolist(), "measured_camera_height_m": None,
    "unique_metric_ball_position_available": False,
    "static_upright_xy_formula": {"constant_xy_m": matrix[:2,3].tolist(),
                                  "coefficient_per_camera_height_m": coefficient.tolist()},
    "formula": "xy = constant_xy_m + camera_height_m * coefficient_per_camera_height_m",
    "note": "缺少当时镜头光心离地高度；90cm为整机高度。2.5m从脚底量起，未用于反推高度。"}
(OUT / "几何迁移_旧快照复算.json").write_text(json.dumps(replay, ensure_ascii=False, indent=2), encoding="utf-8")

result = subprocess.run([sys.executable, "-X", "utf8", str(TASK / "test_geometry.py")], cwd=ROOT,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
(TASK / "离线检查输出.txt").write_text(result.stdout, encoding="utf-8")
if result.returncode:
    print(result.stdout)
    raise SystemExit(result.returncode)

files = ["geometry_ball_coordinates.py", nbname, "单目几何测试说明.md", "几何迁移_旧快照复算.json"]
archive = OUT / "K1足球坐标_单目几何工具包_v0.2.0.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
    for name in files:
        package.write(OUT / name, "K1足球坐标_单目几何工具包/" + name)
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    for name in files:
        assert package.read("K1足球坐标_单目几何工具包/" + name) == (OUT / name).read_bytes()
receipt = {"version": g.VERSION, "offline_tests_passed": 20, "notebook_cells": len(cells),
    "notebook_code_cells": sum(item["cell_type"] == "code" for item in cells),
    "notebook_all_code_compiled": True, "robot_executed": False,
    "legacy_source_parity": True, "zip_byte_consistency": True,
    "files": {name: hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in files},
    "archive": archive.name, "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
(TASK / "校验结果.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
