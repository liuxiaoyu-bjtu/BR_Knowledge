# -*- coding: utf-8 -*-
"""U2-L4 实训手册生成器（单源，重新运行将覆盖 notebooks/U2-L4_状态监测与融合.ipynb）。

内容依据：X课程大纲-v4（U2-L4 状态监测与融合）、U2-L2/L3 已定稿体例（含用户手动调整后的风格）。
SDK 事实（源码 boosteros 内省确认）：
  - get_battery() -> BatteryState：percentage(0-100) / voltage(可 None) / current(可 None，负=放电)
    / power_supply_status("Charging"/"Discharging"/"Full"/"NotCharging"/"Unknown")
    / is_charging / is_low(<20%) / is_critical(<10%) / temperature / charge / capacity / serial_number
    （注意：电池数据不可用时会返回 percentage=100 的兜底假数据，此点不进学生文件）
  - get_fall_down_state() -> FallDownState：state("normal"/"falling"/"fallen"/"getting_up"/"unknown")
    / recoverable(能否自行起身) / is_normal / is_falling / has_fallen / is_getting_up / timestamp
  - get_up(on_done, on_status_change) -> TaskHandle：起身任务，把机器人从倒地拉起回到 walk 站立；不可取消
  - get_mode() -> "damping"/"prepare"/"walk"/"custom"
表述规范：遵循《去AI化表达记录》§1–§19；安全约束遵规则 §3.5 / §3.6。
风格对齐 U2-L2/L3 手动版：传感器「（1）是什么（2）功能与作用（3）获取数据」三段式、
先 print 返回值对象再给属性表格、真实数据用红字「你会发现」、安全态表述 DAMP/prepare 站姿。
"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L4_状态监测与融合.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# # U2-L4：状态监测与融合
cells.append(md("""# U2-L4：状态监测与融合

**课程目标**

1. 能说明电池的剩余电量、电压、充放电状态各表示什么，以及为什么低电量要及时告警。
2. 能说明 K1 摔倒检测的几种状态及其先后变化，以及前倾、后仰触发摔倒保护的机制。
3. 能使用 `get_battery()`、`get_fall_down_state()`、`get_mode()` 读取电池、摔倒状态与当前模式。
4. 能编写一个定时循环，综合电量与摔倒状态做出判断，完成低电量告警。
"""))

# ## 课程大纲映射（审核用）
cells.append(md("""## 课程大纲映射（审核用）

| 轻任务 | 对应 cell | 核心概念 | 轻量概念 |
| --- | --- | --- | --- |
| ⑤ 状态监视器：实时显示电池%/摔倒状态/当前模式 | 实验一 4.2、4.3 | — | C09 定时器（固定间隔循环） |
| ⑥ 安全守护者：摔倒自动 `get_up()`，电量<20% 告警 | 实验二 5.1、5.2 | **B08 多传感器融合**（综合判断而非各看各的） | — |

- 编程线接口覆盖：`get_battery()`、`get_fall_down_state()`、`get_mode()`、`get_up()`。

> 本映射块用于大纲对齐审核；导出 PDF 版本时移除此块。
"""))

# ## 一、电池与电源管理
cells.append(md("""## 一、电池与电源管理

### 1.1 电池的三个数

电池给机器人供电。SDK 里读电池，看到的是三个量：

| 量 | 含义 | 单位 |
| --- | --- | --- |
| `percentage` | 剩余电量，0 到 100 | % |
| `voltage` | 电压 | V（伏特） |
| `power_supply_status` | 充放电状态 | Charging 充电中 / Discharging 放电中 / Full 已充满 / NotCharging 未充电 |

这三个数运维里天天看：电量决定还能跑多久，电压反映电池健康，充放电状态决定现在该插电还是能干活。

### 1.2 低电量为什么要告警

