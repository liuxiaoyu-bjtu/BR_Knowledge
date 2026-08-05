# Chapter\_14\_稳定追球控制

# Chapter 14｜稳定追球控制

> Chapter 11 让 K1 能够在头部相机图像中检测足球，Chapter 12 把足球从图像坐标转换到机器人基座坐标，Chapter 13 进一步引入了行为状态和有限状态机。进入 Chapter 14 后，课程开始把“知道足球在哪里”转化为“让机器人稳定地走到足球前方并停下”。
> 
> 

稳定追球不是简单地让机器人一直向足球走。真实机器人有惯性，视觉检测会抖动，空间定位会有误差，足球也可能暂时离开相机视野。如果控制逻辑只写成：

```Plaintext
看到足球 -> 往足球方向走
看不到足球 -> 停止
```

机器人很容易出现冲过头、左右晃动、靠近后反复启动、检测闪烁时一顿一顿等现象。本章要解决的问题是：在足球位置不断变化、定位结果有噪声的情况下，让 K1 追球过程尽量平稳，并在合适距离停稳。

本章实践代码放在：

```Plaintext
CourseCode/chapter_14_stable_ball_chasing/
```

本章代码目录自包含，包含足球检测、深度增强定位、足球基座坐标打印、稳定追球控制等文件。它不会 import Chapter 11、Chapter 12 或 Chapter 13 的代码文件。多终端启动时只需要进入 Chapter 14 目录，避免章节之间路径交叉。

本章会真实控制 K1 身体移动。运行前必须确认机器人站立稳定，前方和左右两侧留出足够空间。如果机器人出现异常姿态、持续前进或无法停止，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张“RGB 图像 \-\> YOLO 足球检测 \-\> 深度增强空间定位 \-\> 稳定追球控制 \-\> SDK Move 速度命令”的总流程图，突出 Chapter 14 从空间感知进入身体运动控制。

## 14\.1 追球控制任务

追球控制的目标可以用一句话描述：

```Plaintext
让机器人根据足球在基座坐标系下的位置，逐步靠近足球，并在安全距离处稳定停止。
```

这句话包含三个关键点。

第一，控制输入不是图像像素，而是机器人基座坐标系下的足球位置。像素只能说明足球在画面中的位置，例如“偏左一点”“偏下一点”。身体行走需要知道足球在机器人前方多少米、左右偏移多少米，因此本章使用 Chapter 12 同类定位节点输出的 `/vision/ball_position_base`。

第二，控制动作不是一步到位，而是逐步靠近。机器人每隔很短时间读取一次最新足球坐标，然后重新计算身体速度。这样足球坐标有轻微变化时，机器人可以边走边修正。

第三，追球的结束条件不是“碰到足球”，而是在足球前方停稳。后续射门章节会继续处理对齐和踢球动作，本章只负责让机器人靠近足球并停在合适距离。

### 14\.1\.1 追球任务的输入与输出

本章追球控制节点的输入是：

```Plaintext
/vision/ball_position_base
```

它是一个 ROS2（Robot Operating System 2，机器人操作系统 2）字符串话题，消息内容是 JSON 格式。有效消息中会包含：

|字段|含义|
|---|---|
|`valid`|当前定位结果是否有效|
|`x`|足球在机器人前方的距离，单位 m|
|`y`|足球相对机器人中心线的左右偏移，单位 m|
|`z`|足球高度，单位 m|
|`distance`|足球到机器人基座原点的平面距离，单位 m|
|`angle`|足球相对机器人正前方的方位角，单位 rad|
|`method`|定位方法，例如 `depth_sphere`、`depth_median`、`geometry`|

追球控制节点的输出是 Booster SDK（Software Development Kit，软件开发工具包）的身体速度命令：

```Python
Move(vx, vy, vyaw)
```

其中：

|速度量|含义|
|---|---|
|`vx`|前进速度，正数表示向前走|
|`vy`|横向速度，正数表示向左移动|
|`vyaw`|转身角速度，正数表示向左转|

因此，本章控制任务可以画成：

```Plaintext
足球基座坐标 (x, y, distance, angle)
        ↓
距离误差和角度误差
        ↓
追球速度计算
        ↓
Move(vx, vy, vyaw)
```

> 配图建议：放置一张输入输出框图。左侧是 `/vision/ball_position_base`，中间是“稳定追球控制器”，右侧是 `Move(vx, vy, vyaw)`。

