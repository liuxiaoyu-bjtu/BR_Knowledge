# -*- coding: utf-8 -*-
"""U7-L3生成器。2026-10-28以当前学生Notebook反向同步。
重新运行将覆盖对应Notebook；主稿为notebooks/U7-L3_多线程协作.ipynb。
P1修订稿，未登记确认①②；离线核查不代表真机验证。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U7-L3_多线程协作.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U7-L3：多线程协作
cells.append(md("""# U7-L3：多线程协作

**课程目标**

1. 能区分顺序执行与并发，说明检测线程、识别管理线程和运动主循环的职责。
2. 能使用共享记录、锁和停止标志传递检测结果与语音指令，解释指令读取、清空与运动模式的关系。
3. 能运行协作程序，记录指令和运动表现，分别核查Python线程与SDK识别任务是否结束。"""))

# 一、引入
cells.append(md("""## 一、引入

上一课以瓶子验证检测、播报和运动的顺序衔接。主程序等待语音播放时，不再调用取图和控制计算；相机和SDK内部仍可能继续工作。

本课回到来宾场景：检测持续更新来宾在画面中的横向偏差，语音识别接收“过来”“停下”，运动主循环读取这些结果，决定是否发送速度指令。程序接收固定关键词，不生成对话回复。

> 检测和识别各自等待时，运动主循环如何继续处理已有结果？"""))

# 二、线程与共享数据
cells.append(md("""## 二、线程与共享数据

### 2.1 执行关系

线程是同一程序的一条执行路径。`Thread(target=函数名)`指定要运行的函数，调用`start()`才启动。本课新建两个工作线程，加上原来的主线程，共同完成检测、识别管理和运动控制；调度、接口等待及锁仍可能让某条执行路径暂停。

| 执行位置 | 工作 | 传给主循环的信息 |
| :--- | :--- | :--- |
| 检测线程 | 取图、检测并计算偏差 | 来宾偏差、更新时间 |
| 识别管理线程 | 发起识别，等待停止请求并取消任务 | 保存SDK识别任务句柄 |
| SDK识别回调 | 收到文本后匹配关键词 | 最近一条运动指令 |
| 主线程 | 读取共享记录、计算并发送速度 | 当前运动模式及日志 |

U7-L1的订阅回调由SDK工作线程调用。本课的`on_text()`也由SDK调度，识别管理线程并不在循环内逐句识别；它负责识别任务的发起和收尾。"""))

# 2.2 锁与停止请求
cells.append(md("""### 2.2 锁与停止请求

主循环读出旧指令后需要清空指令。如果回调恰好在读取与清空之间写入新指令，新指令可能被清掉。`with lock:`把相关读写放在同一段受保护代码中；其他使用同一把锁的代码等待它退出后再访问。锁保护读写过程，不能保证检测和识别来自同一时刻。

`STOP`是`threading.Event()`创建的停止标志。`is_set()`读取标志，`set()`发出退出请求；工作线程须执行到检查位置才会响应。`join(timeout=...)`等待Python线程，随后用`is_alive()`判断是否退出。`daemon=True`仅影响解释器退出时的行为，正常收尾仍需主动检查。

SDK识别任务有自己的句柄。Python管理线程退出后，仍要用句柄的`done()`核查SDK任务终态；取消请求已提交不能代替任务已结束。"""))

# 三、并发实验
cells.append(md("""## 三、并发实验

⚠️ **注意**：机器人会前进和转向。准备平整通道，来宾在机器人前方可见、行进范围之外，全程由同学保护。程序没有自动测距停止，须在靠近前单独说“停下”；语音识别有延迟，异常时用按钮切回准备模式。

📌 **前置**：上一课运动已结束；场地安静；只使用单独的固定指令。清理旧任务前，不重复创建连接、线程或共享记录。

**STEP 01：首次连接，保存本课线程和任务句柄。**"""))

# 本格首次准备时运行一次。
cells.append(md("""本格首次准备时运行一次。"""))

# import time
cells.append(code("""import time
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech

robot = BoosterRobot()
detector = Detection(model="person")
speech = Speech(robot)
print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())

import threading
threads = []
asr_task = None"""))

# 3.1 初始化共享记录
cells.append(md("""### 3.1 初始化共享记录

**STEP 02：确认旧任务结束，再初始化。**

首次运行时`threads`为空、`asr_task`为`None`。重复实验须先执行STEP 08，确认旧线程与识别任务均已结束，再从本格重新开始。重新创建`STOP`可清除上一轮停止请求；不能在旧线程仍运行时重新绑定它。"""))

# if any(t.is_alive() for t in threads):
cells.append(code("""if any(t.is_alive() for t in threads):
    raise RuntimeError("旧线程尚未退出，请先执行STEP 08")
