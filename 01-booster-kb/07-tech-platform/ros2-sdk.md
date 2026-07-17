---
title: ROS2 SDK
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# ROS2 SDK

## 一、概述

ROS2 SDK 是加速进化基于 ROS2（Robot Operating System 2）标准提供的机器人开发接口，兼容标准 ROS2 生态，支持节点、话题、服务等通信机制。开发者可以使用 C++ 或 Python 进行开发。

### 与标准 ROS2 的关系

- **兼容**：完全兼容 ROS2 Humble/Iron 发行版
- **扩展**：在标准 ROS2 基础上提供机器人专用消息类型和服务
- **增强**：集成加速进化的运动控制、传感器驱动等功能包

## 二、通信机制

### 2.1 节点（Node）

每个机器人控制程序都是一个 ROS2 节点：

```python
import rclpy
from rclpy.node import Node

class MyRobotController(Node):
    def __init__(self):
        super().__init__('my_robot_controller')
        # 初始化
```

### 2.2 话题（Topic）

用于发布/订阅传感器数据和指令：

```python
from booster_msgs.msg import JointCommand, ImuData

# 发布关节指令
self.joint_pub = self.create_publisher(JointCommand, '/k1/joint_command', 10)

# 订阅 IMU 数据
self.imu_sub = self.create_subscription(
    ImuData, '/k1/imu', self.imu_callback, 10
)

def imu_callback(self, msg):
    self.get_logger().info(f'加速度: x={msg.linear_acceleration.x}')
```

### 2.3 服务（Service）

用于请求-响应模式的通信：

```python
from booster_srvs.srv import SetMode

# 服务客户端（调用模式切换）
self.mode_client = self.create_client(SetMode, '/k1/set_mode')

# 发送请求
req = SetMode.Request()
req.mode = "walking"
future = self.mode_client.call_async(req)
```

### 2.4 动作（Action）

用于长时间运行的任务（如走到目标点）：

```python
from booster_msgs.action import WalkToPose

self.walk_client = ActionClient(self, WalkToPose, '/k1/walk_to_pose')
```

## 三、核心话题列表

| 话题 | 消息类型 | 方向 | 说明 |
|------|----------|------|------|
| `/k1/joint_command` | JointCommand | 发布 | 关节控制指令 |
| `/k1/joint_states` | JointState | 订阅 | 关节状态反馈 |
| `/k1/imu` | Imu | 订阅 | IMU 数据 |
| `/k1/camera/head` | Image | 订阅 | 头部摄像头 |
| `/k1/battery` | BatteryState | 订阅 | 电池状态 |
| `/k1/odom` | Odometry | 订阅 | 里程计 |
| `/k1/cmd_vel` | Twist | 发布 | 速度控制指令 |
| `/k1/collision` | CollisionEvent | 订阅 | 碰撞事件 |

## 四、自定义消息类型

### JointCommand

```
std_msgs/Header header
string[] joint_names
float64[] positions
float64[] velocities
float64[] efforts
```

### CollisionEvent

```
std_msgs/Header header
string contact_link
geometry_msgs/Point contact_point
float64 contact_force
```

## 五、快速开始

### 安装

```bash
# 安装 ROS2（Humble）
sudo apt install ros-humble-desktop

# 安装加速进化 ROS2 包
sudo apt install ros-humble-booster-msgs ros-humble-booster-bringup
```

### 运行示例

```bash
# 启动机器人驱动
ros2 launch booster_bringup k1_bringup.launch.py

# 查看话题
ros2 topic list

# 查看关节状态
ros2 topic echo /k1/joint_states
```

### Python 示例：让机器人走路

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SimpleWalker(Node):
    def __init__(self):
        super().__init__('simple_walker')
        self.cmd_pub = self.create_publisher(Twist, '/k1/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = Twist()
        if self.count < 50:  # 前进 5 秒
            msg.linear.x = 0.2
        elif self.count < 100:  # 旋转 5 秒
            msg.angular.z = 0.5
        else:  # 停止
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        self.cmd_pub.publish(msg)
        self.count += 1

def main():
    rclpy.init()
    node = SimpleWalker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## 六、与 BoosterOS SDK 的对比

| 特性 | BoosterOS SDK | ROS2 SDK |
|------|---------------|----------|
| 语言 | Python | C++ / Python |
| 上手难度 | 低 | 中 |
| 灵活性 | 中 | 高 |
| 生态兼容 | 加速进化生态 | ROS2 通用生态 |
| 适用场景 | 教学、快速原型 | 科研、系统集成 |
| 仿真支持 | Booster Studio | Gazebo / Isaac Sim |

## 七、选择建议

- **教学和快速开发**：优先使用 BoosterOS SDK
- **科研和系统集成**：使用 ROS2 SDK，可利用 ROS2 丰富的工具链
- **混合使用**：两个 SDK 可以同时使用，满足不同场景需求