### 14\.1\.2 稳定追球要避免的问题

追球看起来只是“向球走过去”，但真机运行时至少要处理以下问题。

|问题|现象|本章处理方式|
|---|---|---|
|冲过头|机器人靠近足球后仍保持较大速度|设置减速区，越靠近越慢|
|边界抖动|刚停下又重新启动，反复小步移动|使用到位迟滞|
|角度偏大|足球在侧前方时机器人斜着冲过去|角度偏大时优先转向|
|定位闪烁|检测偶尔丢失导致一停一走|设置短暂断档宽限，持续丢失后停止|
|速度过大|命令超过机器人适合的行走范围|对 `vx`、`vy`、`vyaw` 做限幅|

这些问题都不是单靠目标检测就能解决的。目标检测告诉机器人“球在哪里”，控制器要进一步决定“该以多快的速度、朝哪个方向移动”。

## 14\.2 足球位置输入

本章追球节点不直接读取相机图像，而是读取足球在机器人基座坐标系下的位置。这样做有两个好处。

第一，身体运动控制更直接。机器人身体的前进、横移和转身都是相对于机器人自身坐标系发出的命令。足球坐标已经在基座坐标系中，控制器就可以直接用 `x`、`y` 和 `angle` 计算速度。

第二，控制器与视觉检测解耦。YOLO（You Only Look Once，单阶段目标检测模型）负责找足球，深度增强定位负责把足球变成空间坐标，追球控制负责身体运动。每一层只处理自己的问题，排查时也更清楚。

### 14\.2\.1 基座坐标系中的 x、y、z

本章使用的机器人基座坐标系约定如下：

```Plaintext
x 轴：机器人正前方
y 轴：机器人左侧
z 轴：机器人上方
```

当足球在机器人正前方 1\.5 m 处时，可以近似表示为：

```Plaintext
x = 1.5
y = 0.0
```

当足球在机器人左前方时：

```Plaintext
x > 0
y > 0
```

当足球在机器人右前方时：

```Plaintext
x > 0
y < 0
```

追球控制主要使用平面运动，因此重点关注 `x` 和 `y`。`z` 仍会保留在消息中，用于判断定位是否合理，但身体行走主要在地面平面内完成。

> 配图建议：画一张俯视图。机器人位于原点，正前方为 x 轴，左侧为 y 轴，足球点标在左前方，标出 `x`、`y`、`distance` 和 `angle`。

### 14\.2\.2 distance 和 angle 的含义

除了 `x` 和 `y`，定位节点还会发布：

```Plaintext
distance
angle
```

`distance` 是足球到机器人基座原点的平面距离。可以把机器人和足球之间看成一个直角三角形：

```Plaintext
前方距离 = x
左右偏移 = y
斜边距离 = distance
```

计算公式是：

```Plaintext
distance = sqrt(x * x + y * y)
```

其中 `sqrt` 表示开平方。如果 `x = 1.2`，`y = 0.3`，那么：

```Plaintext
distance = sqrt(1.2 * 1.2 + 0.3 * 0.3)
         = sqrt(1.44 + 0.09)
         = sqrt(1.53)
         ≈ 1.237 m
```

`angle` 是足球相对机器人正前方的夹角。它由 `x` 和 `y` 共同决定：

```Plaintext
angle = atan2(y, x)
```

这里不需要把 `atan2` 理解得很复杂。可以先把它看成一个“根据前方距离和左右偏移算方向角”的函数：

- `y = 0` 时，足球在正前方，`angle = 0`；

- `y > 0` 时，足球在左侧，`angle > 0`；

- `y < 0` 时，足球在右侧，`angle < 0`；

- `|y|` 相对 `x` 越大，角度绝对值越大。

角度单位是 `rad`，中文叫弧度。弧度和角度可以换算：

```Plaintext
角度制 = 弧度 * 180 / π
```

例如：

```Plaintext
0.245 rad ≈ 0.245 * 180 / 3.1416 ≈ 14.0°
```

所以 `angle = 0.245` 大约表示足球在机器人左前方 14 度方向。

### 14\.2\.3 有效坐标与无效坐标

追球控制只使用有效坐标。定位节点可能发布无效消息，例如：

```JSON
{"valid": false, "reason": "no_head_pose"}
```

常见无效原因包括：

