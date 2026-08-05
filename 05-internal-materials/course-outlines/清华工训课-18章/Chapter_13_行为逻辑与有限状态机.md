# Chapter\_13\_行为逻辑与有限状态机

# Chapter 13｜行为逻辑与有限状态机

> Chapter 11 让 K1 能够在相机图像中检测足球，Chapter 12 进一步把足球从图像坐标转换为机器人基座坐标。进入 Chapter 13 后，课程从“感知结果”进入“行为组织”：机器人不仅要知道足球在哪里，还要根据“看见球”和“看不见球”的变化，决定当前应该做什么。
> 
> 

本章围绕 FSM（Finite State Machine，有限状态机）展开。有限状态机是一种非常适合入门机器人行为逻辑的方法。它把复杂行为拆成若干明确状态，例如：

```Plaintext
看见足球 -> 跟随足球
看不见足球 -> 转头搜索
长时间看不见足球 -> 可选地原地转身扩大搜索范围
重新看见足球 -> 回到跟随
```

本章实践代码放在：

```Plaintext
CourseCode/chapter_13_head_tracking_fsm/
```

本章代码目录自包含，包含足球检测节点、追踪工具函数、头部跟随控制器和丢球搜索有限状态机。它不会 import Chapter 11 或 Chapter 12 的代码文件。这样多终端运行时只需要进入 Chapter 13 目录，避免路径混乱。

本章会真实控制 K1 头部运动。进阶实践中，如果显式打开身体搜索，机器人会原地慢速转身。运行前必须确认机器人站立稳定，周围留出安全空间。如果机器人出现异常姿态或身体运动无法停止，应立即按下机器人背部 `STAND` 按钮。

配图建议：放置一张“检测结果 \-\> 行为状态 \-\> 头部/身体动作”的总流程图，突出 Chapter 13 从感知输出走向行为控制的作用。

## 13\.1 行为状态

机器人在真实环境中可能遇到这样的情况：足球可能突然离开画面（机器人视野），也可能重新出现；检测模型可能短暂漏检（足球在视野内，因检测模型问题中间某几帧没有检测出足球）；头部搜索一段时间后仍找不到球时，可能需要扩大搜索范围。

因此，机器人行为通常不是“从第一行代码执行到最后一行代码就结束”，而是不断循环：

```Plaintext
读取当前感知结果
  ↓
判断当前状态
  ↓
执行当前状态对应动作
  ↓
根据条件切换状态
  ↓
下一轮继续判断
```

这就是行为状态的意义。状态表示机器人当前处于哪一种行为模式。

### 13\.1\.1 为什么需要状态

假设没有状态，只用一个简单判断：

```Plaintext
如果看到足球：转头跟随
如果看不到足球：转头搜索
```

这个逻辑看起来能用，但真实运行时会出现问题。

第一，检测会短暂抖动。相机一帧看见球，下一帧没看见，再下一帧又看见。如果程序没有状态记忆，头部可能频繁在“跟随”和“搜索”之间跳动。

第二，丢球有时间过程。刚丢球时，可以先只转头搜索；如果持续看不到，再考虑身体原地转身。如果没有状态，就很难表达“先等一段时间，再进入下一步”。

第三，不同动作需要不同收尾。身体搜索时机器人在原地转身，一旦重新看到足球，必须先停止身体，再回到头部跟随。如果只写简单判断，很容易遗漏停止动作。

有限状态机就是为了解决这些问题。

### 13\.1\.2 本章使用的状态

本章正式代码使用三个状态：

|状态|含义|主要动作|
|---|---|---|
|`TRACK`|检测到足球|根据足球偏差控制头部跟随|
|`HEAD_SEARCH`|暂时看不到足球|只转头做连续扫描|
|`BODY_SEARCH`|长时间看不到足球，且允许身体搜索|身体原地慢速转身，头部继续扫描|

其中 `BODY_SEARCH` 是进阶状态，默认不开启。只有运行时显式设置：

```Bash
python3 ball_search_fsm_controller.py --ros-args -p enable_body_search:=true
```

机器人身体才会参与搜索。

### 13\.1\.3 状态、动作和切换条件

理解 FSM 时，可以把三个概念分开：

