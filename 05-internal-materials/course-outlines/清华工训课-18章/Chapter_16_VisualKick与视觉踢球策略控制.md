# Chapter\_16\_VisualKick与视觉踢球策略控制

# Chapter 16｜VisualKick 与视觉踢球策略控制

> 前几章已经完成了足球任务的关键基础：Chapter 11 让 K1 能够检测足球，Chapter 12 把足球转换到机器人基座坐标系，Chapter 14 完成稳定追球，Chapter 15 使用行为树把搜索、追球和停稳拆成可组合节点。进入 Chapter 16 后，任务从“走到足球前方”进一步推进到“在合适时机踢球”。
> 
> 

视觉踢球不是简单地调用一个踢球动作。机器人要先看见足球，估计足球相对身体的位置，追到合适距离，完成踢前对齐，再启动 VisualKick（视觉踢球策略）。VisualKick 启动后，还需要持续向 `/kick_ball` 提供足球位置、期望踢球方向、目标点和力度等信息。只有这些环节配合起来，机器人才能稳定踢到球。

本章实践代码放在：

```Plaintext
CourseCode/chapter_16_visual_kick_strategy/
```

本章代码目录自包含，包含足球检测、深度增强定位、行为树内核、视觉踢球工具、视觉踢球行为树节点和视觉踢球主节点。它不会 import 前面章节的代码文件。

本章会真实控制 K1 头部、身体和 VisualKick。运行前必须确认机器人站立稳定，前方和左右两侧留出足够空间。如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张“足球检测 \-\> 空间定位 \-\> 追球 \-\> 踢前对齐 \-\> VisualKick \-\> 踢球退出”的总流程图。每个模块旁边标出对应 ROS2 话题或 SDK 接口。

## 16\.1 视觉踢球任务

视觉踢球任务可以用一句话描述：机器人根据视觉估计出的足球位置，追到球前，完成踢前对齐，然后调用 VisualKick 踢出足球。

这句话里面包含五个连续步骤：

```Plaintext
看见足球
  ↓
估计足球在机器人基座坐标系下的位置
  ↓
追到合适距离
  ↓
踢前对齐
  ↓
启动 VisualKick 并发布 /kick_ball
```

前四步决定“能不能把足球放到适合踢的位置”，最后一步决定“如何把球踢出去”。

### 16\.1\.1 视觉踢球和普通动作播放的区别

普通动作播放通常是固定轨迹。例如上半身动作回放中，机器人按照预先记录的关节角运动。足球在哪里并不会改变动作本身。

视觉踢球不同。足球位置会影响踢球策略：

- 足球在机器人正前方，踢球策略可以直接执行；

- 足球偏左或偏右，需要先对齐；

- 足球太远，需要继续追球；

- 足球丢失，不能盲目踢；

- 足球被踢出后，需要关闭 VisualKick 并停止。

因此，VisualKick 不是一个孤立动作，而是视觉、定位、追球、对齐和踢球策略共同组成的闭环任务。

### 16\.1\.2 本章任务边界

本章只完成“追球后踢一脚”的视觉踢球策略。任务完成后，节点停止并进入终止态。如果要再次踢球，需要重新启动节点。

这样设计有两个原因。

第一，单次踢球便于观察流程。学习者可以清楚看到：

```Plaintext
搜索 -> 追球 -> 对齐 -> 踢球 -> 停止
```

第二，单次踢球更安全。机器人踢完后停止，不会在球滚动后继续反复追踢。

后续综合项目可以在这个基础上扩展为连续任务，例如踢完后重新找球、继续追球、进入下一轮决策。

### 16\.1\.3 和前面章节的联动

视觉踢球依赖前面章节的多个模块。

|前序模块|在本章中的作用|
|---|---|
|YOLO 足球检测|找到图像中的足球|
|空间定位|输出足球基座坐标 `x`、`y`、`distance`、`angle`|
|稳定追球|让机器人靠近足球，并在合适距离减速|
|行为树|把搜索、追球、对齐、踢球和停止组织成阶段流程|

