# Chapter\_17\_综合项目：自主追球

# Chapter 17｜综合项目：自主追球

> Chapter 17 开始进入工程级整合。前面章节已经分别完成足球检测、空间定位、追球控制和行为树决策，本章不再重复这些原理，而是把它们组织成一个标准 ROS2（Robot Operating System 2，机器人操作系统 2）工程。
> 
> 

本章目标是让学习者理解：

```Plaintext
多个独立脚本如何变成一个 ROS2 包
多个节点如何由 launch 文件一键启动
模型、代码、包配置和启动参数如何放在工程中的固定位置
自主追球系统如何从感知到控制完整运行
```

本章配套代码放在：

```Plaintext
CourseCode/chapter_17_autonomous_chase_system/
```

其中正式 ROS2 工作区是：

```Plaintext
CourseCode/chapter_17_autonomous_chase_system/ros2_ws/
```

本章会真实控制 K1 头部和身体。运行前必须确认机器人站立稳定，周围留出安全空间。如果机器人出现异常姿态、持续移动或无法停止，应立即按下机器人背部 `STAND` 按钮。

> 配图建议：放置一张“ROS2 工作区 \-\> 包 \-\> 节点 \-\> launch 一键启动”的层级图，展示 `ros2_ws/src/k1_autonomous_chase` 的结构。

## 17\.1 项目任务

本章项目任务是构建一个自主追球系统：

```Plaintext
机器人看不到球时搜索
看到球后追球
追到设定距离后停稳
球被移走后重新搜索
```

这不是新增一个全新的算法，而是把前面章节已经完成的功能做工程整合。整合后的系统应具备以下特点：

|要求|含义|
|---|---|
|工程结构清晰|使用标准 ROS2 工作区和包结构|
|节点可独立运行|检测、定位、追球节点都有独立入口|
|支持一键启动|launch 文件同时启动所有必要节点|
|参数集中管理|相机、速度、停稳距离等参数通过 launch 传入|
|真机可运行|连接 K1 SDK（软件开发工具包）后能完成追球效果|

本章最终运行命令是：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true
```

这条命令会同时启动足球检测、足球空间定位和自主追球控制节点。

## 17\.2 ROS2 工程结构

ROS2 工程通常由工作区、包、节点、资源和启动文件组成。先看本章目录：

```Plaintext
chapter_17_autonomous_chase_system/
└── ros2_ws/
    └── src/
        └── k1_autonomous_chase/
            ├── package.xml
            ├── setup.py
            ├── setup.cfg
            ├── resource/
            │   └── k1_autonomous_chase
            ├── launch/
            │   └── autonomous_chase.launch.py
            ├── models/
            │   └── soccer_yolo.pt
            └── k1_autonomous_chase/
                ├── soccer_detection_node.py
                ├── soccer_detection_utils.py
                ├── ball_position_depth_node.py
                ├── ball_localization_utils.py
                ├── autonomous_chase_utils.py
                ├── autonomous_chase_bt_nodes.py
                ├── autonomous_chase_node.py
                └── print_ball_position.py
```

### 17\.2\.1 工作区 ros2\_ws

`ros2_ws` 是 ROS2 工作区。工作区的基本结构是：

```Plaintext
ros2_ws/
└── src/
    └── ROS2 包
