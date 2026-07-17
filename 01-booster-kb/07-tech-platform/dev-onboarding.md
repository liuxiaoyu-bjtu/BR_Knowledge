---
title: 开发者入门指南
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# 开发者入门指南

## 一、欢迎

欢迎加入加速进化（Booster Robotics）开发者社区！本指南将帮助你快速上手加速进化的技术平台，从安装环境到完成第一个机器人项目。

## 二、前置知识

### 必需基础

- Python 编程基础（函数、类、基本数据结构）
- Linux 命令行基本操作

### 加分项

- NumPy 基础
- 机器人学基本概念（关节、自由度、坐标系）
- 强化学习基本概念

## 三、环境搭建

### 3.1 安装 Python

```bash
# Ubuntu
sudo apt update
sudo apt install python3 python3-pip

# macOS
brew install python3

# Windows
# 从 python.org 下载安装包
```

### 3.2 安装 BoosterOS SDK

```bash
pip install boosteros
```

### 3.3 安装 Booster Studio（可选，推荐）

从加速进化官网下载对应平台的安装包：
- Windows: `BoosterStudio-Setup.exe`
- Ubuntu: `BoosterStudio.deb`
- macOS: `BoosterStudio.dmg`

### 3.4 验证安装

```python
# test_installation.py
from boosteros import BoosterRobot

# 连接虚拟仿真
robot = BoosterRobot(robot_type="K1", connection="simulator")
print(f"SDK 版本: {robot.get_version()}")
print("安装成功！")
robot.close()
```

## 四、学习路径

### 阶段一：基础入门（1-2 天）

**目标**：能用代码控制机器人做基本动作

1. 阅读 [BoosterOS SDK 文档](booster-sdk.md)
2. 在 Booster Studio 仿真中运行示例代码
3. 完成以下练习：

```python
# 练习 1：让机器人走正方形
robot = BoosterRobot(robot_type="K1", connection="simulator")
robot.stand_up()
for _ in range(4):
    robot.walk_forward(distance=1.0)
    robot.turn_left(angle=90)
robot.sit_down()

# 练习 2：读取传感器数据
imu = robot.get_imu()
print(f"加速度: {imu.accel}")
battery = robot.get_battery()
print(f"电量: {battery.level}%")
```

### 阶段二：传感器与数据（1-2 天）

**目标**：理解机器人的感知能力

1. 学习 IMU、摄像头、关节传感器的工作原理
2. 练习传感器数据的读取和可视化
3. 实现基于传感器反馈的简单控制

```python
# 练习：基于 IMU 的平衡检测
robot.stand_up()
while True:
    imu = robot.get_imu()
    if abs(imu.accel.y) > 2.0:  # 侧向加速度过大
        print("机器人可能失去平衡！")
        robot.stop()
        break
```

### 阶段三：项目实战（3-5 天）

**目标**：完成一个有实际意义的机器人项目

推荐项目（按难度排序）：

| 项目 | 难度 | 知识点 |
|------|------|--------|
| 机器人舞蹈 | 入门 | 动作序列、时间控制 |
| 自动避障 | 中等 | 传感器反馈、状态机 |
| 视觉跟踪 | 中等 | 摄像头、图像处理 |
| 语音控制 | 中等 | 豆包大模型、语音识别 |
| 足球射门 | 困难 | 感知+决策+控制全流程 |

### 阶段四：进阶学习（持续）

**目标**：掌握高级开发能力

1. **ROS2 开发**：[ROS2 SDK 文档](ros2-sdk.md)
2. **强化学习**：[Booster GYM 文档](booster-gym.md)
3. **Sim2Real**：[Booster Train](booster-train.md) + [Booster Deploy](booster-deploy.md)
4. **RoboCup**：[RoboCup Demo 文档](robocup-demo.md)

## 五、开发工具推荐

| 工具 | 用途 | 推荐度 |
|------|------|--------|
| VS Code | 代码编辑 | 强烈推荐 |
| Booster Studio | 仿真+项目管理 | 强烈推荐 |
| Jupyter Notebook | 实验和探索 | 推荐 |
| Git | 版本控制 | 强烈推荐 |
| TensorBoard | 训练监控 | 推荐 |

## 六、常见问题

### Q：仿真和真机代码需要分开写吗？

不需要。BoosterOS SDK 的接口在仿真和真机下完全一致，只需切换 `connection` 参数即可。

### Q：没有真机可以学习吗？

完全可以。Booster Studio 提供完整的虚拟仿真环境，涵盖真机的全部功能。建议先在仿真中学习，再过渡到真机。

### Q：从哪里获取帮助？

- 官方文档：本文档库
- GitHub Issues：各开源仓库的 Issues 页面
- 开发者社区：[社区链接]
- 技术支持邮箱：[邮箱地址]

## 七、下一步

完成本指南后，建议按以下顺序深入：

1. 完整阅读 [BoosterOS SDK 文档](booster-sdk.md)
2. 尝试 [Booster Studio](booster-studio.md) 的全部功能
3. 运行 [RoboCup Demo](robocup-demo.md) 了解完整项目结构
4. 如果想做强化学习，从 [Booster GYM](booster-gym.md) 开始

祝开发愉快！
