from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
GUIDE = V / '足球测试_第4轮_操作与记录.md'
NEW = V / '足球测试_第4轮_完整能力验证.ipynb'
OLD = V / '足球测试_第4轮_管理器创建与启停.ipynb'
if OLD.exists():
    old = nbf.read(OLD, as_version=4)
    assert all(c.get('execution_count') is None and not c.get('outputs') for c in old.cells if c.cell_type == 'code'), '旧文件已有执行记录，不覆盖'
assert not list((V / '足球测试结果').glob('第4轮_*')), '已有第4轮结果，保留后先核对'
assert not NEW.exists(), '完整测试已存在，不能覆盖现场内容'

GUIDE.write_text('''# 足球SDK完整能力验证：一次现场测试与课程决策

本文件替代尚未执行的“第4轮只测启停”版本。按下表在一次现场测试中逐步完成，最后统一交回记录；中间无需等待助手回读。前3轮数据继续作为依据，不重测检测率或误差性能。

配套：[完整能力验证Notebook](足球测试_第4轮_完整能力验证.ipynb)。共有9个操作步骤，程序自动登记接口、参数、真实返回值、异常堆栈和调用次序；你填写现场表现。

## 1. 本次要作出的决定

| 问题 | 本次证据 | 用于课程的决定 |
| --- | --- | --- |
| 管理器能否实际创建、启停和复用 | 构造、无球位启停，后续各项复用同一对象 | U7-L2能否安排SDK控制实践；停止与重新启动怎样写 |
| 方向和力度怎样设置、更新 | 停用状态的有效/无效参数；活动中修改；三次真实试踢 | 学生应理解的参数、调用时机和可观察效果 |
| update_ball是否接受并使用外部米制位置 | 卷尺实测输入；静止远球连续更新；近球单次输入试踢 | 区分检测、定位、传参和底层控制，决定实验规模 |
| 是否必须教学生建立像素—米映射 | 沿用前3轮字段、深度/内参和源码证据；本次控制使用手量球位隔离验证 | 先判断SDK控制可用性；视觉米制来源未证实时，不把自编标定放进必修主线 |
| 能否让程序自动认定“球已踢出” | 四个方法的实际返回，与现场球的移动分别记录 | 返回None不能当作完成事件；U7-L4/U8要明确观察窗口和交接条件 |

## 2. 现场准备和坐标填写

结束其他运动程序，使用独立Jupyter内核，沿用K1 060100和SDK 1.2.2。按已有操作使机器人处于可进入足球模式的状态，准备足球、卷尺和一名可操作人工控制的观察者。活动测试中有运动或踢球，沿用已熟悉的现场保护和接管方法。

本次球坐标用卷尺实测：x为前向距离，y为侧向距离，向左为正、向右为负，单位米。记录你使用的机身地面参考点，例如机身中线投影和前后原点的具体量法。**该量法是本次操作定义，不代表已经确认SDK内部控制原点。** 每项活动测试都重新摆球、实测并填写，不自动使用上次坐标。

机器人与球保持不动后填写BALL_X、BALL_Y。示例：若实测前方0.62米、左侧0.03米，填写`BALL_X = 0.62`、`BALL_Y = 0.03`。示例值不能直接用于活动测试。代码用实测时和启动后的里程计补偿机身位移，避免把启动前坐标直接当作当前坐标。

STEP 05中，球应静止放在前方至少1.2米，侧向0.3米以内，观察阶段禁止移动球；机器人行进0.15米或估计球距小于0.8米时提前stop，观察窗口设为2秒。这些数值仅用于本次接近试验的行进限制，不是SDK能力阈值或跟球精度标准。若球提前移动，立即中断当前格，让finally尝试stop，记录本项条件已改变。

STEP 06～08为真实试踢。球放在前方合适位置，可参考官方示例约0.6米并填写实际测量值。这几项只发送一次经过机身位移补偿的当前球位，随后等待2秒观察；看到球被踢动可立即中断单元格结束观察。球移动后不再使用“球静止”的假设继续发送旧球位。

## 3. 一次完成的操作表

| 步骤 | 操作 | 需要观察和记录 |
| --- | --- | --- |
| 01 连接、准备记录 | 运行一次 | 连接成功与否、环境和模式；模式读取失败单独保存，不挡住构造 |
| 02 实际创建与补充查询 | 原样运行 | 构造是否实际返回；里程计是否可读；TF单次查询仅补充记录，失败不挡住管理器测试 |
| 03 无球位启停 | 把足球移开，输入“启停” | start与stop实际返回、模式与现场表现。失败后活动部分跳过，仍执行04可行项与09汇总 |
| 04 参数与返回值 | 原样运行 | 停用状态调用方向、力度、球位；包含无效力度/非数值球位的预期ValueError。finally中再次stop，清除试验参考；本步数值是停用状态的参数样本，不代表实际球位 |
| 05 活动中持续更新 | 摆远球，实测填写本格BALL_X、BALL_Y，输入“执行” | 连续update_ball的实际返回；至少两次更新后实际改变direction和power；观察接近/转向。力度的真实作用留给近球试踢 |
| 06 基线试踢 | 重新摆近球，重新测量，输入“执行” | direction=0、power=1；是否接近、踢动，实际方向、停止后的表现 |
| 07 改方向并重启 | 恢复机器人和球，重新测量，输入“执行” | 同一个管理器重新start；direction=0.25 rad（约向左14°）、power=1；记录能否观察到方向作用，不要求命中率 |
| 08 改力度并重启 | 再次恢复并测量，输入“执行” | direction=0、power=2；与06比较是否有可辨别变化。没有明显变化也如实记录，不据此宣称力度无效 |
| 09 汇总 | 原样运行，填写下方记录 | 保存原始JSON、自动汇总、当前本机SDK源码；明确已调用、失败和未执行项 |

STEP 05在静止球假设下，根据里程计计算当前机身相对球位；它是教师隔离SDK输入与控制能力的测试工具，不是已验证的视觉跟球方案，也不要求学生学习这段转换。STEP 06～08逐项stop、重新测量、重新start，连同05已覆盖停止后复用、不同指令和新球位的重新设置。

如上游调用失败，后续依赖项可在同一次测试中跳过，直接保存完整错误。此次记录将据此作“当前条件下可用/需收缩课程任务”的决定，不默认再开启一轮探查。只有具体错误妨碍决定时，才提出针对该错误的补测。

## 4. 现场记录（请填写）

| 项目 | 记录 |
| --- | --- |
| 日期/测试人/观察者 | 待填 |
| 机器人、SDK、模式是否沿用 | K1 060100、SDK 1.2.2；有变化请写明 |
| 卷尺测量原点及量法 | 待填，明确机身参考点，不只写“机器人前方” |
| 02构造/里程计/TF结果 | 待填，错误不用手抄，程序保存 |
| 03 start前、start后、stop后的实际表现 | 待填 |
| 04参数调用与预期ValueError是否正常 | 待填，或填写异常 |
| 05球是否全程静止；机器人是否接近或转向；停止是否正常 | 待填，球移动或提前中断须写明 |
| 06是否接近、是否踢动、实际方向、stop后表现 | 待填；没有踢动也如实记 |
| 07同对象重启是否正常；方向作用是否可观察 | 待填 |
| 08同对象重启是否正常；力度变化是否可观察 | 待填；无法区分也如实记 |
| 是否有stop返回但现场仍出现后续运动 | 待填 |
| 哪些步骤跳过，原因是什么 | 待填；正常全部完成也写明 |
| 是否修改代码或观察窗口 | 待填改动；未改则写“未修改” |
| 最终怎样恢复机器人，当前状态是否正常 | 待填 |
| 结果目录 | 待填具体`第4轮完整_日期_时间`子目录 |

保存Notebook输出，把整个结果目录复制到知识库`实验验证/足球测试结果/`，再告诉助手“完整测试已记录”。接口返回值和次数由程序保存，不用手工统计。

## 5. 结果怎样决定U7内容

| 记录结果 | 课程处理 |
| --- | --- |
| 构造或启停无法完成 | 当前环境不支持学生试踢主线；保留图像识别、接口输入输出分析，控制部分暂作教师演示/待条件具备，不让学生调SDK内部实现 |
| 手量米制球位可以驱动控制，尚无经过核实的视觉米制球位 | U7-L2可设计定点球位输入与短时控制实验；学生理解坐标和调用。取消从零标定作为必修前置，暂不宣称已实现自主找球/连续视觉踢球 |
| 连续更新和活动中指令更新可调用、现场有对应表现 | 在已验证输入条件下讲持续更新与指令设置；区分测试静止球与真实移动球，不把odom静止球换算当作通用跟球 |
| 单次球位不够完成试踢，但接口可调用 | 说明持续球位来源是完整应用的缺口；不把失败简单归为SDK无法踢球，也不临时增加复杂标定课程 |
| 不同方向/力度返回正常但现场效果不清楚 | 教授参数语义与调用，不设“精确方向/力度控制”的学习成果 |
| 启停、球位、指令及复用在本次条件下可用 | U7-L4/U8可复用这组经过验证的控制条件；自动定位/球已踢出判断另需独立可靠数据，不能从None返回值推得 |

四个公开方法`start/stop/update_command/update_ball`成功时预期返回None，实际值会照实保存。这个类没有公开“踢球成功”返回、视觉球位查询或每轮任务句柄；外部球位、现场效果与接口返回必须分开判断。本次覆盖公开方法及课程用法，不逐个单测私有辅助函数，不做性能或高强度压力测试。窗口检查发生在SDK调用返回后，不会强制中断阻塞中的SDK调用；现场继续使用既有人工接管方式。

前3轮已知：检测有Ball框但distance_m为空；深度和相机内参可读，单位/配准与控制原点未明确；管理器源码只维护odom中的虚拟目标方向。一次手量输入实验能隔离控制能力，不能证明视觉定位已解决。回读本次后，应给出U7-L2/L3/L4和U8足球分支的保留、删改及待核事项，随后回到课程开发。

## 6. 助手回读与课程决策（待记录后填写）

| 项目 | 结论 |
| --- | --- |
| 构造与四方法的实际调用/返回/异常 | 待回读 |
| 活动中指令更新、持续球位更新 | 待回读 |
| 实际试踢、停止与同对象重启 | 待回读 |
| 返回和现场效果的差异 | 待回读 |
| 视觉球位来源当前可证实到哪一步 | 待回读 |
| U7-L2应保留与删改 | 待回读 |
| U7-L3/L4与U8需要同步的部分 | 待回读 |
| 是否有必须补测的具体故障 | 待回读；无则直接进入课程修订 |
''', encoding='utf-8')

cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s): cells.append(nbf.v4.new_code_cell(s.strip()))
md('''# 足球SDK完整能力验证

按[完整操作与记录](足球测试_第4轮_操作与记录.md)在同一次现场测试中完成9步，最后统一交回记录。覆盖创建与全部四个公开方法：start、stop、update_command、update_ball，以及活动中更新、真实试踢和停止后复用。

卷尺提供本次测试的实际球位；静止球与odom只用于隔离控制接口。前3轮数据沿用，不要求先解决视觉定位或从零标定。活动代码受现场人工控制，stop报错时结束后续运动并按既有流程接管。''')
md('''## STEP 01　连接与记录

仅运行一次。准备和日志函数已放在本格，原样执行，无需阅读或修改辅助函数。SDK方法的实际返回、参数与完整异常会自动保存。模式读取失败不会阻断构造。

重复运行此格会保留已有连接和记录目录。重新开始前先确认机器人控制已停止并人工恢复，再重启内核；内核重启不能代替stop。''')
code((TASK / '公共代码.py').read_text(encoding='utf-8'))
md('''## STEP 02　实际创建、读取里程计，补充TF

原样运行一次。构造独立记录；里程计和TF分别尝试，失败不会被误记为构造失败。TF只是补充信息，后面的手量坐标测试不依赖它。''')
code('''if "构造与查询" in report["cases"]:
    raise RuntimeError("本项已有记录，继续STEP 03")
report["current_case"] = "构造与查询"
report["cases"]["构造与查询"] = {}
try:
    soccer = call("SoccerKickManager", SoccerKickManager, robot)
except Exception:
    report["manager_created"] = False
else:
    report["manager_created"] = True
try:
    report["initial_odom"] = pose()
except Exception as exc:
    report["initial_odom_error"] = repr(exc)
try:
    transform = call("get_transform", robot.get_transform,
                     target_frame="trunk", source_frame="head_color_optical_frame")
    matrix = np.asarray(transform.to_matrix())
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise ValueError("TF矩阵结构不是有限4×4")
    report["transform"] = {"source": transform.source_frame, "target": transform.target_frame,
                           "matrix": matrix.tolist()}
except Exception as exc:
    report["transform_error"] = repr(exc)
save()
print("管理器实际创建：", report.get("manager_created"))''')
md('''## STEP 03　无球位启动与停止

先移开足球，确认机器人可进入足球模式，再输入“启停”。start返回后观察一秒，finally中尝试stop。没有球位和指令，不期待踢球。

这两个返回和现场变化分开记录。stop不会自动切回其他模式。若启停失败，仍可执行参数检查与最后汇总，活动试验自动跳过。''')
code('''baseline()''')
md('''## STEP 04　停用时的参数、返回和异常

本格使用停用状态的参数样本，不代表实际球位置。依次调用方向/力度、球位，以及越界力度和非数值球位；预期不合法输入报ValueError。最后调用stop清空全部试验参考，才允许进行活动测试。

这些调用覆盖接口输入和返回；停用状态正常返回不代表已经驱动踢球。''')
code('''label = "停用参数检查"
if can_run(label):
    report["cases"][label] = {"checks": []}
    report["current_case"] = label
    row = report["cases"][label]
    try:
        call("update_command", soccer.update_command, direction=0.0, power=1.0)
        call("update_command", soccer.update_command, direction=-0.25, power=10.0)
        call("update_ball", soccer.update_ball, x=0.6, y=0.0)
        invalid = [("power=0", soccer.update_command, {"direction": 0.0, "power": 0.0}),
                   ("power=11", soccer.update_command, {"direction": 0.0, "power": 11.0}),
                   ("x非数值", soccer.update_ball, {"x": "invalid", "y": 0.0})]
        for name, function, kwargs in invalid:
            method = "update_ball" if name == "x非数值" else "update_command"
            try:
                call(method, function, **kwargs)
            except ValueError:
                row["checks"].append({"input": name, "expected_ValueError": True})
            except Exception as exc:
                row["checks"].append({"input": name, "unexpected_error": repr(exc)})
            else:
                row["checks"].append({"input": name, "expected_ValueError": False})
    except (Exception, KeyboardInterrupt) as exc:
        row["error"] = repr(exc)
    finally:
        stop_control(row)
    save()
    print("停用参数检查已记录；未把参数样本作为真实球位试踢。")''')