本章主节点不是从零开始做所有事情，而是把这些能力串成完整视觉踢球流程。

代码中的流程为：

```Plaintext
Sequence: VisualKickTask
├── Selector: ApproachUntilKickReady
│   ├── KickReadyDistance
│   ├── Sequence[BallAvailable, ChaseBall]
│   └── SearchBall
├── AlignForKick
├── VisualKickOnce
└── StopAfterKick
```

可以把它理解为：

```Plaintext
先靠近足球
再对齐足球
再踢一脚
最后停止
```

> 配图建议：放置一张行为树图。上方是 `VisualKickTask` 顺序节点，下方四个阶段分别标为“靠近”“对齐”“踢球”“停止”。

## 16\.2 VisualKick 策略接口

VisualKick 是 Booster SDK（Software Development Kit，软件开发工具包）提供的视觉踢球策略接口。它不是单独依靠一个固定动作完成踢球，而是结合视觉输入和 `/kick_ball` 目标消息，让机器人执行适合当前足球位置的踢球策略。

在代码中，VisualKick 的调用形式是：

```Python
self.client.VisualKick(True)
```

关闭时：

```Python
self.client.VisualKick(False)
```

在支持版本选择的 SDK 中，还可以传入踢球动作版本：

```Python
self.client.VisualKick(True, VisualKickVersion.kV2)
```

本章代码封装在：

```Plaintext
CourseCode/chapter_16_visual_kick_strategy/visual_kick_utils.py
```

核心类是：

```Python
RobotVisualKickInterface
```

### 16\.2\.1 VisualKick 的前置模式

VisualKick 需要机器人处于适合足球策略的模式。代码中连接机器人后会依次执行：

```Plaintext
Prepare -> Walking -> kSoccer
```

其中：

- `Prepare` 用于准备机器人运动控制；

- `Walking` 让机器人进入可行走控制状态；

- `kSoccer` 是足球相关策略使用的模式。

本章主节点默认：

```Plaintext
use_soccer_mode = true
```

连接后会尝试切入 `kSoccer` 足球模式：

```Python
self.client.ChangeMode(RobotMode.kSoccer)
```

如果没有成功进入足球模式，VisualKick 可能无法正常执行。因此启动主节点后，必须观察日志中是否出现：

```Plaintext
切换机器人到 kSoccer 足球模式 ...
```

如果日志提示切换失败，应先检查 SDK 和机器人系统版本是否匹配。

### 16\.2\.2 VisualKick 启动后还要持续发布 /kick\_ball

VisualKick 启动后，程序不能只调用一次 `VisualKick(True)` 就结束。视觉踢球策略需要持续知道：

- 足球当前在哪里；

- 希望往哪个方向踢；

- 目标点在哪里；

- 踢球力度是多少。

这些信息通过 `/kick_ball` 话题发送。本章 `VisualKickOnce` 节点在 `KICK` 阶段会反复执行：

```Python
self.kick_publisher.publish(...)
```

这就是“VisualKick 与视觉联动”的核心：SDK 负责踢球策略执行，ROS2 话题负责持续提供视觉目标数据。

### 16\.2\.3 kV1 与 kV2 两种踢球版本

本章代码支持两个 VisualKick 版本：

```Plaintext
kV1
kV2
```

可以通过参数选择：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV1
```

或：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV2
```

两种版本可以按下面方式理解。

|版本|特点|适合场景|风险|
|---|---|---|---|
|`kV1`|出脚更快、踢得更近|想观察快速触球，球距和对齐很稳定|对测距和对齐更敏感，坐标偏差大时更容易踢空|
|`kV2`|踢得更远、容差更大|默认视觉踢球实践、对测距误差更宽容|动作可能更慢，空间要求更高|

本章默认使用：

```Plaintext
kick_version = kV2
```