|reason|含义|
|---|---|
|`no_ball_payload`|还没有收到足球检测结果|
|`not_detected`|当前图像未检测到足球|
|`low_conf`|足球检测置信度过低|
|`no_head_pose`|没有收到头部位姿，无法完成坐标转换|
|`all_estimators_failed`|深度定位和几何定位都失败|
|`out_of_safe_range`|计算出的坐标超出合理范围|

稳定追球控制节点内部使用 `BallPositionReader` 读取话题。它会做三层过滤：

1. JSON 能否解析；

2. `valid` 是否为 `true`；

3. `x` 和 `y` 是否处在控制范围内。

本章默认控制范围是：

```Plaintext
min_x = 0.0
max_x = 6.0
max_abs_y = 3.0
```

也就是说，足球必须位于机器人前方 0 到 6 m 范围内，左右偏移绝对值不超过 3 m。超出范围的坐标不会用于身体控制。

### 14\.2\.4 为什么要设置坐标超时

机器人不能永远相信旧坐标。如果足球已经离开画面，控制器还继续使用几秒前的位置，机器人就可能朝错误方向移动。

本章设置了两个时间参数：

```Plaintext
lost_timeout_sec = 0.60
ball_lost_grace_sec = 0.80
```

含义是：

- 最近 0\.60 秒内收到有效坐标，认为足球位置新鲜；

- 超过 0\.60 秒后，进入短暂断档宽限，用最近可靠坐标平滑过渡；

- 超过宽限时间仍没有新坐标，进入 `LOST`，身体速度归零。

这个设计的目的不是让机器人长时间相信旧坐标，而是避免目标检测偶尔漏一两帧时，身体控制立刻停走切换。真实相机和检测模型都会有抖动，适当的时间宽限可以让追球更连续。

如果运行场地较小，或者希望更保守，可以缩短宽限时间：

```Bash
python3 stable_chase_controller.py --ros-args -p ball_lost_grace_sec:=0.2
```

## 14\.3 距离误差与角度误差

控制器要让机器人追球，首先要知道“现在离目标差多少”。这个“差多少”就是误差。

本章追球控制主要使用两类误差：

```Plaintext
距离误差：机器人离足球还差多远
角度误差：足球相对机器人正前方偏了多少
```

距离误差决定“还要不要往前走、走多快”。角度误差决定“要不要转身、转多快”。

### 14\.3\.1 接近距离 approach

很多学习者会自然想到用 `distance` 作为停车依据。`distance` 是足球到机器人基座原点的斜线距离，看起来确实像“离足球多远”。但追球停车时，更关键的是机器人正前方距离 `x`。

看一个例子：

```Plaintext
x = 0.78 m
y = 0.50 m
distance = sqrt(0.78 * 0.78 + 0.50 * 0.50)
         ≈ 0.93 m
```

如果只看 `distance`，会觉得足球还在 0\.93 m 外；但从机器人正前方看，足球前后距离已经只有 0\.78 m。继续前进就可能过近。

因此，本章定义一个用于减速和停车的接近距离：

```Python
def approach_distance(x, y, distance):
    if x > 0.08:
        return x
    return distance
```

多数情况下，`approach = x`。当 `x` 非常小，足球可能已经接近身体侧面，才用 `distance` 作为兜底。

这个细节很重要：追球停车看的是“前方还剩多少空间”，不是单纯看斜线距离。

### 14\.3\.2 停车距离 stop\_dist

本章默认停车距离是：

```Plaintext
stop_dist = 0.78 m
```

含义是：当 `approach <= 0.78` 时，机器人认为已经追到足球前方，应停止身体移动。

这个距离不能设置得太小。真实机器人从收到速度命令到身体完全停住需要时间，足球定位也会有误差。如果 `stop_dist` 过小，机器人可能冲到球上方，影响后续对齐或踢球。

如果场地较小、机器人速度较慢，可以略微减小；如果追球时容易冲过头，应增大：

```Bash
python3 stable_chase_controller.py --ros-args -p stop_dist:=0.9
```

### 14\.3\.3 角度误差 angle

角度误差使用定位消息中的 `angle`。它表示足球相对机器人正前方偏了多少。

控制器用一个简单比例关系生成转身角速度：

```Plaintext
vyaw = angle * turn_gain
```

默认：

```Plaintext
turn_gain = 2.00
```

例如：

```Plaintext
angle = 0.20 rad
vyaw = 0.20 * 2.00 = 0.40 rad/s
```

