# Chapter\_15\_行为树：把复杂行为拆成可组合动作

# Chapter 15｜行为树：把复杂行为拆成可组合动作

> Chapter 13 使用 FSM（Finite State Machine，有限状态机）组织“跟随、搜索、身体搜索”等状态，Chapter 14 进一步实现了稳定追球控制。进入 Chapter 15 后，课程开始使用 BT（Behavior Tree，行为树）组织更复杂的机器人行为。
> 
> 

**行为树**可以把复杂任务拆成一组可组合的小节点。每个小节点只负责一个很明确的问题，例如：

```Plaintext
是否看见足球
是否已经到位
追球
保持停止
搜索足球
```

然后再用组合节点把这些小节点拼成完整决策：

```Plaintext
如果看见球且到位 -> 停住
否则如果看见球 -> 追球
否则 -> 搜索球
```

本章先从一个不连接机器人、不依赖 ROS2 的最小行为树演示开始，把 `tick`、节点返回状态、`Sequence`、`Selector` 和黑板数据讲清楚。理解这些基础之后，再迁移到足球追球决策，让 K1 通过行为树完成“搜索、追球与停稳”。

本章实践代码放在：

```Plaintext
CourseCode/chapter_15_behavior_tree_football_decision/
```

本章代码目录自包含，包含最小行为树内核、原理演示脚本、足球行为树叶子节点、BT 版足球追球节点、足球检测和空间定位代码。它不会 import 前面章节的代码文件。

本章 BT 版足球追球会真实控制 K1 头部和身体。运行前必须确认机器人站立稳定，前方和左右两侧留出安全空间。如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张“最小行为树 \-\> 足球行为树 \-\> K1 真机行为”的章节总览图。左侧是抽象节点，中间是足球决策树，右侧是 K1 搜索、追球、停稳的照片或示意图。

## 15\.1 行为树任务结构

行为树是一种用树形结构组织行为决策的方法。它常用于游戏 AI、移动机器人、足球机器人、服务机器人等场景。行为树的优点是结构清晰、节点可复用、执行过程容易观察。

一棵行为树由两类节点组成：

```Plaintext
组合节点：负责调度子节点
叶子节点：负责判断条件或执行动作
```

可以把组合节点理解为“组织者”，把叶子节点理解为“具体干活的节点”。

### 15\.1\.1 从最小任务开始理解行为树

先看一个和足球无关的最小任务：

```Plaintext
如果电量足够并且看到目标，就走向目标；
如果电量足够但没看到目标，就搜索目标；
如果电量不足，就充电。
```

这个任务可以写成普通 `if/else`：

```Python
if battery_enough and target_visible:
    walk_to_target()
elif battery_enough:
    search_target()
else:
    charge_battery()
```

普通 `if/else` 可以完成简单任务，但当任务越来越复杂时，代码会逐渐变成很多层嵌套判断：

```Plaintext
先判断电量
再判断目标
再判断距离
再判断动作是否完成
再判断是否需要切换到其他策略
```

行为树把这些判断拆成节点，再通过树结构表达优先级和流程。

最小行为树可以写成：

```Plaintext
Selector: DemoRoot
├── Sequence: ApproachWhenReady
│   ├── BatteryEnough
│   ├── TargetVisible
│   └── WalkToTarget
├── Sequence: SearchWhenBatteryEnough
│   ├── BatteryEnough
│   └── SearchTarget
└── ChargeBattery
```

这棵树的含义是：

1. 优先尝试“电量足够、看到目标、走向目标”；

2. 如果看不到目标，但电量足够，就搜索目标；

3. 如果电量不足，就充电。

这就是行为树的第一层价值：把决策逻辑画成一棵树，而不是写成越来越深的 `if/else`。

### 15\.1\.2 tick：行为树每一拍运行一次

行为树不是只运行一次。机器人程序通常会按固定频率不断运行行为树，例如每秒 20 次：

```Plaintext
第 1 拍：读取传感器 -> tick 行为树 -> 发送控制命令
第 2 拍：读取传感器 -> tick 行为树 -> 发送控制命令
第 3 拍：读取传感器 -> tick 行为树 -> 发送控制命令
...
```

这里的“运行一拍”通常叫 `tick`。可以把 `tick` 理解为“让行为树根据当前世界状态做一次判断和动作输出”。