电量低不能硬撑。人形机器人走路全靠电机发力，电量掉下去，电机出力变小、平衡控制变差，摔的概率升高；要是走到一半断电，机器人会直接瘫倒，还可能摔坏关节。所以真实机器人都会设一条告警线。K1 的 SDK 里，电量低于 20% 就是 `is_low`，低于 10% 是 `is_critical`。到了告警线，先停下充电，再继续任务。

### 1.3 获取电池数据

调用 `get_battery()` 可以拿到电池数据。
"""))

cells.append(code("""bat = robot.get_battery()

print("获取的返回值：", bat)"""))

cells.append(md("""`get_battery()` 的返回值是 `BatteryState` 类型，包含如下信息：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `percentage` | `float` | 剩余电量百分比，0–100 |
| `voltage` | `float` 或 `None` | 电压，单位 V |
| `current` | `float` 或 `None` | 电流，单位 A，负数表示放电 |
| `power_supply_status` | `str` | 充放电状态字符串 |
| `is_charging` | `bool` | 是否在充电 |
| `is_low` | `bool` | 电量是否低于 20% |
| `is_critical` | `bool` | 电量是否低于 10% |

下面读出几个关键字段查看。
"""))

cells.append(code("""bat = robot.get_battery()

print("剩余电量：", round(bat.percentage, 1), "%")
print("电压：", bat.voltage, "V")
print("充放电状态：", bat.power_supply_status)
print("是否在充电：", bat.is_charging)
print("是否低电量：", bat.is_low)"""))

cells.append(md("""机器人待机时，电量读数比较稳；一旦让它走路，电机开始发力，电量会掉得比静止时快。这也是「看状态要在干活之前看」的原因——出发前先确认电量够不够跑完这一场。
"""))

# ## 二、摔倒检测与起身
cells.append(md("""## 二、摔倒检测与起身

### 2.1 摔倒状态的几档

K1 身上有一套摔倒检测，靠 IMU 和关节角度判断自己是不是要摔了。它把机器人状态分成几档：

| 状态 `state` | 机器人此刻在干什么 |
| --- | --- |
| `normal` | 正常站立或坐着，姿态稳定 |
| `falling` | 正在摔倒，身体倾斜已经超过安全线 |
| `fallen` | 已经摔倒在地 |
| `getting_up` | 正在起身 |
| `unknown` | 还没收到有效状态 |

正常时读出来是 `normal`。往前一栽或往后一仰，超过安全角度，状态会从 `normal` 变成 `falling`，倒地后变成 `fallen`。

### 2.2 前倾与后仰的保护

人形机器人重心高，前倾、后仰是最常见的两种摔法。K1 用 IMU 的俯仰角（pitch）判断：身体往前倒、pitch 超过阈值，判为前倾；往后仰、pitch 反向超过阈值，判为后仰。一旦判定要摔，控制系统先进入保护动作——收起胳膊、放低重心，尽量让机器人「软着陆」，减少对关节和结构的冲击。这一步就是 U2-L2 里提过的「倾斜超过安全阈值触发 PROTECT 保护模式」。

### 2.3 摔倒之后怎么起身

机器人倒地后，调用 `get_up()`，它会自己从倒地的姿势重新站起来，回到 walk 站立状态。这个动作返回一个任务句柄（`TaskHandle`），一旦开始就不能中途取消——和 U1-L4 做预定义动作时看到的任务句柄是同一类。

### 2.4 获取摔倒状态

调用 `get_fall_down_state()` 可以拿到当前摔倒状态。
"""))

cells.append(code("""fs = robot.get_fall_down_state()

print("获取的返回值：", fs)"""))

cells.append(md("""`get_fall_down_state()` 的返回值是 `FallDownState` 类型，包含如下信息：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `state` | `str` | 当前摔倒状态：`normal` / `falling` / `fallen` / `getting_up` / `unknown` |
| `recoverable` | `bool` | 摔倒后能否自行起身 |
| `timestamp` | `float` | 秒级时间戳 |
| `is_normal` | `bool` | 是否正常 |
| `has_fallen` | `bool` | 是否已摔倒 |
| `is_getting_up` | `bool` | 是否正在起身 |