如果足球在左前方，`angle` 为正，机器人向左转；如果足球在右前方，`angle` 为负，机器人向右转。

这就是比例控制的基本思想：误差越大，修正动作越大；误差越小，修正动作越小。

### 14\.3\.4 为什么不能只转向或只平移

机器人追球时同时有三个自由度：

```Plaintext
vx    前进
vy    横移
vyaw  转身
```

如果只用 `vx` 前进，足球在侧前方时机器人可能走偏。

如果只用 `vyaw` 转身，机器人会先原地对准足球，再前进，动作比较慢。

如果只用 `vy` 横移，机器人可能侧向移动过多，不适合稳定靠近。

本章控制器采用组合方式：

```Plaintext
前进速度 vx：由 x 决定
横向速度 vy：由 y 决定
转身速度 vyaw：由 angle 决定
```

再通过减速、限幅和转向优先因子让动作变得稳定。

> 配图建议：画一张机器人俯视图，用三个箭头标出 `vx`、`vy`、`vyaw`。`vx` 指向前方，`vy` 指向左侧，`vyaw` 用旋转箭头表示。

## 14\.4 速度控制与停稳

有了距离误差和角度误差，还不能直接把 `x`、`y`、`angle` 发给机器人。控制器还要处理速度上限、接近减速、转向优先和停稳迟滞。

本章稳定追球的速度计算位于：

```Plaintext
CourseCode/chapter_14_stable_ball_chasing/chase_control_utils.py
```

核心类是：

```Python
StableChasePolicy
```

它的输入是 `BallPosition`，输出是 `ChaseCommand`。

### 14\.4\.1 速度初值

追球时，最直接的速度初值可以写成：

```Plaintext
vx = x
vy = y
vyaw = angle * turn_gain
```

这不是最终速度，而是一个方向明确的初始控制量。

例如：

```Plaintext
x = 1.2
y = 0.2
angle = 0.165
turn_gain = 2.0
```

得到：

```Plaintext
vx = 1.2
vy = 0.2
vyaw = 0.33
```

但 `vx = 1.2 m/s` 对 K1 追球来说偏快，后面必须做限幅。`vy` 和 `vyaw` 也同样需要限制。

### 14\.4\.2 速度限幅 clamp

限幅的意思是把速度限制在安全范围内。代码中使用：

```Python
def clamp(value, low, high):
    return max(low, min(high, value))
```

这行代码可以用三句话理解：

1. 如果 `value` 小于 `low`，返回 `low`；

2. 如果 `value` 大于 `high`，返回 `high`；

3. 如果 `value` 在范围内，原样返回。

本章默认限幅为：

```Plaintext
vx_limit = 0.60 m/s
vy_limit = 0.25 m/s
vyaw_limit = 1.00 rad/s
```

最终限幅代码是：

```Python
vx = clamp(vx, -0.10, vx_limit)
vy = clamp(vy, -vy_limit, vy_limit)
vyaw = clamp(vyaw, -vyaw_limit, vyaw_limit)
```

其中 `vx` 允许很小的负值，是为了保留控制器扩展空间。但在本章默认安全范围内，足球必须在机器人前方，因此通常不会主动倒退。

### 14\.4\.3 减速区 slow\_dist

只有限幅还不够。假设足球在 2 m 外，机器人以较快速度前进；当足球进入 0\.78 m 停车距离时才突然速度变成 0，机器人可能因为惯性冲过头。

更合理的做法是：离足球远时正常走，进入减速区后逐渐降速。

本章默认：

```Plaintext
stop_dist = 0.78
chase_slow_dist = 1.35
```

含义是：

```Plaintext
approach >= 1.35 m   正常追球
0.78 m < approach < 1.35 m   按比例减速
approach <= 0.78 m   停止
```

减速系数的公式是：

```Plaintext
slow = (approach - stop_dist) / (chase_slow_dist - stop_dist)
```

并且限制在 0 到 1 之间。

看几个例子。

当 `approach = 1.35`：

```Plaintext
slow = (1.35 - 0.78) / (1.35 - 0.78)
     = 1.0
```

表示不减速。

当 `approach = 1.065`，刚好在 0\.78 和 1\.35 中间：

```Plaintext
slow = (1.065 - 0.78) / (1.35 - 0.78)
     = 0.285 / 0.57
     = 0.5
```

表示线速度降为一半。

当 `approach = 0.78`：

```Plaintext
slow = 0
```

表示身体速度归零。