```

编译时在工作区根目录执行：

```Bash
colcon build --symlink-install
```

编译完成后会生成：

```Plaintext
build/
install/
log/
```

其中 `install/` 是运行时最重要的目录。每次打开新终端运行 ROS2 包之前，都要执行：

```Bash
source install/setup.bash
```

这一步会把当前工作区中的包加入 ROS2 环境，使 `ros2 run` 和 `ros2 launch` 能找到它们。

### 17\.2\.2 包 k1\_autonomous\_chase

`k1_autonomous_chase` 是本章唯一的 ROS2 包。它是一个 `ament_python` 包，适合放 Python 节点。

关键文件包括：

|文件|作用|
|---|---|
|`package.xml`|声明包名、依赖和构建类型|
|`setup.py`|注册 Python 包、可执行节点、模型文件和 launch 文件|
|`setup.cfg`|指定脚本安装目录|
|`resource/k1_autonomous_chase`|ROS2 包索引用的资源标记|
|`launch/autonomous_chase.launch.py`|一键启动文件|
|`models/soccer_yolo.pt`|足球检测模型|
|`k1_autonomous_chase/*.py`|实际节点和工具代码|

### 17\.2\.3 package\.xml

`package.xml` 描述这个包依赖哪些 ROS2 包。

本章包中有：

```XML
<buildtool_depend>ament_python</buildtool_depend>
<depend>rclpy</depend>
<depend>std_msgs</depend>
<depend>sensor_msgs</depend>
<depend>geometry_msgs</depend>
<depend>cv_bridge</depend>
```

含义是：

- `ament_python`：这是 Python 类型 ROS2 包；

- `rclpy`：Python 版 ROS2 客户端库；

- `std_msgs`：使用 `String` 等标准消息；

- `sensor_msgs`：使用图像和相机内参消息；

- `geometry_msgs`：使用头部位姿消息；

- `cv_bridge`：图像消息与 OpenCV 图像之间转换。

如果节点 import 了某个 ROS2 消息包，却没有在 `package.xml` 中声明，工程在迁移到新环境时容易出现依赖缺失。

### 17\.2\.4 setup\.py

`setup.py` 负责把 Python 文件注册成 ROS2 可执行节点。

本章注册了四个入口：

```Python
"soccer_detection_node = k1_autonomous_chase.soccer_detection_node:main"
"ball_position_depth_node = k1_autonomous_chase.ball_position_depth_node:main"
"print_ball_position = k1_autonomous_chase.print_ball_position:main"
"autonomous_chase_node = k1_autonomous_chase.autonomous_chase_node:main"
```

编译并 source 后，可以单独运行：

```Bash
ros2 run k1_autonomous_chase soccer_detection_node
ros2 run k1_autonomous_chase ball_position_depth_node
ros2 run k1_autonomous_chase autonomous_chase_node
```

`setup.py` 还会安装模型和 launch 文件：

```Python
(os.path.join("share", package_name, "launch"), glob("launch/*.launch.py"))
(os.path.join("share", package_name, "models"), glob("models/*.pt"))
```

这样 launch 文件可以用包路径找到模型，而不依赖当前终端所在目录。

### 17\.2\.5 launch 文件

`launch/autonomous_chase.launch.py` 是一键启动文件。它负责同时启动三个功能节点：

```Plaintext
soccer_detection_node
ball_position_depth_node
autonomous_chase_node
```

它还负责设置：

- 相机图像话题；

- 深度图话题；

- 相机内参话题；

- 模型路径；

- 是否驱动机器人；

- 机器人 IP；

- 追球速度和停稳距离。

工程级运行时，不再需要手动开多个终端分别运行脚本。只要使用：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true
```

就能启动完整系统。

## 17\.3 系统架构

本章自主追球系统由三层组成：

```Plaintext
感知层：足球检测
定位层：足球基座坐标
决策与控制层：自主追球行为树
```

话题流如下：

```Plaintext
/boostercamera/head/rgb
        ↓
soccer_detection_node
        ↓ /vision_detection/ball
ball_position_depth_node
        ↓ /vision/ball_position_base
autonomous_chase_node
        ↓ Booster SDK Move / RotateHead
K1 机器人
```

> 配图建议：放置一张 ROS2 计算图。节点用圆角矩形，话题用箭头，SDK 控制接口用单独箭头连接到 K1。

### 17\.3\.1 感知层节点

感知层节点是：

```Plaintext
soccer_detection_node
```

它订阅 RGB 图像，发布：

```Plaintext
/vision_detection/ball
```

在工程中，模型路径由 launch 文件传入：

```Python
model_path = os.path.join(pkg_share, "models", "soccer_yolo.pt")
```

这样模型不再依赖相对路径。只要包正确安装，节点就能找到模型。

### 17\.3\.2 定位层节点

定位层节点是：

```Plaintext
ball_position_depth_node
```

它订阅：

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

自主追球节点只关心 `/vision/ball_position_base`，不直接处理图像和深度图。

### 17\.3\.3 决策与控制层节点

决策与控制层节点是：

```Plaintext
autonomous_chase_node
```

它读取足球基座坐标，运行行为树：

```Plaintext
有球且到位 -> 保持停止
有球但未到位 -> 追球
无球 -> 搜索
```

然后通过 Booster SDK 控制：

```Plaintext
Move(vx, vy, vyaw)
RotateHead(pitch, yaw)
```

本章不再把检测、定位和控制放在一个脚本里，而是让每个节点只负责一个清晰功能。

## 17\.4 感知与定位模块

工程整合时，感知与定位模块主要优化三点：

```Plaintext
模型路径工程化
相机话题参数化
定位结果话题稳定
```

### 17\.4\.1 模型路径工程化

独立脚本中，模型通常放在同目录的 `models/` 下。ROS2 工程中，模型会安装到包的 share 目录。

launch 文件中通过：

```Python
pkg_share = get_package_share_directory("k1_autonomous_chase")
model_path = os.path.join(pkg_share, "models", "soccer_yolo.pt")
```

获取模型路径。这样无论从哪个目录执行 launch，模型都能被找到。

### 17\.4\.2 相机预设

launch 文件提供两个相机预设：

```Plaintext
booster
realsense
```

默认：

```Plaintext
camera:=booster
```

使用统一头部相机话题：

```Plaintext
/boostercamera/head/rgb
/boostercamera/head/depth
/boostercamera/head/rgb/camera_info
```

如果需要使用 RealSense 原始话题：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py camera:=realsense enable_motion:=true
```

### 17\.4\.3 定位输出检查

工程启动前可以单独运行定位打印节点：

```Bash
ros2 run k1_autonomous_chase print_ball_position
```

理想输出类似：

```Plaintext
x=1.480m y=-0.050m z=0.090m distance=1.481m angle=-0.034rad method=depth_median
```

如果定位结果不稳定，不要继续启动身体运动。先排查检测、深度、头部位姿和相机内参。

## 17\.5 行为与控制模块

本章追球系统的行为与控制模块位于：

```Plaintext
k1_autonomous_chase/autonomous_chase_node.py
k1_autonomous_chase/autonomous_chase_bt_nodes.py
k1_autonomous_chase/autonomous_chase_utils.py
```

### 17\.5\.1 行为树节点整合

自主追球行为树为：

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

这里不重复解释行为树原理，只强调工程分工：

|文件|工程职责|
|---|---|
|`autonomous_chase_bt_nodes.py`|定义行为树叶子节点|
|`autonomous_chase_utils.py`|定义黑板、足球坐标读取、追球速度和 K1 控制接口|
|`autonomous_chase_node.py`|创建 ROS2 节点，读取参数，构建行为树，运行 tick 循环|

### 17\.5\.2 参数由 launch 统一传入

工程运行时常用参数由 launch 文件统一声明：

```Plaintext
enable_motion
robot_ip
stop_dist
vx_limit
vy_limit
vyaw_limit
```

例如降低速度：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py \
  enable_motion:=true vx_limit:=0.35 vy_limit:=0.15 vyaw_limit:=0.6
```

这种方式比在代码里硬改参数更适合工程调试。

## 17\.6 运行方式：完整追球流程

### 17\.6\.1 编译工程

进入工作区：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_17_autonomous_chase_system/ros2_ws
```

编译：

```Bash
colcon build --symlink-install
```

加载环境：

```Bash
source install/setup.bash
```

每次新开终端都要重新执行 `source install/setup.bash`。

### 17\.6\.2 一键启动

真机运行：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2M3NTc4ZWM2YWI3MjE3YjlkYjQzODZiZGZjMTVmYjhfNGEzNTQ5MTJhMThiZWQ4NDZjYTU4NDYwNTAyNWIxYWVfSUQ6NzY2NzA2MjYzNjc4MDk5NzYwMV8xNzg1ODM5ODQ3OjE3ODU5MjYyNDdfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjczMjRhMjZkZjA4ODI0ZWZhODAzMzFiNmU3N2Q1ZGFfYTEzY2FhYTAwZjlhOGMzMzdmYzBiOTY5NjZhOWNjMmFfSUQ6NzY2NzA2MjcyNjM4ODMzNzg2OV8xNzg1ODM5ODQ3OjE3ODU5MjYyNDdfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjU2ZjkwMWYzYmNlM2U4NTIzODU1NzA0OTBlMTJlYzVfMWU3M2NiNzRiNDExMzJhNjZmZDdjYzFkZDc1ZWU4NmZfSUQ6NzY2NzA2MzEzNTE5MDE0MTg5N18xNzg1ODM5ODQ3OjE3ODU5MjYyNDdfVjM)

启动后应看到三个节点输出：

```Plaintext
soccer_detection_node
ball_position_depth_node
autonomous_chase_node
```

预期效果：

1. 足球不在画面中时，机器人身体停止，头部扫描；

2. 足球进入画面后，系统发布足球检测和基座坐标；

3. 自主追球节点进入 `CHASE`；

4. 足球进入停稳距离后，节点进入 `HOLD`；

5. 足球被移走后，节点回到 `SEARCH`。

### 17\.6\.3 常用启动命令

使用 RealSense 原始话题：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py camera:=realsense enable_motion:=true
```

修改机器人 IP：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true robot_ip:=192.168.1.10
```

降低速度：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py \
  enable_motion:=true vx_limit:=0.35 vy_limit:=0.15 vyaw_limit:=0.6
```

增大停稳距离：

```Bash
ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true stop_dist:=0.9
```

### 17\.6\.4 运行中查看话题

另开终端并 source：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_17_autonomous_chase_system/ros2_ws
source install/setup.bash
```

查看话题：

```Bash
ros2 topic list
```

查看足球检测：

```Bash
ros2 topic echo /vision_detection/ball
```

查看足球基座坐标：

```Bash
ros2 topic echo /vision/ball_position_base
```

查看节点：

```Bash
ros2 node list
```

## 17\.7 常见问题排查与项目检查

### 17\.7\.1 launch 找不到包

现象：

```Plaintext
Package 'k1_autonomous_chase' not found
```

处理：

```Bash
cd /Users/zoe/Documents/CodeX/Book/CourseCode/chapter_17_autonomous_chase_system/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 17\.7\.2 模型文件找不到

检查：

```Plaintext
src/k1_autonomous_chase/models/soccer_yolo.pt
```

是否存在。若修改过 `setup.py` 或移动了模型文件，需要重新：

```Bash
colcon build --symlink-install
source install/setup.bash
```

### 17\.7\.3 机器人不动

检查 launch 参数：

```Plaintext
enable_motion:=true
```

还要检查 SDK 是否可用、`robot_ip` 是否正确、机器人是否站立稳定。

### 17\.7\.4 一直 SEARCH

说明系统没有拿到有效足球坐标。按顺序检查：

1. `soccer_detection_node` 是否检测到足球；

2. `/vision_detection/ball` 是否发布；

3. `ball_position_depth_node` 是否输出有效 `/vision/ball_position_base`；

4. 是否有头部位姿 `/head_pose`；

5. 深度图和 RGB 图像是否对齐。

### 17\.7\.5 项目检查清单

完成本章后，应能确认：

|检查项|期望|
|---|---|
|`colcon build --symlink-install`|成功完成|
|`ros2 launch k1_autonomous_chase autonomous_chase.launch.py enable_motion:=true`|一键启动三个节点|
|`/vision_detection/ball`|能发布足球检测|
|`/vision/ball_position_base`|能发布有效基座坐标|
|`autonomous_chase_node`|能在 `SEARCH`、`CHASE`、`HOLD` 之间切换|
|真机效果|能搜索、追球、停稳|

本章完成后，前面分散的足球感知、定位和追球控制已经整合为一个 ROS2 工程。后续 Chapter 18 会在同样工程组织方式上加入 `/kick_ball` 消息包和 VisualKick 视觉踢球策略。