原因是视觉定位存在误差，踢前对齐也不可能完全精确。`kV2` 对误差更宽容，更适合作为默认版本。

如果 `kV2` 能稳定踢到球，再尝试 `kV1`，观察两者在出脚速度、触球位置和踢球距离上的差异。

### 16\.2\.4 power 力度参数

`power` 是 `/kick_ball` 消息中的力度参数。它不是 VisualKick 版本，而是踢球目标数据的一部分。

本章按以下规则使用：

```Plaintext
power < 5   偏传球，力度较轻
power > 5   偏射门，力度较大
power = 5   不建议使用，处在分界附近
```

默认值是：

```Plaintext
power = 3.0
```

它更接近轻传球，适合先观察策略是否能稳定踢到球。

如果希望演示射门，可以改成：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p power:=8.0
```

调大 `power` 前应确认三件事：

1. 足球基座坐标稳定；

2. 踢前对齐能进入 `ALIGN_DONE`；

3. 机器人前方有足够空间。

不要在坐标不稳定或对齐明显偏差时直接使用大力度射门。力度越大，足球飞出后越难在小场地内控制。

### 16\.2\.5 kick\_dir 踢球方向

`kick_dir` 表示期望踢球方向，单位为弧度，方向相对机器人自身坐标系：

```Plaintext
kick_dir = 0.0   向机器人正前方踢
kick_dir > 0     向左前方踢
kick_dir < 0     向右前方踢
```

例如，向左前方踢：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_dir:=0.4
```