下面读出几个关键字段查看。
"""))

cells.append(code("""fs = robot.get_fall_down_state()

print("摔倒状态：", fs.state)
print("能否自行起身：", fs.recoverable)
print("是否正常：", fs.is_normal)
print("是否已摔倒：", fs.has_fallen)"""))

cells.append(md("""机器人安静站立或坐着时，读出来是 `normal`。课堂上要看到 `falling`、`fallen` 这几个状态，需要真实地让机器人前倾或后仰，这一步有风险，由教师演示，学生不自行操作。
"""))

# ## 三、综合判断
cells.append(md("""## 三、综合判断

前两课是一路一路单独读：电池读电池，IMU 读 IMU，里程计读里程计。真到用的时候，很多判断要几路数据合起来看。

比如「现在要不要停」：

- 只看电量：电量低就停，简单。
- 再带上模式一起看：电量低、又在 walk 走路，更该停；电量低、但机器人本来就在趴着休息，就没那么急。

再比如「摔倒之后怎么办」：

- 摔倒状态是 `fallen`，还要看 `recoverable` 能不能自行起身：能，就调 `get_up()`；不能，就得人工去扶。

把几路传感器数据放到一起、综合出一个结论，就是**多传感器融合**。它的意思就是综合判断，不各看各的。真到做控制的时候，比如让机器人走直线，也常常要同时看里程计和 IMU 两路数据。
"""))

# ## 四、实验一：状态监视器
cells.append(md("""## 四、实验一：状态监视器

**实验名称**：状态监视器

**实验目标**：定时循环读取电池、摔倒状态与当前模式，实时显示这三项，观察它们的变化。

⚠️ **安全**：本课有两次实验。

- **本次状态监视器**只读数据，不发送运动 / 动作指令，机器人保持坐姿、趴姿（DAMP 模式）或 `prepare` 模式的站姿即可，<font color="red">不需要进入 walk 模式</font>。
- **实验二 安全守护者**里的「起身动作」会让机器人运动，需要在教师监督下进行。

**前置准备**：K1 已开机并与电脑建立连接（见 U1-L1）；已完成 U1-L2（模式切换与安全）、U2-L2（传感器速览）、U2-L3（IMU 与里程计）。

### 4.1 连接机器人
"""))

cells.append(code("""from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()
print("已连接 K1")"""))

# ### 4.2 读三项
cells.append(md("""### 4.2 先各读一次

先把三路数据各读一次，确认接口都通。
"""))

cells.append(code("""bat = robot.get_battery()
fs = robot.get_fall_down_state()
mode = robot.get_mode()

print("电量：", round(bat.percentage, 1), "%")
print("摔倒状态：", fs.state)
print("当前模式：", mode)"""))

# ### 4.3 定时循环
cells.append(md("""### 4.3 定时循环实时显示

像 U2-L3 那样，用固定间隔循环做一个「监视器」，每 1 秒刷新一次，连刷 10 秒。
"""))

cells.append(code("""import time

print("状态监视器启动，每 1 秒刷新一次，共 10 秒。")
print()
print(" 序号   电量     摔倒状态     当前模式")
print("-" * 44)

for i in range(10):
    bat = robot.get_battery()
    fs = robot.get_fall_down_state()
    mode = robot.get_mode()
    print(f"  {i:>2}   {bat.percentage:5.1f}%   {fs.state:<10}   {mode}")
    time.sleep(1)"""))

cells.append(md("""<font color="red">你会发现：</font>机器人安静不动时，这三项基本不变——电量偶尔降 0.1%，摔倒状态一直是 `normal`，模式那列也不动。给机器人换个姿势，或者轻轻拨一下，看摔倒状态那列会不会跟着变。
"""))

# ## 五、实验二：安全守护者
cells.append(md("""## 五、实验二：安全守护者