每次 `tick` 都会从根节点开始。根节点再按照自己的规则调用子节点。子节点继续调用自己的子节点，直到运行到叶子节点。

> 配图建议：画一张 `tick` 传播图。箭头从根节点向下传播到叶子节点，再把状态从叶子节点向上传回根节点。

### 15\.1\.3 三种返回状态

行为树节点每次被 `tick` 后，会返回三种状态之一：

|状态|中文含义|典型场景|
|---|---|---|
|`SUCCESS`|成功|条件满足，或动作已经完成|
|`FAILURE`|失败|条件不满足，或当前动作不可执行|
|`RUNNING`|运行中|动作还没完成，下一拍继续|

这三种状态是行为树的核心。尤其是 `RUNNING`，它让行为树很适合机器人控制。

例如，“走向目标”不是一瞬间完成的。机器人这一拍开始走，下一拍还在走，再下一拍可能仍然没到。这个动作不能每一拍都返回 `SUCCESS`，因为还没完成；也不能返回 `FAILURE`，因为它并没有失败。它应该返回：

```Plaintext
RUNNING
```

等机器人真正到达目标附近后，再返回：

```Plaintext
SUCCESS
```

### 15\.1\.4 根节点、组合节点和叶子节点

一棵行为树通常有一个根节点。根节点下面可以连接组合节点，也可以直接连接叶子节点。

本章最小行为树内核在：

```Plaintext
CourseCode/chapter_15_behavior_tree_football_decision/behavior_tree_core.py
```

其中定义了：

```Python
class Status(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"
```

每个节点都有一个 `tick()` 方法：

```Python
def tick(self) -> Status:
    return self.update()
```

对叶子节点来说，`tick()` 默认调用 `update()`。例如条件节点在 `update()` 中判断条件是否满足，动作节点在 `update()` 中发送控制命令。

组合节点会重写 `tick()`，因为组合节点需要决定“先 tick 哪个子节点、遇到什么状态时停止、向父节点返回什么状态”。

## 15\.2 行为树节点类型

行为树可以有很多节点类型。本章只使用最基础、最常用的四类：

```Plaintext
Condition 条件节点
Action 动作节点
Sequence 顺序节点
Selector 选择节点
```

其中 Condition 和 Action 都属于叶子节点；Sequence 和 Selector 属于组合节点。

### 15\.2\.1 Condition 条件节点

Condition（条件节点）只判断条件，不执行复杂动作。它通常只返回：

```Plaintext
SUCCESS 或 FAILURE
```

例如：

```Plaintext
BatteryEnough：电量是否足够
TargetVisible：是否看到目标
BallAvailable：是否有可用足球坐标
ArrivedAtBall：是否已经到位
```

条件满足时返回 `SUCCESS`，条件不满足时返回 `FAILURE`。

在足球行为树中：

```Plaintext
BallAvailable
```

会检查黑板里的足球坐标是否有效。如果有效，返回 `SUCCESS`；如果无效，返回 `FAILURE`。

### 15\.2\.2 Action 动作节点

Action（动作节点）负责执行动作。动作节点可能返回三种状态：

|返回状态|含义|
|---|---|
|`SUCCESS`|动作已经完成|
|`FAILURE`|动作无法执行或失败|
|`RUNNING`|动作正在执行|

例如：

```Plaintext
WalkToTarget：走向目标
SearchTarget：搜索目标
ChaseBall：追球
HoldPosition：保持停止
SearchBall：搜索足球
```

机器人控制中的动作经常返回 `RUNNING`。比如 `ChaseBall` 每一拍根据最新足球坐标发送一次 `Move(vx, vy, vyaw)`，只要追球任务还在继续，就返回 `RUNNING`。

这和普通函数不同。普通函数往往执行完就结束，而行为树动作节点可以在多拍中持续运行。

### 15\.2\.3 Sequence 顺序节点

Sequence（顺序节点）可以理解为“按顺序完成所有步骤”。它从左到右依次 tick 子节点。

规则如下：

|子节点返回|Sequence 反应|
|---|---|
|`SUCCESS`|继续 tick 下一个子节点|
|`FAILURE`|立刻停止，并返回 `FAILURE`|
|`RUNNING`|立刻停止，并返回 `RUNNING`|
|全部子节点 `SUCCESS`|返回 `SUCCESS`|