if asr_task is not None and not asr_task.done():
    raise RuntimeError("旧识别任务尚未结束，请保留句柄并执行STEP 08")

lock = threading.Lock()
STOP = threading.Event()
shared = {"guest_error": None, "vision_time": None, "command": None,
          "worker_error": None}
KP = 0.0005
SPEED = 0.2
MAX_YAW = 0.3
RUN_SECONDS = 20.0
MAX_VISION_AGE = 1.0  # 检测结果更新后允许使用的秒数，需现场调试"""))

# 3.2 检测线程
cells.append(md("""### 3.2 检测线程

**STEP 03：定义取图与检测函数。**

本课用`person`模型，在类别为`person`的候选中选评分最高的一条。课堂只安排一名来宾；此规则不构成跨帧身份跟踪。

`guest_error=None`表示没有可用来宾，`0`表示来宾位于画面中心。`vision_time`记录检测返回后的本地时间，主循环用它限制旧结果继续使用的时长；它不是图像采集时间。检测异常会保存错误并发出停止请求。"""))

# def detect_loop():
cells.append(code("""def detect_loop():
    try:
        while not STOP.is_set():
            img = robot.get_image(img_type="rgb")
            results = detector.detect(img.to_numpy())
            guest = None
            for r in results:
                if r.class_name == "person":
                    if guest is None or r.confidence > guest.confidence:
                        guest = r
            error = None
            if guest is not None:
                error = guest.bbox.center_x - img.width / 2
            with lock:
                shared["guest_error"] = error
                shared["vision_time"] = time.monotonic()
            time.sleep(0.2)
    except Exception as exc:
        with lock:
            shared["worker_error"] = str(exc)
        STOP.set()"""))

# 3.3 识别回调
cells.append(md("""### 3.3 识别回调

**STEP 04：定义文本处理函数。**

识别文字包含“停下”时写入`stop`，否则检查“过来”。停止关键词优先；关键词匹配无法理解否定，“不要过来”也可能触发前进，因此实验只单独说固定指令。

共享记录保存最近一条指令，快速连续输入可能覆盖尚未读取的指令。每次说完后观察模式日志，再发下一条。"""))

# def on_text(text):
cells.append(code("""def on_text(text):
    if STOP.is_set():
        return
    print("识别文本：", text)
    command = None
    if "停下" in text:
        command = "stop"
    elif "过来" in text:
        command = "approach"
    if command is not None:
        with lock:
            shared["command"] = command"""))

# **STEP 05：定义识别任务管理函数。**
cells.append(md("""**STEP 05：定义识别任务管理函数。**

函数保存`asr_task`，每隔0.2秒检查停止请求和任务是否结束。`global`表示给连接格中的句柄变量赋值，便于主程序收尾时继续检查原任务。`finally`在退出管理循环时请求取消并有限等待；若未确认结束，保留句柄供STEP 08复查。"""))

# def talk_loop():
cells.append(code("""def talk_loop():
    global asr_task
    try:
        asr_task = speech.recognize_stream(on_result=on_text)
        while not STOP.is_set() and not asr_task.done():
            time.sleep(0.2)
    except Exception as exc:
        with lock:
            shared["worker_error"] = str(exc)
    finally:
        STOP.set()
        if asr_task is not None and not asr_task.done():
            asr_task.cancel()
            asr_task.wait(timeout=3.0)"""))

# 3.4 运动主循环
cells.append(md("""### 3.4 运动主循环

**STEP 06：定义主循环。**

收到`approach`后，`mode`保持前进模式；清空`command`只是表示本次指令已经读取。之后即使没有新指令，也会按当前模式继续控制。目标丢失或结果更新超过`MAX_VISION_AGE`时发送零速度；目标重新出现后可能继续前进。收到`stop`则保持停止模式，直到再次收到`approach`。

身体角速度按当前偏差计算并限幅。主循环持续到20秒上限或停止标志置位；“停下”只改变运动模式，不提前结束代码格。主循环退出时，`finally`发送零速度并请求工作线程退出。"""))

# def motion_loop():
cells.append(code("""def motion_loop():
    mode = "idle"
    t0 = time.monotonic()
    try:
        while time.monotonic() - t0 < RUN_SECONDS and not STOP.is_set():
            with lock:
                error = shared["guest_error"]
                vision_time = shared["vision_time"]
                command = shared["command"]
                shared["command"] = None
            if command == "approach":
                mode = "approach"
                print("运动模式：前进")
            elif command == "stop":
                mode = "stop"
                print("运动模式：停止")
            fresh = vision_time is not None and time.monotonic() - vision_time <= MAX_VISION_AGE
            if mode == "approach" and error is not None and fresh:
                yaw_rate = max(-MAX_YAW, min(MAX_YAW, -KP * error))
                robot.set_velocity(SPEED, 0, yaw_rate)
            else:
                robot.set_velocity(0, 0, 0)
            time.sleep(0.5)
    finally:
        robot.set_velocity(0, 0, 0)
        STOP.set()"""))