**实验名称**：安全守护者

**实验目标**：编写判断逻辑——电量低于 20% 打印告警，检测到摔倒时调用 `get_up()` 起身。

<font color="red">本实验的「起身动作」会让机器人运动。起身前确认周围 1 米内没有人；`get_up()` 仅在机器人确实摔倒、教师监督时运行，学生不自行触发。</font>

### 5.1 低电量告警
"""))

cells.append(code("""import time

for i in range(10):
    bat = robot.get_battery()
    if bat.is_low:
        print(f"第 {i} 秒：电量 {bat.percentage:.1f}%，低于 20%，请充电")
    else:
        print(f"第 {i} 秒：电量 {bat.percentage:.1f}%，正常")
    time.sleep(1)"""))

cells.append(md("""<font color="red">你会发现：</font>电量在 20% 以上时，循环里一直打印「正常」，看不到告警行。想看看告警长什么样，把判断条件临时改成 `bat.percentage < 60` 再跑一遍——这只是为了看到告警的输出效果，真正的告警线仍然是 20%。

### 5.2 摔倒起身
"""))

cells.append(md("""机器人摔倒后，用 `get_up()` 让它自己重新站起来。这个动作幅度大，返回一个不可取消的任务句柄。下面的代码仅在机器人确实摔倒、周围清空、教师监督时运行。
"""))

cells.append(code("""# 仅当机器人确实摔倒、周围清空、教师监督时运行这一格
handle = robot.get_up()
print("已下发起身任务，机器人开始起身")"""))

cells.append(md("""起身完成后机器人回到 walk 站立状态。之后按 U1-L2 学过的收尾流程处理：先切回 `prepare` 站稳，再由人工扶着让机器人坐下，确认坐稳后进入 `damping`。
"""))

# ## 六、观察与记录
cells.append(md("""## 六、观察与记录

| 观察项 | 你看到的 | 说明 |
| --- | --- | --- |
| 剩余电量 |  | 百分比是多少？ |
| 电压 |  | 单位 V |
| 充放电状态 |  | Charging / Discharging / Full？ |
| 是否低电量 |  | `is_low` 是 True 还是 False？ |
| 摔倒状态 |  | 正常时是什么？ |
| 能否自行起身 |  | `recoverable` 的值 |
| 当前模式 |  | damping / prepare / walk？ |
| 定时循环里三项的变化 |  | 10 秒内电量、摔倒状态、模式有没有变化？ |

**想一想**

1. 「电量低」这一条，为什么还要结合「当前模式」一起看才有意义？
2. 检测到摔倒状态是 `fallen`，程序直接调 `get_up()` 之前，还要先看哪个字段？为什么？
3. 状态监视器和安全守护者的差别在哪——一个只是显示，一个要动手，这个差别在程序里是怎么体现的？
"""))

# ## 七、扩展阅读
cells.append(md("""## 七、扩展阅读：机器人的自我保护机制

真正投入使用的机器人，几乎都有一套自我保护机制，本课的「摔倒检测 + 低电量告警」只是其中两环。工业机器人和服务机器人常见的还有：

| 机制 | 触发条件 | 机器人做什么 |
| --- | --- | --- |
| 急停按钮 | 人按下 | 立即断电、所有关节锁死 |
| 电子围栏 | 人进入危险区 | 减速或停机 |
| 碰撞检测 | 关节力矩突变 | 停下并后退一步 |
| 低电量返航 | 电量低于阈值 | 自动回充电桩 |

这套机制的设计和测试，是机器人「安全测试 / 运维」岗位的核心工作：故意制造前倾、后仰、撞墙、断电这些场景，确认机器人在每种情况下都能安全停住或恢复，不伤人、不摔坏自己。

本课读到的摔倒状态和电量，正是这些保护动作要依据的那几路数据。
"""))

nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