因此，Sequence 很像逻辑中的“并且”。所有条件都满足，后续动作才能执行。

看一个例子：

```Plaintext
Sequence: ApproachWhenReady
├── BatteryEnough
├── TargetVisible
└── WalkToTarget
```

运行过程：

1. `BatteryEnough` 返回 `SUCCESS`，说明电量足够；

2. `TargetVisible` 返回 `SUCCESS`，说明看到目标；

3. `WalkToTarget` 开始执行，可能返回 `RUNNING`；

4. Sequence 收到 `RUNNING` 后，整条分支也返回 `RUNNING`。

如果第一步电量不足，`BatteryEnough` 返回 `FAILURE`，Sequence 立刻失败，不会继续运行 `TargetVisible` 和 `WalkToTarget`。

这就是 Sequence 的用途：先判断前置条件，再执行动作。

### 15\.2\.4 Selector 选择节点

Selector（选择节点）也叫 fallback（回退节点）。它从左到右尝试子节点，优先执行前面的分支。

规则如下：

|子节点返回|Selector 反应|
|---|---|
|`FAILURE`|继续 tick 下一个子节点|
|`SUCCESS`|立刻停止，并返回 `SUCCESS`|
|`RUNNING`|立刻停止，并返回 `RUNNING`|
|全部子节点 `FAILURE`|返回 `FAILURE`|

Selector 很适合表达“优先策略失败后，退到下一个策略”。

例如：

```Plaintext
Selector: DemoRoot
├── Sequence: ApproachWhenReady
├── Sequence: SearchWhenBatteryEnough
└── ChargeBattery
```

含义是：

1. 优先尝试走向目标；

2. 如果走向目标这条分支失败，就尝试搜索目标；

3. 如果搜索目标也失败，就充电。

在足球决策中，Selector 可以表达：

```Plaintext
优先保持停稳
其次追球
最后搜索
```

### 15\.2\.5 反应式行为树

本章足球行为树使用 `memory=False` 的组合节点。它的含义是：每一拍都从第一个子节点重新评估。

这叫反应式行为树。反应式的意思是：环境一变化，树马上重新判断。

例如，机器人正在追球时，足球突然进入停车距离。下一拍行为树会重新从第一条分支开始：

```Plaintext
BallAvailable -> SUCCESS
ArrivedAtBall -> SUCCESS
HoldPosition -> RUNNING
```

于是机器人立即进入保持停止。

再例如，机器人已经停住，足球被移远。下一拍：

```Plaintext
BallAvailable -> SUCCESS
ArrivedAtBall -> FAILURE
ChaseBall -> RUNNING
```

于是机器人重新追球。

这种“每拍重新判断优先级”的能力，是足球机器人使用行为树的重要原因。

> 配图建议：画一张 Selector 的反应式执行图。第一拍进入 Chase，第二拍因为到位进入 Hold，第三拍因为丢球进入 Search。

## 15\.3 黑板数据

行为树中很多节点需要共享数据。例如：

```Plaintext
BallAvailable 需要读取足球是否有效
ArrivedAtBall 需要读取足球距离
ChaseBall 需要读取足球坐标并写入速度命令
SearchBall 需要知道搜索开始时间
```

如果每个节点都自己订阅话题、自己保存状态，代码会变得混乱。更常见的做法是使用黑板。

Blackboard（黑板）是行为树节点共享数据的地方。它可以保存传感器输入、任务状态、动作结果和调试信息。

### 15\.3\.1 最小演示中的黑板

本章最小演示脚本在：

```Plaintext
CourseCode/chapter_15_behavior_tree_football_decision/simple_behavior_tree_demo.py
```

其中定义了一个最小黑板：

```Python
@dataclass
class DemoBlackboard:
    battery: float = 0.50
    target_visible: bool = False
    distance_to_target: float = 2.0
```

这三个字段代表：

|字段|含义|
|---|---|
|`battery`|当前电量|
|`target_visible`|是否看到目标|
|`distance_to_target`|离目标还有多远|

不同节点会读取或修改这些字段：

|节点|读取字段|修改字段|
|---|---|---|
|`BatteryEnough`|`battery`|无|
|`TargetVisible`|`target_visible`|无|
|`WalkToTarget`|`distance_to_target`、`battery`|距离减小、电量降低|
|`SearchTarget`|`target_visible`|搜索成功后把 `target_visible` 改为 `True`|
|`ChargeBattery`|`battery`|电量增加|

