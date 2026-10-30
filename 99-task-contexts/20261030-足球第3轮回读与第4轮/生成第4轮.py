from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
GUIDE = V / '足球测试_第4轮_操作与记录.md'
NOTEBOOK = V / '足球测试_第4轮_管理器创建与启停.ipynb'
assert not GUIDE.exists() and not NOTEBOOK.exists(), '已有第4轮文件，不覆盖现场记录'

GUIDE.write_text('''# 足球测试第4轮：实际创建管理器，测试启停与重启

第3轮的管理器测试被创建前的`get_mode()`报错挡住，构造函数没有执行。TF查询则发生时间外推错误，尚未取得矩阵。本轮修正测试代码，把连接、模式读取、构造和启停分别记录；模式读取失败不会再被记成构造失败。

配套代码：[第4轮Notebook](足球测试_第4轮_管理器创建与启停.ipynb)。按六步逐格运行，只需填写第2部分的现场记录。程序会保存调用结果和完整报错。

## 1. 操作步骤

沿用K1 060100、SDK 1.2.2。在独立内核运行，结束其他运动程序，按既有操作让机器人处于可进入足球模式的行走状态。取走足球，留出站立和可能调整步态的空间。STEP 04、05会实际开启底层视觉踢球控制；每次观察三秒后，程序在`finally`中调用`stop()`。三秒仅为本轮观察窗口，不是响应性能要求。

| 步骤 | 怎么做 | 应看什么/程序保存什么 |
| --- | --- | --- |
| STEP 01：连接 | 运行一次 | 新建结果目录；连接结果、公开模式和原始模式分别保存。模式读取失败仍可继续STEP 02、03；连接本身失败则直接运行06 |
| STEP 02：再查TF | 原样运行 | 相机到trunk查询至多三次，成功就结束；保存每次返回或完整报错。全部失败也继续STEP 03 |
| STEP 03：创建 | 原样运行一次 | 实际执行`SoccerKickManager(robot)`，只按构造本身的结果判定。失败就跳过04、05，执行06交记录 |
| STEP 04：第一次启停 | 确认场地与机器人状态后，输入“启停” | `start()`返回后观察三秒，随后调用`stop()`；看是否出现步态、模式或其他实际变化。异常也会尝试stop并保存报错 |
| STEP 05：停止后重启 | 先确认04的stop无报错、现场状态正常，再输入“重启” | 复用同一个管理器，再次start、观察、stop。04失败时本步自动跳过 |
| STEP 06：保存 | 原样运行 | 生成能力汇总、原始JSON和本机接口实现文本。把整个结果目录复制回知识库，填写下表 |

这次不发送球位或方向/力度指令，因此“没有踢球动作”符合本轮条件。`start()`负责进入足球模式并开启控制；`stop()`关闭视觉踢球控制并清空球位、目标参考，**不会主动切回prepare或walk**。公开模式名称可能是别名，程序另读原始模式供核对。

如果stop报错或现场状态异常，结束本轮，按已有人工控制流程接管，不执行重启，不靠重启Jupyter内核代替机器人停止。正常结束后也按既有操作切回本次实验需要的模式。

STEP 01误运行第二次会保留已有连接和目录，继续后续格即可。需要从头再测时，先确认本轮stop无报错且机器人已由人工恢复，再重启内核。STEP 04、05各只执行一次，代码会阻止同一格重复启动。

## 2. 本轮记录（请填写）

| 项目 | 本轮填写 |
| --- | --- |
| 测试日期/测试人 | 待填 |
| 机器人/SDK环境是否沿用 | K1 060100、SDK 1.2.2；有变化请改 |
| 测试开始时模式与实际姿态 | 待填 |
| STEP 01连接是否成功 | 待填 |
| STEP 02是否取得矩阵 | 待填，或写“仍报错” |
| STEP 03是否实际创建成功 | 待填 |
| 创建时有无实际变化 | 待填 |
| STEP 04 start与stop分别是否返回/报错 | 待填 |
| 第一次start后与stop后，机器人分别有什么表现 | 待填；没有变化也如实写 |
| STEP 05是否执行，start与stop分别是否返回/报错 | 待填 |
| 重启后的现场表现，是否与第一次不同 | 待填；跳过则写原因 |
| 实验后如何恢复，当前机器人是否正常 | 待填 |
| 是否修改代码 | 未修改/写明改动 |
| 结果目录 | 待填具体第4轮子目录 |
| 其他异常或备注 | 待填 |

保存Notebook输出，把整个`第4轮_日期_时间/`复制到知识库`实验验证/足球测试结果/`，然后告诉助手“第4轮已记录”。出现失败直接交已有结果，无需反复运行或更换SDK。

## 3. 本轮判定与后续范围

| 项目 | 本轮如何登记 |
| --- | --- |
| 创建 | 构造函数实际返回才记“成功”；读取模式或连接失败另记，不能混为构造失败 |
| 启动/停止 | 每次分别登记是否调用、是否返回、错误；结合现场表现审读。返回None不等于已验证踢球效果 |
| 重启 | 仅在第一次启停均返回、现场正常后，用同一对象再次实际启停 |
| TF | 有返回则检查有限4×4结构；最多三次重试仅用于排查上一轮时间错误，无测距精度要求 |
| 后续仍需实际测试 | `update_command`的方向和力度更新、`update_ball`及持续更新、完整试踢与带指令的停止后重启 |

本机源码显示：管理器用里程计固定一个虚拟目标方向，外部仍须提供当前机器人坐标系下的米制球位。它没有在类中自动识别或测量足球。球位来源、深度单位/配准和控制原点继续保留待核，当前不要求像素—米标定。

本轮只核实这些SDK功能是否可用，不设检出率、距离误差或用时验收阈值，也不登记U7/U8整课确认。

## 4. 助手审读区

| 项目 | 结论 |
| --- | --- |
| 数据目录与环境 | 待回读 |
| TF结果 | 待回读 |
| 实际创建结果 | 待回读 |
| 第一次start、stop | 待回读 |
| 停止后重启 | 待回读 |
| 现场表现与接口返回的对应 | 待回读 |
| 下一轮 | 读取本轮记录后安排 |
''', encoding='utf-8')

cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s): cells.append(nbf.v4.new_code_cell(s.strip()))

md('''# 足球测试第4轮：管理器创建与启停

对应[操作与记录表](足球测试_第4轮_操作与记录.md)。本轮实际创建管理器，再测试两次启停，第二次复用同一对象。TF最多重试三次；每项的异常分别保存。

使用独立内核，结束其他运动程序，取走足球。STEP 04、05会实际开启视觉踢球控制，每次观察三秒后尝试stop。本轮不下发球位、方向或力度。发生stop报错或现场异常，按已有人工流程接管，结束本轮。''')
md('''## STEP 01　连接并建立记录

运行一次。连接成功后，即使模式读取失败，也会保留连接继续测试。重复运行此格会提示沿用已有连接，保持原目录。

重新开始整轮前，先确认控制已停止、机器人已人工恢复，再通过Jupyter的“内核→重启内核”清理Python连接。内核重启不能代替机器人停止。''')
code('''TESTER = "xy"
ROBOT_ID = "060100"
FIRMWARE = "1.8.1"

import sys
import json
import time
import math
import inspect
import traceback
import importlib.metadata
from datetime import datetime
from pathlib import Path
import numpy as np

if "robot" in globals() or "report" in globals():
    raise RuntimeError("已有本轮连接或记录，不重复初始化；请继续后续格")
OUTPUT = Path.cwd() / "足球测试结果" / datetime.now().strftime("第4轮_%Y%m%d_%H%M%S_%f")
OUTPUT.mkdir(parents=True, exist_ok=False)
report = {"test": "足球第4轮_实际创建与启停_v1", "created_at": datetime.now().isoformat(),
          "tester": TESTER, "robot_id": ROBOT_ID, "firmware_note": FIRMWARE,
          "python": sys.version, "capabilities": {}, "cycles": {}, "errors": []}

def json_safe(value):
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value

def save():
    (OUTPUT / "原始记录.json").write_text(
        json.dumps(json_safe(report), ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")

def record_error(stage, exc):
    item = {"stage": stage, "error": repr(exc), "traceback": traceback.format_exc()}
    report["errors"].append(item)
    print(stage, "：", repr(exc))
    save()
    return item

def read_modes(label):
    # 两条读取各自记录；失败不会挡住后面的构造函数或停止调用。
    row = {"label": label}
    try:
        row["public_mode"] = str(robot.get_mode())
    except Exception as exc:
        row["public_mode_error"] = repr(exc)
        record_error(label + "/get_mode", exc)
    try:
        value = robot.loco_client.GetMode().mode
        row["raw_mode"] = str(value)
        row["raw_mode_value"] = getattr(value, "value", None)
    except Exception as exc:
        row["raw_mode_error"] = repr(exc)
        record_error(label + "/GetMode", exc)
    report.setdefault("mode_snapshots", []).append(row)
    save()
    print(label, row)
    return row

try:
    report["sdk_version"] = importlib.metadata.version("boosteros")
    from boosteros.robots.booster import BoosterRobot, SoccerKickManager
    robot = BoosterRobot(enable_tf_listener=True)
except Exception as exc:
    report["capabilities"]["机器人连接"] = "失败"
    record_error("连接", exc)
    raise
report["capabilities"]["机器人连接"] = "成功"
save()
try:
    report["robot_info"] = repr(robot.robot_info)
except Exception as exc:
    record_error("读取robot_info", exc)
read_modes("连接后")
print("SDK：", report["sdk_version"])
print("结果目录：", OUTPUT.resolve())''')
md('''## STEP 02　复查相机到trunk的TF

先等一秒让新连接接收数据，再调用相同公开接口，最多三次。每次请求或报错都保留；失败也继续STEP 03。

这些等待用于排查缓存时间问题，不能保证解决上一轮外推错误。代码不改SDK内部时间，不把trunk直接当作已确认的踢球坐标原点。''')
code('''SOURCE_FRAME = "head_color_optical_frame"
TARGET_FRAME = "trunk"
if "tf_attempts" in report:
    raise RuntimeError("本轮TF已记录，不覆盖；请继续STEP 03")
report["tf_attempts"] = []
report["capabilities"]["相机到trunk变换"] = "未取得"
time.sleep(1.0)
try:
    frames = list(robot.list_frames())
    report["frames"] = frames
    if SOURCE_FRAME not in frames or TARGET_FRAME not in frames:
        report["capabilities"]["相机到trunk变换"] = "坐标系本轮未列出"
        print("坐标系列表：", frames)
    else:
        for attempt in range(1, 4):
            row = {"attempt": attempt, "source_frame": SOURCE_FRAME, "target_frame": TARGET_FRAME}
            try:
                transform = robot.get_transform(target_frame=TARGET_FRAME, source_frame=SOURCE_FRAME)
                row["call_returned"] = True
                matrix = np.asarray(transform.to_matrix())
                row["transform"] = {"source_frame": transform.source_frame,
                                    "target_frame": transform.target_frame,
                                    "header": repr(transform.header),
                                    "translation": np.asarray(transform.translation).tolist(),
                                    "rotation": np.asarray(transform.rotation).tolist(),
                                    "matrix": matrix.tolist()}
                row["matrix_structure_ok"] = bool(matrix.shape == (4, 4) and np.isfinite(matrix).all())
                report["capabilities"]["相机到trunk变换"] = "已取得" if row["matrix_structure_ok"] else "返回结构待核实"
                print("第", attempt, "次：取得返回")
                print(matrix)
            except Exception as exc:
                row["error"] = record_error("TF第" + str(attempt) + "次", exc)
            report["tf_attempts"].append(row)
            save()
            if row.get("call_returned"):
                break
            if attempt < 3:
                time.sleep(0.2)
except Exception as exc:
    record_error("列出TF坐标系", exc)
save()
print("TF结果：", report["capabilities"]["相机到trunk变换"])''')
md('''## STEP 03　实际创建管理器

下面的`SoccerKickManager(robot)`就是构造调用，不在它前面附加模式读取。程序分别保存“已进入构造调用”和“调用是否返回”，完整报错可以定位到SDK中的具体一行。

成功后再读模式。创建失败则跳过STEP 04、05，直接运行STEP 06；本内核不反复创建。''')
code('''if report.get("manager_create_attempted") or "soccer" in globals():
    raise RuntimeError("本轮已尝试创建管理器，不重复创建；请继续后续格")
report["manager_create_attempted"] = True
save()
try:
    soccer = SoccerKickManager(robot)
except Exception as exc:
    report["capabilities"]["实际创建管理器"] = "失败"
    record_error("SoccerKickManager构造", exc)
else:
    report["manager_type"] = type(soccer).__module__ + "." + type(soccer).__name__
    report["capabilities"]["实际创建管理器"] = "成功"
    save()
    print("管理器实际创建成功；尚未启动。")
    read_modes("创建后")
save()
print("创建结果：", report["capabilities"]["实际创建管理器"])''')
md('''## STEP 04　第一次启动与停止

确认其他运动程序已结束、机器人处于可启动状态，输入“启停”。代码实际执行`start()`，返回后观察三秒，再在`finally`中执行`stop()`。创建失败会自动跳过。

原始模式、两个方法的返回和报错分别保存。请观察机器人实际表现；没有球位和指令时，不期待它踢球。stop返回后可能仍处于足球模式，这是本机实现的行为。stop报错时先人工接管，本轮不继续重启。''')
code('''def test_start_stop(label):
    if label in report["cycles"]:
        print("本步已有记录，不重复启动：", label)
        return
    row = {"start_attempted": False, "start_returned": False,
           "stop_attempted": False, "stop_returned": False}
    report["cycles"][label] = row
    save()
    try:
        row["start_attempted"] = True
        report["control_uncertain"] = True
        save()
        soccer.start()
        row["start_returned"] = True
        save()
        print(label, "start已返回；观察三秒，随后调用stop。")
        time.sleep(3.0)
    except (Exception, KeyboardInterrupt) as exc:
        row["start_or_observation_error"] = record_error(label + "/start或观察", exc)
    finally:
        # start报错也尝试关闭，避免它已部分完成模式切换或开启控制。
        row["stop_attempted"] = True
        try:
            soccer.stop()
        except (Exception, KeyboardInterrupt) as exc:
            row["stop_error"] = record_error(label + "/stop", exc)
            print("stop未正常返回，请人工接管，本轮不继续重启。")
        else:
            row["stop_returned"] = True
            report["control_uncertain"] = False
            print(label, "stop已返回；请核对现场状态。")
        save()
    # 模式读取放在停止尝试之后，不能阻断finally中的stop。
    read_modes(label + "停止尝试后")

if report["capabilities"].get("实际创建管理器") != "成功":
    print("创建未成功，跳过启停，继续STEP 06。")
elif "第一次启停" in report["cycles"]:
    print("第一次启停已有记录，不重复启动。")
elif input("已确认可启动，输入“启停”继续：").strip() == "启停":
    test_start_stop("第一次启停")
else:
    print("未启动；可以继续STEP 06保存。")''')
