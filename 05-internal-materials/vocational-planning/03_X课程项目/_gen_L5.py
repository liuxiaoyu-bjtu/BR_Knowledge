# -*- coding: utf-8 -*-
"""U2-L1 实训手册生成器（P1 实验代码骨架版）。
重新运行本脚本将覆盖生成 notebooks/U2-L1_ROS2通信基础.ipynb。
本版仅含 P1 内容：ROS2 命令行观测实验的代码 cell + 极简 markdown 脚手架（实验标题/目标占位）。
不写完整知识讲解、不写课程大纲映射块（映射块为 P2 阶段补全）。
"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L1_ROS2通信基础.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []
# # U2-L1：ROS2 通信基础（课头：课程级，仅课程名 + 课程目标，不写安全/前置）
cells.append(md("# U2-L1：ROS2 通信基础\n\n**课程目标**\n\n1. 理解为什么机器人系统需要 ROS2——多进程通信需求；认识 Node（节点）、Topic（话题）、发布-订阅、Message（消息）等基础通信概念（ROS2 通信五元组）。\n2. 掌握 ROS2 话题观测四件套（`ros2 topic list` / `echo` / `hz` / `info`），能读懂 K1 当前系统中的话题与消息类型。\n3. 通过一次简单的发布/订阅体验，理解「发布者与订阅者按话题名解耦」这一 ROS2 核心机制。\n"))
# ## 一、ROS2 系统观察：话题观测四件套（实验头：实验级，含名称/目标/⚠️安全/📌前置）
cells.append(md("## 一、ROS2 系统观察：话题观测四件套\n\n**目标**：在本机（或 K1）已加载 ROS2 环境的终端中，用四件套命令观察机器人当前的话题通信状况，建立「ROS2 不是操作系统、而是机器人软件之间的通信框架」的直观认识（核心概念 C01 节点 / C02 话题 / C05 消息）。\n\n⚠️ **安全**：本实验为**观测课**，仅读取系统信息，**不发送任何运动 / 动作指令**；若误调用控制服务导致机器人移动，立即按下背部 `STAND` 按钮回到准备模式。运行前确认 ROS2 环境已加载（Booster Studio 已预置；独立环境需先 `source /opt/ros/humble/setup.bash`）。多组共用机器人时，话题命名加组号后缀避免互相干扰。\n\n📌 **前置**：已完成 U1 四课（连接、模式、运动、头/步态/动作）；本实验不依赖 `BoosterRobot()` SDK，而是直接操作 ROS2 命令行。\n"))
# ### 1.1 确认 ROS2 环境
cells.append(md("### 1.1 确认 ROS2 环境\n\n运行下面单元格确认 `ros2` 命令可用；若报 `command not found`，请先在终端执行 `source /opt/ros/humble/setup.bash` 后再启动本 notebook 的 kernel。\n"))
# [code] ros2 --version
cells.append(code("!ros2 --version"))
# ### 1.2 列出当前话题（list）
cells.append(md("### 1.2 列出当前话题（list）\n\n`ros2 topic list` 列出系统中所有正在广播的话题。每一行是一个**话题（Topic）**——一条持续的数据通道。\n"))
# [code] ros2 topic list
cells.append(code("!ros2 topic list"))
# ### 1.3 查看单个话题详情（info）
cells.append(md("### 1.3 查看单个话题详情（info）\n\n`ros2 topic info <话题名>` 显示该话题的**消息类型（Type）**、发布者数量（Publisher count）与订阅者数量（Subscription count）。下面以图像话题为例；若本机话题名不同，先用 `ros2 topic list` 找到真实图像话题名再替换。\n"))
# [code] ros2 topic info /camera/image_raw
cells.append(code("!ros2 topic info /camera/image_raw    # 若本话题不存在，先 ros2 topic list 查看真实图像话题名（如 /boostercamera/head/rgb）再替换"))
# ### 1.4 订阅并查看一条消息（echo --once）
cells.append(md("### 1.4 订阅并查看一条消息（echo）\n\n`ros2 topic echo <话题名>` 实时打印该话题发布的消息；`--once` 只打印最新一条后退出，适合快速查看消息结构。\n"))
# [code] ros2 topic echo /camera/image_raw --once
cells.append(code("!ros2 topic echo /camera/image_raw --once"))
# ### 1.5 测量发布频率（hz）
cells.append(md("### 1.5 测量发布频率（hz）\n\n`ros2 topic hz <话题名>` 测量话题的发布频率（Hz）。运行后会持续统计，请手动中断（菜单「内核 → 中断」或按 I/I）后继续。\n"))
# [code] ros2 topic hz /camera/image_raw
cells.append(code("!ros2 topic hz /camera/image_raw"))
# ## 二、发布与订阅体验（五元组的 pub / sub）
cells.append(md("## 二、发布与订阅体验（五元组的 pub / sub）\n\n**目标**：亲手发布一条字符串消息到自建话题，再用 `echo` 订阅观察，体会「发布者（C03）与订阅者（C04）不需要互相知道对方、只约定同一话题名与消息类型」的解耦本质（轻量概念 E01 事件循环 / E02 回调的雏形）。\n\n<font color=\"red\">本实验仅向自建话题 `/greeting_u2l1` 发布一条字符串，**不控制机器人**；若多组共用环境，请把话题名改为 `/greeting_u2l1_groupN`（N 为组号）以免互相干扰。</font>\n"))
# ### 2.1 启动发布者（后台进程）
cells.append(md("### 2.1 启动发布者（后台进程）\n\n下面用 Python `subprocess` 在后台启动一个 `ros2 topic pub`，每秒发布一次问候消息；随后在 2.2/2.3 用 `echo` 观察，最后在 2.4 自动停止发布者。\n"))
# [code] 启动后台 publisher
cells.append(code("import subprocess, time, signal, os\n\nTOPIC = \"/greeting_u2l1\"   # 多组请改为 /greeting_u2l1_groupN\npub = subprocess.Popen(\n    [\"ros2\", \"topic\", \"pub\", \"-r\", \"2\", TOPIC, \"std_msgs/String\", \"data: Hello K1\"],\n    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n)\nprint(\"发布者已启动，PID =\", pub.pid, \" 话题 =\", TOPIC)\ntime.sleep(2)"))
# ### 2.2 订阅并查看（echo / info）
cells.append(md("### 2.2 订阅并查看（echo / info）\n\n发布者已在后台运行。下面查看该话题的发布/订阅数量，并读取一条消息。\n"))
# [code] topic info + echo --once
cells.append(code("!ros2 topic info /greeting_u2l1\nprint(\"--- 读取一条消息 ---\")\n!ros2 topic echo /greeting_u2l1 --once"))
# ### 2.3 体验「多订阅者」
cells.append(md("### 2.3 体验「多订阅者」\n\nROS2 允许同一话题有多个订阅者。再启动一个 `echo`（后台），然后查看 `info` 中 Subscription count 是否从 1 变为 2——这正是「发布者不感知订阅者」的解耦体现。\n"))
# [code] 第二个订阅者 + info
cells.append(code("sub = subprocess.Popen(\n    [\"ros2\", \"topic\", \"echo\", \"/greeting_u2l1\"],\n    stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n)\nprint(\"第二个订阅者已启动，PID =\", sub.pid)\ntime.sleep(2)\n!ros2 topic info /greeting_u2l1\nsub.send_signal(signal.SIGINT); sub.wait()\nprint(\"第二个订阅者已停止\")"))
# ### 2.4 停止发布者并收尾
cells.append(md("### 2.4 停止发布者并收尾\n"))
# [code] 停止发布者
cells.append(code("pub.send_signal(signal.SIGINT); pub.wait()\nprint(\"发布者已停止，话题 /greeting_u2l1 已无发布者\")"))
# ## 三、观察与记录（非代码占位）
cells.append(md("## 三、观察与记录（非代码）\n\n| 观察项 | 你看到的输出 | 说明 |\n| --- | --- | --- |\n| `ros2 topic list` 话题数量 |  | 系统里大概有几个数据通道？ |\n| 图像话题的 Type |  | 是 `sensor_msgs/msg/Image` 吗？ |\n| 图像话题的 Pub / Sub 数 |  | 谁在发？谁在看？ |\n| `hz` 测得的帧率 |  | 大致多少 Hz？ |\n| 发布/订阅实验中 Sub count 的变化 |  | 多一个订阅者为啥发布者无感？ |\n\n> 想一想：为什么 `ros2 topic pub` 和 `ros2 topic echo` 两个互不相识的终端，能通过 `/greeting_u2l1` 这个名字交换消息？如果把话题名改错一个字母会怎样？\n"))
nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
