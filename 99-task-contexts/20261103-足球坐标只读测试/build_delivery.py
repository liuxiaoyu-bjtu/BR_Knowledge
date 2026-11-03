"""生成Notebook入口、运行离线检查、打包；不连接机器人。"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
OUT = ROOT / "04-shared/sdk-tests/足球坐标只读测试"


def cell(kind, source):
    result = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


cells = [
    cell("markdown", """# K1足球坐标静态只读测试

目的：Ball框 → 深度与内参 → 相机三维球心 → get_transform → trunk候选坐标。

保持机器人、头部和球静止。本程序只查询数据，不发送头部、身体、模式或踢球命令。无需教师JSON。

默认深度比例0.001只是毫米候选假设；同像素配准和深度表示光轴Z也需现场核对。计算成功仍是候选值。
"""),
    cell("code", """from pathlib import Path
from probe_ball_coordinates import run_probe
"""),
    cell("markdown", """## 填写本次参数

先把一颗球放在视野内。`KNOWN_XY=None`可先观察坐标；知道trunk原点和轴向后再填写卷尺值。

现有detector应为soccer模型；如果不是，将下一格的DETECTOR设为None，由工具创建足球检测器。
"""),
    cell("code", """DEPTH_SCALE_M = 0.001    # 待核对的米/原始深度单位，不能靠dtype确认
KNOWN_XY = None           # 可选：(实测x, 实测y)，单位米，使用本次目标帧原点
BALL_RADIUS_M = None      # 可选：实测足球半径，单位米
NOTE = "正前方静止球"    # 每次改为本次位置和观察情况
OUTPUT_ROOT = "足球坐标测试结果"

ROBOT = globals().get("robot")
DETECTOR = globals().get("detector")
"""),
    cell("markdown", """## 采集一次并计算

复用已有robot/detector；未传入时由模块创建并缓存。先取RGB、深度和TF，后执行检测。

结束时打印记录目录与ZIP，错误时也保存已有数据。本次检测可能耗时约数秒。
"""),
    cell("code", """report = run_probe(
    robot=ROBOT, detector=DETECTOR,
    depth_scale_m=DEPTH_SCALE_M, known_xy=KNOWN_XY,
    ball_radius_m=BALL_RADIUS_M, note=NOTE, output_root=OUTPUT_ROOT,
)
"""),
    cell("markdown", """## 核对选中的球与数值

`candidate_only`表示候选值已经算出，不代表已可供踢球控制。

将球移到左侧、右侧或向前移动卷尺量得的距离，停稳后修改NOTE并重运行参数格和采集格。比较左右符号及前后差值；球位变化时，机器人与头部保持不动。
"""),
    cell("code", """from IPython.display import display, Image as DisplayImage

folder = Path(report["output_dir"])
picture = folder / "selected_ball.png"
if not picture.exists():
    picture = folder / "rgb.png"
if picture.exists():
    display(DisplayImage(filename=str(picture)))

display({
    "状态": report["status"],
    "候选球心[x,y,z]米": report["candidate_center_target_m"],
    "拟合诊断值（可能已拒用）": report.get("diagnostic_center_target_m"),
    "拒用原因": report.get("sphere_fit_rejection_reasons"),
    "球面拟合": report.get("sphere_fit"),
    "卷尺比较": report.get("measurement_comparison"),
    "RGB/深度时间差秒": report.get("rgb_depth_skew_s"),
    "TF/RGB时间差秒": report.get("transform", {}).get("tf_minus_rgb_s"),
    "检测耗时秒": report.get("detection_elapsed_s"),
    "提示": report["warnings"],
    "异常": report.get("error"),
})
"""),
    cell("markdown", """若需要回读分析，保留并反馈本次ZIP即可。它包含原图、原单位深度、内参、矩阵、计算结果和异常。

trunk候选坐标与SoccerKickManager当前控制身体坐标的关系仍需确认。当前静态测试不会将结果传入update_ball，也不承担运动中的时延补偿。
"""),
]
notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                          "language_info": {"name": "python", "version": "3.10"}},
            "nbformat": 4, "nbformat_minor": 5}
for i, c in enumerate(cells):
    c["id"] = f"probe-{i+1:02}"
(OUT / "K1足球坐标_只读测试.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for c in cells:
    if c["cell_type"] == "code":
        compile("".join(c["source"]), "notebook_cell", "exec")
run = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", str(TASK / "tests"), "-v"],
                     capture_output=True, text=True, encoding="utf-8")
(TASK / "离线检查输出.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
if run.returncode:
    raise RuntimeError(run.stdout + run.stderr)
import re
tests = int(re.search(r"Ran (\d+) tests?", run.stdout + run.stderr).group(1))
package = OUT / "K1足球坐标_测试工具包_v0.1.1.zip"
files = [OUT / n for n in ["probe_ball_coordinates.py", "K1足球坐标_只读测试.ipynb", "README.md"]]
with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.name)
with zipfile.ZipFile(package) as archive:
    for path in files:
        assert archive.read(path.name) == path.read_bytes()
report = {"offline_tests": tests, "result": "passed", "robot_run": False, "notebook_cells": len(cells),
          "code_cells": sum(c["cell_type"] == "code" for c in cells),
          "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(files[0].read_bytes()).hexdigest()}
(TASK / "校验结果.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
