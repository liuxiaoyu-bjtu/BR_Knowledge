---
title: Booster Train
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# Booster Train

## 一、概述

Booster Train 是基于 NVIDIA Isaac Lab 的大规模并行训练框架，专为人形机器人的强化学习训练优化，支持 GPU 并行仿真和高效的策略学习。

### 技术栈

- **仿真引擎**：NVIDIA Isaac Sim / Isaac Lab
- **深度学习**：PyTorch
- **并行计算**：CUDA
- **强化学习**：PPO / SAC / 自定义算法

## 二、核心特性

1. **大规模并行**：单 GPU 支持数千个并行仿真环境
2. **人形机器人优化**：针对人形机器人的动力学和运动学优化
3. **域随机化**：内置丰富的域随机化策略
4. **课程学习**：支持从简单到困难的渐进式训练
5. **检查点恢复**：支持训练中断后从检查点恢复

## 三、安装

```bash
# 前置依赖
# 1. 安装 NVIDIA Isaac Sim
# 2. 安装 Isaac Lab

# 安装 Booster Train
git clone https://github.com/BoosterRobotics/booster_train.git
cd booster_train
pip install -e .
```

## 四、训练配置

### 4.1 基础配置

```python
from booster_train.config import TrainConfig

config = TrainConfig(
    task="soccer",
    num_envs=4096,
    env_spacing=3.0,
    max_episode_length=500,
    
    # 训练参数
    algorithm="ppo",
    learning_rate=3e-4,
    num_steps_per_env=24,
    max_iterations=2000,
    save_interval=100,
    
    # 硬件配置
    device="cuda:0",
    headless=True,
)
```

### 4.2 域随机化配置

```python
config.domain_randomization = {
    "friction": {"range": [0.5, 1.5]},
    "mass": {"range": [0.8, 1.2]},
    "joint_damping": {"range": [0.8, 1.2]},
    "ground_roughness": {"range": [0.0, 0.02]},
    "push_force": {"range": [0.0, 50.0], "interval": 100},
    "observation_noise": {"range": [0.0, 0.01]},
}
```

## 五、训练流程

### 5.1 启动训练

```bash
python scripts/train.py \
    --task soccer \
    --num_envs 4096 \
    --headless \
    --max_iterations 2000
```

### 5.2 训练监控

```python
# 使用 TensorBoard 监控
tensorboard --logdir logs/

# 查看关键指标
# - 平均奖励 (mean_reward)
# - 策略损失 (policy_loss)
# - 价值损失 (value_loss)
# - 成功率 (success_rate)
```

### 5.3 恢复训练

```bash
python scripts/train.py \
    --task soccer \
    --resume logs/soccer_ppo/checkpoint_1000.pt
```

## 六、预定义任务

| 任务 | 说明 | 训练时间（4096 envs, A100） |
|------|------|---------------------------|
| `walk` | 双足行走 | ~2 小时 |
| `run` | 双足跑步 | ~4 小时 |
| `kick` | 定点踢球 | ~3 小时 |
| `dribble` | 带球移动 | ~6 小时 |
| `soccer` | 足球综合 | ~12 小时 |
| `push_recovery` | 抗干扰恢复 | ~3 小时 |

## 七、模型导出

训练完成后导出策略模型：

```python
from booster_train.utils import export_policy

# 导出为 ONNX（跨平台推理）
export_policy(
    checkpoint="logs/soccer_ppo/model_2000.pt",
    output="soccer_policy.onnx",
    format="onnx"
)

# 导出为 TorchScript（PyTorch 推理）
export_policy(
    checkpoint="logs/soccer_ppo/model_2000.pt",
    output="soccer_policy.pt",
    format="torchscript"
)
```

## 八、训练技巧

1. **渐进式训练**：先训练行走，再训练跑步，最后训练足球
2. **奖励调优**：从简单奖励开始，逐步增加复杂度
3. **域随机化**：训练后期逐步增加随机化强度
4. **早停策略**：成功率连续 100 轮不提升时提前停止
5. **多种子训练**：使用不同随机种子训练多个模型，选择最佳

## 九、与 Booster GYM 的区别

| 特性 | Booster Train | Booster GYM |
|------|---------------|-------------|
| 仿真引擎 | Isaac Lab | Gymnasium / Isaac Gym |
| 并行规模 | 数千环境 | 数十到数百环境 |
| 物理精度 | 高（Isaac Sim） | 中 |
| 硬件要求 | NVIDIA GPU（推荐 A100） | NVIDIA GPU（推荐 RTX 30 系） |
| 适用场景 | 大规模生产训练 | 研究、教学、快速实验 |
| 上手难度 | 较高 | 较低 |
