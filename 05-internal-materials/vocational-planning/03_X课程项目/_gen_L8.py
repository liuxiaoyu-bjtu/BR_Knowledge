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
【2026-10-19 补录】此前 _regen_from_nb.py 的 DOC 与 PAIRS 都漏了本文件（对账 PAIRS 里有、反向重建
PAIRS 里没有），故 _gen_L8.py 一直靠手改维持单源。本次补登 DOC ＋ PAIRS，此后可正常反向重建。
同日 U2 四课补 P3：末尾按 U1-L4 体例加「检查点、思考题与学习评价」（X.1 / X.2 / X.3），
「观察与记录」里的「想一想」移入 X.2 并补 1 题，扩展阅读节号随之后移。
【2026-10-20 回写】U2 全单元标题与去 AI 表达复审（用户指令）。本课改 9 处，且结构被用户重排：
  用户手动把连接格提到 §一 末尾（cell 3「（1）先连接机器人」/ cell 4 连接代码），
  消除「robot 先用后连」的 Run All 报错；实验一重编为 4.1「三路数据各读一次」/ 4.2「定时循环实时显示」。
  本次一并改：1.2「低电量告警线」、2.3「摔倒后的起身」、三级「三、多传感器融合」、
  「运维里天天看」改写、删「真到用的时候」「不各看各的」、DAMP 写法按 §8.30 统一为「阻尼模式 DAMP」。格数仍 34。
【2026-10-20 P4对照复审回写】区分两条告警线与模式含义；联合条件和四个假设情景保留学生占位，起身默认teacher_confirmed=False，仅教师确认全部条件后演示；35格（25 Markdown / 10 code）。以当前正文为准，旧稿中的自动起身及保护阈值推断已撤回。"""
import json, os
OUT = os.path.join(os.path.dirname(__file__), "notebooks", "U2-L4_状态监测与融合.ipynb")
def md(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
cells = []

# U2-L4：状态监测与融合
cells.append(md("""# U2-L4：状态监测与融合

**课程目标**

1. 能解释剩余电量、电压和充放电状态，区分 `is_low` 与 `is_critical` 两条告警线。
2. 能读懂摔倒状态，说明调用起身任务前需要检查的状态与现场条件。
3. 能定时读取电池、摔倒状态和当前模式，补全电量与模式的联合判断，并用给定情景检查各分支的输出。"""))

# 课程大纲映射（审核用）
cells.append(md("""## 课程大纲映射（审核用）

| 轻任务 | 对应位置 | 核心概念 | 轻量概念 |
| --- | --- | --- | --- |
| ⑤ 状态监视器：显示电池、摔倒状态、当前模式 | 实验一 4.1、4.2 | — | C09 定时循环 |
| ⑥ 安全守护者：联合告警、检查起身条件 | 实验二 5.1、5.2 | B08 多传感器融合：多来源状态的综合判断 | — |

- 接口覆盖：`get_battery()`、`get_fall_down_state()`、`get_mode()`；`get_up()` 为教师有条件演示。
- 学生必做：完成告警分支与情景验证，读取摔倒状态并判断起身条件。无需制造摔倒。

> 本映射块用于大纲审核，导出学生 PDF 时移除。"""))

# 一、电池与电源管理
cells.append(md("""## 一、电池与电源管理

### 1.1 电池的三个字段

电池给机器人供电。本节先看 SDK 返回的三个字段：

| 量 | 含义 | 单位 |
| --- | --- | --- |
| `percentage` | 剩余电量，0 到 100 | % |
| `voltage` | 电压 | V（伏特） |
| `power_supply_status` | 充放电状态 | Charging 充电中 / Discharging 放电中 / Full 已充满 / NotCharging 未充电 / Unknown 未知 |

日常检查需要结合这三个字段：电量用于估计剩余可用时间，电压用于检查当前供电情况，充放电状态用于确认是否正在充电。电池是否健康还需要结合容量、温度、使用记录等信息，不能凭一次电压读数判断。

### 1.2 低电量告警线

