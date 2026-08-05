# Chapter\_18\_综合项目：视觉踢球

# Chapter 18｜综合项目：视觉踢球

> Chapter 18 是视觉足球任务的收尾项目。本章在 Chapter 17 的 ROS2 工程结构基础上，继续加入 `/kick_ball` 自定义消息包和 VisualKick（视觉踢球）策略节点，形成完整的视觉踢球系统。
> 
> 

本章不再重复讲 YOLO（目标检测模型）、空间坐标转换、行为树和 VisualKick 的基础原理，重点放在：

```Plaintext
如何把消息包和功能包放进同一个 ROS2 工作区
如何编译自定义消息 brain/msg/Kick
如何一键启动检测、定位和视觉踢球节点
如何用参数切换 kV1/kV2、power 和 kick_dir
如何检查完整踢球闭环是否工作
```

本章配套代码放在：

```Plaintext
CourseCode/chapter_18_visual_kick_project/
```

正式 ROS2 工作区是：

```Plaintext
CourseCode/chapter_18_visual_kick_project/ros2_ws/
```

本章会真实控制 K1 头部、身体和 VisualKick。运行前必须确认机器人站立稳定，前方空间充足。如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张 Chapter 18 工程架构图。左侧是 `brain` 消息包，右侧是 `k1_visual_kick_project` 功能包，中间标出 `/kick_ball` 消息关系。

## 18\.1 项目任务

本章项目任务是构建一个视觉踢球系统：

```Plaintext
搜索足球
追到足球前方
踢前对齐
启动 VisualKick
持续发布 /kick_ball
踢完后停止
```

最终一键启动命令是：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py enable_motion:=true
```

这条命令会同时启动：

```Plaintext
足球检测节点
足球空间定位节点
视觉踢球策略节点
```

并依赖同一工作区内的：

```Plaintext
brain/msg/Kick
```

消息类型。

## 18\.2 系统架构

本章工作区包含两个 ROS2 包：

```Plaintext
ros2_ws/
└── src/
    ├── brain/
    └── k1_visual_kick_project/
```

其中：

|包|类型|作用|
|---|---|---|
|`brain`|`ament_cmake` 消息包|定义 `/kick_ball` 使用的 `Kick.msg`|
|`k1_visual_kick_project`|`ament_python` 功能包|检测、定位、视觉踢球策略和 launch|

### 18\.2\.1 brain 消息包

`brain` 包结构：

```Plaintext
brain/
├── CMakeLists.txt
├── package.xml
└── msg/
    └── Kick.msg
```

`Kick.msg` 内容为：

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

这个消息包的作用是让 Python 节点可以 import：

```Python
from brain.msg import Kick
```

如果没有编译并 source 当前工作区，视觉踢球节点就无法发布 `/kick_ball`。

### 18\.2\.2 k1\_visual\_kick\_project 功能包

功能包结构：

```Plaintext
k1_visual_kick_project/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
├── launch/
│   └── visual_kick_system.launch.py
├── models/
│   └── soccer_yolo.pt
└── k1_visual_kick_project/
    ├── soccer_detection_node.py
    ├── ball_position_depth_node.py
    ├── visual_kick_utils.py
    ├── visual_kick_bt_nodes.py
    ├── visual_kick_strategy_node.py
    └── print_ball_position.py
```

`package.xml` 中声明：

```XML
<depend>brain</depend>
```

这表示功能包依赖 `brain` 消息包。编译整个工作区时，ROS2 会先生成消息，再安装功能包。

### 18\.2\.3 一键启动结构

`visual_kick_system.launch.py` 启动三个运行节点：

```Plaintext
soccer_detection_node
ball_position_depth_node
visual_kick_strategy_node
```

系统话题流为：

```Plaintext
/boostercamera/head/rgb
        ↓
soccer_detection_node
        ↓ /vision_detection/ball
ball_position_depth_node
        ↓ /vision/ball_position_base
visual_kick_strategy_node
        ├── Booster SDK Move / RotateHead / VisualKick
        └── /kick_ball
