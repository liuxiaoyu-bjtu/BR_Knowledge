from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第3轮_机身变换与管理器创建.ipynb'
cells = []
def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))
def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# 足球测试第3轮：机身变换与管理器创建

对应[操作与记录表](足球测试_第3轮_操作与记录.md)。这次用本机已有坐标系查TF，实际创建一个管理器，并保存本机接口实现。

保持机器人静止，结束其他课程任务。五步逐格运行，不调用start、stop、update_command或update_ball，不切模式、不运行运动。接口失败如实保存，不自行换版本或修改SDK。''')
md('''## STEP 01　连接与记录目录

沿用前两轮信息，有变化再改。运行一次，后续复用连接。若连接失败，保留报错，运行STEP 05保存即可。''')
code('''TESTER = "xy"
ROBOT_ID = "060100"
FIRMWARE = "1.8.1"

import sys
import json
import math
import inspect
import importlib.metadata
from datetime import datetime
from pathlib import Path
import numpy as np

if "robot" in globals():
    raise RuntimeError("已有robot连接，不重复运行；请继续后续格")
OUTPUT = Path.cwd() / "足球测试结果" / datetime.now().strftime("第3轮_%Y%m%d_%H%M%S_%f")
OUTPUT.mkdir(parents=True, exist_ok=False)
report = {"test": "足球第3轮_TF与管理器创建_v1", "created_at": datetime.now().isoformat(),
          "tester": TESTER, "robot_id": ROBOT_ID, "firmware_note": FIRMWARE,
          "python": sys.version, "capabilities": {}}

def json_safe(value):
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value

