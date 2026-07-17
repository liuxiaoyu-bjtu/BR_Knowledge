---
title: Booster GYM
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# Booster GYM

## 一、概述

Booster GYM 是加速进化开源的强化学习训练框架，基于 Gymnasium 标准接口，专注于人形机器人的运动控制训练，尤其是足球运动场景。

- **开源地址**：https://github.com/BoosterRobotics/booster_gym
- **许可协议**：MIT License
- **依赖**：Python 3.8+, Gymnasium, PyTorch, Isaac Gym（可选）

## 二、核心特性

1. **Gymnasium 兼容**：标准 `reset() / step() / render()` 接口
2. **并行训练**：支持 Isaac Gym 多环境并行训练
3. **足球专项**：内置足球运动控制环境和奖励函数
4. **Sim2Real 就绪**：训练策略可直接导出部署
5. **可扩展**：支持自定义环境和奖励函数

## 三、安装

```bash
# 基础安装
pip install booster-gym

# 从源码安装（推荐）
git clone https://github.com/BoosterRobotics/booster_gym.git
cd booster_gym
pip install -e .

# 如需 Isaac Gym 并行训练
# 先安装 Isaac Gym Preview，然后：
pip install -e ".[isaacgym]"
```

## 四、快速开始

### 4.1 基础用法

```python
import gymnasium as gym
import booster_gym

env = gym.make("Booster-Walk-v0")
obs, info = env.reset()

for _ in range(1000):
    action = env.action_space.sample()  # 随机动作（替换为你的策略）
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

### 4.2 可用环境

| 环境 ID | 说明 | 难度 |
|---------|------|------|
| `Booster-Walk-v0` | 双足行走 | 入门 |
| `Booster-Run-v0` | 双足跑步 | 中等 |
| `Booster-Kick-v0` | 定点踢球 | 中等 |
| `Booster-Dribble-v0` | 带球移动 | 困难 |
| `Booster-Soccer-1v1-v0` | 1v1 足球对抗 | 困难 |

## 五、训练示例

### 5.1 PPO 训练（单环境）

```python
import gymnasium as gym
import booster_gym
from stable_baselines3 import PPO

env = gym.make("Booster-Walk-v0")
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=1_000_000)
model.save("booster_walk_ppo")

# 测试
obs, _ = env.reset()
for _ in range(1000):
    action, _ = model.predict(obs)
    obs, reward, terminated, truncated, _ = env.step(action)
    if terminated or truncated:
        obs, _ = env.reset()
```

### 5.2 Isaac Gym 并行训练

```python
from booster_gym.tasks import SoccerTask
from booster_gym.runners import OnPolicyRunner

task = SoccerTask(
    num_envs=4096,
    env_spacing=3.0,
    headless=True
)

runner = OnPolicyRunner(
    task,
    train_device="cuda:0",
    num_steps_per_env=24,
    max_iterations=1500
)

runner.learn()
runner.save("soccer_policy.pt")
```

## 六、奖励函数设计

Booster GYM 提供了模块化的奖励函数组件：

```python
from booster_gym.rewards import (
    VelocityReward,      # 速度奖励
    EnergyReward,        # 能量惩罚
    BalanceReward,       # 平衡奖励
    BallDistanceReward,  # 球距奖励
    GoalReward           # 进球奖励
)

reward_config = {
    "velocity": {"weight": 1.0, "target_speed": 0.5},
    "energy": {"weight": -0.01},
    "balance": {"weight": 0.5},
    "ball_distance": {"weight": 2.0},
}
```

## 七、模型导出与部署

```python
# 导出 ONNX
model.export_onnx("policy.onnx")

# 导出 TorchScript
model.export_torchscript("policy.pt")

# 部署到机器人（配合 Booster Deploy）
from booster_deploy import DeployManager
deploy = DeployManager(robot_type="K1")
deploy.load_policy("policy.pt")
deploy.run()
```

## 八、环境配置

### 自定义环境参数

```python
env = gym.make("Booster-Walk-v0", 
    render_mode="human",        # 渲染模式
    max_episode_steps=500,      # 最大步数
    control_freq=50,            # 控制频率 Hz
    domain_randomization=True,  # 域随机化
)
```

## 九、性能基准

| 环境 | 算法 | 训练步数 | 成功率 |
|------|------|----------|--------|
| Booster-Walk-v0 | PPO | 1M | 95% |
| Booster-Run-v0 | PPO | 5M | 85% |
| Booster-Kick-v0 | PPO | 3M | 90% |
| Booster-Dribble-v0 | PPO | 10M | 75% |
| Booster-Soccer-1v1-v0 | PPO | 20M | 60% |

## 十、贡献指南

欢迎贡献新环境、改进奖励函数或提交 Bug 修复。请参考仓库中的 CONTRIBUTING.md。
