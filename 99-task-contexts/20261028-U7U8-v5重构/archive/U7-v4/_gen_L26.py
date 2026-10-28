# -*- coding: utf-8 -*-
"""U7-L2生成器。2026-10-28以当前学生Notebook反向同步。
重新运行将覆盖对应Notebook；主稿为notebooks/U7-L2_视觉-运动-语音桥接.ipynb。
P1修订稿，未登记确认①②；离线核查不代表真机验证。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U7-L2_视觉-运动-语音桥接.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U7-L2：视觉-运动-语音桥接
cells.append(md("""# U7-L2：视觉-运动-语音桥接

**课程目标**

1. 能说明目标检测、运动控制和语音合成各自的输入、输出及等待位置。
2. 能使用通用模型筛选瓶子，将检测框横向偏差换成转向速度，并在语音播放后重新取图。
3. 能比较不播报、先播报再运动及加入状态检查的流程，记录计时范围、结束原因和现场表现。"""))

# 一、引入
cells.append(md("""## 一、引入

U3已经使用通用检测模型读取类别和检测框，U4把目标偏差用于运动控制，U5完成文字合成与播放。本课以瓶子（`bottle`）作为目标物，把这些调用组织在同一段程序中。

机器人检测到瓶子后播报固定文字，再根据新画面计算转向和前进速度。语音等待期间主程序暂停，因此播报前的检测框不能直接作为播报后的运动依据。

> 目标检测、语音播报和运动控制怎样按条件衔接？"""))

# 二、数据与控制条件
cells.append(md("""## 二、数据与控制条件

### 2.1 接口的输入与输出

| 功能 | 输入 | 输出 | 本课关注的等待 |
| :--- | :--- | :--- | :--- |
| 目标检测 | 当前图像数组 | 类别、模型评分、检测框 | 从取图到检测返回 |
| 运动控制 | 前进速度与转向角速度 | 速度指令；后续读取里程计 | 检测、控制计算及循环间隔 |
| 语音合成与播放 | 固定文字 | 音频数据、播放任务状态 | 合成结果返回及播放等待返回 |

SDK提供检测、语音和运动接口。程序还需筛选`bottle`、计算框中心偏差，并决定何时播报、何时运动。检测框给出图像位置，未提供瓶子与机器人的实际间距；`distance_m`不能在本实验中当作测距结果。

### 2.2 感知与行动

每轮获取图像、检测目标、计算速度，再发出短时运动指令，随后读取新画面。这种根据感知结果调整行动的关系称为**感知－行动耦合**。

本课的播报在主循环中执行，合成与播放等待会暂停后续控制计算。播报后用`continue`进入下一轮，重新取图再计算速度。下一课再学习把检测和语音任务管理放在不同线程中。"""))

# 三、瓶子目标实验
cells.append(md("""## 三、瓶子目标实验

⚠️ **注意**：机器人会前进和转向。留出2米以上的平整通道，瓶子放在通道前方、相机能看见的位置，支架和人员均在行进范围外。按设定前向位移核对剩余间距，全程由同学在伸手可及处保护；异常时用按钮切回准备模式。

📌 **前置**：机器人已开机、配网；准备一只可稳定检出的瓶子。每次运行前人工恢复相同起点、朝向和瓶子位置；`reset_odom()`只重置读数，不会让机器人返回起点。

**STEP 01：连接并加载通用模型。** 本格首次准备时运行一次；重复实验从参数与检测检查开始。"""))

# 连接后查看当前模式。
cells.append(md("""连接后查看当前模式。"""))

# import time
cells.append(code("""import time
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech

robot = BoosterRobot()
detector = Detection(model="default")
speech = Speech(robot)
print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())"""))

# 3.1 参数与目标筛选
cells.append(md("""### 3.1 参数与目标筛选

**STEP 02：设置参数，定义瓶子筛选函数。**

`find_bottle()`先检测，再按类别筛选。同一帧有多个瓶子时，按U3-L3的方法选择评分最高的一条；评分不等于真实正确概率，也不保证连续帧选中同一只瓶子，课堂先只放一只。

`TARGET_X_M`是相对本次清零位置的目标前向位移，保留1.2米作为待现场核对的示例值。它既不是与瓶子的间距，也不是转弯后的累计路程。先由教师按通道和初始间距调整。