|概念|解释|本章例子|
|---|---|---|
|状态|当前处于哪种行为模式|`TRACK`、`HEAD_SEARCH`、`BODY_SEARCH`|
|动作|当前状态下要做什么|跟随、扫头、原地转身|
|切换条件|什么情况下进入另一个状态|看见球、丢球超时、搜索时间超过阈值|

例如：

```Plaintext
状态：TRACK
动作：头部跟随足球
切换条件：超过 ball_timeout_sec 没有可靠足球检测 -> HEAD_SEARCH
```

再例如：

```Plaintext
状态：HEAD_SEARCH
动作：头部左右上下扫描
切换条件：重新看到足球 -> TRACK
切换条件：搜索超过 3 秒且 enable_body_search=true -> BODY_SEARCH
```

配图建议：放置一张状态卡片图，每张卡片包含“状态名、输入、动作、切换条件”。

## 13\.2 FSM 有限状态机

FSM 的全称是 Finite State Machine，中文是有限状态机。它的名字可以拆开理解：

- `Finite`：有限，表示状态数量是有限的；

- `State`：状态，表示机器人当前处于某种行为模式；

- `Machine`：机器，表示状态之间按照规则自动切换。

有限状态机不是机器人专用概念。生活中也有很多类似例子。比如红绿灯：

```Plaintext
红灯 -> 绿灯 -> 黄灯 -> 红灯
```

每个灯色都是一个状态，时间到了就切换到下一个状态。电梯也可以看成状态机：

```Plaintext
待机 -> 关门 -> 上行 -> 开门 -> 待机
```

机器人行为也可以这样组织。

### 13\.2\.1 FSM 的基本结构

一个有限状态机通常包括：

```Plaintext
状态集合
当前状态
输入事件
状态切换规则
每个状态下执行的动作
```

本章的状态集合是：

```Plaintext
TRACK
HEAD_SEARCH
BODY_SEARCH
```

输入事件主要来自足球检测结果：

```Plaintext
ball.visible = true
ball.visible = false
丢球持续时间
enable_body_search 参数
```

状态切换规则可以写成：

```Plaintext
如果看到足球：
    进入 TRACK
否则：
    如果刚丢球或身体搜索未启用：
        进入 HEAD_SEARCH
    如果头部搜索超过指定时间且身体搜索已启用：
        进入 BODY_SEARCH
```

### 13\.2\.2 FSM 和普通 if 判断的区别

FSM 里面也会用 `if` 判断，但 FSM 不是简单堆叠 if。它多了一个核心变量：

```Plaintext
当前状态
```

有了当前状态，程序就能记住“上一刻正在做什么”。例如：

- 只有从 `TRACK` 切换到 `HEAD_SEARCH` 时，才重置搜索计时；

- 只有从 `BODY_SEARCH` 切换回 `TRACK` 时，才需要停止身体转身；

- 进入 `TRACK` 时要重置低通滤波，避免搜索阶段残留数据影响跟随。

这些逻辑都依赖“状态记忆”。

### 13\.2\.3 本章 FSM 的状态转移图

本章 FSM 可以用文字画成下面这样：

```Plaintext
看见足球
      ┌──────────────────────────┐
      │                          │
      v                          │
  ┌─────────┐    丢球超时     ┌─────────────┐
  │ TRACK   │ ─────────────> │ HEAD_SEARCH │
  └─────────┘                └─────────────┘
       ^                         │
       │                         │  搜索超过阈值
       │                         │  且允许身体搜索
       │                         v
       │                    ┌─────────────┐
       └─────────────────── │ BODY_SEARCH │
            看见足球         └─────────────┘
```

其中：

- `TRACK` 是正常跟随；

- `HEAD_SEARCH` 是刚丢球后的低风险搜索；

- `BODY_SEARCH` 是扩大搜索范围的进阶动作。

配图建议：用正式流程图重新绘制上述状态转移图。箭头上标注“看见足球”“丢球超时”“搜索超过阈值且允许身体搜索”。

### 13\.2\.4 为什么不一丢球就转身体

身体搜索比头部搜索风险更高。头部搜索只转头，机器人身体不移动；身体搜索会让机器人原地转身，虽然不前进、不横移，但仍然需要更大的安全空间。

因此，本章状态机采用两段式搜索：