md('''## STEP 05　远处静止球：连续球位与活动中指令更新

将球放在前方至少1.2米、侧向0.3米以内，机器人和球保持不动，实测后填写本格两个数值。执行后球保持静止。代码补偿启动后的机身位移，连续发送当前机身坐标；两次球位后再把方向改为0.20 rad、力度改为2。

观察窗口设为2秒，读到行进达到0.15米或估计球距小于0.8米会提前stop。若球被碰动，立即中断当前格。此步验证持续输入与活动中更新，不判定实际踢球力度；临时odom换算不属于学生必修代码。''')
code('''BALL_X = None  # 填本项实测前向距离（米），至少1.2
BALL_Y = None  # 填本项实测侧向距离（米），左正右负
motion_case("连续球位与活动中指令更新", BALL_X, BALL_Y, continuous=True, observe_s=2.0)''')
md('''## STEP 06　基线真实试踢

恢复机器人、重新摆球。按实际坐标原点量好本次球位，填写本格数值，再输入“执行”。方向为正前方、力度为1。只下发一次启动后补偿的当前球位，再等待2秒观察；看到球踢动可立即中断。

记录是否接近、是否踢动、实际方向以及stop后的表现。未踢动也保留结果，不自行延长到无人看护的持续运行。''')
code('''BALL_X = None  # 重新实测；约0.6米只是官方示例，不是直接可用的固定值
BALL_Y = None
motion_case("基线试踢", BALL_X, BALL_Y, direction=0.0, power=1.0, observe_s=2.0)''')
md('''## STEP 07　改变方向，停止后复用

重新恢复并实测球位，复用原管理器重新start。本项方向改为0.25 rad（约向左14°）、力度仍为1。记录重启是否正常、方向作用是否可观察。结束仍stop。

即使前一项未踢动，只要接口无异常、现场条件正常，也可继续本项；如有异常或stop失败，代码自动跳过后续活动。''')
code('''BALL_X = None  # 本项重新测量
BALL_Y = None
motion_case("改方向与重启", BALL_X, BALL_Y, direction=0.25, power=1.0, observe_s=2.0)''')
md('''## STEP 08　改变力度，再次复用

重新恢复并实测球位。本项方向回到0，力度改为2。与STEP 06比较是否有可辨别变化；地面、摆球和单次输入都会影响实际表现，没有明显区别时记录“本次无法区分”。不作精度、力度比例或成功率测试。''')
code('''BALL_X = None  # 本项重新测量
BALL_Y = None
motion_case("改力度与重启", BALL_X, BALL_Y, direction=0.0, power=2.0, observe_s=2.0)''')
md('''## STEP 09　保存覆盖清单与课程决策记录

原样运行。本格保存当前SDK管理器和TF适配层源码、自动方法覆盖表。表中“正常返回”是调用事实，不等于踢球成功；参数检查中的预期ValueError另见原始JSON。被跳过的项目不会被记成已验证。

填写[现场记录](足球测试_第4轮_操作与记录.md)，把整个结果目录复制回知识库后告诉助手“完整测试已记录”。助手据此给出U7/U8课程删改结论，不默认再拆下一轮。stop报错时先按已有人工流程恢复机器人。''')
code('''import inspect
sources = [("SoccerKickManager", SoccerKickManager)] if "SoccerKickManager" in globals() else []
if "robot" in globals():
    sources += [("BoosterRobot_get_mode", type(robot).get_mode)]
    try:
        sources.append(("RosAdapter_get_transform", robot.ros_adapter.get_transform))
    except Exception:
        pass
report["sdk_sources"] = []
for name, obj in sources:
    row = {"name": name}
    try:
        filename = name + "_本机实现.txt"
        (OUTPUT / filename).write_text(inspect.getsource(obj), encoding="utf-8")
        row["source_file"] = filename
    except Exception as exc:
        row["error"] = repr(exc)
    report["sdk_sources"].append(row)
save()
lines = ["# 足球SDK完整能力测试汇总", "", "时间：" + report["created_at"],
         "SDK：" + report.get("sdk_version", "未取得"), "",
         "| 方法 | 调用次数 | 正常返回次数 | 返回类型/值 |", "| --- | --- | --- | --- |"]
for method in ["SoccerKickManager", "start", "stop", "update_command", "update_ball"]:
    rows = [r for r in report["calls"] if r["method"] == method]
    returned = [r for r in rows if r.get("returned")]
    values = sorted(set(r["return_type"] + ":" + r["return_repr"] for r in returned))
    line = "| " + method + " | " + str(len(rows)) + " | " + str(len(returned)) + " | " + "; ".join(values) + " |"
    lines.append(line)
    print(line)
lines += ["", "## 场景", "", "| 项目 | 代码执行结果 |", "| --- | --- |"]
for label in ["构造与查询", "无球位启停", "停用参数检查", "连续球位与活动中指令更新", "基线试踢", "改方向与重启", "改力度与重启"]:
    row = report["cases"].get(label)
    status = "未执行" if row is None else json.dumps(row, ensure_ascii=False, default=str)
    lines.append("| " + label + " | " + status.replace("|", "/") + " |")
lines += ["", "现场球是否移动、方向/力度效果、stop后表现与测量原点见人工记录。",
          "SDK直接视觉米制球位来源尚未证实；手量+静止球odom测试不能替代视觉定位。",
          "回读后作U7/U8课程决策；未执行项和故障不能写成已验证。"]
(OUTPUT / "能力汇总.md").write_text("\\n".join(lines), encoding="utf-8")
print("结果目录：", OUTPUT.resolve())
print("填写现场记录后交助手，进入课程边界与实验设计修订。")''')
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'}, 'purpose': 'soccer_complete_capability_v2', 'robot_executed': False})
nbf.validate(nb)
NEW.write_text(nbf.writes(nb), encoding='utf-8')
if OLD.exists():
    OLD.unlink()
print({'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
