# -*- coding: utf-8 -*-
"""U7-L4生成器。2026-10-28以当前学生Notebook反向同步。
重新运行将覆盖对应Notebook；主稿为notebooks/U7-L4_小剧场预演.ipynb。
P1修订稿，未登记确认①②；离线核查不代表真机验证。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U7-L4_小剧场预演.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U7-L4：小剧场预演
cells.append(md("""# U7-L4：小剧场预演

**课程目标**

1. 能为预演各幕填写开始条件、完成条件及未完成时的处理。
2. 能用动作单元函数和固定顺序列表组织检测、运动、语音与致意动作，说明何时继续、何时结束。
3. 能依据程序条件和SDK任务状态记录各幕结果、用时及现场表现，指出最后完成或未完成的幕。"""))

# 一、引入
cells.append(md("""## 一、引入

L1观察了多路传感器数据的时间差，L2以瓶子验证了检测、播报与运动衔接，L3在来宾场景中用线程处理检测和语音指令。本课将来宾接待编排为一段预演，为每幕规定开始条件、完成判断和未完成时的处理。

> 连续执行多个行为时，怎样根据上一幕的结果决定是否继续，并留下可核对的记录？"""))

# 二、幕次与完成条件
cells.append(md("""## 二、幕次与完成条件

### 2.1 预演幕表

本片段面向前方可见的来宾：机器人先对准来宾并完成设定前向位移，再致意，最后播报并沿当前朝向前进。第三幕用于观察语音与移动衔接，来宾在通道外保持前方可见；本程序没有转身或带路路线。

| 幕 | 开始条件 | 完成条件 | 未完成时处理 |
| :--- | :--- | :--- | :--- |
| 一、迎宾 | 开始预演，本帧检出来宾 | 前向位移与对准条件同时满足 | 未检出、状态异常或轮数耗尽，结束整段 |
| 二、致意 | 幕一完成 | 致意任务返回SUCCEEDED | 失败、取消或等待后仍未结束，结束整段 |
| 三、播报与前进 | 幕二完成 | 播放成功、前方仍检出来宾、位移达标 | 播放未成功、目标丢失或轮数耗尽，结束整段 |

相邻幕之间按表中条件交接，任一幕未完成都不进入下一幕。机器人与来宾的间距由现场核对，里程计前向位移不直接表示间距。"""))

# 2.2 顺序列表与函数
cells.append(md("""### 2.2 顺序列表与函数

每幕写成一个函数，返回`"完成"`或具体未完成原因。`script`列表保存幕名和函数名，`for`循环按列表顺序取出，`step()`才调用函数。函数名后不加括号时，列表登记的是函数本身。

这里使用固定顺序和结果判断组织流程。U5-L4用“待机、会话已发起、停止请求已发出”等应用状态管理会话；本课没有另设可分支跳转的显式状态机。U6-L4的顺序素材编排提供了顺序执行的基础，本课增加每幕的条件与结果记录。

新增一幕时，需定义函数、填写条件，并把函数加入列表；修改某幕内部步骤时，修改对应函数。

### 2.3 结果与用时

`log`记录幕名、返回原因和执行用时。动作等待返回后仍需检查任务状态，只有`SUCCEEDED`才记为完成。日志能定位已记录的幕及有限原因；幕内具体步骤不能确认时记“待查”。后续未执行的幕记“未执行”。"""))

# 三、预演实验
cells.append(md("""## 三、预演实验

⚠️ **注意**：机器人会移动、致意和播报。留出3米以上平整通道；按迎宾和末幕位移之和核对活动范围，来宾在通道外保持前方可见，人员不得挡在行进方向。全程安排同学保护，异常时用按钮切回准备模式。

📌 **前置**：上一课主循环已结束，工作线程与SDK识别任务均已确认退出；已核对致意动作适用模式和活动范围。每次预演前人工恢复站位和朝向。

**STEP 01：首次连接。** 本格保存动作句柄，后续重试须先核查原任务，不能重复初始化覆盖句柄。"""))

# 连接并准备检测器、语音和动作句柄。
cells.append(md("""连接并准备检测器、语音和动作句柄。"""))

# import time
cells.append(code("""import time
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech

robot = BoosterRobot()
detector = Detection(model="person")
speech = Speech(robot)
print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())

motion_task = None"""))

# 3.1 素材与参数
cells.append(md("""### 3.1 素材与参数

**STEP 02：查看动作清单，填写下一格的动作ID。**

选择已经在U1/U6验证过的致意动作，按清单核对适用模式；不要直接使用未测试动作。"""))

# for action in robot.list_actions():
cells.append(code("""for action in robot.list_actions():
    print(action)"""))

# **STEP 03：设置预演参数。**
cells.append(md("""**STEP 03：设置预演参数。**

`APPROACH_X_M`是迎宾幕相对清零位置的目标前向位移；`FORWARD_X_M`是末幕重新清零后的前向位移。示例值1.2米和1.0米须按现场间距调整。每幕清零只改变读数参考，不改变站位。