```

> 配图建议：放置一张完整 ROS2 话题图，包含 `/vision_detection/ball`、`/vision/ball_position_base` 和 `/kick_ball`。

## 18\.3 追球、停稳与对齐

视觉踢球不是直接启动 VisualKick。工程中先复用追球系统：

```Plaintext
足球检测 -> 足球定位 -> 追球到准备距离
```

进入准备距离后，系统不再继续前冲，而是进入踢前对齐：

```Plaintext
Move(0.0, vy, vyaw)
```

这里的工程重点不是重新解释控制公式，而是理解模块边界：

|阶段|节点/文件|输出|
|---|---|---|
|足球检测|`soccer_detection_node.py`|`/vision_detection/ball`|
|空间定位|`ball_position_depth_node.py`|`/vision/ball_position_base`|
|追球对齐|`visual_kick_bt_nodes.py`|`Move(vx, vy, vyaw)`|
|踢球策略|`visual_kick_strategy_node.py`|`VisualKick` 和 `/kick_ball`|

### 18\.3\.1 准备距离

launch 文件可传入：

```Plaintext
stop_dist
```

默认：

```Plaintext
stop_dist = 0.78
```

运行时可以调整：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true stop_dist:=0.9
```

如果机器人靠球太近后才踢，增大 `stop_dist`；如果停得太远踢不到，减小 `stop_dist`，但要留出安全余量。

### 18\.3\.2 对齐阶段

对齐阶段由：

```Plaintext
AlignForKick
```

执行。它只做横向移动和转向，不继续前进。

对齐完成或对齐超时后，进入 VisualKick 阶段。这样设计可以避免机器人在球前不断前冲，降低踢空概率。

## 18\.4 VisualKick 触发

VisualKick 触发由 `visual_kick_strategy_node` 管理。系统进入 `KICK` 模式时会执行：

```Plaintext
停止身体
低头看球
VisualKick(True)
持续发布 /kick_ball
```

踢球完成后执行：

```Plaintext
VisualKick(False)
Move(0, 0, 0)
头部回正
```

### 18\.4\.1 kV1/kV2 参数

launch 文件提供：

```Plaintext
kick_version
```

默认：

```Plaintext
kick_version:=kV2
```

使用 `kV1`：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_version:=kV1
```

使用 `kV2`：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_version:=kV2
```

工程运行建议：

|阶段|建议|
|---|---|
|首次跑通|使用 `kV2`|
|坐标和对齐稳定后|再对比 `kV1`|
|小场地或安全距离不足|先低力度，不急于用射门参数|

### 18\.4\.2 power 参数

launch 文件提供：

```Plaintext
power
```

默认：

```Plaintext
power:=3.0
```

轻传球：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true power:=3.0
```

射门：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true power:=8.0
```

规则：

```Plaintext
power < 5  偏传球
power > 5  偏射门
power = 5  不建议作为调试值
```

### 18\.4\.3 kick\_dir 参数

`kick_dir` 控制期望踢球方向。

正前方：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_dir:=0.0
```

左前方：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_dir:=0.4
```

右前方：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_dir:=-0.4
```

## 18\.5 程序案例：视觉踢球系统

### 18\.5\.1 编译工程

进入工作区：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_18_visual_kick_project/ros2_ws
```

编译：

```Bash
colcon build --symlink-install
```

加载环境：

```Bash
source install/setup.bash
```

如果修改了 `Kick.msg`、`package.xml`、`setup.py` 或 launch 文件，应重新编译并 source。

### 18\.5\.2 检查消息类型

编译并 source 后，检查消息是否可见：