`error`为框中心横坐标减画面中心，正值表示目标偏右。`-KP * error`使身体向右转；`set_velocity()`第三参数是角速度，不能当作头部角度或每轮累加的转角。本课每轮根据当前偏差重算，并限制角速度。"""))

# TARGET_CLASS = "bottle"
cells.append(code("""TARGET_CLASS = "bottle"
NEAR_PIXELS = 20
TARGET_X_M = 1.2        # 相对起点的目标前向位移（米），按现场调整
KP = 0.0005            # 像素偏差到身体角速度的比例系数
MAX_YAW = 0.3          # 身体角速度上限（rad/s），需真机调试
MAX_ROUNDS = 200


def find_bottle():
    img = robot.get_image(img_type="rgb")
    results = detector.detect(img.to_numpy(), confidence=0.5)
    best = None
    for r in results:
        if r.class_name == TARGET_CLASS:
            if best is None or r.confidence > best.confidence:
                best = r
    return img, best"""))

# **STEP 03：静止检查目标。**
cells.append(md("""**STEP 03：静止检查目标。**

本格只取图和检测。确认输出类别为`bottle`，并用同帧检测框核对瓶子位置。没有结果时调整光照、距离或摆放位置后重试，确认筛选正常后再运行运动程序。"""))

# img, bottle = find_bottle()
cells.append(code("""img, bottle = find_bottle()
if bottle is None:
    print("当前帧未检出bottle，请调整后重新检查")
else:
    print("目标类别：", bottle.class_name, "评分：", round(bottle.confidence, 2))
    print("横向偏差（像素）：", bottle.bbox.center_x - img.width / 2)
    detector.plot(img.to_numpy(), [bottle])"""))

# 3.2 播报与状态检查
cells.append(md("""### 3.2 播报与状态检查

**STEP 04：定义播报和摔倒状态检查函数。**

`result()`等待合成结果，`wait()`等待播放任务返回；只有播放状态为`SUCCEEDED`才把播报步骤记为成功。调用这些函数前要先运行定义格，定义本身不会播报或移动。

`fallen()`读取`has_fallen`和`is_falling`。后面的程序在每轮开头、发速度前检查；检测、合成、播放等待和短时移动期间并非连续监测，现场保护仍须保持。不要推倒机器人测试。"""))

# MESSAGE = "已检测到瓶子，准备向前移动。"
cells.append(code("""MESSAGE = "已检测到瓶子，准备向前移动。"


def say(text):
    audio = speech.synthesize(text).result()
    playback = robot.play_sound(audio)
    status = playback.wait()
    print("播放任务状态：", status)
    return status == "SUCCEEDED"


def fallen():
    state = robot.get_fall_down_state()
    return state.has_fallen or state.is_falling"""))

# 3.3 单轮控制
cells.append(md("""### 3.3 单轮控制

**STEP 05：定义一次控制计算与短时移动。**

`move_one_step()`接收本轮图像和已选瓶子，计算横向偏差与剩余前向位移。条件已满足或状态异常时，返回结束原因；否则发送一次短时速度指令，再发送零速度，返回`None`表示下一轮继续。循环、播报及计时由下一格的实验函数组织。

定义本格不会移动机器人。函数运行时的零速度收尾也由外层实验的`finally`保护。"""))

# def move_one_step(img, bottle, with_protection):
cells.append(code("""def move_one_step(img, bottle, with_protection):
    error = bottle.bbox.center_x - img.width / 2
    remain = TARGET_X_M - robot.get_odom().pose_2d[0]
    if abs(error) < NEAR_PIXELS and remain <= 0.05:
        return "满足位移与对准条件"
    if with_protection and fallen():
        return "状态保护"
    yaw_rate = max(-MAX_YAW, min(MAX_YAW, -KP * error))
    robot.set_velocity(max(0.0, min(0.3, remain)), 0, yaw_rate)
    time.sleep(0.5)
    robot.set_velocity(0, 0, 0)
    return None"""))

# 3.4 实验流程
cells.append(md("""### 3.4 实验流程

**STEP 06：定义可重复调用的实验流程。**

函数参数`with_speech`决定是否播报，`with_protection`决定是否检查摔倒状态。通过参数比较流程，可让各次实验使用同一份控制逻辑。

`reason`初始为“达到轮数上限”，只有偏差与前向位移同时满足条件才改为“满足位移与对准条件”。`try`内执行实验，`finally`在正常结束、异常或中断时尝试发送零速度指令。