向右前方踢：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_dir:=-0.4
```

需要注意，`kick_dir` 是期望方向，不是一定能精确达到的轨迹。实际效果还会受到足球位置、机器人站姿、地面摩擦、球与脚接触点等因素影响。

## 16\.3 `/kick_ball` 数据机制

`/kick_ball` 是 VisualKick 使用的踢球目标话题。本章代码通过 `KickPublisher` 发布该话题。

消息类型是：

```Plaintext
brain/msg/Kick
```

字段结构为：

```Plaintext
std_msgs/Header header
float64 x
float64 y
float64 dir
float64 goal_x
float64 goal_y
float64 robot_theta_to_field
float64 power
```

本章代码运行环境需要能够导入：

```Python
from brain.msg import Kick
```

如果当前环境没有 `brain` 消息包，节点会提示无法发布 `/kick_ball`。这不是 Python 语法问题，而是 ROS2 自定义消息包没有在当前环境中可用。

### 16\.3\.1 x 和 y：足球相对机器人位置

`x` 和 `y` 来自 `/vision/ball_position_base`：

```Plaintext
x：足球在机器人正前方的距离
y：足球相对机器人中心线的左右偏移
```

本章发布 `/kick_ball` 时使用当前足球坐标：

```Python
msg.x = float(ball.x)
msg.y = float(ball.y)
```

这两个字段让 VisualKick 知道足球相对机器人脚下的位置。

如果 `x` 明显不准，机器人会在错误距离上出脚；如果 `y` 明显不准，机器人可能脚从球旁边掠过。因此，启动 VisualKick 前必须先确认足球基座坐标稳定。

### 16\.3\.2 dir：期望踢球方向

`dir` 对应参数：

```Plaintext
kick_dir
```

它表示期望踢球方向，单位是弧度。代码中：

```Python
msg.dir = float(kick_dir)
```

常用值：

```Plaintext
0.0    正前方
0.4    左前方
-0.4   右前方
```

如果机器人已经通过对齐让足球位于身体正前方，`kick_dir=0.0` 是最容易观察的设置。

### 16\.3\.3 goal\_x 和 goal\_y：目标点

`goal_x` 和 `goal_y` 表示目标点相对机器人的位置。本章默认：

```Plaintext
goal_x = 3.0
goal_y = 0.0
```

可以理解为：目标在机器人正前方约 3 m 处。

这两个字段用于给踢球策略提供目标方向参考。对于本章单次踢球实践，重点先观察机器人是否能稳定触球和把球踢出；目标点精细控制可以放到后续综合任务中继续扩展。

### 16\.3\.4 robot\_theta\_to\_field：场地方向

`robot_theta_to_field` 表示机器人相对场地坐标系的朝向。完整足球比赛任务中，机器人需要知道场地方向、球门位置和自身姿态。

本章还没有引入完整场地定位，因此默认：

```Plaintext
robot_theta_to_field = 0.0
```

这表示暂时把机器人当前朝向看作场地方向基准。

### 16\.3\.5 power：力度

`power` 表示踢球力度。它与 `kick_version` 不同。

可以这样区分：

```Plaintext
kick_version：选择 VisualKick 动作版本，例如 kV1 或 kV2
power：告诉踢球策略这次更像传球还是射门
```

本章建议按阶段使用：

|阶段|power|目的|
|---|---|---|
|初次跑通|`3.0`|轻传球，风险较低|
|确认能稳定触球|`4.0`|稍加力度|
|射门观察|`8.0`|大力度踢出|

不建议直接从大力度开始。先确认视觉坐标、对齐和 VisualKick 能稳定工作，再逐步增加力度。

## 16\.4 踢球触发条件

VisualKick 不能在任意时刻启动。若足球太远、太偏、坐标不稳定，直接启动踢球很容易踢空。

本章设置了四类触发条件：

```Plaintext
足球坐标有效
足球进入准备距离
踢前对齐完成或对齐超时
/kick_ball 能发布
```

### 16\.4\.1 条件一：足球坐标有效

本章主节点读取：

```Plaintext
/vision/ball_position_base
```

只有消息有效时，才进入追球或踢球流程。

有效坐标至少需要：

- `valid = true`；

- `x`、`y` 在控制范围内；

- 坐标没有超过超时时间。

如果足球坐标无效，行为树会进入：

```Plaintext
SearchBall
```

此时机器人身体停止，头部扫描，等待重新看到足球。

### 16\.4\.2 条件二：足球进入准备距离

本章使用 `stop_dist` 作为踢球准备距离：

```Plaintext
stop_dist = 0.78 m
```

当 `approach <= stop_dist` 时，机器人不再继续前冲，而是进入踢前对齐阶段。

其中 `approach` 通常使用前方距离 `x`：

```Python
approach = approach_distance(ball.x, ball.y, ball.distance)
```

这样做的原因在 Chapter 14 已经讲过：踢球前更关心足球离机器人前方还有多远，而不是单纯看斜线距离。

为了避免坐标在边界附近抖动，本章设置：

```Plaintext
ready_hysteresis = 0.22
```

进入准备距离后，足球只有重新远离到 `stop_dist + ready_hysteresis` 之外，才会退出准备状态。

### 16\.4\.3 条件三：踢前对齐

进入准备距离后，机器人还不能立刻踢。足球可能在身体左侧或右侧，或者机器人朝向不正。

本章使用 `AlignForKick` 做踢前对齐。它只做两类动作：

```Plaintext
横向移动 vy
原地转向 vyaw
```

不再继续前进。代码中：

```Python
self.robot.move(0.0, vy, vyaw)
```

对齐完成条件为：

```Plaintext
abs(angle) <= align_yaw_tol
abs(y) <= align_y_tol
```

默认值：

```Plaintext
align_yaw_tol = 0.12 rad
align_y_tol = 0.08 m
```

含义是：

- 足球方位角足够接近正前方；

- 足球左右偏移足够小。

如果对齐一直无法完成，`adjust_timeout_sec` 到达后会进入 VisualKick，让 VisualKick 做最后修正：

```Plaintext
adjust_timeout_sec = 4.0
```

这不是说对齐不重要，而是防止机器人在小范围内长时间左右调整。

### 16\.4\.4 条件四：/kick\_ball 可发布

启动 VisualKick 后，本章节点会持续发布 `/kick_ball`。如果当前环境无法导入 `brain.msg.Kick`，节点无法发布踢球目标。

本章参数：

```Plaintext
require_kick_msg = true
```

表示默认要求 `/kick_ball` 消息可用。如果缺少消息包，节点会进入 `KICK_FAILED` 并重置流程。

如果只想检查前面搜索、追球、对齐逻辑，可以临时设置：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p require_kick_msg:=false
```

