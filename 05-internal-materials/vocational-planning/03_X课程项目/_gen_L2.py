# -*- coding: utf-8 -*-
# 生成 U1-L2 实训手册 notebook（新 实训手册体例，对齐 L1）
# 规则：首 cell 课头=课程级(课程目标)；实验头=实验级(名称/目标/安全/前置)；
# markdown source 逐行带 \n 列表存储(§8.5)；删除 课程设计备忘(§3.7)；保留 walk 安全多 cell 拆分(§3.8)
import json, os

OUT = r"d:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L2_运行模式与安全.ipynb"

cells = []
def md(text):
    cells.append(("md", text))
def code(text):
    cells.append(("code", text))

md(r'''# U1-L2：运行模式与安全

> **课程目标**：
> 1. 认识 K1 的四种运行模式及其物理含义与安全要点；
> 2. 学会用 BoosterOS SDK 以程序方式查看并切换运行模式；
> 3. 理解模式之间的安全切换关系，养成规范、安全的操作习惯。''')

md(r'''## 一、K1 的运行模式

在开始写程序之前，先理解 K1 为什么需要“运行模式”：机器人不同的姿态与动作需要不同的底层控制策略，运行模式就是切换这些策略的开关。下面认识四种模式的物理含义与安全要点。''')

md(r'''### 1.1 四种运行模式（对照表）

| 模式 | 含义 | 能否运动 | 安全要点 |
|---|---|---|---|
| `damping` | 阻尼 / 软态。关节有阻尼但整体是“软”的，无法维持站立；可坐椅子上或趴地面 | 否 | 开机默认状态 |
| `prepare` | 准备模式。维持站立就绪姿态；通过 **Stand** 把机器人拉起到站立 | 否（仅就绪） | 行走前必须先到达此模式 |
| `walk` | 行走模式。可接收速度指令使机器人运动，靠动态平衡维持站立 | 是（需配合速度） | **只能由已直立站立的 prepare 进入**；趴姿进入会乱踢 |
| `custom` | 进阶自定义模式。需用户单独编程才能产生动作 | 取决于编程 | 未编程前比 damping 更软，无法支撑站立 |

> 📌 本课实操只涉及 `damping` / `prepare` / `walk` 三种；`custom` 为进阶模式，需单独编程，不在本课实操范围内。''')

md(r'''## 二、用程序查看并切换运行模式

**实验名称**：K1 运行模式查看与安全切换

**实验目标**：通过 `BoosterRobot` 以程序方式读取 K1 当前运行模式，并在安全约束下练习 `damping` / `prepare` / `walk` 的切换，理解模式间的正确顺序。

> ⚠️ **安全提示**：本实验会切换机器人运行模式，涉及姿态变化。
> - 操作前确认：K1 已开机、周围无遮挡与人员紧贴、地面空旷。
> - 进入 `walk` 前必须先 `prepare` 并已 **STAND 直立站稳**；本实验不发送速度指令，机器人保持原地。
> - **严禁从 `walk` 直接切回 `damping`**：`walk` 为站立动态平衡态，`damping` 为软态无法维持站立，直接切换会导致机器人瘫倒。

> 📌 **前置准备**：本实验需在 K1 已完成开机、配网（连接同一 WiFi）、查看 IP，并能用 BoosterStudio 成功连接机器人之后进行。''')

md(r'''### 2.1 连接 K1 机器人

`BoosterRobot` 是编写程序操作 K1 的入口。运行下面单元格建立连接。

- 若连接失败，请检查：K1 是否开机、电脑与 K1 是否同一 WiFi、SDK 是否已安装。
- 若提示 `ModuleNotFoundError: No module named 'boosteros'`，代表 boosteros 尚未安装。''')

code(r'''from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()
print("已连接 K1，准备探索运行模式 🤖")''')

md(r'''### 2.2 读取当前运行模式

`get_mode()` 返回机器人当前运行模式。认识机器人的第一步，是看清它“现在处于什么状态”。运行下面单元格，观察当前模式。

> 💡 之前你可能用过 K1 上的按钮切换 damping / prepare / walk；下面我们用 SDK 的 `set_mode()` **以程序方式**控制模式——按钮适合人工即时操作，程序适合让机器人按流程自动执行，这正是学习机器人编程的意义。''')