记录中的“播报步骤用时”从发起合成计到播放等待返回；“播报后控制流程用时”包含重新检测、控制和等待。未播报时记整段控制流程用时，不能称为纯运动时间。"""))

# def run_trial(with_speech=False, with_protection=False):
cells.append(code("""def run_trial(with_speech=False, with_protection=False):
    robot.reset_odom()
    control_start = time.monotonic()
    announced = False
    reason = "达到轮数上限"
    speech_seconds = None
    try:
        for i in range(MAX_ROUNDS):
            if with_protection and fallen():
                reason = "状态保护"
                break
            img, bottle = find_bottle()
            if bottle is None:
                reason = "未检出bottle"
                break
            if with_speech and not announced:
                speech_start = time.monotonic()
                speech_ok = say(MESSAGE)
                speech_seconds = time.monotonic() - speech_start
                if not speech_ok:
                    reason = "播放任务未成功"
                    break
                announced = True
                control_start = time.monotonic()
                continue  # 播报后重新取图，不沿用旧检测框
            result = move_one_step(img, bottle, with_protection)
            if result is not None:
                reason = result
                break
    finally:
        robot.set_velocity(0, 0, 0)
    print("结束原因：", reason)
    print("播报步骤用时（秒）：", speech_seconds)
    label = "播报后控制流程" if announced else "本次流程"
    print(f"{label}用时：{time.monotonic() - control_start:.1f} 秒")"""))

# 3.5 运行与对照
cells.append(md("""### 3.5 运行与对照

**开始下面程序前，机器人应处于行走模式。** 如果当前不在行走模式：先用按钮切到准备模式，等机器人站直站稳；再切到行走模式。确认模式后再运行代码。

每次执行前恢复相同起点和瓶子位置，并核对`TARGET_X_M`。以下运行格分别执行一次；看完输出、完成人工复位后再执行下一格，不能连续“全部运行”。“满足位移与对准条件”表示本课程序条件成立，实际运动和间距仍需现场观察。"""))

# **STEP 07：运行不播报的对照。**
cells.append(md("""**STEP 07：运行不播报的对照。**"""))

# run_trial()
cells.append(code("""run_trial()"""))

# **STEP 08：复位后，运行先播报再运动的流程。**
cells.append(md("""**STEP 08：复位后，运行先播报再运动的流程。**"""))

# run_trial(with_speech=True)
cells.append(code("""run_trial(with_speech=True)"""))

# **STEP 09：复位后，加入摔倒状态检查。**
cells.append(md("""**STEP 09：复位后，加入摔倒状态检查。**"""))

# run_trial(with_speech=True, with_protection=True)
cells.append(code("""run_trial(with_speech=True, with_protection=True)"""))

# 四、收尾
cells.append(md("""## 四、收尾

先用按钮把机器人切回**准备模式**，等它站直站稳；再由人工扶着切到**阻尼模式**（damping），扶机器人坐下，确认坐稳。不要从行走模式直接切到阻尼模式。"""))

# 五、观察与记录
cells.append(md("""## 五、观察与记录

### 5.1 流程对照

先记录起点、瓶子位置和`TARGET_X_M`。未进入播报或控制阶段时填“未执行”；失败时保留输出原因，不填成到位。

| 运行方式 | 播报步骤用时（秒） | 本次／播报后控制流程用时（秒） | 结束原因 | 现场表现 |
| :--- | :--- | :--- | :--- | :--- |
| STEP 07 不播报 | — | | | |
| STEP 08 先播报 | | | | |
| STEP 09 状态检查 | | | | |

### 5.2 检查点

- 能从通用检测结果中筛选`bottle`，说明多个候选时的选择规则。
- 能解释横向偏差、身体角速度和前向位移的含义。
- 能指出播报期间主程序的等待位置，解释播报后重新取图的原因。
- 已记录流程用时与实际结束原因，能说明状态检查的时机和局限。

### 5.3 思考题

1. 播报期间瓶子被移走，下一轮会怎样结束？若沿用旧检测框会怎样？
2. `reset_odom()`后前进1.2米，能否据此断定与瓶子的间距是1.2米？还需知道什么？
3. 当前问候采用固定文字。如果需要检测持续更新，同时接收语音指令，哪些工作需要分开执行？"""))


for i, cell in enumerate(cells, 1):
    cell["id"] = f"u7l2-{i:02d}"

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
