---
title: BoosterOS SDK
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# BoosterOS SDK

## 一、概述

BoosterOS SDK 是加速进化提供的 Python SDK，用于连接机器人、读取传感器数据、下发运动控制指令。一套代码可同时操作 K1/T1 真机和 Booster Studio 虚拟仿真环境。

### 安装

```bash
pip install boosteros
```

### 支持的平台

| 平台 | 真机支持 | 仿真支持 |
|------|----------|----------|
| Ubuntu 20.04+ | K1 / T1 | Booster Studio |
| Windows 10+ | T1 | Booster Studio |
| macOS 12+ | - | Booster Studio |

## 二、核心类：BoosterRobot

`BoosterRobot` 是所有操作的入口类，封装了与机器人的连接、控制、数据读取等功能。

### 2.1 构造与连接

```python
from boosteros import BoosterRobot

# 连接真机（K1）
robot = BoosterRobot(robot_type="K1", connection="wifi", ip="192.168.1.100")

# 连接真机（T1）
robot = BoosterRobot(robot_type="T1", connection="usb")

# 连接虚拟��真
robot = BoosterRobot(robot_type="K1", connection="simulator")
```

### 2.2 运动控制

```python
# 基本运动
robot.walk_forward(distance=0.5, speed=0.3)     # 前进 0.5 米
robot.turn_left(angle=90)                        # 左转 90 度
robot.stand_up()                                  # 起立
robot.sit_down()                                  # 坐下

# 关节控制
robot.set_joint_angle("left_shoulder", 45)       # 设置关节角度
robot.set_joint_angles({"left_shoulder": 45, "right_shoulder": -45})

# 动作序列
robot.play_action("wave")                        # 挥手
robot.play_action("kick")                        # 踢球
robot.play_action("dance")                       # 舞蹈

# 速度控制
robot.set_walk_velocity(vx=0.3, vy=0.0, vtheta=0.0)  # 持续行走
robot.stop()                                      # 停止
```

### 2.3 传感器读取

```python
# IMU 数据
imu = robot.get_imu()
print(f"加速度: {imu.accel}, 角速度: {imu.gyro}")

# 关节状态
joints = robot.get_joint_states()
for name, state in joints.items():
    print(f"{name}: 角度={state.angle}, 力矩={state.torque}")

# 电池状态
battery = robot.get_battery()
print(f"电量: {battery.level}%, 电压: {battery.voltage}V")

# 摄像头图像
image = robot.get_camera_image(camera="head")
```

### 2.4 模式切换

```python
# 切换控制模式
robot.set_mode("position")    # 位置控制模式
robot.set_mode("velocity")    # 速度控制模式
robot.set_mode("torque")      # 力矩控制模式（高级）

# 安全模式
robot.emergency_stop()        # 急停
robot.set_mode("idle")        # 空闲模式
```

### 2.5 回调与事件

```python
# 传感器数据回调
def on_imu(data):
    print(f"IMU 更新: {data.accel}")

robot.subscribe("imu", on_imu, interval_ms=50)

# 碰撞检测
def on_collision(data):
    print(f"碰撞检测: {data.contact_point}")
    robot.stop()

robot.subscribe("collision", on_collision)

# 停止订阅
robot.unsubscribe("imu")
```

## 三、完整示例

### 示例 1：让机器人走路

```python
from boosteros import BoosterRobot
import time

robot = BoosterRobot(robot_type="K1", connection="simulator")

robot.stand_up()
time.sleep(2)

robot.walk_forward(distance=1.0, speed=0.3)
time.sleep(5)

robot.turn_left(angle=180)
time.sleep(3)

robot.walk_forward(distance=1.0, speed=0.3)
time.sleep(5)

robot.sit_down()
robot.close()
```

### 示例 2：读取传感器数据

```python
from boosteros import BoosterRobot

robot = BoosterRobot(robot_type="K1", connection="wifi", ip="192.168.1.100")

# 读取所有关节状态
joints = robot.get_joint_states()
for name, state in joints.items():
    print(f"{name}: {state.angle:.2f}°")

# 读取电池
battery = robot.get_battery()
print(f"电量: {battery.level}%")

robot.close()
```

### 示例 3：与 Booster Studio 配合使用

```python
from boosteros import BoosterRobot

# 在 Booster Studio 中打开仿真场景后，使用此代码连接
robot = BoosterRobot(robot_type="K1", connection="simulator")

# 后续代码与真机完全一致
robot.stand_up()
robot.play_action("wave")
robot.sit_down()

robot.close()
```

## 四、API 参考

### BoosterRobot 构造参数

| 参数 | 类型 | 说明 |
|------|------|------|
| robot_type | str | 机器人类型："K1" 或 "T1" |
| connection | str | 连接方式："wifi" / "usb" / "simulator" |
| ip | str | WiFi 连接时的 IP 地址 |
| port | int | 端口号（默认 9555） |

### 常用方法速查

| 方法 | 说明 |
|------|------|
| stand_up() | 起立 |
| sit_down() | 坐下 |
| walk_forward(distance, speed) | 前进 |
| walk_backward(distance, speed) | 后退 |
| turn_left(angle) | 左转 |
| turn_right(angle) | 右转 |
| set_joint_angle(joint, angle) | 设置关节角度 |
| get_joint_states() | 获取所有关节状态 |
| get_imu() | 获取 IMU 数据 |
| get_battery() | 获取电池状态 |
| get_camera_image(camera) | 获取摄像头图像 |
| play_action(name) | 播放预设动作 |
| stop() | 停止运动 |
| emergency_stop() | 紧急停止 |
| set_mode(mode) | 切换控制模式 |
| subscribe(topic, callback) | 订阅数据流 |
| close() | 断开连接 |

## 五、注意事项

1. 操作前确保机器人电量充足（建议 > 20%）
2. 真机操作时保持安全距离，预留急停操作空间
3. 仿真和真机代码通用，开发时优先在仿真环境测试
4. 长时间不操作时调用 `sit_down()` 降低功耗