但真机踢球效果需要 `/kick_ball` 正常发布。

### 16\.4\.5 VisualKick 退出条件

VisualKick 启动后不能无限运行。本章设置三个退出条件：

|条件|含义|
|---|---|
|足球距离超过 `kicked_range`|认为足球已经被踢出|
|足球在最短保持时间后丢失|认为球离开视野或滚出检测范围|
|超过 `kick_timeout_sec`|兜底退出|

默认值：

```Plaintext
kick_min_dwell_sec = 1.5
kicked_range = 1.2
kick_timeout_sec = 8.0
```

`kick_min_dwell_sec` 很重要。它避免刚启动 VisualKick 时因为瞬间坐标抖动就误判“踢完”。只有超过最短保持时间后，才检查是否踢出、丢球或超时。

## 16\.5 程序案例：视觉踢球节点

本章代码目录为：

```Plaintext
CourseCode/chapter_16_visual_kick_strategy/
```

文件结构如下：

```Plaintext
chapter_16_visual_kick_strategy/
├── soccer_ball_detector.py
├── soccer_detection_utils.py
├── ball_position_depth_node.py
├── ball_localization_utils.py
├── print_ball_position.py
├── behavior_tree_core.py
├── visual_kick_utils.py
├── visual_kick_bt_nodes.py
├── visual_kick_strategy_node.py
├── README.md
└── models/
    └── soccer_yolo.pt
```

### 16\.5\.1 检测与定位文件

本章仍然需要足球检测和空间定位：

```Plaintext
soccer_ball_detector.py
ball_position_depth_node.py
```

运行顺序是：

```Plaintext
RGB 图像 -> YOLO 足球检测 -> 深度增强定位 -> /vision/ball_position_base
```

视觉踢球节点只读取 `/vision/ball_position_base`，不直接处理图像。这样做能保持模块边界清晰：

- 检测节点负责找足球；

- 定位节点负责算空间坐标；

- 视觉踢球节点负责决策和控制。

### 16\.5\.2 visual\_kick\_utils\.py

`visual_kick_utils.py` 是本章视觉踢球公共工具。

其中 `KickPublisher` 负责发布 `/kick_ball`：

```Python
msg.x = float(ball.x)
msg.y = float(ball.y)
msg.dir = float(kick_dir)
msg.goal_x = float(goal_x)
msg.goal_y = float(goal_y)
msg.robot_theta_to_field = float(robot_theta_to_field)
msg.power = float(power)
```

`RobotVisualKickInterface` 负责 SDK 控制：

```Python
self.client.Move(vx, vy, vyaw)
self.client.RotateHead(pitch, yaw)
self.client.VisualKick(start, version)
```

它还负责解析踢球版本：

```Python
normalize_kick_version("kV1") -> "kV1"
normalize_kick_version("kV2") -> "kV2"
```

如果输入不是 `kV1`，默认按 `kV2` 处理。这样可以避免大小写或输入格式造成节点崩溃。

### 16\.5\.3 visual\_kick\_bt\_nodes\.py

`visual_kick_bt_nodes.py` 把视觉踢球拆成行为树叶子节点。

|节点|类型|作用|
|---|---|---|
|`BallAvailable`|条件节点|判断是否有有效足球坐标|
|`KickReadyDistance`|条件节点|判断是否进入踢球准备距离|
|`ChaseBall`|动作节点|追球到准备距离附近|
|`SearchBall`|动作节点|看不到球时停止身体并扫头|
|`AlignForKick`|动作节点|踢前横向和转向对齐|
|`VisualKickOnce`|动作节点|启动 VisualKick 并持续发布 `/kick_ball`|
|`StopAfterKick`|动作节点|踢球结束后停止|

