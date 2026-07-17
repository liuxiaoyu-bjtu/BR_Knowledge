---
title: RoboCup Demo
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# RoboCup Demo

## 一、概述

RoboCup Demo 是加速进化开源的 RoboCup 人形机器人足球赛完整参考方案，涵盖感知定位、决策规划和运动执行全流程，展示了从理论到实践的完整机器人开发范式。

### 开源信息

- **开源地址**：GitHub（加速进化官方仓库）
- **许可协议**：MIT License
- **适用平台**：K1 机器人 + Booster Studio 仿真

## 二、系统架构

```
┌──────────────────────────────────────────────────────┐
│                     决策层                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ 比赛策略   │  │ 角色分配   │  │ 行为状态机     │  │
│  └────────────┘  └────────────┘  └────────────────┘  │
├──────────────────────────────────────────────────────┤
│                     感知层                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ 自定位     │  │ 球检测     │  │ 队友/对手检测  │  │
│  │ (IMU+视觉) │  │ (视觉)     │  │ (视觉)         │  │
│  └────────────┘  └────────────┘  └────────────────┘  │
├──────────────────────────────────────────────────────┤
│                     执行层                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ 行走控制   │  │ 踢球动作   │  │ 摔倒恢复       │  │
│  │ (RL策略)   │  │ (关键帧)   │  │ (RL策略)       │  │
│  └────────────┘  └────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## 三、感知模块

### 3.1 自定位

利用 IMU 和视觉信息估计机器人在场地中的位置：

```python
from robocup_demo.perception import Localization

loc = Localization(robot_type="K1")

# 更新定位
loc.update(imu_data=imu, camera_image=image)

# 获取位置
position = loc.get_position()  # (x, y, theta)
print(f"当前位置: x={position.x:.2f}, y={position.y:.2f}")
```

### 3.2 球检测

基于视觉的足球检测和跟踪：

```python
from robocup_demo.perception import BallDetector

detector = BallDetector()

# 检测球
image = robot.get_camera_image(camera="head")
ball = detector.detect(image)

if ball:
    print(f"球位置: ({ball.x:.2f}, {ball.y:.2f}), 置信度: {ball.confidence:.2f}")
```

### 3.3 场线检测

识别场地白线，用于定位校正：

```python
from robocup_demo.perception import FieldDetector

field = FieldDetector()
lines = field.detect_lines(image)
corners = field.detect_corners(image)
```

## 四、决策模块

### 4.1 行为状态机

```python
from robocup_demo.decision import StateMachine, states

class SoccerStateMachine(StateMachine):
    def __init__(self):
        super().__init__()
        self.add_state("SEARCH_BALL", self.search_ball)
        self.add_state("APPROACH_BALL", self.approach_ball)
        self.add_state("DRIBBLE", self.dribble)
        self.add_state("KICK", self.kick)
        self.add_state("RETURN", self.return_to_position)
        self.set_initial("SEARCH_BALL")

    def search_ball(self):
        # 旋转搜索球
        if ball_detected:
            return "APPROACH_BALL"
        robot.turn_left(angle=30)

    def approach_ball(self):
        # 走向球
        if close_to_ball:
            return "DRIBBLE"
        robot.walk_to(ball_position)

    def dribble(self):
        # 带球
        if near_goal:
            return "KICK"
        robot.dribble_to(goal_position)

    def kick(self):
        # 射门
        robot.kick(direction=goal_direction)
        return "RETURN"
```

### 4.2 比赛策略

```python
from robocup_demo.decision import GameStrategy

strategy = GameStrategy(
    role="striker",         # striker / defender / goalkeeper
    formation="2-1",        # 阵型
    aggressive_level=0.7    # 进攻倾向
)

action = strategy.decide(
    ball_position=ball,
    teammate_positions=teammates,
    opponent_positions=opponents,
    game_time=remaining_time,
    score=(our_score, their_score)
)
```

## 五、执行模块

### 5.1 运动控制

```python
from robocup_demo.execution import MotionController

motion = MotionController(robot_type="K1")

# 加载预训练策略
motion.load_policy("walk", "walk_policy.pt")
motion.load_policy("kick", "kick_policy.pt")
motion.load_policy("getup", "getup_policy.pt")

# 行走
motion.walk_to(target_x=1.0, target_y=0.5, target_theta=0.0)

# 踢球
motion.kick(power=0.8, direction=45)

# 摔倒恢复
if motion.is_fallen():
    motion.get_up()
```

## 六、完整示例

### 单机器人 Demo

```python
from robocup_demo import SoccerRobot

robot = SoccerRobot(robot_type="K1", connection="simulator")
robot.initialize()

# 开始比赛循环
while robot.is_running():
    robot.perceive()     # 感知
    robot.decide()       # 决策
    robot.execute()      # 执行

robot.shutdown()
```

### 多机器人对战

```bash
# 启动仿真服务器
python -m robocup_demo.server --num_robots 4

# 启动红队
python -m robocup_demo.agent --team red --role striker --server localhost
python -m robocup_demo.agent --team red --role defender --server localhost

# 启动蓝队
python -m robocup_demo.agent --team blue --role striker --server localhost
python -m robocup_demo.agent --team blue --role defender --server localhost
```

## 七、学习路径

RoboCup Demo 适合作为进阶学习项目，建议学习路径：

```
1. 理解系统架构 → 阅读架构文档
2. 运行仿真 Demo → 观察机器人行为
3. 修改感知参数 → 调整球检测阈值等
4. 修改决策逻辑 → 调整状态机行为
5. 训练运动策略 → 使用 Booster GYM 训练
6. 部署到真机 → 体验真实比赛
```

## 八、扩展方向

| 方向 | 说明 | 难度 |
|------|------|------|
| 改进感知 | 使用深度学习提升检测精度 | 中等 |
| 优化策略 | 设计更智能的比赛策略 | 中等 |
| 多机协作 | 实现队友之间的配合传球 | 困难 |
| 对抗学习 | 训练对抗性比赛策略 | 困难 |
| 迁移到真机 | Sim2Real 部署优化 | 中等 |
