# -*- coding: utf-8 -*-
"""U7-L1生成器。2026-10-28以当前学生Notebook反向同步。
重新运行将覆盖对应Notebook；主稿为notebooks/U7-L1_多传感器订阅.ipynb。
P1修订稿，未登记确认①②；离线核查不代表真机验证。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U7-L1_多传感器订阅.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U7-L1：多传感器订阅
cells.append(md("""# U7-L1：多传感器订阅

**课程目标**

1. 能比较按需读取与订阅的取数方式，说明主程序与订阅回调的执行关系。
2. 能同时订阅相机、IMU和里程计，记录收到的条数、估算接收速率及末次时间戳，并结束订阅。
3. 能在时间戳单位和计时基准一致的前提下，计算末次数据的时间差，解释正负号，并区分时间差观察与数据同步。"""))

# 一、引入
cells.append(md("""## 一、引入

U4已把图像中的目标偏差和里程计读数用于同一个运动任务。图像和里程计各自更新，程序读取的两份数据可能对应不同的时刻；目标或机器人移动时，这种差异会影响判断。

本课同时接收相机、IMU和里程计数据，记录接收条数及末次时间戳，观察各路数据的更新情况。

> 联合使用传感器数据前，怎样检查它们记录的时刻相差多少？"""))

# 二、读取与订阅
cells.append(md("""## 二、读取与订阅

### 2.1 按需读取

`get_image()`、`get_imu()`、`get_odom()`等接口由主程序主动调用，返回最近的缓存数据。调用时刻与数据采集时刻可能不同，采集时刻需查看数据的时间戳。

### 2.2 持续接收

`subscribe_image()`、`subscribe_imu()`、`subscribe_odom()`先登记回调函数，SDK随后把到达的数据交给回调处理。实际收到的数量受推送、队列和处理速度影响。

| 比较项 | 按需读取 | 订阅 |
| :--- | :--- | :--- |
| 发起方式 | 主程序调用读取接口 | 主程序登记回调，SDK在数据到达时调用 |
| 返回内容 | 最近的缓存数据 | 订阅句柄；数据通过回调接收 |
| 执行位置 | 本课主程序 | SDK工作线程 |
| 结束方式 | 一次调用返回 | 用句柄调用`unsubscribe()` |

线程是程序的一条执行路径。本课主程序在`sleep()`中等待时，SDK工作线程仍可执行回调，更新计数和时间戳；主程序稍后读取这些记录。本课用`with`上下文管理订阅句柄，退出上下文时自动调用退订。"""))

# 2.3 时间戳与队列
cells.append(md("""### 2.3 时间戳与队列

| 数据 | 时间戳读法 |
| :--- | :--- |
| 图像 | `image.header.timestamp` |
| IMU | `imu.timestamp` |
| 里程计 | `odom.timestamp` |

**相减前须由教师核实本机三路时间戳的单位和计时基准。** 单位为秒且计时基准一致时，差值乘1000可换算为毫秒。单位或基准尚未核实时，先记录原值，暂不解释差值。

本课比较各路最后收到的数据。两份时间戳之差表示它们记录的时刻相隔多久，不能直接表示数据距当前时刻有多久，也没有完成同步配对或重采样。

数据到达快于回调处理时，待处理数据会排队。传感器订阅的`queue_size`默认是0，表示不设上限；设置有限容量后，`overflow`决定队列满时的处理：`block`等待、`drop_oldest`丢弃最旧的待处理数据、`drop_newest`丢弃新到的数据，默认是`drop_oldest`。U5-L1的音频流排队对象是声音块，这里是待处理的传感器数据；参数约束须分别查接口。本实验沿用传感器订阅默认设置，进行短时计数。"""))

# 三、订阅实验
cells.append(md("""## 三、订阅实验

⚠️ **注意**：本课读取传感器数据，机器人保持坐姿或站姿，无需进入行走模式。

📌 **前置**：机器人已开机、配网；上一课的订阅已退订。

**STEP 01：连接机器人。**"""))

# import time
cells.append(code("""import time

from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()

print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())"""))

# **STEP 02：定义回调，订阅并观察5秒。**
cells.append(md("""**STEP 02：定义回调，订阅并观察5秒。**

`count`保存收到的条数，`last`保存各路末次时间戳。每个回调更新对应记录，避免频繁打印影响处理。先定义函数，再把函数名传给订阅接口。