> 配图建议：画一条横轴为 `approach`、纵轴为 `slow` 的折线图。`0.78 m` 处为 0，`1.35 m` 处为 1，中间直线连接。

### 14\.4\.4 转向优先因子

足球不一定在机器人正前方。如果足球在很偏的侧前方，机器人直接前进和横移可能会走出弯曲路线，甚至越走越偏。此时更合理的策略是先让身体朝向足球，再逐步靠近。

本章使用一个“转向优先因子”折减线速度：

```Python
score = distance * abs(angle)
turn_factor = 1.0 / (1.0 + exp(3.0 * (score - 1.0)))
```

这里的 `exp` 是指数函数。学习者不需要深入掌握指数函数，只需要理解这个因子的效果：

- `score` 小，说明球不远或角度不大，`turn_factor` 接近 1；

- `score` 大，说明球又远又偏，`turn_factor` 接近 0；

- `turn_factor` 只折减 `vx` 和 `vy`，不直接折减 `vyaw`。

也就是说，球偏得厉害时，机器人少向前冲，多转身对准。

例如：

```Plaintext
distance = 1.0
angle = 0.2
score = 1.0 * 0.2 = 0.2
```

此时偏角不大，线速度基本保留。

再看：

```Plaintext
distance = 2.0
angle = 0.8
score = 2.0 * 0.8 = 1.6
```

此时足球又远又偏，线速度会明显减小，机器人更倾向于先转向足球。

这种设计能减少机器人“斜着冲”的情况。

### 14\.4\.5 到位迟滞

如果只设置一个停车距离，机器人可能在边界附近反复启动和停止。

例如 `stop_dist = 0.78`：

```Plaintext
当前定位 x = 0.779 -> 停止
下一帧定位 x = 0.782 -> 又开始追
下一帧定位 x = 0.777 -> 又停止
```

这种现象不是机器人“想动”，而是定位结果在边界附近抖动。解决方法是迟滞。

本章默认：

```Plaintext
arrive_hysteresis = 0.22
```

含义是：

```Plaintext
第一次进入 stop_dist = 0.78 m 时停止
停稳后，只有 approach > 0.78 + 0.22 = 1.00 m 时才重新追球
```

这样形成了一个停止带：

```Plaintext
0.78 m 到 1.00 m 之间：保持停止
```

迟滞可以显著减少边界抖动。

> 配图建议：画一条距离轴，标出 `0.78 m` 的停止线和 `1.00 m` 的重新启动线，中间区域标注“保持停止”。

### 14\.4\.6 速度计算完整流程

综合起来，稳定追球每一轮控制循环执行如下步骤：

```Plaintext
读取足球基座坐标
  ↓
判断坐标是否有效、是否超时、是否在安全范围内
  ↓
计算 approach
  ↓
如果已经到位且仍在迟滞区域内：停止
  ↓
计算 slow 减速系数
  ↓
计算 turn_factor 转向优先因子
  ↓
计算 vx、vy、vyaw
  ↓
对速度限幅
  ↓
发送 Move(vx, vy, vyaw)
```

对应代码在 `StableChasePolicy.compute()` 中：

```Python
approach = approach_distance(ball.x, ball.y, ball.distance)

slow = approach_speed_scale(approach, self.stop_dist, self.chase_slow_dist)
turn_factor = turn_priority_factor(ball.distance, ball.angle)

vx = ball.x * turn_factor * slow
vy = ball.y * turn_factor * slow
vyaw = ball.angle * self.turn_gain
```

再经过限幅：

```Python
vx = clamp(vx, -0.10, self.vx_limit)
vy = clamp(vy, -self.vy_limit, self.vy_limit)
vyaw = clamp(vyaw, -self.vyaw_limit, self.vyaw_limit)
```

这就是本章稳定追球的核心。

## 14\.5 程序案例：稳定追球节点

本章代码目录为：

```Plaintext
CourseCode/chapter_14_stable_ball_chasing/
```

文件结构如下：

```Plaintext
chapter_14_stable_ball_chasing/
├── soccer_ball_detector.py
├── soccer_detection_utils.py
├── ball_position_depth_node.py
├── ball_localization_utils.py
├── print_ball_position.py
├── chase_control_utils.py
├── stable_chase_controller.py
├── README.md
└── models/
    └── soccer_yolo.pt
```

其中，前四个文件构成视觉到空间坐标的输入链路，后两个文件构成追球控制链路。

