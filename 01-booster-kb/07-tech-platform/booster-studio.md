---
title: Booster Studio
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# Booster Studio

## 一、概述

Booster Studio 是加速进化推出的一体化 Agent 开发平台，集虚拟仿真、真机连接、数据可视化、项目开发于一体，为机器人开发者提供从原型验证到真机部署的完整工作流。

### 核心定位

- **一站式开发环境**：无需切换多个工具，一个平台完成全部开发
- **虚实结合**：同一套代码在仿真和真机上无缝运行
- **降低门槛**：无需实体机器人即可开始开发和学习

## 二、平台支持

| 操作系统 | 支持版本 | 说明 |
|----------|----------|------|
| Windows | 10 / 11 | 完整支持 |
| Ubuntu | 20.04 / 22.04 | 完整支持 |
| macOS | 12+ (Apple Silicon) | 仿真模式支持 |

## 三、核心能力

### 3.1 虚拟仿真

- 高保真物理引擎，模拟真实机器人运动学和动力学
- 支持 K1 和 T1 机器人模型
- 可自定义仿真场景（足球场、障碍物、地形等）
- 传感器仿真（摄像头、IMU、力传感器）

```python
# 在 Booster Studio 仿真环境中运行
from boosteros import BoosterRobot

robot = BoosterRobot(robot_type="K1", connection="simulator")
robot.stand_up()
robot.walk_forward(distance=2.0)
robot.close()
```

### 3.2 真机连接

- 支持 WiFi / USB 多种连接方式
- 实时数据流传输
- 一键切换仿真/真机模式

### 3.3 数据可视化

- 实时关节角度可视化
- IMU 数据曲线
- 摄像头画面预览
- 3D 机器人姿态显示

### 3.4 项目开发

- 内置代码编辑器（Python 语法高亮、自动补全）
- 项目管理（创建、导入、版本管理）
- 集成终端
- 支持外部 IDE 联动（VS Code）

## 四、教学价值

Booster Studio 在教学中具有独特的虚实结合优势：

### 4.1 降低硬件门槛

- 学生可以在没有实体机器人的情况下进行编程学习
- 一个班级可以共享少量真机 + 每人一个仿真环境
- 大大降低学校的初始投入

### 4.2 提高教学效率

- 仿真中可以加速、暂停、回放，便于教学演示
- 不怕学生操作失误损坏设备
- 支持批量部署和统一管理

### 4.3 衔接真实场景

- 仿真中验证通过的程序，可以无缝切换到真机运行
- 学生经历"仿真开发→真机验证"的完整工程流程
- 培养工程思维和调试能力

## 五、使用流程

```
创建项目 → 编写代码 → 仿真测试 → 真机验证 → 导出部署
```

### 5.1 创建项目

1. 打开 Booster Studio
2. 点击"新建项目"
3. 选择项目模板（空白/行走控制/足球/自定义）
4. 命名并创建

### 5.2 编写代码

在内置编辑器或外部 IDE 中编写 Python 代码：

```python
from boosteros import BoosterRobot

def main():
    robot = BoosterRobot(robot_type="K1", connection="simulator")
    robot.stand_up()
    
    # 你的控制逻辑
    for i in range(10):
        robot.walk_forward(distance=0.3)
        robot.turn_left(angle=36)
    
    robot.sit_down()
    robot.close()

if __name__ == "__main__":
    main()
```

### 5.3 仿真测试

- 点击"运行"按钮
- 在 3D 视图中观察机器人行为
- 使用数据面板查看传感器数据
- 调试和修改代码

### 5.4 真机验证

- 切换连接模式为"真机"
- 输入机器人 IP 地址
- 点击"连接"并运行
- 观察真机执行效果

## 六、场景模板

Booster Studio 内置了多个场景模板：

| 模板 | 说明 | 适用场景 |
|------|------|----------|
| 空旷场地 | 无干扰的自由空间 | 基础运动测试 |
| 足球场 | 标准足球场地 | 足球相关开发 |
| 障碍赛道 | 含障碍物的路径 | 导航/避障开发 |
| 阶梯地形 | 不同高度的平台 | 步态鲁棒性测试 |
| 自定义 | 用户自定义场景 | 特定需求 |

## 七、系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| 内存 | 8 GB | 16 GB |
| 显卡 | 集成显卡 | NVIDIA GTX 1060+ |
| 存储 | 5 GB | 10 GB SSD |