这几个节点组成：

```Plaintext
Sequence: VisualKickTask
```

顶层使用带记忆的顺序节点。它的意义是：已经进入对齐阶段后，不再每一拍回到追球阶段，除非对齐失败或足球丢失。

这和 Chapter 15 的反应式追球树不同。追球可以每拍重新判断；单次踢球更像一个阶段流程：

```Plaintext
先靠近
再对齐
再踢
再停止
```

因此这里使用 `Sequence(memory=True)`。

### 16\.5\.4 visual\_kick\_strategy\_node\.py

`visual_kick_strategy_node.py` 是本章主节点。

每一拍执行：

```Python
self.blackboard.ball = self.reader.latest()
status = self.tree.tick()
```

如果整棵树返回 `SUCCESS`，表示踢球流程完成：

```Python
self.robot.safe_shutdown()
self.done = True
```

节点进入终止态，不再继续追球或踢球。

如果返回 `FAILURE`，表示流程中断，例如对齐时足球丢失、足球远离准备距离、`/kick_ball` 消息不可用等。节点会关闭 VisualKick、停止身体，并重置行为树：

```Python
self.robot.visual_kick(False)
self.robot.stop(force=True)
self.tree.reset()
```

这样可以避免中途异常后 VisualKick 仍保持开启。

## 16\.6 运行方式与效果说明：策略踢球

本节按逐步运行检查的方式推进。不要一开始就直接启动 VisualKick。先确认检测，再确认定位，再确认追球和对齐，最后启动视觉踢球。

### 16\.6\.1 进入代码目录

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_16_visual_kick_strategy
```

### 16\.6\.2 启动足球检测

终端 1：

```Bash
python3 soccer_ball_detector.py
```

效果说明：

- 足球在画面中时，检测节点应持续发布 `/vision_detection/ball`；

- 如果检测不到，先调整足球位置、光照和相机视角；

- 不要在检测不稳定时继续启动踢球节点。

### 16\.6\.3 启动足球空间定位

终端 2：

```Bash
python3 ball_position_depth_node.py
```

它会发布：

```Plaintext
/vision/ball_position_base
```

如果定位节点提示 `no_head_pose`、`not_detected`、`all_estimators_failed` 等无效原因，需要先排查定位链路。

### 16\.6\.4 打印足球基座坐标

终端 3：

```Bash
python3 print_ball_position.py
```

把足球放在机器人正前方约 1\.5 m 处，观察输出：

```Plaintext
x=1.480m y=-0.030m z=0.090m distance=1.481m angle=-0.020rad method=depth_median
```

检查顺序：

1. `valid` 是否为有效输出；

2. `x` 是否接近真实前方距离；

3. `y` 是否接近左右偏移；

4. `angle` 是否在足球正前方时接近 0；

5. `method` 是否稳定，不要频繁大幅跳变。

如果把足球放在左前方，`y` 和 `angle` 应为正；放在右前方，应为负。如果符号相反，应先检查坐标系转换。

### 16\.6\.5 启动视觉踢球策略节点

终端 4：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p robot_ip:=127.0.0.1
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ODVhM2UzYWJlZWZkMjczNGZhMjZhMDk3MDM4Nzk1NTNfMDZmMDIwNGFjZjhhMTVlODkzYzRiMjFlNWE3YTY4NjRfSUQ6NzY2NzA2MDgxMDU2NDU4NjY5OV8xNzg1ODM5ODM5OjE3ODU5MjYyMzlfVjM)

启动日志应包含：

```Plaintext
Chapter 16 VisualKick 视觉踢球策略节点已启动。
流程：搜索/追球 -> 踢前对齐 -> VisualKick -> 停止。
kick_version=kV2, power=3.0 (pass), kick_dir=0.00rad
```

连接 SDK 后还应看到：

```Plaintext
切换机器人到 Prepare 模式 ...
切换机器人到 Walking 模式 ...
切换机器人到 kSoccer 足球模式 ...
```

如果没有进入 `kSoccer`，先不要继续调踢球参数，应先解决模式切换问题。

### 16\.6\.6 观察阶段一：SEARCH

如果足球不在画面中，日志会出现：

```Plaintext
mode=SEARCH
```

此时预期效果：

- 机器人身体停止；

- 头部左右扫描；

- 找到足球后自动进入追球。

如果进入 `SEARCH` 但头部不动，检查 SDK 是否连接成功，或者是否设置了 `enable_motion=false`。

### 16\.6\.7 观察阶段二：CHASE

足球被检测并定位后，节点进入：

```Plaintext
mode=CHASE
```

此时预期效果：

- 机器人向足球靠近；

- 足球偏左时，机器人向左修正；

- 足球偏右时，机器人向右修正；

- 接近 `stop_dist` 后减速。

日志中会有：

```Plaintext
vx=... vy=... vyaw=... approach=... slow=...
```

其中：

- `approach` 越接近 `stop_dist`，`slow` 越小；

- `vx` 是前进速度；

- `vy` 是横向速度；

- `vyaw` 是转身速度。

如果追球太快，降低速度：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p vx_limit:=0.35 -p vy_limit:=0.15 -p vyaw_limit:=0.6
```