### 14\.5\.1 足球检测节点

`soccer_ball_detector.py` 订阅 K1 头部 RGB 图像，使用 `models/soccer_yolo.pt` 检测足球，并发布：

```Plaintext
/vision_detection/ball
```

它输出的是像素级检测结果，包括足球中心点、检测框、置信度和图像尺寸。这些结果还不能直接用于身体追球，因为身体控制需要空间坐标。

本章复制检测节点到 Chapter 14 目录，是为了保证本章代码可以独立运行。后续章节如果继续使用检测节点，也会复制到对应章节目录并改成该章节的功能命名。

### 14\.5\.2 深度增强空间定位节点

`ball_position_depth_node.py` 订阅：

```Plaintext
/vision_detection/ball
/boostercamera/head/depth
/head_pose
/boostercamera/head/rgb/camera_info
```

并发布：

```Plaintext
/vision/ball_position_base
```

它优先使用深度图估计足球空间位置。深度定位失败时，会回退到几何方法。输出中最重要的字段是：

```Plaintext
x
y
distance
angle
```

追球控制节点只要订阅这个话题，就不需要理解 YOLO 检测框如何转换成空间坐标。

### 14\.5\.3 追球控制公共工具

`chase_control_utils.py` 主要包含四部分。

第一，`BallPositionReader` 负责读取足球基座坐标：

```Python
self.subscription = node.create_subscription(
    String,
    self.ball_pos_topic,
    self._on_msg,
    10,
)
```

它会统计消息数、有效坐标数、无效消息数、超范围数量和解析失败数量。程序退出时会打印这些统计，便于排查定位链路是否稳定。

第二，`StableChasePolicy` 负责计算速度命令：

```Python
command = self.policy.compute(ball)
```

它不会直接控制机器人，只输出一个 `ChaseCommand`。这样做的好处是控制逻辑和 SDK 调用分开，代码更容易阅读和调试。

第三，`BodyMotionController` 负责连接 Booster SDK 并发送：

```Python
self.client.Move(vx, vy, vyaw)
```

SDK 调用被封装在一个类里，主节点不需要在控制循环中反复写连接细节。

第四，若程序退出，`BodyMotionController.stop()` 会发送：

```Python
Move(0.0, 0.0, 0.0)
```

确保身体运动收尾。

### 14\.5\.4 稳定追球主节点

`stable_chase_controller.py` 是本章主控制节点。

它启动后会声明参数：

```Python
self.declare_parameter("stop_dist", 0.78)
self.declare_parameter("chase_slow_dist", 1.35)
self.declare_parameter("arrive_hysteresis", 0.22)
self.declare_parameter("vx_limit", 0.60)
self.declare_parameter("vy_limit", 0.25)
self.declare_parameter("vyaw_limit", 1.00)
self.declare_parameter("turn_gain", 2.00)
```

这些参数与本章前面讲过的控制概念一一对应。

主控制循环在 `on_timer()` 中：

```Python
ball = self.reader.latest()
command = self.policy.compute(ball)
```

如果模式是 `LOST` 或 `HOLD`，节点发送停止命令：

```Python
self.motion.stop(force=command.mode != self.last_mode)
```

如果模式是 `CHASE`，节点发送追球速度：

```Python
self.motion.move(command.vx, command.vy, command.vyaw)
```

三个模式的含义如下：

|mode|含义|身体动作|
|---|---|---|
|`CHASE`|有有效足球坐标，且未到停车距离|根据速度命令追球|
|`HOLD`|已进入停车距离或迟滞停止带|保持停止|
|`LOST`|没有可用足球坐标|停止并等待新坐标|

控制器会按固定间隔打印状态，例如：

```Plaintext
x=1.220m y=0.180m distance=1.233m angle=0.146rad age=0.03s method=depth_median |
mode=CHASE vx=0.550 vy=0.081 vyaw=0.292 approach=1.220 slow=0.77 turn_factor=0.93 reason=tracking_ball
```

这行日志可以拆成两部分：

1. 左侧是足球位置；

2. 右侧是控制器输出。

排查问题时，不要只看机器人有没有动，还要看 `mode`、`approach`、`slow`、`vx`、`vy` 和 `vyaw` 是否符合预期。

## 14\.6 运行方式：追球、减速与停止

本节给出本章代码的完整运行方式。运行前确认机器人站立稳定，周围空间充足，足球放在机器人前方约 1\.5 m 到 2\.0 m 处。