机器人运动时需要持续供电。电量不足时应结束运动任务，按安全流程停稳并安排充电；不能等到断电才处理。SDK 中，电量低于 20% 时 `is_low` 为 True，低于 10% 时 `is_critical` 为 True。低于 10% 时两者会同时为 True。

### 1.3 获取电池数据

调用 `get_battery()` 可以拿到电池数据。"""))

# （1）先连接机器人
cells.append(md("""（1）先连接机器人"""))

# from boosteros.robots.booster import BoosterRobot
cells.append(code("""from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()
print("已连接 K1")"""))

# （2）查看电池数据
cells.append(md("""（2）查看电池数据"""))

# bat = robot.get_battery()
cells.append(code("""bat = robot.get_battery()

print("获取的返回值：", bat)"""))

# `get_battery()` 的返回值是 `BatteryState` 类型，包含如下信息：
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

# bat = robot.get_battery()
cells.append(code("""bat = robot.get_battery()

print("剩余电量：", round(bat.percentage, 1), "%")
print("电压：", bat.voltage, "V")
print("充放电状态：", bat.power_supply_status)
print("是否在充电：", bat.is_charging)
print("是否低电量：", bat.is_low)"""))

# 运动时电机耗电通常比静止时多，但短时间内电量百分比可能没有可见变化。出发前应结合电量、任务时长和现场要求判断是否…
cells.append(md("""运动时电机耗电通常比静止时多，但短时间内电量百分比可能没有可见变化。出发前应结合电量、任务时长和现场要求判断是否继续；本课不通过耗尽电量来验证告警。"""))

# 二、摔倒检测与起身
cells.append(md("""## 二、摔倒检测与起身

### 2.1 摔倒状态

`get_fall_down_state()` 返回系统判断的摔倒状态。先认识这些值：

| `state` | 含义 |
| --- | --- |
| `normal` | 系统报告正常状态 |
| `falling` | 系统报告正在摔倒 |
| `fallen` | 系统报告已摔倒 |
| `getting_up` | 系统报告正在起身 |
| `unknown` | 状态未知，不能据此判断可以动作 |

一次摔倒、起身过程可能经历 `normal → falling → fallen → getting_up → normal`。采样间隔较长时可能看不到中间状态；`unknown` 也不属于这条先后顺序。

### 2.2 倾斜、摔倒与保护

U2-L3 读过俯仰角和横滚角。身体倾斜会改变这些读数，倾斜过大可能导致失去平衡。姿态数据可以用于摔倒检测，但仅凭本课接口，不能确定 K1 内部使用了哪些判据、阈值和保护动作。课堂以系统返回的摔倒状态为准，不通过推倒机器人来寻找触发角度。

### 2.3 摔倒后的起身

`get_up()` 用于下发起身任务，返回 `TaskHandle`。该任务不可取消，调用前必须确认 `state == "fallen"`、`recoverable` 为 True，并由教师检查倒地姿势、周围空间和设备情况。任务已下发不等于已成功站起，还要观察实际动作和后续状态。

### 2.4 获取摔倒状态

先查看完整返回值，再读取所需字段。"""))

# fs = robot.get_fall_down_state()
cells.append(code("""fs = robot.get_fall_down_state()

print("获取的返回值：", fs)"""))

# `get_fall_down_state()` 的返回值是 `FallDownState` 类型，包含如下信息：
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

# fs = robot.get_fall_down_state()
cells.append(code("""fs = robot.get_fall_down_state()

print("摔倒状态：", fs.state)
print("能否自行起身：", fs.recoverable)
print("是否正常：", fs.is_normal)
print("是否已摔倒：", fs.has_fallen)"""))

# 记录现场读到的状态；静止时通常会读到 `normal`。如果读到 `unknown`，先请教师检查设备和数据是否…
cells.append(md("""记录现场读到的状态；静止时通常会读到 `normal`。如果读到 `unknown`，先请教师检查设备和数据是否就绪。学生不制造摔倒，也不通过晃动机器人来追求状态变化。"""))

# 三、多传感器融合与综合判断
cells.append(md("""## 三、多传感器融合与综合判断

U2-L3 提到，姿态估计可以结合不同测量来源。多传感器融合还可用于位置估计、目标判断等任务，不同任务使用的算法各不相同。