这就是黑板的基本作用：让节点之间通过共享数据协作，而不是互相直接调用。

### 15\.3\.2 运行最小行为树演示

进入本章代码目录：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_15_behavior_tree_football_decision
```

运行：

```Bash
python3 simple_behavior_tree_demo.py
```

终端会输出类似：

```Plaintext
tick | status  | battery | visible | distance
-----+---------+---------+---------+---------
   1 | RUNNING |    0.50 |   False |    2.00
   2 | SUCCESS |    0.50 |    True |    2.00
   3 | RUNNING |    0.48 |    True |    1.65
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YmJmNmRmNzAwMGIwMzI4MjAyNDdmOWFkNTM1ZWUwOWJfNWFjNzExOGFmMzZmZjFkYWM4MWEwMTczOGY1ZWI2NGFfSUQ6NzY2NzA0NzE1MzQyODEzODk1Nl8xNzg1ODM5ODMyOjE3ODU5MjYyMzJfVjM)

这张表要从“每一拍”角度理解：

- 第 1 拍还没看到目标，所以进入搜索，搜索动作还没完成，返回 `RUNNING`；

- 第 2 拍搜索成功，目标变为可见；

- 第 3 拍行为树重新从根节点开始判断，发现目标可见，于是进入走向目标；

- 后续几拍持续靠近，直到距离足够小。

这个脚本虽然不控制机器人，但它把行为树的状态传播讲得很清楚。先理解这个过程，再看足球行为树会容易很多。

### 15\.3\.3 足球行为树中的黑板

足球行为树的黑板定义在：

```Plaintext
CourseCode/chapter_15_behavior_tree_football_decision/football_bt_utils.py
```

核心字段包括：

```Python
@dataclass
class FootballBlackboard:
    ball: BallPosition
    mode: str
    mode_reason: str
    arrived_latch: bool
    search_start_time: float
    last_command: ChaseCommand
```

这些字段的作用如下：

|字段|作用|
|---|---|
|`ball`|当前拍使用的足球基座坐标|
|`mode`|当前行为模式，例如 `CHASE`、`HOLD`、`SEARCH`|
|`mode_reason`|进入当前模式的原因|
|`arrived_latch`|到位迟滞标志|
|`search_start_time`|当前搜索动作开始时间|
|`last_command`|最近一次追球速度命令|

主节点每一拍先更新黑板：

```Python
self.blackboard.ball = self.reader.latest()
```

然后运行行为树：

```Python
status = self.tree.tick()
```

叶子节点只读取和修改黑板，不直接互相调用。这样行为树结构更清楚，日志也更容易解释。

## 15\.4 追球行为树

理解最小行为树后，就可以迁移到足球决策。

足球追球任务可以拆成三个优先级：

```Plaintext
第一优先级：看见足球且已经到位 -> 保持停止
第二优先级：看见足球但还没到位 -> 追球
第三优先级：看不到足球 -> 搜索
```

对应行为树为：

```Plaintext
Selector: FootballDecision
├── Sequence: HoldWhenArrived
│   ├── BallAvailable
│   ├── ArrivedAtBall
│   └── HoldPosition
├── Sequence: ChaseWhenVisible
│   ├── BallAvailable
│   └── ChaseBall
└── SearchBall
```

这棵树虽然不大，但已经体现了行为树的核心思想：

- 用 Selector 表达优先级；

- 用 Sequence 表达前置条件和动作；

- 用叶子节点封装最小判断或动作；

- 每一拍重新评估，让机器人对足球位置变化做出反应。

> 配图建议：把上面的行为树画成正式树状图。每个节点旁边标注节点类型：Selector、Sequence、Condition、Action。

### 15\.4\.1 第一分支：到位保持

第一条分支是：

```Plaintext
Sequence: HoldWhenArrived
├── BallAvailable
├── ArrivedAtBall
└── HoldPosition
```

它表达的是：

```Plaintext
如果有足球坐标，并且已经到达停车距离，就保持停止。
```

`BallAvailable` 是条件节点。它读取黑板中的 `ball`：

```Python
if self.blackboard.ball.valid:
    return Status.SUCCESS
return Status.FAILURE
```

`ArrivedAtBall` 也是条件节点。它计算 `approach`，并带有迟滞逻辑：