code(r'''print("当前运行模式：", robot.get_mode())''')

md(r'''## 三、模式切换实操：阻尼 ↔ 准备（趴姿练习）

先在**趴姿**下练习 `damping` 与 `prepare` 的切换，体会两种模式下关节阻尼的差异。趴姿下切换最安全，不会因为站立失败而摔倒。''')

code(r'''# 读取当前模式
print("切换前：", robot.get_mode())

# 切换到 prepare（趴姿下进入，仅就绪，不会站立）
robot.set_mode("prepare")
print("切换后：", robot.get_mode())''')

code(r'''# 回到 damping（软态，适合坐姿/趴姿收尾）
robot.set_mode("damping")
print("切换后：", robot.get_mode())''')

md(r'''## 四、行走模式的安全切换（重点）

要让机器人行走，必须严格遵守安全顺序。下面先回顾规范，再用“多步 + 人工确认”的方式走一遍安全路径。''')

md(r'''### 4.1 安全规范（必读）

- **STAND 确认**：每次进入 `walk` 前，必须确认已处于 `prepare` 模式，且**直立站稳**、周围安全。
- **walk 只能来自站立的 prepare**：`walk` 靠动态平衡维持站立，只能由“已 STAND 直立的 prepare”进入；趴姿进入会关节乱动、腿部乱踢。
- **严禁 walk → damping 直接切换**：站立态直接切 `damping` 会让机器人瘫倒。停止顺序应为 `walk → prepare`（回到站立稳定）→ 坐下 → `damping`。''')

md(r'''### 4.2 行走安全路径（多步 + 人工窗口）

下面把“准备 → 进入 walk → 安全停止”拆成独立单元格，每步之间留出人工操作时间。**只有确认机器人已手动拉起、直立站稳、周围空旷、教师监督时，才运行进入 walk 的那一格。**''')

md(r'''**步骤 1**：先确保机器人处于 `prepare` 且已直立站稳（手动拉起）。运行下一格发送准备指令。''')

code(r'''# 确保处于站立准备态（需先手动拉起机器人到 STAND 直立站立）
robot.set_mode("prepare")''')

md(r'''> 🛑 **人工确认**：确定已手动拉起、处于直立站立、周围开阔、教师监督下，再运行下一格进入 walk。''')

code(r'''# 确认已 STAND 直立站稳后再运行（本实验不发送速度，机器人原地）
robot.set_mode("walk")
print("当前模式：", robot.get_mode())''')

md(r'''**步骤 3（停止）**：`walk → prepare` 回到站立稳定，**禁止 walk → damping** 直接切换。''')

code(r'''# 安全停止：回到站立稳定，禁止直接切 damping
robot.set_mode("prepare")
print("实验结束，当前模式：", robot.get_mode())''')

md(r'''**步骤 4（收尾）**：需要关机时，先让机器人坐下/趴好，再进入 `damping` 软态收尾。''')

code(r'''# 仅当确认机器人已坐下或趴好时，才执行以下阻尼收尾：
robot.set_mode("damping")''')

md(r'''## 五、检查点、思考题与学习评价''')

md(r'''### 5.1 分步检查点（完成一项就在框里打勾 ✓）
- [ ] 连接成功：运行 2.1 后显示“已连接 K1”。
- [ ] 读模式：2.2 能读出当前运行模式。
- [ ] 趴姿切换：第三节在趴姿下成功 `damping ↔ prepare` 切换。
- [ ] 行走安全路径：第四节按“准备 → 人工确认 → walk → 安全停止”顺序完成，未出现 walk→damping。
- [ ] 收尾正确：实验结束回到 `damping` 软态。''')

md(r'''### 5.2 思考题
1. 为什么 `walk` 必须由“已直立站立的 prepare”进入，而不能从趴姿的 prepare 进入？
2. 如果误把 `walk` 直接切到 `damping`，会发生什么？为什么这是危险的？
3. 用程序 `set_mode()` 切换模式，和用手动按钮切换，各适合什么场景？''')