```Plaintext
刚丢球 -> 先 HEAD_SEARCH
持续找不到 -> 可选 BODY_SEARCH
```

这样做有两个好处：

第一，很多丢球只是短暂漏检。只要转头扫一下，足球可能很快回到画面中，没有必要让身体参与。

第二，身体搜索必须更谨慎。只有确认机器人周围安全，并显式打开 `enable_body_search`，才进入 `BODY_SEARCH`。

## 13\.3 TRACK、FIND 与 SCAN

正式大纲中使用 `TRACK`、`FIND`、`SCAN` 来描述本章行为。它们分别代表：

|行为概念|含义|
|---|---|
|`TRACK`|看见足球后持续跟随|
|`FIND`|丢球后尝试重新找回足球|
|`SCAN`|找球过程中执行的扫描动作|

在本章代码中，为了让动作更具体，`FIND/SCAN` 被拆成两个工程状态：

|大纲概念|代码状态|说明|
|---|---|---|
|`TRACK`|`TRACK`|头部跟随足球|
|`FIND/SCAN`|`HEAD_SEARCH`|只用头部扫描找球|
|`FIND/SCAN`|`BODY_SEARCH`|身体原地转身，同时头部继续扫描|

这样命名能让学习者一眼看出每个状态到底控制了哪些部件。

### 13\.3\.1 TRACK：看见球就跟随

`TRACK` 的输入来自 Chapter 11 的检测话题：

```Plaintext
/vision_detection/ball
```

其中最重要的两个字段是：

```Plaintext
error_norm_x
error_norm_y
```

它们表示足球中心点相对图像中心的归一化偏差。

如果：

```Plaintext
error_norm_x > 0
```

说明足球在画面右侧。K1 头部 yaw 约定中，左转为正、右转为负，因此目标 yaw 要减小。

如果：

```Plaintext
error_norm_y > 0
```

说明足球在画面下方。为了让足球回到画面中心，头部 pitch 要向下修正。

代码中的控制公式是：

```Plaintext
target_yaw = current_yaw - yaw_gain * error_norm_x
target_pitch = current_pitch + pitch_gain * error_norm_y
```

这里的 `gain` 是控制增益，可以理解成“偏差转成头部角度变化的比例”。

### 13\.3\.2 为什么要低通滤波

目标检测框会有轻微抖动。即使足球没有动，模型输出的中心点也可能在几个像素范围内变化。如果把这些变化直接变成头部命令，头部会一直细微抖动。

低通滤波的作用是让输入变平滑。代码中使用：

```Plaintext
smooth = alpha * 当前偏差 + (1 - alpha) * 上一次平滑值
```

如果 `alpha` 较大，头部反应更快；如果 `alpha` 较小，头部更稳但反应更慢。

本章默认：

```Plaintext
filter_alpha = 0.30
```

可以理解为：新检测结果占 30%，上一轮平滑结果占 70%。

> 配图建议：画一张曲线图，对比“原始检测偏差抖动曲线”和“低通滤波后的平滑曲线”。

### 13\.3\.3 HEAD\_SEARCH：丢球后只转头搜索

当检测结果长时间没有可靠足球时，状态机进入：

```Plaintext
HEAD_SEARCH
```

这个状态不移动身体，只控制头部按照连续函数扫描。代码中使用正弦函数生成头部 yaw 和 pitch：

```Plaintext
yaw = home_yaw + yaw_amplitude * sin(phase)
pitch = home_pitch + pitch_amplitude * sin(phase + π/2)
```

如果不熟悉正弦函数，可以把它理解成一个平滑来回摆动的数值。它会在最大值和最小值之间连续变化，不会突然跳变。

头部搜索使用正弦函数的好处是：

- 动作连续；

- 不容易产生突然大角度跳动；

- 扫描范围和周期容易调参；

- 适合真实机器人头部运动。

### 13\.3\.4 BODY\_SEARCH：扩大搜索范围

如果只转头搜索一段时间仍看不到足球，并且显式打开了身体搜索，状态机进入：

```Plaintext
BODY_SEARCH
```

这个状态中，机器人身体执行：

```Plaintext
Move(0.0, 0.0, vyaw)
```

含义是：