如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

### 14\.6\.1 进入代码目录

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_14_stable_ball_chasing
```

本章所有命令都在这个目录下运行。

### 14\.6\.2 启动足球检测

终端 1：

```Bash
python3 soccer_ball_detector.py
```

看到足球后，检测节点会持续发布 `/vision_detection/ball`。如果终端持续提示未检测到足球，应先调整足球位置、光照和相机视角。

### 14\.6\.3 启动空间定位

终端 2：

```Bash
python3 ball_position_depth_node.py
```

该节点会订阅检测结果、深度图和头部位姿，并发布 `/vision/ball_position_base`。

如果定位节点一直输出无效原因，可以在下一步用打印节点确认。

### 14\.6\.4 打印足球基座坐标

终端 3：

```Bash
python3 print_ball_position.py
```

理想输出类似：

```Plaintext
x=1.480m y=-0.120m z=0.090m distance=1.485m angle=-0.081rad method=depth_median
```

其中：

- `x` 接近足球到机器人前方的距离；

- `y` 接近足球相对中心线的左右偏移；

- `angle` 接近足球相对正前方的方位角；

- `method` 表示当前使用的定位方法。

启动追球前，建议先观察 5 到 10 秒。如果 `x`、`y` 跳动非常大，不要急着启动身体控制，应先排查深度图、光照和检测稳定性。

### 14\.6\.5 启动稳定追球控制

终端 4：

```Bash
python3 stable_chase_controller.py --ros-args -p robot_ip:=127.0.0.1
```

如果 SDK 连接地址不是 `127.0.0.1`，应改成实际地址。

启动后观察终端日志中的 `mode`：

```Plaintext
mode=CHASE
```

表示机器人正在追球。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjlkYWZkNjFmN2Y3MWNkOTQxODk2ZDJkN2JhZGViYWFfOTQ4ZDgyNGQ1ZjYyYmI5M2Q3Yjk0OTNlMTVjODExZThfSUQ6NzY2MzMyMTQ4MjAxMzg4Nzc3MV8xNzg1ODM5ODIzOjE3ODU5MjYyMjNfVjM)

```Plaintext
mode=HOLD
```

表示机器人已经进入停车距离或迟滞停止带。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTdkMmYxZGM1ZTg5ZTM4N2Q3NmU2NjA1NDUzMWU3NjlfZDI3YjY3NGViOTBiZDI5YTU2ZWUxNzU5NGI4ODFlY2VfSUQ6NzY2MzMyMTYzMDc4MTA0OTgxMl8xNzg1ODM5ODIzOjE3ODU5MjYyMjNfVjM)

```Plaintext
mode=LOST
```

表示控制器没有可用足球坐标，身体应停止。

### 14\.6\.6 观察追球效果

正常效果应符合以下过程：

1. 足球在前方较远处，机器人开始向足球靠近；

2. 足球偏左时，机器人向左转并适当横移；

3. 足球偏右时，机器人向右转并适当横移；

4. 进入 `chase_slow_dist` 后，机器人明显减速；

5. 进入 `stop_dist` 后，机器人停止；

6. 足球没有重新远离到迟滞带外时，机器人保持停止。

如果机器人动作过快，可以降低速度上限：

```Bash
python3 stable_chase_controller.py --ros-args -p vx_limit:=0.35 -p vy_limit:=0.15 -p vyaw_limit:=0.6
```

如果机器人冲得太近，可以增大停车距离：

```Bash
python3 stable_chase_controller.py --ros-args -p stop_dist:=0.9
```

如果机器人靠近后反复小步启动，可以增大迟滞：

```Bash
python3 stable_chase_controller.py --ros-args -p arrive_hysteresis:=0.35
```

### 14\.6\.7 停止程序

停止时建议按以下顺序操作：

1. 先在稳定追球控制终端按 `Ctrl+C`；

2. 确认终端输出追球控制节点停止；

3. 再停止空间定位节点；

4. 最后停止足球检测节点。

如果机器人没有按预期停止，立即按机器人背部 `STAND` 按钮。

## 14\.7 常见问题排查

### 14\.7\.1 检测节点能看到足球，但追球节点一直 LOST

先检查 `/vision/ball_position_base` 是否有效：

```Bash
python3 print_ball_position.py
```

如果打印：

```Plaintext
invalid reason=no_head_pose
```

说明空间定位没有收到头部位姿。需要确认 K1 头部位姿话题是否发布，或者定位节点订阅的 `head_pose_topic` 参数是否正确。

如果打印：

```Plaintext
invalid reason=not_detected
```

说明定位节点没有收到有效足球检测。检查检测节点是否启动、模型路径是否正确、足球是否在画面中。

如果打印：

```Plaintext
invalid reason=out_of_safe_range
```

说明定位结果超出安全范围。可能是深度数据异常、相机外参不准确，或者足球确实离机器人太远。

### 14\.7\.2 机器人追球时左右晃动

左右晃动通常来自三个原因：

1. `y` 坐标跳动；

2. `vy_limit` 设置过大；

3. `vyaw_limit` 或 `turn_gain` 设置过大。

可以先降低横向和转身速度：

```Bash
python3 stable_chase_controller.py --ros-args -p vy_limit:=0.12 -p vyaw_limit:=0.5
```

如果仍然晃动，观察 `print_ball_position.py` 中的 `y` 和 `angle` 是否剧烈跳变。若定位本身不稳定，应先排查视觉和深度链路。

### 14\.7\.3 机器人靠近后停不稳

如果机器人进入足球附近后反复启动，优先检查 `approach` 是否在 `stop_dist` 附近抖动。

可尝试：

```Bash
python3 stable_chase_controller.py --ros-args -p arrive_hysteresis:=0.35
```

如果机器人仍冲得太近，可增大停车距离：

```Bash
python3 stable_chase_controller.py --ros-args -p stop_dist:=0.9
```

如果机器人减速太晚，可增大减速区：

```Bash
python3 stable_chase_controller.py --ros-args -p chase_slow_dist:=1.6
```

### 14\.7\.4 机器人不动，但日志显示 CHASE

先看 `enable_motion` 参数是否为 `true`。本章默认是 `true`。

再检查 SDK 是否连接成功。启动稳定追球节点时应看到类似：

```Plaintext
Booster SDK 连接完成，身体速度控制已就绪。
```

如果 SDK 导入失败，说明当前 Python 环境不是 K1 机器人运行环境，或 Booster SDK 没有安装。

还要检查 `vx`、`vy`、`vyaw` 是否接近 0。如果 `mode=CHASE` 但速度很小，可能是足球已经进入减速区，或者 `turn_factor` 因角度较大而强烈折减了线速度。

### 14\.7\.5 机器人朝足球方向不准

先确认坐标符号是否正确。

把足球放在机器人左前方，`print_ball_position.py` 中应看到：

```Plaintext
y > 0
angle > 0
```

把足球放在机器人右前方，应看到：

```Plaintext
y < 0
angle < 0
```

如果符号相反，说明坐标转换链路存在问题，需要检查相机外参、头部位姿和坐标系约定。

### 14\.7\.6 足球距离不稳定

距离不稳定可能来自深度图噪声。可以观察定位方法：

```Plaintext
method=depth_sphere
method=depth_median
method=geometry
```

如果频繁在多种方法之间切换，说明深度图或检测框质量可能不稳定。可以尝试：

1. 调整足球与机器人距离，让足球完整出现在画面中；

2. 避免强反光、过暗或背景颜色接近足球；

3. 检查深度图话题是否与 RGB 图像对齐；

4. 适当提高 `min_conf`，过滤低置信度检测。

## 14\.8 本章小结

本章完成了从足球空间坐标到 K1 身体追球控制的闭环。

学习者需要掌握以下要点：

1. 追球控制使用的是机器人基座坐标系下的 `x`、`y`、`distance` 和 `angle`，不是图像像素。

2. `distance = sqrt(x * x + y * y)` 表示斜线距离，`angle = atan2(y, x)` 表示方位角。

3. 停车和减速主要看 `approach`，通常使用前方距离 `x`，而不是单纯使用斜线距离。

4. `vx` 控制前进，`vy` 控制横移，`vyaw` 控制转身。

5. 稳定追球需要速度限幅、减速区、转向优先因子和到位迟滞。

6. 真机运行前要先确认足球基座坐标稳定，再启动身体追球控制。

7. 机器人异常移动时，应立即按下机器人背部 `STAND` 按钮。

完成本章后，K1 已经能够在看见足球后靠近并停在足球前方。后续章节会继续在此基础上组织更复杂的行为，例如行为树组合、追球后的对齐、射门动作和完整任务流程。