def save():
    (OUTPUT / "原始记录.json").write_text(
        json.dumps(json_safe(report), ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")

try:
    report["sdk_version"] = importlib.metadata.version("boosteros")
    from boosteros.robots.booster import BoosterRobot, SoccerKickManager
    robot = BoosterRobot(enable_tf_listener=True)
    report["robot_info"] = repr(robot.robot_info)
    report["mode"] = str(robot.get_mode())
    report["capabilities"]["机器人连接"] = "成功"
except Exception as exc:
    report["connect_error"] = repr(exc)
    report["capabilities"]["机器人连接"] = "失败"
    save()
    raise
save()
print("SDK：", report["sdk_version"], "模式：", report["mode"])
print("结果目录：", OUTPUT.resolve())''')
md('''## STEP 02　查询相机到trunk的变换

这两个名称来自第2轮的实际列表。代码再次确认它们存在，再查询一次：source是相机，target是trunk。请求参数与返回字段一起保存。

本格只确认能否读变换，不计算球位，不认定trunk就是踢球控制的参考原点。失败则保存错误，继续STEP 03。''')
code('''SOURCE_FRAME = "head_color_optical_frame"
TARGET_FRAME = "trunk"
try:
    frames = list(robot.list_frames())
    report["frames"] = frames
    report["transform_request"] = {"source_frame": SOURCE_FRAME, "target_frame": TARGET_FRAME}
    if SOURCE_FRAME not in frames or TARGET_FRAME not in frames:
        report["capabilities"]["相机到trunk变换"] = "坐标系本轮未列出"
        print("本轮坐标系列表：", frames)
    else:
        transform = robot.get_transform(target_frame=TARGET_FRAME, source_frame=SOURCE_FRAME)
        matrix = np.asarray(transform.to_matrix())
        matrix_ok = bool(matrix.shape == (4, 4) and np.isfinite(matrix).all())
        report["transform"] = {"returned_source_frame": transform.source_frame,
                               "returned_target_frame": transform.target_frame,
                               "header": repr(transform.header),
                               "translation": np.asarray(transform.translation).tolist(),
                               "rotation": np.asarray(transform.rotation).tolist(),
                               "matrix": matrix.tolist(), "matrix_structure_ok": matrix_ok}
        report["capabilities"]["相机到trunk变换"] = "已取得" if matrix_ok else "返回结构待核实"
        print("实际请求：", SOURCE_FRAME, "→", TARGET_FRAME)
        print("返回源/目标：", transform.source_frame, "→", transform.target_frame)
        print("平移：", transform.translation)
        print("矩阵：")
        print(matrix)
except Exception as exc:
    report["transform_error"] = repr(exc)
    report["capabilities"]["相机到trunk变换"] = "接口报错"
    print("TF查询：", repr(exc))
save()
print("本格结果：", report["capabilities"]["相机到trunk变换"])''')
md('''## STEP 03　保存本机接口实现

原样运行。Python会读取已安装包中管理器类、get_image和get_transform的说明与实现，保存为本地文本；不会执行其中的方法。你不需要阅读或解释这些代码。

某段源码不可读取时保留说明，仍可继续创建管理器。这些文件供助手判断启停顺序、坐标处理和数据定义，不代替后续实测。''')
code('''objects = [("SoccerKickManager", SoccerKickManager),
           ("BoosterRobot_get_image", type(robot).get_image),
           ("BoosterRobot_get_transform", type(robot).get_transform)]
source_records = []
for label, obj in objects:
    row = {"name": label, "module": getattr(obj, "__module__", "未知"),
           "doc": inspect.getdoc(obj)}
    try:
        row["file"] = inspect.getfile(obj)
    except (TypeError, OSError) as exc:
        row["file_error"] = repr(exc)
    try:
        source = inspect.getsource(obj)
        filename = label + "_本机实现.txt"
        (OUTPUT / filename).write_text(source, encoding="utf-8")
        row["source_file"] = filename
        print(label, "：已保存本机实现")
    except (TypeError, OSError) as exc:
        row["source_error"] = repr(exc)
        print(label, "：源码不可直接读取，已记录说明")
    source_records.append(row)
report["sdk_sources"] = source_records
report["capabilities"]["本机接口实现读取"] = "已记录"
save()''')
md('''## STEP 04　实际创建管理器

只运行一次。下面会执行SoccerKickManager(robot)，不调用start。保存创建前后模式；请在记录表填机器人是否有实际状态变化。

创建失败就保留报错，不反复创建，也不自行调用start来尝试解决。创建成功仅代表这一项可用，其余四个方法仍待逐项实测。''')
code('''if "soccer" in globals():
    raise RuntimeError("本内核已有soccer对象，不重复创建")
try:
    report["mode_before_create"] = str(robot.get_mode())
    soccer = SoccerKickManager(robot)
    report["manager_type"] = type(soccer).__module__ + "." + type(soccer).__name__
    report["capabilities"]["创建足球管理器"] = "成功"
    print("创建成功；未调用start或其他控制方法。")
    try:
        report["mode_after_create"] = str(robot.get_mode())
        print("创建前后模式：", report["mode_before_create"], "→", report["mode_after_create"])
    except Exception as exc:
        report["mode_after_create_error"] = repr(exc)
        print("创建成功，但创建后模式读取失败：", repr(exc))
except Exception as exc:
    report["manager_create_error"] = repr(exc)
    report["capabilities"]["创建足球管理器"] = "失败"
    print("创建管理器：", repr(exc))
save()''')
md('''## STEP 05　保存并结束

前面失败或尚未执行的步骤也可汇总。把目录填回[操作与记录表](足球测试_第3轮_操作与记录.md)，保存Notebook输出，将结果文件夹复制回知识库，再告诉助手“第3轮已记录”。

本轮到这里结束。没有启动管理器，无需在本轮追加stop或模式切换。start、update_command、update_ball、stop及停止后重启仍须后续实际测试。''')
code('''save()
lines = ["# 足球第3轮：TF与管理器创建", "", "时间：" + report["created_at"],
         "", "SDK：" + report.get("sdk_version", "未取得"), "",
         "| 检查项 | 本轮结果 |", "| --- | --- |"]
for name in ["机器人连接", "相机到trunk变换", "本机接口实现读取", "创建足球管理器"]:
    status = report["capabilities"].get(name, "未执行")
    lines.append("| " + name + " | " + status + " |")
    print(name, "：", status)
lines += ["", "## 错误与备注", ""]
for key, value in report.items():
    if key.endswith("_error"):
        lines += ["- " + key + "：`" + str(value).replace("`", "'") + "`"]
lines += ["", "本轮只创建管理器与读取TF/实现，四个控制方法未实际调用，不登记通过。"]
(OUTPUT / "能力汇总.md").write_text("\\n".join(lines), encoding="utf-8")
print("结果目录：", OUTPUT.resolve())
print("本轮结束；填写记录后交助手回读。")''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'}, 'purpose': 'soccer_round3_tf_manager_creation_v1',
    'robot_executed': False})
nbf.validate(nb)
if OUT.exists():
    old = nbf.read(OUT, as_version=4)
    assert old.metadata.get('purpose') == 'soccer_round3_tf_manager_creation_v1'
    assert all(c.get('execution_count') is None and not c.get('outputs')
               for c in old.cells if c.cell_type == 'code'), '已有现场输出，不覆盖'
OUT.write_text(nbf.writes(nb), encoding='utf-8')
print({'path': str(OUT), 'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