本课将这些信息用于提示判断：**把电池读数、系统报告的摔倒状态和当前模式放在一起，判断应该给出什么提示**。当前模式是控制状态，并非传感器测量值。因此，这里做的是多来源状态的综合判断，不涉及姿态融合算法的实现。

例如，电量低时都需要安排充电，但提示还要说明当前模式：

| 电量条件 | 当前模式 | 本课程序的提示 |
| --- | --- | --- |
| `is_low == True` | `walk` | 电量低，当前为 walk；请教师按流程结束运动、停稳后充电 |
| `is_low == True` | 其他模式 | 电量低；保持安全状态，安排充电 |
| `is_low == False` | 任意模式 | 电量未触发低电量告警；显示模式 |

`walk` 只表明机器人处于可运动的控制模式，不能据此断言它正在走路。即使机器人静止，低电量也需要处理。上述程序仅打印提示，不会自动停止机器人。

起身判断则需要同时检查 `fallen`、`recoverable`，再由教师确认现场条件。某一个字段满足要求，还不能直接下发动作。"""))

# 四、实验一：状态监视器
cells.append(md("""## 四、实验一：状态监视器

**实验名称**：状态监视器

**实验目标**：定时循环读取电池、摔倒状态与当前模式，实时显示这三项，观察它们的变化。

⚠️ **安全**：本课有两次实验。

- **本次状态监视器**只读数据，不发送运动 / 动作指令，机器人保持阻尼模式（DAMP）下的坐姿、趴姿，或准备模式（PREP）下的站姿即可，<font color="red">不需要进入行走模式（WALK）</font>。
- **实验二 安全守护者**里的「起身动作」会让机器人运动，仅由教师在符合条件时演示，学生完成只读检查和判断。

**前置准备**：K1 已开机并与电脑建立连接（见 U1-L1）；已完成 U1-L2（模式切换与安全）、U2-L2（传感器速览）、U2-L3（IMU 与里程计）。"""))

# 4.1 三路数据各读一次
cells.append(md("""### 4.1 三路数据各读一次

先把三路数据各读一次，确认接口都通。
"""))

# bat = robot.get_battery()
cells.append(code("""bat = robot.get_battery()
fs = robot.get_fall_down_state()
mode = robot.get_mode()

print("电量：", round(bat.percentage, 1), "%")
print("摔倒状态：", fs.state)
print("当前模式：", mode)"""))

# 4.2 定时循环实时显示
cells.append(md("""### 4.2 定时循环实时显示

用 `for` 循环采集 10 轮，每轮读完后等待 1 秒。读取和输出也需要时间，因此相邻两轮通常略长于 1 秒。这里用序号标记轮次，不把序号当作精确计时。"""))

# import time
cells.append(code("""import time

print("状态监视器启动，每轮读取后等待 1 秒，共 10 轮。")
print()
print(" 序号   电量     摔倒状态     当前模式")
print("-" * 44)

for i in range(10):
    bat = robot.get_battery()
    fs = robot.get_fall_down_state()
    mode = robot.get_mode()
    print(f"  {i:>2}   {bat.percentage:5.1f}%   {fs.state:<10}   {mode}")
    time.sleep(1)"""))

# 记录第 1 轮和第 10 轮的电量、摔倒状态与模式。短时间内三项都可能不变，这也是有效记录。保持机器人原有的安全…
cells.append(md("""记录第 1 轮和第 10 轮的电量、摔倒状态与模式。短时间内三项都可能不变，这也是有效记录。保持机器人原有的安全姿势，不为观察变化而拨动或倾斜它。"""))

# 五、实验二：安全守护者
cells.append(md("""## 五、实验二：安全守护者

**实验目标**：补全电量与模式的联合告警，使用假设情景检查分支；读取摔倒状态，判断是否具备申请起身演示的条件。

**操作范围**：5.1 只读数据、打印提示；5.2 的动作调用默认关闭。起身由教师按现场条件决定是否演示，无需为本课主动制造摔倒。

### 5.1 电量与模式的联合告警

`and` 表示两个条件同时成立。下面第一条分支留给你补全：电量低，并且当前处于 `walk` 模式。