`KP`把像素偏差换成身体角速度，与头部位置角不同；本课采用当前偏差计算并限幅。"""))

# GREET_ID = "____"       # 从上一格清单填写已验证动作ID
cells.append(code("""GREET_ID = "____"       # 从上一格清单填写已验证动作ID
NEAR_PIXELS = 20
APPROACH_X_M = 1.2
FORWARD_X_M = 1.0
KP = 0.0005
MAX_YAW = 0.3
ACTION_TIMEOUT = 15.0   # 按已验证的动作时长调整

if GREET_ID == "____":
    raise ValueError("请先填写并核对致意动作ID")"""))

# 3.2 检测与播放
cells.append(md("""### 3.2 检测与播放

**STEP 04：定义公共函数。**

`find_guest()`按`person`类别和模型评分选择来宾，课堂只安排一名来宾。`say()`合成后等待播放，并返回播放状态。`fallen()`检查已经摔倒或正在摔倒；程序在幕开始前及运动循环中读取，不能覆盖接口阻塞和两次检查之间的所有时刻。"""))

# def find_guest():
cells.append(code("""def find_guest():
    img = robot.get_image(img_type="rgb")
    results = detector.detect(img.to_numpy())
    best = None
    for r in results:
        if r.class_name == "person":
            if best is None or r.confidence > best.confidence:
                best = r
    return img, best


def say(text):
    audio = speech.synthesize(text).result()
    return robot.play_sound(audio).wait()


def fallen():
    state = robot.get_fall_down_state()
    return state.has_fallen or state.is_falling"""))

# 3.3 迎宾幕
cells.append(md("""### 3.3 迎宾幕

**STEP 05：定义迎宾函数。**

每轮检测来宾、计算偏差和剩余前向位移。第一次未检出便结束本幕，未设置等候来宾功能；200轮耗尽也不算完成。`finally`保证函数返回或异常退出时尝试发送零速度。定义格不会启动运动。"""))

# def act_approach():
cells.append(code("""def act_approach():
    robot.reset_odom()
    try:
        for i in range(200):
            if fallen():
                return "状态保护"
            img, guest = find_guest()
            if guest is None:
                return "未检出来宾"
            error = guest.bbox.center_x - img.width / 2
            remain = APPROACH_X_M - robot.get_odom().pose_2d[0]
            if abs(error) < NEAR_PIXELS and remain <= 0.05:
                return "完成"
            if fallen():
                return "状态保护"
            yaw_rate = max(-MAX_YAW, min(MAX_YAW, -KP * error))
            robot.set_velocity(max(0.0, min(0.3, remain)), 0, yaw_rate)
            time.sleep(0.5)
            robot.set_velocity(0, 0, 0)
        return "达到迎宾轮数上限"
    finally:
        robot.set_velocity(0, 0, 0)"""))

# 3.4 致意幕
cells.append(md("""### 3.4 致意幕

**STEP 06：定义致意函数。**

保存`motion_task`后有限等待。只有`SUCCEEDED`才返回“完成”；`FAILED`和`CANCELLED`均保留实际状态。等待后任务仍未结束时请求取消并再次等待，整段预演结束。取消不等于动作完整完成；未确认终态前保留原句柄，不能重开预演。"""))

# def act_greet():
cells.append(code("""def act_greet():
    global motion_task
    if motion_task is not None and not motion_task.done():
        return "旧动作任务尚未结束"
    motion_task = robot.do_action(GREET_ID)
    status = motion_task.wait(timeout=ACTION_TIMEOUT)
    if status == "SUCCEEDED":
        return "完成"
    if not motion_task.done():
        motion_task.cancel()
        motion_task.wait(timeout=3.0)
        return "动作等待超时；当前状态：" + str(motion_task.status)
    return "动作未成功：" + str(status)"""))

# 3.5 播报与前进幕
cells.append(md("""### 3.5 播报与前进幕

**STEP 07：定义末幕函数。**

先播报“接下来向前移动，请留在通道外观看。”播放成功后重新取图；来宾须始终在前方可见且不挡通道。程序沿当前方向前进，不转身，不实现真实带路。"""))

# def act_forward():
cells.append(code("""def act_forward():
    try:
        status = say("接下来向前移动，请留在通道外观看。")
        if status != "SUCCEEDED":
            return "播放未成功：" + str(status)
        robot.reset_odom()
        for i in range(100):
            if fallen():
                return "状态保护"
            img, guest = find_guest()
            if guest is None:
                return "未检出来宾"
            if robot.get_odom().pose_2d[0] >= FORWARD_X_M:
                return "完成"
            if fallen():
                return "状态保护"
            robot.set_velocity(0.2, 0, 0)
            time.sleep(0.5)
            robot.set_velocity(0, 0, 0)
        return "达到前进轮数上限"
    finally:
        robot.set_velocity(0, 0, 0)"""))

# 3.6 预演执行
cells.append(md("""### 3.6 预演执行

**STEP 08：登记幕次。**