```Python
approach = approach_distance(ball.x, ball.y, ball.distance)
```

如果 `approach <= stop_dist`，说明进入停车距离。进入停车距离后，`arrived_latch` 变为 `True`。只要足球没有离开：

```Plaintext
stop_dist + arrive_hysteresis
```

机器人就保持停止。

`HoldPosition` 是动作节点。它发送停止命令：

```Python
self.robot.stop()
```

并让头部继续朝向足球附近。这样机器人身体不动，但头部仍保持观察。

### 15\.4\.2 第二分支：看到球就追

第二条分支是：

```Plaintext
Sequence: ChaseWhenVisible
├── BallAvailable
└── ChaseBall
```

它表达的是：

```Plaintext
如果有足球坐标，但第一分支没有成功，说明还没到位，于是追球。
```

注意，这条分支没有再写 `NotArrived`。因为第一分支已经在它前面。如果“有球且到位”成立，Selector 会停在第一分支，不会运行第二分支。只有第一分支失败，第二分支才有机会运行。

这就是行为树中优先级的作用。

`ChaseBall` 会根据足球坐标计算速度：

```Python
command = self.policy.compute(ball)
```

再发送身体命令：

```Python
self.robot.move(command.vx, command.vy, command.vyaw)
```

速度计算沿用 Chapter 14 的稳定追球思路，包括：

- 前进速度上限；

- 横向速度上限；

- 转身速度上限；

- 进入减速区后线性减速；

- 足球偏角较大时优先转向。

行为树不替代控制算法。行为树负责决定“现在该运行哪个动作”，控制算法负责决定“动作内部的速度是多少”。

### 15\.4\.3 第三分支：看不到球就搜索

第三条分支是：

```Plaintext
SearchBall
```

它是 Selector 的最后一个子节点。只有前两条分支都失败时，才会运行它。

前两条分支都会先检查 `BallAvailable`。如果没有有效足球坐标：

```Plaintext
BallAvailable -> FAILURE
```

第一条分支失败，第二条分支也失败，于是 Selector 运行 `SearchBall`。

本章的 `SearchBall` 做两件事：

1. 身体停止；

2. 头部用三角波左右扫描。

代码中：

```Python
self.robot.stop()
self.robot.scan_head(...)
```

这样做比一丢球就让身体转身更安全。看不到球时，机器人先停止身体，只通过头部扩大观察范围。后续更复杂的足球任务可以在行为树中增加“长时间找不到球后身体转身”的分支。

### 15\.4\.4 为什么行为树比单个控制循环更清楚

Chapter 14 的稳定追球控制节点用一个控制循环处理 `CHASE`、`HOLD` 和 `LOST`。这种写法简单直接，适合讲控制算法。

Chapter 15 使用行为树后，控制逻辑变成了可组合结构：

```Plaintext
条件节点：BallAvailable、ArrivedAtBall
动作节点：HoldPosition、ChaseBall、SearchBall
组合节点：Sequence、Selector
```

这种结构更适合继续扩展。例如后续要加入踢球，可以增加：

```Plaintext
AlignToKick
VisualKick
KickFinished
```

不需要把所有逻辑都塞进一个很长的 `if/else`。

### 15\.4\.5 行为树和有限状态机的关系

FSM 和行为树都能组织机器人行为。两者不是谁完全替代谁，而是适合表达不同结构。

FSM 强调“当前处于哪个状态”，适合状态数量少、切换关系明确的任务。例如 Chapter 13 的 `TRACK`、`HEAD_SEARCH`、`BODY_SEARCH`。

行为树强调“每一拍按优先级重新评估任务”，适合任务可以拆成条件和动作组合的场景。例如：

```Plaintext
有球且到位 -> 保持
有球未到位 -> 追球
无球 -> 搜索
```

两者可以结合使用。行为树的某个叶子节点内部也可以是一个小 FSM；FSM 的某个状态内部也可以运行一棵小行为树。

## 15\.5 程序案例：BT 版追球

本章代码目录为：

```Plaintext
CourseCode/chapter_15_behavior_tree_football_decision/
```

文件结构如下：