```Plaintext
vx = 0.0      不前进
vy = 0.0      不横移
vyaw = 0.25   原地慢速转身
```

身体搜索只用于扩大视野，不用于追球。重新检测到足球后，程序会先调用：

```Plaintext
body.stop(force=True)
```

让身体停止转身，再回到 `TRACK`。

## 13\.4 状态切换逻辑

本章有限状态机主循环在：

```Plaintext
ball_search_fsm_controller.py
```

核心函数是：

```Python
on_control_tick()
```

它按固定频率执行：

```Plaintext
读取最近足球检测
  ↓
如果看到足球：TRACK
  ↓
如果看不到足球：HEAD_SEARCH 或 BODY_SEARCH
```

### 13\.4\.1 足球是否可见

足球可见不是简单判断当前帧有没有检测到球。本章使用 `BallReader` 保存最近一次可靠检测，并设置有效时间窗口：

```Plaintext
ball_timeout_sec = 1.00
```

如果最近一次可靠检测距离当前时间不超过 1 秒，仍认为足球可用。这样可以减少一两帧漏检带来的状态抖动。

同时，`BallReader` 会过滤低置信度结果：

```Plaintext
min_conf = 0.50
```

置信度低于阈值的检测不会作为可靠足球。

### 13\.4\.2 从 HEAD\_SEARCH 回到 TRACK

只要检测到可靠足球，状态机会立即进入：

```Plaintext
TRACK
```

进入 `TRACK` 时会做两件事：

1. 重置低通滤波，避免搜索阶段残留偏差影响跟随；

2. 如果之前处于 `BODY_SEARCH`，先停止身体转身。

这能保证机器人重新看到足球后，不会一边身体转圈一边尝试头部跟随。

### 13\.4\.3 从 TRACK 进入 HEAD\_SEARCH

当 `TRACK` 中足球丢失超过有效时间窗口，状态机会进入：

```Plaintext
HEAD_SEARCH
```

进入 `HEAD_SEARCH` 时，程序记录搜索开始时间：

```Python
self.search_start_time = time.time()
```

这个时间用于判断是否已经搜索超过阈值。

### 13\.4\.4 从 HEAD\_SEARCH 进入 BODY\_SEARCH

进入 `BODY_SEARCH` 需要同时满足两个条件：

```Plaintext
enable_body_search = true
搜索时间 >= head_search_before_body_sec
```

默认参数是：

```Plaintext
enable_body_search = false
head_search_before_body_sec = 3.0
```

也就是说，默认不会进入身体搜索。需要身体搜索时，必须显式运行：

```Bash
python3 ball_search_fsm_controller.py --ros-args -p enable_body_search:=true
```

配图建议：放置一张时间线图，展示“丢球 0\-3 秒：HEAD\_SEARCH；超过 3 秒且允许身体搜索：BODY\_SEARCH；重新看到球：TRACK”。

## 13\.5 程序案例：丢球搜索节点

本章代码目录结构如下：

```Plaintext
chapter_13_head_tracking_fsm/
  soccer_ball_detector.py
  soccer_detection_utils.py
  football_tracking_utils.py
  head_follow_controller.py
  ball_search_fsm_controller.py
  models/
    soccer_yolo.pt
  README.md
```

### 13\.5\.1 检测节点

本章仍然需要足球检测节点：

```Plaintext
soccer_ball_detector.py
```

它发布：

```Plaintext
/vision_detection/ball
```

后续两个控制脚本都订阅这个话题。

虽然 Chapter 11 已经写过检测节点，本章仍然复制一份，原因是：每章代码要能独立运行，不能要求学习者从其他章节目录启动文件。

### 13\.5\.2 追踪工具文件

追踪公共工具在：

```Plaintext
football_tracking_utils.py
```

它包含：

|类或函数|作用|
|---|---|
|`BallReader`|订阅检测话题，保留最近一次可靠足球|
|`BallInfo`|保存足球可见性、中心点、置信度和误差|
|`LowPassFilter2D`|平滑 `error_norm_x/error_norm_y`|
|`HeadController`|连接 SDK，发送 `RotateHead`|
|`BodyController`|可选原地转身搜索和停止|
|`clamp`|限制数值范围，避免角度越界|

这些工具把“检测解析”和“运动控制”分开，使主控制脚本更容易阅读。