### 16\.6\.8 观察阶段三：ALIGN

足球进入准备距离后，节点进入：

```Plaintext
mode=ALIGN
```

此时机器人不再前进，只做横向和转向调整：

```Plaintext
Move(0.0, vy, vyaw)
```

目标是让：

```Plaintext
abs(angle) <= align_yaw_tol
abs(y) <= align_y_tol
```

默认：

```Plaintext
align_yaw_tol = 0.12
align_y_tol = 0.08
```

对齐完成后会进入：

```Plaintext
mode=ALIGN_DONE
```

如果对齐时间超过 `adjust_timeout_sec`，也会进入下一阶段，让 VisualKick 做最后修正。若对齐一直很慢，可以适当放宽容差：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p align_yaw_tol:=0.18 -p align_y_tol:=0.12
```

### 16\.6\.9 观察阶段四：KICK

进入 `KICK` 后，节点会：

1. 停止身体；

2. 让头部低头看球；

3. 调用 `VisualKick(True)`；

4. 持续发布 `/kick_ball`；

5. 等待足球被踢出、丢失或超时。

日志中会看到：

```Plaintext
mode=KICK
kick_msgs=...
```

`kick_msgs` 表示已经发布的 `/kick_ball` 消息数量。如果它一直为 0，应检查 `brain.msg.Kick` 是否可用。

### 16\.6\.10 观察阶段五：FINISHED

踢球结束后，节点进入：

```Plaintext
mode=FINISHED
```

可能原因：

|reason|含义|
|---|---|
|`ball_moved_beyond_kicked_range`|足球距离超过 `kicked_range`，认为已踢出|
|`ball_lost_after_kick`|踢球最短保持时间后足球丢失|
|`kick_timeout`|超时兜底退出|

进入 `FINISHED` 后，节点会关闭 VisualKick、停止身体、回正头部，并进入终止态。

### 16\.6\.11 kV1/kV2 与 power 的逐步运行建议

建议按下面顺序调整。

第一步，默认设置：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV2 -p power:=3.0
```

目的：先确认能追到、能对齐、能触球。

第二步，仍用 `kV2`，稍加力度：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV2 -p power:=4.0
```

目的：观察球是否能稳定滚出。

第三步，演示射门：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV2 -p power:=8.0
```

目的：观察大力度射门效果。此时必须保证前方空间充足。