```Plaintext
chapter_15_behavior_tree_football_decision/
├── behavior_tree_core.py
├── simple_behavior_tree_demo.py
├── football_bt_utils.py
├── football_bt_nodes.py
├── bt_football_chase_node.py
├── soccer_ball_detector.py
├── soccer_detection_utils.py
├── ball_position_depth_node.py
├── ball_localization_utils.py
├── print_ball_position.py
├── README.md
└── models/
    └── soccer_yolo.pt
```

### 15\.5\.1 behavior\_tree\_core\.py

`behavior_tree_core.py` 是本章极简行为树内核。

它没有依赖第三方行为树库，而是用少量代码实现三态和两种组合节点。这样可以直接看到行为树内部如何运行。

核心状态：

```Python
class Status(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"
```

Sequence 的核心逻辑是：

```Python
for child in self.children:
    status = child.tick()
    if status is Status.RUNNING:
        return Status.RUNNING
    if status is Status.FAILURE:
        return Status.FAILURE
return Status.SUCCESS
```

Selector 的核心逻辑是：

```Python
for child in self.children:
    status = child.tick()
    if status is Status.RUNNING:
        return Status.RUNNING
    if status is Status.SUCCESS:
        return Status.SUCCESS
return Status.FAILURE
```

这两段逻辑是理解行为树的关键。Sequence 是“全部通过才通过”，Selector 是“找到一个可用分支就停”。

### 15\.5\.2 simple\_behavior\_tree\_demo\.py

`simple_behavior_tree_demo.py` 用最小任务演示行为树执行过程。它不需要 ROS2 和 SDK，可以直接运行：

```Bash
python3 simple_behavior_tree_demo.py
```

脚本中的树结构是：

```Plaintext
Selector: DemoRoot
├── Sequence: ApproachWhenReady
│   ├── BatteryEnough
│   ├── TargetVisible
│   └── WalkToTarget
├── Sequence: SearchWhenBatteryEnough
│   ├── BatteryEnough
│   └── SearchTarget
└── ChargeBattery
```

这个脚本的作用不是控制机器人，而是帮助学习者把三件事看清楚：

1. `Selector` 如何从上到下选择分支；

2. `Sequence` 如何按顺序检查条件和动作；

3. `RUNNING` 如何表示一个动作正在持续执行。

### 15\.5\.3 football\_bt\_utils\.py

`football_bt_utils.py` 封装足球行为树共享工具。

其中 `BallPositionReader` 订阅：

```Plaintext
/vision/ball_position_base
```

并把最近一次可靠足球坐标提供给黑板。

`ChaseVelocityPolicy` 根据足球位置计算速度：

```Python
command = self.policy.compute(ball)
```

输出：

```Plaintext
vx
vy
vyaw
approach
slow_scale
turn_factor
```

`RobotControlInterface` 封装 K1 控制：

```Python
self.client.Move(vx, vy, vyaw)
self.client.RotateHead(pitch, yaw)
```

这样行为树叶子节点不用直接处理 SDK 连接细节，只需要调用 `robot.move()`、`robot.stop()`、`robot.scan_head()`。

### 15\.5\.4 football\_bt\_nodes\.py

`football_bt_nodes.py` 是本章足球行为树的重点。它把足球决策拆成五个叶子节点。

|节点|类型|返回特点|
|---|---|---|
|`BallAvailable`|条件节点|有有效足球坐标返回 `SUCCESS`，否则 `FAILURE`|
|`ArrivedAtBall`|条件节点|到位或处于迟滞停止带返回 `SUCCESS`|
|`ChaseBall`|动作节点|发送追球速度，返回 `RUNNING`|
|`HoldPosition`|动作节点|停止身体，返回 `RUNNING`|
|`SearchBall`|动作节点|停止身体并扫描头部，返回 `RUNNING`|

这里要注意动作节点为什么常返回 `RUNNING`。

`ChaseBall` 不是“一次调用就追到球”。它每一拍只发送一组速度命令，然后下一拍继续根据新坐标修正。因此它返回 `RUNNING`。

`HoldPosition` 也不是“完成后退出”。只要足球仍在停车距离内，机器人就要继续保持停止，因此它也返回 `RUNNING`。

`SearchBall` 会持续扫描头部，直到行为树下一拍发现足球有效，才由 Selector 切换到追球分支。

### 15\.5\.5 bt\_football\_chase\_node\.py

`bt_football_chase_node.py` 是本章真机主节点。

它每一拍执行：

```Python
self.blackboard.ball = self.reader.latest()
status = self.tree.tick()
```