### 13\.5\.3 头部跟随控制器

头部跟随脚本是：

```Plaintext
head_follow_controller.py
```

它只实现 `TRACK` 行为：

```Plaintext
读取足球检测
  ↓
判断足球可见
  ↓
读取 error_norm_x / error_norm_y
  ↓
低通滤波
  ↓
计算 pitch/yaw
  ↓
调用 RotateHead
```

这个脚本适合作为第一步实践。只有确认头部跟随方向正确、动作平稳后，再进入完整 FSM 搜索。

### 13\.5\.4 足球搜索 FSM 控制器

完整状态机脚本是：

```Plaintext
ball_search_fsm_controller.py
```

它实现：

```Plaintext
TRACK
HEAD_SEARCH
BODY_SEARCH
```

其中 `BODY_SEARCH` 默认关闭。这样做是为了让本章从低风险头部动作开始，再逐步扩展到身体动作。

## 13\.6 运行方式：跟随、找回与扫描

本章实践分为两个主要案例。

### 13\.6\.1 实践案例一：头部跟随足球

进入本章代码目录：

```Bash
cd /home/booster/Workspace/chapter_13_head_tracking_fsm
source /opt/ros/humble/setup.bash
```

终端 1 启动足球检测：

```Bash
python3 soccer_ball_detector.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDFkMWI3NDViOWU1NzYyNGMzMDc2ZDY3OWExODc2ZjNfNWI4MjY3ZDYwYTc5NjIxMTg3YmZkNDQ0Yzg1ZDY4YTJfSUQ6NzY2MzMxNjAzMDM3OTQyODgwOV8xNzg1ODM5ODExOjE3ODU5MjYyMTFfVjM)

终端 2 启动头部跟随：

```Bash
python3 head_follow_controller.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OTQ4MWVlZjhlYjJhNGZjNzRjNWViMzRhZTQxYjhjOWVfYWJkYmQyMTgyMzk2ZGZhMmE0MTE4OTkzZTFlZTM4ZTJfSUQ6NzY2MzMxNjA5Mjc3NzcyOTAwM18xNzg1ODM5ODExOjE3ODU5MjYyMTFfVjM)

运行时缓慢移动足球，观察 K1 头部是否跟随足球方向调整。

正常输出类似：

```Plaintext
ball=(358,220) conf=0.82 norm=(0.119,-0.083) smooth=(0.042,-0.029) -> pitch=0.596 yaw=-0.008
```

字段含义：

|字段|含义|
|---|---|
|`norm`|原始归一化偏差|
|`smooth`|低通滤波后的偏差|
|`pitch/yaw`|发送给头部的目标角度|

如果足球向画面右侧移动，yaw 应向右修正；如果足球回到画面中心附近，头部命令变化应逐渐变小。

### 13\.6\.2 实践案例二：丢球后头部搜索

终端 1 仍然运行足球检测：

```Bash
python3 soccer_ball_detector.py
```

终端 2 启动 FSM 控制器：

```Bash
python3 ball_search_fsm_controller.py
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDEwODdlODlhNWFkNmY3YjJkZjZhZWJlMzI4NWQ0Y2ZfMmUwNzdkMWM2OTQzYzVkN2ZiOGU2ZGYxOWY0Mzg4OTVfSUQ6NzY2MzMxNjUyMjc2OTg2MTkxOF8xNzg1ODM5ODExOjE3ODU5MjYyMTFfVjM)

运行过程：

1. 将足球放入画面，机器人进入 `TRACK`；

2. 将足球移出画面，机器人进入 `HEAD_SEARCH`；

3. 头部开始左右上下连续扫描；

4. 将足球重新放入画面，机器人回到 `TRACK`。

HEAD\_SEARCH 输出示例：

```Plaintext
mode=HEAD_SEARCH elapsed=1.5s pitch=0.620 yaw=0.310
```

状态切换输出示例：

```Plaintext
状态切换：TRACK -> HEAD_SEARCH
状态切换：HEAD_SEARCH -> TRACK
```

### 13\.6\.3 进阶实践：身体原地搜索

身体搜索会让机器人原地慢速转身。运行前确认机器人周围没有障碍物，学习者不要站在机器人转身范围内。

启动方式：

```Bash
python3 ball_search_fsm_controller.py --ros-args -p enable_body_search:=true
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWYxZjljNDU3M2M1Y2ZjYjNkN2ZhNzM3ZTczZjg3NGNfMTU0NDU1MGMwNWI4YjRjMDYzOGQ5ZDNiYWYxM2EyNWFfSUQ6NzY2MzMxODUxMDM5OTY3MTI3Nl8xNzg1ODM5ODExOjE3ODU5MjYyMTFfVjM)