md(r'''### 5.3 学习评价

请独立完成以下题目，检验本实验的掌握情况。

**一、判断题**（对的打√，错的打×）

1. 调用 `set_mode("walk")` 让机器人获得行走能力前，必须先 `set_mode("prepare")` 且机器人已 STAND 直立站稳。（    ）

**二、填空题**

2. K1 四种运行模式中，关节有阻尼但整体是“软”的、无法维持站立、只能在坐姿或趴姿下进入的模式是 ______。

**三、选择题**（单选）

3. 下列哪种切换顺序存在安全隐患，会导致站立的机器人直接瘫倒在地？（    ）
   A. `prepare → walk`　　B. `walk → prepare`　　C. `walk → damping`　　D. `damping → prepare`

> 参考答案（教师留存，勿印发给学生）：
> 1. √　2. `damping`（阻尼模式）　3. C''')

md(r'''## 六、扩展阅读：安全操作与职业素养

规范、安全地操作机器人，不只是本课的纪律要求，更是机器人应用 / 运维相关职业的核心素养。

### 6.1 为什么“安全切换”值得重视
机器人由高扭矩关节电机驱动，姿态切换不当可能造成设备损坏或人员受伤。工业现场对“上电 / 就绪 / 运行 / 停机”有严格的状态机与急停流程——本课练习的 `prepare / walk / damping` 顺序，正是这一思想的简化入门。

### 6.2 相关职业方向
| 方向 | 典型岗位 | 与本课关联 |
|---|---|---|
| 本体厂商研发 | 运动控制算法工程师 | 模式与平衡控制是日常 |
| 系统集成 / 应用开发 | 机器人应用开发工程师 | 用 BoosterOS SDK 写程序、调度模式 |
| 运维实施 | 现场实施 / 技术支持 | 配网、连接、安全启停与调试 |

> 为什么值得了解：你在本课写下的 `set_mode("prepare")` / `set_mode("walk")`，正是机器人工程师每天要面对的“状态机”操作。''')

md(r'''## 课程大纲映射（Phase 2 · 确认①审核用）

> 本块为大纲设计与代码单元的对应审查材料，供确认①审核。定稿进入 Phase 3 后，除“知识原理”所需内容外，其余可移出学生版（P7 导出 PDF 时统一删除）。

### 一、单元定位与边界
- 本单元（U1 人形机器人初探与运动控制）是学生第一次接触具身智能实体机器人开发。
- **知识线**：运行模式与状态机；**实操线**：连接 → 查看模式 → 安全切换。
- 本单元为开环操作（发指令、看状态），与 U4 的闭环形成对照。

### 二、本课知识线 / 技能线（双主线）
- **知识线**：四种运行模式的物理含义与安全要点；状态机思想入门。
- **技能线**：`pip install boosteros` → `BoosterRobot()` 连接 → `get_mode()` / `set_mode()` 查看与切换。
- **行业/职业认知锚点（U1）**：机器人安全操作规范与职业素养（本体研发 / 应用开发 / 运维实施）。

### 三、核心概念标注（对照 v4 编号）
- **SDK 程序控制（E06，同 L1）**：`BoosterRobot` 统一入口 + `set_mode()` / `get_mode()`。
- **运行模式 / 状态机**：damping / prepare / walk / custom 及其安全切换（编号以 v4 大纲为准）。

### 四、轻任务 ↔ 代码 cell 对应表（审核要点）
| 轻任务 | 对应步骤 | 可运行 cell | 状态 |
|---|---|---|---|
| ① 连接 K1 | 2.1 | `BoosterRobot()` | ✅ |
| ① 读取当前模式 | 2.2 | `get_mode()` | ✅ |
| ① 趴姿切换 damping↔prepare | 三 | `set_mode("prepare")` / `set_mode("damping")` | ✅ |
| ① 行走安全路径 | 四 | `set_mode("prepare")` → `set_mode("walk")` → `set_mode("prepare")` | ✅ |''')

def split_lines(text):
    lines = text.split("\n")
    out = []
    for i, l in enumerate(lines):
        if i < len(lines) - 1:
            out.append(l + "\n")
        else:
            if l != "":
                out.append(l)
    return out

nb_cells = []
for t, x in cells:
    if t == "md":
        nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": split_lines(x)})
    else:
        nb_cells.append({"cell_type": "code", "execution_count": None,
                         "metadata": {}, "outputs": [], "source": split_lines(x)})

nb = {
    "cells": nb_cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13"}
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("DONE cells=%d -> %s" % (len(nb_cells), OUT))