```Bash
ros2 interface show brain/msg/Kick
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTBlY2Y2MzBlMGYxYWM4ZjBmODVkYzZhYzk2OGU2YTVfM2E2ZjJmMjFjNDc0ZGVlNWY2MDVmM2ZjNmUyNGFjNjhfSUQ6NzY2NzA2NTE1NTQ4NTc5NzY1OF8xNzg1ODM5ODUzOjE3ODU5MjYyNTNfVjM)

应看到：

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

如果看不到该消息，说明 `brain` 包没有正确编译或当前终端没有 source 工作区。

### 18\.5\.3 一键启动视觉踢球系统

真机运行：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py enable_motion:=true
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzdmYzAyZTIwNjIwY2NjYmM0ZjIyOWJjMjI1ZmI4ZTdfMjRmNmJkNDlhYTUxZTRkNjAwYTg1OGZhN2UyYTU4NGZfSUQ6NzY2NzA2NjIzNjE1Njc0MjU4NV8xNzg1ODM5ODUzOjE3ODU5MjYyNTNfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjhmYjdiMGM3YjVlYTdmYWFlZTljN2ZmN2Y3MGE5MDBfYzRkMTcyNGFkYjdkZWUxOTE3YThkZjIyNTFhM2EwNjNfSUQ6NzY2NzA2NjM4NDc3NzcxMDU1MV8xNzg1ODM5ODUzOjE3ODU5MjYyNTNfVjM)

预期启动节点：

```Plaintext
soccer_detection_node
ball_position_depth_node
visual_kick_strategy_node
```

启动后日志应显示：

```Plaintext
Chapter 18 VisualKick 视觉踢球系统节点已启动。
流程：搜索/追球 -> 踢前对齐 -> VisualKick -> 停止。
```

如果 `brain.msg.Kick` 不可用，节点会阻止连接 SDK，避免机器人追到球前才发现无法发布 `/kick_ball`。

## 18\.6 运行方式：完整踢球闭环

### 18\.6\.1 逐步检查

先检查话题：

```Bash
ros2 topic list
```

确认至少包含：

```Plaintext
/vision_detection/ball
/vision/ball_position_base
/kick_ball
```

查看足球基座坐标：

```Bash
ros2 topic echo /vision/ball_position_base
```

查看踢球消息：

```Bash
ros2 topic echo /kick_ball
```

只有进入 `KICK` 阶段后，`/kick_ball` 才会持续发布。

### 18\.6\.2 完整效果说明

正常流程如下：

1. `SEARCH`：无球时身体停止，头部扫描；

2. `CHASE`：看到球后追球；

3. `ALIGN`：进入准备距离后踢前对齐；

4. `KICK`：启用 VisualKick 并发布 `/kick_ball`；

5. `FINISHED`：足球被踢出、丢失或超时后停止。

日志中的关键字段：

|字段|含义|
|---|---|
|`mode`|当前阶段|
|`reason`|进入当前阶段的原因|
|`x/y/distance/angle`|足球基座坐标|
|`kick_msgs`|已发布 `/kick_ball` 消息数量|

### 18\.6\.3 推荐运行顺序

第一次运行：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_version:=kV2 power:=3.0
```

确认能稳定触球后，再提高力度：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_version:=kV2 power:=8.0
```

再对比 `kV1`：

```Bash
ros2 launch k1_visual_kick_project visual_kick_system.launch.py \
  enable_motion:=true kick_version:=kV1 power:=3.0
```

## 18\.7 常见问题排查与项目检查

### 18\.7\.1 colcon build 失败

优先看是否是消息包错误。检查：

```Plaintext
src/brain/msg/Kick.msg
src/brain/CMakeLists.txt
src/brain/package.xml
```

`Kick.msg` 中使用了 `std_msgs/Header`，因此 `brain` 包必须声明 `std_msgs` 依赖。

### 18\.7\.2 visual\_kick\_strategy\_node 无法导入 brain\.msg\.Kick

处理：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_18_visual_kick_project/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 interface show brain/msg/Kick
```

只有消息可见后，再启动视觉踢球系统。

### 18\.7\.3 没有 /kick\_ball

`/kick_ball` 只在进入 `KICK` 阶段后发布。如果系统还在 `SEARCH`、`CHASE` 或 `ALIGN`，不会持续看到 `/kick_ball`。

如果已经进入 `KICK` 但没有消息，检查：

```Plaintext
brain/msg/Kick 是否可见
足球坐标是否仍有效
visual_kick_strategy_node 是否报错
```

### 18\.7\.4 VisualKick 无动作

检查日志是否成功切换：

```Plaintext
kSoccer 足球模式
```

还要检查：

- `enable_motion:=true`；

- SDK 是否可导入；

- 机器人是否站稳；

- `use_soccer_mode` 是否保持默认开启。

### 18\.7\.5 项目检查清单

完成本章后，应能确认：

|检查项|期望|
|---|---|
|`colcon build --symlink-install`|同时编译 `brain` 和 `k1_visual_kick_project`|
|`ros2 interface show brain/msg/Kick`|能显示 Kick 消息字段|
|一键启动|`ros2 launch k1_visual_kick_project visual_kick_system.launch.py enable_motion:=true`|
|感知链路|`/vision_detection/ball` 正常|
|定位链路|`/vision/ball_position_base` 有效|
|踢球链路|`KICK` 阶段发布 `/kick_ball`|
|真机效果|搜索、追球、对齐、踢球、停止|

完成 Chapter 18 后，足球视觉任务已经从单章脚本升级为 ROS2 工程化项目。学习者可以继续在这个结构上扩展更复杂的足球行为，例如连续追球、目标球门选择、路径规划和多策略切换。