运行过程：

1. 机器人先进入 `HEAD_SEARCH`；

2. 如果超过 `head_search_before_body_sec` 仍看不到足球，进入 `BODY_SEARCH`；

3. 身体原地慢速转身，同时头部继续扫描；

4. 重新看到足球后，身体停止，回到 `TRACK`。

BODY\_SEARCH 输出示例：

```Plaintext
mode=BODY_SEARCH elapsed=3.4s vyaw=0.250 pitch=0.620 yaw=0.310
```

如果身体运动异常或没有停止，应立即按下机器人背部 `STAND` 按钮。

## 13\.7 常见问题排查

### 13\.7\.1 检测正常但头部不动

先确认控制脚本是否连接 SDK 成功。正常应看到类似：

```Plaintext
Booster SDK 连接完成，头部控制已就绪。
```

如果提示无法导入：

```Plaintext
booster_robotics_sdk_python
```

说明当前环境不是 K1 SDK 运行环境，或 SDK 没有正确安装。

### 13\.7\.2 头部方向反了

先不要急着改增益。按顺序检查：

1. 检测框是否准确覆盖足球；

2. `error_norm_x` 是否符合预期：足球在画面右侧应为正；

3. 当前 SDK 中 yaw 正负方向是否与程序注释一致；

4. 相机画面是否被镜像或使用了错误话题。

如果确认 SDK yaw 方向与本章假设不同，再调整 `track_by_error()` 中 yaw 的符号。

### 13\.7\.3 头部抖动明显

常见原因：

- 检测框抖动；

- 置信度阈值过低；

- `yaw_gain` 或 `pitch_gain` 过大；

- `filter_alpha` 过大；

- 足球太近，画面中位置变化被放大。

可以先尝试：

```Bash
python3 head_follow_controller.py --ros-args -p yaw_gain:=0.12 -p pitch_gain:=0.10 -p filter_alpha:=0.20
```

如果抖动来自检测框本身，应回到 Chapter 11 检查检测模型和图像输入。

### 13\.7\.4 丢球后频繁在 TRACK 和 HEAD\_SEARCH 之间切换

这通常表示检测结果不稳定。可以检查：

- `min_conf` 是否过高或过低；

- `ball_timeout_sec` 是否太短；

- 足球是否在画面边缘；

- 光照是否导致模型短暂漏检。

适当增大：

```Plaintext
ball_timeout_sec
```

可以减少一两帧漏检带来的状态抖动，但设置过大也会让机器人更晚进入搜索。

### 13\.7\.5 身体搜索后没有停止

如果重新看到足球后身体仍在转，立即按下机器人背部 `STAND` 按钮。

随后检查：

- 终端是否仍在运行；

- 是否进入了 `TRACK`；

- `body.stop(force=True)` 是否被调用；

- SDK 是否正常接收 `Move(0, 0, 0)`。

身体搜索只应在确认安全的场地中开启。

## 13\.8 本章小结

本章完成了从“检测足球”到“根据检测结果组织行为”的过渡。学习者应掌握：

- 什么是 FSM（有限状态机）；

- 状态、动作、切换条件之间的关系；

- 为什么机器人行为需要状态记忆；

- `TRACK`、`HEAD_SEARCH`、`BODY_SEARCH` 的含义；

- 足球像素偏差如何转换成头部 pitch/yaw 命令；

- 低通滤波如何减少头部抖动；

- 丢球后为什么先头部搜索，再可选身体搜索；

- 如何在 K1 真机上运行头部跟随和丢球搜索。

完成本章后，机器人已经不只是“看见足球”，而是能够根据足球是否可见，在跟随和搜索之间自动切换。下一章将在 Chapter 12 的空间位置基础上，把行为从“转头看球”推进到“身体稳定追球”。