下一格包含订阅、等待和退订，按顺序完整运行。主程序等待期间，回调仍可更新记录；`with`管理三份订阅句柄，正常结束或中断等待时都会退出上下文并退订。退订后再读取统计值。"""))

# SECONDS = 5.0                   # 设置的观察时长（秒）
cells.append(code("""SECONDS = 5.0                   # 设置的观察时长（秒）

count = {"图像": 0, "IMU": 0, "里程计": 0}
last = {}                       # 各路最后收到的数据时间戳

def on_image(image):
    count["图像"] += 1
    last["图像"] = image.header.timestamp

def on_imu(imu):
    count["IMU"] += 1
    last["IMU"] = imu.timestamp

def on_odom(odom):
    count["里程计"] += 1
    last["里程计"] = odom.timestamp

with robot.subscribe_image(on_image), robot.subscribe_imu(on_imu), robot.subscribe_odom(on_odom):
    print(f"三路已订阅，观察 {SECONDS:.0f} 秒")
    time.sleep(SECONDS)
print("已退出订阅上下文，三路均已退订")"""))

# **STEP 03：查看接收条数和估算接收速率。**
cells.append(md("""**STEP 03：查看接收条数和估算接收速率。**

条数除以设置的5秒，近似表示本程序每秒收到多少条数据。三路依次订阅和退订，实际观察时段略有差异；结果还受传输、调度和回调处理影响，不能直接当成硬件采样频率。"""))

# for name in ["图像", "IMU", "里程计"]:
cells.append(code("""for name in ["图像", "IMU", "里程计"]:
    t = last.get(name)
    if t is None:
        print(f"{name}：这 {SECONDS:.0f} 秒里一条都没收到")
    else:
        print(f"{name}：{count[name]:4d} 条，约 {count[name] / SECONDS:5.1f} 条/秒，"
              f"最后一条的时间戳 {t:.3f}")"""))

# **STEP 04：比较末次时间戳。**
cells.append(md("""**STEP 04：比较末次时间戳。**

确认单位为秒且计时基准一致后，将下一格的`TIMESTAMPS_VERIFIED`改为`True`。输出按“前一路－后一路”计算：正值表示前一路较晚，负值表示前一路较早。例如图像－IMU为−20毫秒，表示这份图像比这份IMU早20毫秒。

完整重复STEP 02～04三次，每次都先结束订阅再重新开始。比较各组差值的最小值和最大值，观察本次采集的变化范围。"""))

# TIMESTAMPS_VERIFIED = False  # 教师核实单位为秒且计时基准一致后改为True
cells.append(code("""TIMESTAMPS_VERIFIED = False  # 教师核实单位为秒且计时基准一致后改为True
names = ["图像", "IMU", "里程计"]

if not TIMESTAMPS_VERIFIED:
    print("先核实时间戳单位与计时基准，本次仅记录原值")
else:
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if a in last and b in last:
                print(f"{a}－{b}：{(last[a] - last[b]) * 1000:+.1f} 毫秒")
            else:
                print(f"{a}－{b}：缺少数据，无法计算")"""))

# 四、观察与记录
cells.append(md("""## 四、观察与记录

### 4.1 接收情况

| 传感器 | 收到条数 | 估算接收速率（条/秒） | 末次时间戳 |
| :--- | :--- | :--- | :--- |
| 图像 | | | |
| IMU | | | |
| 里程计 | | | |

### 4.2 末次数据的时间差

时间戳单位：______；计时基准是否核实：______。未核实时填“待核实”。

| 前一路－后一路 | 第1次（毫秒） | 第2次 | 第3次 | 最小值／最大值 |
| :--- | :--- | :--- | :--- | :--- |
| 图像－IMU | | | | |
| 图像－里程计 | | | | |
| IMU－里程计 | | | | |

### 4.3 检查点

- 能说明按需读取与订阅各由谁发起，主程序等待时回调为何仍可更新数据。
- 已记录各路接收条数与估算接收速率，并确认全部订阅已退订。
- 能说明时间戳相减的前提，以及正、负差值分别表示什么。
- 能区分末次数据的相对时间差、数据距当前时刻的年龄和同步处理。

### 4.4 思考题

1. 图像比IMU早几十毫秒，目标和机器人都在转动时，联合判断方位可能受什么影响？
2. 回调处理慢于数据到达时，有限队列中等待或丢弃各有什么代价？
3. 同样的时间差，对静止目标与快速移动目标有何不同影响？本课记录是否足以制定通用同步阈值？"""))


for i, cell in enumerate(cells, 1):
    cell["id"] = f"u7l1-{i:02d}"

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