md('''## STEP 05　停止后再次启动

只有第一次start与stop均正常返回，且你确认现场状态正常后，才输入“重启”。此步复用原来的`soccer`，再次实际调用start与stop；没有创建第二个对象。

第一次启停失败会自动跳过。此时保留错误交助手分析，不用自行反复启停或改SDK。''')
code('''first = report["cycles"].get("第一次启停", {})
if not first.get("start_returned") or not first.get("stop_returned") or first.get("start_or_observation_error"):
    print("第一次启停未全部返回，跳过重启，继续STEP 06。")
elif report.get("control_uncertain", True):
    print("控制关闭情况待处理，跳过重启，继续STEP 06。")
elif "停止后重启" in report["cycles"]:
    print("重启已有记录，不重复执行。")
elif input("确认第一次启停后现场正常，输入“重启”继续：").strip() == "重启":
    test_start_stop("停止后重启")
else:
    print("未重启；继续STEP 06保存。")''')
md('''## STEP 06　保存并交回记录

原样运行。本格会补存模式读取、机型识别和TF适配层的本机实现，供助手定位错误；你无需读源码。取不到源码也会保留原因，照常生成汇总。

把整个结果目录复制回知识库，填写[本轮记录](足球测试_第4轮_操作与记录.md)。如果stop报错或现场异常，先人工恢复机器人，再结束内核。正常结束后也按既有操作切回所需模式。

下一轮仍要测试方向、力度、球位更新与实际踢球；本轮启停返回不能代替这些功能的验证。''')
code('''source_records = []
if "robot" in globals():
    objects = [("BoosterRobot_get_mode", type(robot), "get_mode"),
               ("BoosterRobot_get_model", type(robot), "_get_model"),
               ("RosAdapter_get_transform", getattr(robot, "ros_adapter", None), "get_transform")]
    for label, owner, attr in objects:
        row = {"name": label}
        try:
            obj = getattr(owner, attr)
            row["doc"] = inspect.getdoc(obj)
            row["file"] = inspect.getfile(obj)
            filename = label + "_本机实现.txt"
            (OUTPUT / filename).write_text(inspect.getsource(obj), encoding="utf-8")
            row["source_file"] = filename
        except Exception as exc:
            row["error"] = repr(exc)
        source_records.append(row)
report["sdk_sources"] = source_records
save()
lines = ["# 足球第4轮：实际创建与启停", "", "时间：" + report["created_at"],
         "SDK：" + report.get("sdk_version", "未取得"), "",
         "| 检查项 | 结果 |", "| --- | --- |"]
for name in ["机器人连接", "相机到trunk变换", "实际创建管理器"]:
    lines.append("| " + name + " | " + report["capabilities"].get(name, "未执行") + " |")
for label in ["第一次启停", "停止后重启"]:
    row = report["cycles"].get(label)
    status = "未执行" if row is None else (
        "start调用/返回=" + str(row["start_attempted"]) + "/" + str(row["start_returned"])
        + "；stop调用/返回=" + str(row["stop_attempted"]) + "/" + str(row["stop_returned"]))
    lines.append("| " + label + " | " + status + " |")
lines += ["", "## 错误", ""]
for item in report["errors"]:
    lines.append("- " + item["stage"] + "：" + item["error"])
lines += ["", "现场表现见人工记录；启停返回不代表试踢成功。方向/力度及球位更新仍未测试。"]
(OUTPUT / "能力汇总.md").write_text("\\n".join(lines), encoding="utf-8")
print("结果目录：", OUTPUT.resolve())
print("请填写第4轮记录，交助手回读。")''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'purpose': 'soccer_round4_actual_creation_start_stop_v1', 'robot_executed': False})
nbf.validate(nb)
NOTEBOOK.write_text(nbf.writes(nb), encoding='utf-8')
print({'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