本格只创建列表，不调用幕函数。先核对幕名、函数和幕表一致，再执行预演。"""))

# script = [("一 · 迎宾", act_approach),
cells.append(code("""script = [("一 · 迎宾", act_approach),
          ("二 · 致意", act_greet),
          ("三 · 播报与前进", act_forward)]"""))

# **开始下面程序前，机器人应处于行走模式。** 如果当前不在行走模式：先用按钮切到准备模式，等机器人站直站稳；再…
cells.append(md("""**开始下面程序前，机器人应处于行走模式。** 如果当前不在行走模式：先用按钮切到准备模式，等机器人站直站稳；再切到行走模式。确认模式后再运行代码。

**STEP 09：按顺序执行预演。**

每幕开始前检查状态；函数返回“完成”才进入下一幕。异常时记录异常所在幕并退出，后续幕不执行；`finally`发送零速度，并在需要时请求取消尚未结束的动作。现场模式异常须按教师要求人工处理。"""))

# if motion_task is not None and not motion_task.done():
cells.append(code("""if motion_task is not None and not motion_task.done():
    raise RuntimeError("旧动作尚未结束，请先执行STEP 11")
log = []
try:
    for name, step in script:
        t0 = time.monotonic()
        try:
            result = "状态保护" if fallen() else step()
        except Exception as exc:
            result = "异常：" + str(exc)
        seconds = time.monotonic() - t0
        log.append((name, result, seconds))
        print(f"{name}：{result}，用时 {seconds:.1f} 秒")
        if result != "完成":
            print("本幕未完成，结束整段预演")
            break
finally:
    robot.set_velocity(0, 0, 0)
    if motion_task is not None and not motion_task.done():
        motion_task.cancel()
        motion_task.wait(timeout=3.0)
print("预演流程结束；继续检查日志和任务状态")"""))

# **STEP 10：查看各幕记录。**
cells.append(md("""**STEP 10：查看各幕记录。**

未执行的幕显示“未执行”；异常时保留原因。用时包含幕内检测、接口调用与等待，不能直接当作实际移动或动作时长。"""))

# print("幕 | 结果 | 用时（秒）")
cells.append(code("""print("幕 | 结果 | 用时（秒）")
for name, step in script:
    record = None
    for row in log:
        if row[0] == name:
            record = row
    if record is None:
        print(name, "| 未执行 | —")
    else:
        print(f"{record[0]} | {record[1]} | {record[2]:.1f}")"""))

# **STEP 11：确认动作任务结束。**
cells.append(md("""**STEP 11：确认动作任务结束。**

任务未结束时保留句柄，稍后重新执行本格；确认结束并人工恢复起点后，才能重跑STEP 09。若需修改参数，先修改并运行参数格与相应定义格，再登记幕次。"""))

# robot.set_velocity(0, 0, 0)
cells.append(code("""robot.set_velocity(0, 0, 0)
if motion_task is None:
    print("本次未发起致意任务")
else:
    if not motion_task.done():
        motion_task.cancel()
        motion_task.wait(timeout=3.0)
    print("动作状态：", motion_task.status, "已结束：", motion_task.done())
    if motion_task.status == "FAILED":
        print("动作错误：", motion_task.error)
    if not motion_task.done():
        print("任务尚未结束，保留句柄，请教师检查")"""))

# 四、收尾
cells.append(md("""## 四、收尾

先用按钮把机器人切回**准备模式**，等它站直站稳；再由人工扶着切到**阻尼模式**（damping），扶机器人坐下，确认坐稳。不要从行走模式直接切到阻尼模式。"""))

# 五、观察与记录
cells.append(md("""## 五、观察与记录

### 5.1 各幕结果

| 幕 | 开始条件 | 结果或未完成原因 | 用时（秒） | 现场表现 |
| :--- | :--- | :--- | :--- | :--- |
| 一、迎宾 | | | | |
| 二、致意 | | | | |
| 三、播报与前进 | | | | |

未执行的幕填“未执行”，用时填“—”。任务状态与现场表现分别记录，不能由等待返回推断动作完整完成。

### 5.2 未完成记录

| 最后记录的幕 | 日志原因 | 可确认的幕内步骤／待查 | 当时现象 |
| :--- | :--- | :--- | :--- |
| | | | |

本次未出现异常时填“未出现”；日志没有提供的幕内信息填“待查”。

### 5.3 检查点

- 能按实际代码填写各幕开始条件、完成条件和未完成时的处理。
- 能说明列表保存函数名、循环调用函数及返回值决定是否继续的关系。
- 已分别记录程序结果、SDK动作状态和现场表现，未执行幕有明确标记。
- 已核查动作终态，重复预演前完成站位复原和任务检查。

### 5.4 思考题

1. 如果增加“等待来宾”的开场幕，需怎样定义等待上限和未检出时的返回结果？
2. 致意任务返回`CANCELLED`时，为什么不能把本幕记为“完成”？
3. 若整段预演要求不超过40秒，现有日志能支持哪些调整？还需记录哪些幕内步骤才能继续定位耗时？"""))


for i, cell in enumerate(cells, 1):
    cell["id"] = f"u7l4-{i:02d}"

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