第四步，对比 `kV1`：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV1 -p power:=3.0
```

目的：观察更快出脚版本对坐标精度的要求。若 `kV1` 踢空，而 `kV2` 能踢到，通常说明定位或对齐还不够稳定。

## 16\.7 常见问题排查

### 16\.7\.1 无法导入 brain\.msg\.Kick

现象：

```Plaintext
无法导入 brain.msg.Kick，/kick_ball 无法发布
```

原因是当前 ROS2 环境没有 `brain/msg/Kick` 消息类型。VisualKick 需要 `/kick_ball` 目标消息，真机踢球时应在包含该消息包的 K1 环境中运行。

### 16\.7\.2 VisualKick 没反应

优先检查模式切换日志：

```Plaintext
切换机器人到 kSoccer 足球模式 ...
```

如果切换失败，VisualKick 可能不会执行。还要检查：

- SDK 是否成功导入；

- 机器人是否已经站立稳定；

- `enable_motion` 是否为 `true`；

- `use_soccer_mode` 是否为 `true`。

### 16\.7\.3 进入 KICK 但 kick\_msgs 一直为 0

这说明 VisualKick 阶段已经启动，但 `/kick_ball` 没有成功发布。

检查：

1. `brain.msg.Kick` 是否可用；

2. `require_kick_msg` 是否为 `true`；

3. `ball.valid` 是否仍然为有效状态。

如果踢球阶段足球坐标丢失，节点无法继续发布有效 `x`、`y`。

### 16\.7\.4 踢空

踢空通常不是单一原因。按顺序检查：

1. 足球基座坐标是否稳定；

2. `x` 是否接近真实前方距离；

3. `y` 和 `angle` 在正前方时是否接近 0；

4. 是否进入 `ALIGN_DONE`；

5. 是否使用了过于敏感的 `kV1`；

6. `stop_dist` 是否过远或过近。

优先使用：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kick_version:=kV2 -p power:=3.0
```

确认能稳定触球后，再调整其他参数。

### 16\.7\.5 踢得太轻或太重

力度由 `power` 控制。

轻传球：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p power:=3.0
```

射门：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p power:=8.0
```

不建议使用：

```Plaintext
power = 5.0
```

因为它处在传球和射门分界附近，不利于判断效果。

### 16\.7\.6 踢完后不退出

如果球已经踢出，但节点没有进入 `FINISHED`，检查 `kicked_range`。

默认：

```Plaintext
kicked_range = 1.2
```

如果场地小，球踢出后距离没有超过 1\.2 m，可以降低：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p kicked_range:=1.0
```

如果 VisualKick 一直运行，检查 `kick_timeout_sec` 是否设置过大。

### 16\.7\.7 对齐时间太长

如果机器人长时间在球前左右微调，可以：

1. 放宽对齐容差；

2. 缩短对齐超时；

3. 检查 `y` 和 `angle` 是否抖动。

放宽容差：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p align_yaw_tol:=0.18 -p align_y_tol:=0.12
```

缩短超时：

```Bash
python3 visual_kick_strategy_node.py --ros-args -p adjust_timeout_sec:=2.5
```

## 16\.8 本章小结

本章完成了从追球到视觉踢球的完整策略控制。

学习者需要掌握以下要点：

1. VisualKick 不是孤立动作，它依赖视觉检测、空间定位、追球和踢前对齐。

2. VisualKick 启动前应进入 `kSoccer` 足球模式。

3. `/kick_ball` 为 VisualKick 持续提供足球位置、踢球方向、目标点和力度。

4. `kV1` 出脚更快但更依赖精准测距和对齐；`kV2` 踢得更远、容差更大，适合作为默认版本。

5. `power < 5` 更接近传球，`power > 5` 更接近射门，不建议使用 `power = 5`。

6. 踢球触发需要满足有效坐标、准备距离、踢前对齐和 `/kick_ball` 可发布等条件。

7. 踢球后要根据球被踢出、丢球或超时关闭 VisualKick 并停止机器人。

完成本章后，K1 已经能够完成“搜索足球、追到球前、踢前对齐、视觉踢球、踢完停止”的单次视觉踢球流程。后续综合项目可以把该流程继续扩展为更完整的自主足球任务。