# 3.5 启动与退出
cells.append(md("""### 3.5 启动与退出

**开始下面程序前，机器人应处于行走模式。** 如果当前不在行走模式：先用按钮切到准备模式，等机器人站直站稳；再切到行走模式。确认模式后再运行代码。

**STEP 07：启动工作线程并运行主循环。**

`Thread`先创建线程对象，`start()`才执行函数；主循环紧接着在当前代码格运行。不要在启动线程后留出人工等待格。STEP 02～06应已顺序运行；下面的检查用于拒绝直接重复启动。主循环结束或中断后都要继续执行STEP 08。"""))

# if STOP.is_set() or any(t.is_alive() for t in threads):
cells.append(code("""if STOP.is_set() or any(t.is_alive() for t in threads):
    raise RuntimeError("请先收尾，再从STEP 02初始化")
if asr_task is not None and not asr_task.done():
    raise RuntimeError("旧识别任务未结束，不能重开")
threads = [threading.Thread(target=detect_loop, daemon=True),
           threading.Thread(target=talk_loop, daemon=True)]
try:
    for t in threads:
        t.start()
    motion_loop()
finally:
    robot.set_velocity(0, 0, 0)
    STOP.set()
print("主循环已结束，已请求工作线程退出；继续执行STEP 08")"""))

# **STEP 08：核查线程与识别任务。**
cells.append(md("""**STEP 08：核查线程与识别任务。**

`join()`返回后还需检查`is_alive()`。识别任务取消后检查`done()`，未结束时保留原句柄，稍后重新运行本格；全部结束前不得重新初始化或启动。日志可能交错，按“识别文本”“运动模式”“线程”“识别任务”的标签阅读。发送零速度不等于已用现场观测证明机器人停稳。"""))

# robot.set_velocity(0, 0, 0)
cells.append(code("""robot.set_velocity(0, 0, 0)
STOP.set()
for t in threads:
    if t.ident is not None:
        t.join(timeout=3.0)
    print("线程：", t.name, "仍在运行：", t.is_alive())
if asr_task is not None:
    if not asr_task.done():
        asr_task.cancel()
        asr_task.wait(timeout=3.0)
    print("识别任务：", asr_task.status, "已结束：", asr_task.done())
    if asr_task.status == "FAILED":
        print("识别错误：", asr_task.error)
with lock:
    print("工作线程错误：", shared["worker_error"])
ready = not any(t.is_alive() for t in threads) and (asr_task is None or asr_task.done())
print("本次资源全部结束：", ready)
print("已发送零速度指令，请观察机器人是否停稳")"""))

# 四、收尾
cells.append(md("""## 四、收尾

先用按钮把机器人切回**准备模式**，等它站直站稳；再由人工扶着切到**阻尼模式**（damping），扶机器人坐下，确认坐稳。不要从行走模式直接切到阻尼模式。"""))

# 五、观察与记录
cells.append(md("""## 五、观察与记录

### 5.1 分工记录

| 执行位置 | 读写的数据或句柄 | 等待位置 | 退出判断 |
| :--- | :--- | :--- | :--- |
| 检测线程 | | | |
| 识别管理线程与SDK回调 | | | |
| 运动主循环 | | | |

### 5.2 指令与运动

| 发出的指令 | 识别文本 | 模式日志 | 机器人表现 |
| :--- | :--- | :--- | :--- |
| 过来 | | | |
| 停下 | | | |

线程是否全部退出：______；SDK识别任务状态：______；`done()`结果：______。

### 5.3 检查点

- 能指出两个自建线程、主线程及SDK回调的职责，区分识别与对话生成。
- 能解释锁保护的读写过程，以及`command`清空后`mode`为何仍可保持。
- 已观察固定指令对模式的影响，并核对目标丢失或结果变旧时的处理。
- 已分别核查线程退出和SDK任务终态，重复运行前重新初始化。

### 5.4 思考题

1. 减小检测循环的0.2秒间隔，处理频率和计算开销可能怎样变化？减小识别管理循环的间隔，会直接提高SDK识别速度吗？
2. 主循环读出指令后、清空前，回调写入新指令会有什么后果？同一把锁怎样保护这段操作？
3. 识别管理线程已经退出，但`asr_task.done()`仍为假时，为什么还不能重开识别？"""))


for i, cell in enumerate(cells, 1):
    cell["id"] = f"u7l3-{i:02d}"

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