第一行更新黑板中的足球坐标。第二行运行行为树。

启动时，主节点会构建树：

```Python
self.tree = build_football_tree(
    self.blackboard,
    self.robot,
    self.policy,
    self.tree_params,
)
```

树的结构会在日志中打印：

```Plaintext
Selector(
  Sequence[BallAvailable, ArrivedAtBall, HoldPosition],
  Sequence[BallAvailable, ChaseBall],
  SearchBall
)
```

运行日志类似：

```Plaintext
tree=RUNNING mode=CHASE reason=ball_available_not_arrived |
x=1.220m y=0.180m distance=1.233m angle=0.146rad age=0.03s method=depth_median |
vx=0.550 vy=0.081 vyaw=0.292 approach=1.220 slow=0.77 turn_factor=0.93
```

这行日志可以拆成三部分：

1. 行为树状态和当前模式；

2. 足球基座坐标；

3. 最近一次追球速度命令。

调试行为树时，重点看 `mode` 为什么切换，而不是只看机器人有没有动。

## 15\.6 运行方式：搜索、追球与停稳

本节给出本章完整运行方式。运行前确认机器人站立稳定，周围空间充足，足球放在机器人前方约 1\.5 m 到 2\.0 m 处。

如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

### 15\.6\.1 进入代码目录

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_15_behavior_tree_football_decision
```

### 15\.6\.2 先运行最小行为树演示

```Bash
python3 simple_behavior_tree_demo.py
```

观察输出中的：

```Plaintext
status
battery
visible
distance
```

重点理解：行为树每一拍都会读取黑板数据，返回状态，并让黑板发生变化。

### 15\.6\.3 启动足球检测

终端 1：

```Bash
python3 soccer_ball_detector.py
```

检测节点会发布：

```Plaintext
/vision_detection/ball
```

如果持续检测不到足球，先调整足球位置、光照和相机视角。

### 15\.6\.4 启动足球空间定位

终端 2：

```Bash
python3 ball_position_depth_node.py
```

定位节点会发布：

```Plaintext
/vision/ball_position_base
```

### 15\.6\.5 打印足球基座坐标

终端 3：

```Bash
python3 print_ball_position.py
```

启动 BT 版追球前，建议先观察坐标是否稳定。理想输出类似：

```Plaintext
x=1.480m y=-0.120m z=0.090m distance=1.485m angle=-0.081rad method=depth_median
```

如果 `x`、`y` 或 `angle` 跳动很大，应先排查视觉和深度链路。

### 15\.6\.6 启动 BT 版足球追球

终端 4：

```Bash
python3 bt_football_chase_node.py --ros-args -p robot_ip:=127.0.0.1
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTczYjE4NGJmYWNiZWQ3OTZlZWY5OGU2ZTI4YzhhNTlfMGZlOTIzMjNkZmZiYTkwNjQzNGE3ZjM4YTVlYzgyZmRfSUQ6NzY2NzA1MDYxMDUxMjQ0ODQ2Nl8xNzg1ODM5ODMyOjE3ODU5MjYyMzJfVjM)

如果 SDK 连接地址不是 `127.0.0.1`，应改成实际地址。

正常情况下会看到：

```Plaintext
Chapter 15 BT 版足球追球节点已启动。
行为树结构：Selector(...)
Booster SDK 连接完成，行为树控制接口已就绪。
```

### 15\.6\.7 观察三种行为效果

本章真机运行重点观察三种行为。

第一，无球搜索：

```Plaintext
mode=SEARCH
```

机器人身体停止，头部左右扫描。

第二，有球追球：

```Plaintext
mode=CHASE
```

机器人根据足球基座坐标靠近足球，头部朝向足球附近。

第三，到位保持：

```Plaintext
mode=HOLD
```

机器人身体停止，并继续观察足球。

这三个模式正好对应行为树的三条分支：

```Plaintext
HoldWhenArrived
ChaseWhenVisible
SearchBall
```

### 15\.6\.8 调整参数

降低追球速度：

```Bash
python3 bt_football_chase_node.py --ros-args -p vx_limit:=0.35 -p vy_limit:=0.15 -p vyaw_limit:=0.6
```

增大停车距离：

```Bash
python3 bt_football_chase_node.py --ros-args -p stop_dist:=0.9
```