先预测当前设备会进入哪个分支，再运行并核对。"""))

# import time
cells.append(code("""import time

for i in range(10):
    bat = robot.get_battery()
    mode = robot.get_mode()
    # 任务：把下一行的 False 换成 bat.is_low and mode == "walk"
    if False:
        print(f"第 {i + 1} 轮：电量 {bat.percentage:.1f}%，当前为 walk；请教师按流程结束运动、停稳后充电")
    elif bat.is_low:
        print(f"第 {i + 1} 轮：电量 {bat.percentage:.1f}%，模式 {mode}；保持安全状态，安排充电")
    else:
        print(f"第 {i + 1} 轮：电量未触发低电量告警，模式 {mode}")
    time.sleep(1)"""))

# 电量充足时只会进入最后一条分支。验证其他分支时，使用下格的假设数据，不改变真实告警阈值，也不让机器人进入低电量或…
cells.append(md("""电量充足时只会进入最后一条分支。验证其他分支时，使用下格的假设数据，不改变真实告警阈值，也不让机器人进入低电量或切换到 walk。

**情景验证步骤**：

1. 先填写下表中的预期提示。
2. 将下一格的 `pass` 替换为上格补全后的整段 `if / elif / else`，去掉电量百分比和轮次，只保留三种提示。把 `bat.is_low` 换成 `low`，保留 `mode` 判断。
3. 运行后逐行核对。①和②都应告警，但提示内容不同；③和④不触发低电量告警。如果①和②输出完全相同，检查联合条件与分支顺序。

| 假设情景 | `low` | `mode` | 预期提示 | 实际提示 |
| --- | --- | --- | --- | --- |
| ① | True | walk |  |  |
| ② | True | prepare |  |  |
| ③ | False | walk |  |  |
| ④ | False | damping |  |  |

这些变量只代表假设情景，不是机器人当前读数，也不发送控制指令。验证通过后，再运行一次上格的真实读取程序，记录当前模式与对应提示。"""))

# 假设数据，仅用于检查判断分支
cells.append(code("""# 假设数据，仅用于检查判断分支
cases = [(True, "walk"), (True, "prepare"), (False, "walk"), (False, "damping")]

for low, mode in cases:
    print("情景：", low, mode)
    # 将上格的三条判断分支改写到这里，替换 pass
    pass"""))

# 5.2 起身条件检查与教师演示
cells.append(md("""### 5.2 起身条件检查与教师演示

所有学生先读取 `state` 和 `recoverable`，口头说明是否满足起身的状态条件。正常或未知状态都不应下发起身任务。

下格将教师现场确认与数据条件分开：`teacher_confirmed = False` 时只检查，不下发动作。只有教师确认机器人确实倒地、姿势适合起身、周围 1 米无人且设备正常后，才可将其改为 True 并亲自运行。`recoverable` 为 True 不能代替现场检查。不具备演示条件时保持 False，即可完成本课任务。"""))

# 默认只读检查；动作演示由教师现场确认后亲自运行
cells.append(code("""# 默认只读检查；动作演示由教师现场确认后亲自运行
teacher_confirmed = False
fs = robot.get_fall_down_state()
print("摔倒状态：", fs.state, "能否自行起身：", fs.recoverable)

if fs.state == "fallen" and fs.recoverable and teacher_confirmed:
    handle = robot.get_up()
    print("已下发起身任务，请观察实际动作与后续状态")
else:
    print("未下发起身任务，请核对状态条件和教师现场确认")"""))

# 若教师演示了起身，应观察实际站立情况，并重新读取摔倒状态与模式，确认结果。起身后按 U1-L2 的收尾流程处理：…
cells.append(md("""若教师演示了起身，应观察实际站立情况，并重新读取摔倒状态与模式，确认结果。起身后按 U1-L2 的收尾流程处理：先切回准备模式（PREP），由人工扶着让机器人坐下，确认坐稳后进入阻尼模式（DAMP）。本课未执行动作的组保持原有安全姿势。"""))

# 六、观察与记录
cells.append(md("""## 六、观察与记录

随操作填写，不必等到课末。

| 观察项 | 你的记录 | 说明 |
| --- | --- | --- |
| 电池三项 |  | 电量百分比、电压、充放电状态；缺失值照实记为 None |
| 两条告警线 |  | `is_low`、`is_critical` 的含义与当前 `is_low` 值 |
| 摔倒状态 |  | `state`、`recoverable` 的实际读数 |
| 当前模式 |  | `get_mode()` 返回值 |
| 10 轮采集 |  | 首末两轮三项是否变化 |
| 联合告警 |  | 真实读数对应哪个分支、提示是什么 |
| 四个假设情景 |  | 在 5.1 表中记录预期与实际提示，标出是否一致 |
| 起身条件 |  | 状态条件是否满足；为何仍需教师检查现场 |

若未进行起身演示，记录“未执行”，无需补造动作结果。"""))

# 七、检查点、思考题与学习评价
cells.append(md("""## 七、检查点、思考题与学习评价
"""))

# 7.1 分步检查点
cells.append(md("""### 7.1 分步检查点

- [__] 读出电池的电量、电压、充放电状态，能说明两条告警线。
- [__] 读出 `state`、`recoverable` 与当前模式。
- [__] 完成 10 轮三项状态显示，记录是否变化。
- [__] 补全电量与模式的联合条件，并用四个假设情景核对全部分支。
- [__] 情景验证后重新读取真实状态，说明本轮提示的依据。
- [__] 能说明起身前的数据条件和教师现场确认；默认未下发起身任务。"""))

# 7.2 思考题
cells.append(md("""### 7.2 思考题

课堂讨论第 1、2 题，第 3、4 题课后完成。

1. 电量低时，`walk` 与 `prepare` 两种情景为什么需要不同提示？两种情景是否都需要安排充电？
2. `state == "fallen"` 且 `recoverable` 为 True，是否可以立即起身？还需要检查什么？
3. 本课告警程序只打印提示。要实现自动安全停机，还需要明确哪些动作、现场条件和验证要求？
4. 每轮读数据花 2 秒，再 `sleep(1)`，相邻两轮约隔几秒？这对短暂出现的状态有什么影响？"""))

# 7.3 学习评价
cells.append(md("""### 7.3 学习评价

1. 电量低于 10% 时，`is_low` 与 `is_critical` 会同时为 True。（判断）
2. 起身调用前应先确认 `state` 为 ______、`recoverable` 为 ______，并由教师检查现场。
3. 假设 `low = True`，分别令 `mode = "walk"` 和 `mode = "prepare"`。写出你的程序输出的两条提示，并说明为什么不能只判断 `low`。

> 参考答案（教师留存，导出学生 PDF 时移除）：
> 1. √。2. `fallen`；True。3. walk 提示请教师按流程结束运动、停稳后充电；prepare 提示保持安全状态、安排充电。电量条件决定是否告警，模式条件用于区分提示；两者均需处理低电量。"""))

# 八、扩展阅读：机器人的保护功能
cells.append(md("""## 八、扩展阅读：机器人的保护功能

机器人保护功能需要结合硬件、控制系统和现场条件设计。常见例子包括：

| 功能 | 触发依据 | 可能的处理 |
| --- | --- | --- |
| 急停 | 人按下急停装置 | 按设备规定停止危险运动；制动、断电方式由设备设计决定 |
| 安全区域监测 | 人或物进入指定区域 | 按系统配置减速或停止 |
| 碰撞检测 | 力矩、接触等信号异常 | 停止或采用规定的避让动作 |
| 低电量处理 | 电量达到设定条件 | 提示充电，或在具备导航与充电设施时返回充电位置 |

各设备具备的功能和触发后的行为不同。不能把“急停”一律理解为断电后关节锁死，也不能认为有碰撞检测就一定会后退。保护功能应依据设备手册，在规定的测试条件下由有资质人员验证。学生课堂不自行进行推倒、碰撞、断电等试验。

本课读取的状态与打印的提示，可帮助理解保护程序所需的信息；它们不能代替设备本身的安全功能。"""))


nb = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
json.dump(nb, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "cells=", len(cells))