增大到位迟滞：

```Bash
python3 bt_football_chase_node.py --ros-args -p arrive_hysteresis:=0.35
```

调整头部搜索周期：

```Bash
python3 bt_football_chase_node.py --ros-args -p search_cycle_sec:=5.0
```

关闭看见球时头部跟随：

```Bash
python3 bt_football_chase_node.py --ros-args -p track_head_with_ball:=false
```

### 15\.6\.9 停止程序

停止时建议按以下顺序：

1. 先在 BT 版足球追球终端按 `Ctrl+C`；

2. 确认终端输出节点停止；

3. 再停止空间定位节点；

4. 最后停止足球检测节点。

如果机器人没有按预期停止，立即按机器人背部 `STAND` 按钮。

## 15\.7 常见问题排查

### 15\.7\.1 行为树一直 SEARCH

`SEARCH` 表示前两条分支都失败：

```Plaintext
BallAvailable -> FAILURE
```

先运行：

```Bash
python3 print_ball_position.py
```

如果定位消息无效，根据 `reason` 排查：

|reason|处理方向|
|---|---|
|`not_detected`|检查足球是否在画面中，模型是否加载成功|
|`no_head_pose`|检查头部位姿话题|
|`all_estimators_failed`|检查深度图和相机参数|
|`out_of_safe_range`|检查定位结果是否明显异常|

### 15\.7\.2 有球但没有进入 CHASE

先看日志中的足球坐标：

```Plaintext
x=...
y=...
distance=...
angle=...
```

如果坐标有效，再看 `mode`。如果直接进入 `HOLD`，说明 `approach` 已经小于 `stop_dist`，机器人认为已经到位。可把足球放远一些，或调小停车距离。

### 15\.7\.3 mode=CHASE 但机器人不动

检查三件事：

1. SDK 是否连接成功；

2. `enable_motion` 是否为 `true`；

3. 日志中的 `vx`、`vy`、`vyaw` 是否接近 0。

如果速度接近 0，可能是足球已经进入减速区，或者角度太大导致线速度被转向优先因子折减。

### 15\.7\.4 到位后反复 CHASE 和 HOLD

这是停车边界抖动。可增大迟滞：

```Bash
python3 bt_football_chase_node.py --ros-args -p arrive_hysteresis:=0.35
```

如果仍然抖动，应观察 `print_ball_position.py` 中的 `x` 和 `distance` 是否剧烈变化。

### 15\.7\.5 搜索时头部不扫描

先确认 BT 节点进入：

```Plaintext
mode=SEARCH
```

如果已经进入 `SEARCH` 但头部不动，检查 SDK 是否连接成功。如果运行时显式设置了：

```Plaintext
enable_motion=false
```

行为树仍会打印状态，但不会发送真实头部和身体命令。

### 15\.7\.6 搜索后重新看见球，为什么能自动切回追球

因为本章使用的是反应式 Selector。每一拍都从第一条分支重新评估。

当搜索过程中重新获得有效足球坐标时，下一拍：

```Plaintext
BallAvailable -> SUCCESS
```

如果还没到位，第一条分支失败，第二条分支运行：

```Plaintext
ChaseBall -> RUNNING
```

于是行为自动从 `SEARCH` 切到 `CHASE`。这不是额外写了状态切换代码，而是行为树结构自然产生的效果。

## 15\.8 本章小结

本章完成了从行为树原理到足球决策的迁移。

学习者需要掌握以下要点：

1. 行为树每一拍通过 `tick` 从根节点开始运行。

2. 节点返回 `SUCCESS`、`FAILURE`、`RUNNING` 三种状态。

3. Sequence 表示“按顺序执行，全部成功才成功”。

4. Selector 表示“按优先级选择，第一个可用分支运行”。

5. 黑板用于在节点之间共享传感器输入、行为模式和动作结果。

6. 足球追球行为树由三条优先级分支组成：到位保持、看到球追球、看不到球搜索。

7. 行为树负责选择动作，追球控制算法负责计算 `Move(vx, vy, vyaw)`。

8. 真机运行前应先确认足球基座坐标稳定，再启动 BT 版足球追球节点。

完成本章后，K1 的足球任务已经不再只是单个控制循环，而是被拆成可组合的行为树节点。后续章节可以在这棵树上继续增加对齐、视觉踢球和完整任务流程。

