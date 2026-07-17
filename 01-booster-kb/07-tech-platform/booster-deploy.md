---
title: Booster Deploy
module: 07-tech-platform
status: completed
created: 2026-07-16
---

# Booster Deploy

## 一、概述

Booster Deploy 是加速进化的 Sim2Real 部署工具链，用于将仿真中训练好的强化学习策略无缝部署到 K1/T1 真机上，解决仿真与真实世界之间的"现实差距"（Reality Gap）问题。

### 核心挑战

仿真环境与真实世界存在差距：
- 物理参数差异（摩擦、阻尼、质量分布）
- 传感器噪声和延迟
- 执行器动力学特性
- 环境不确定性

Booster Deploy 通过域随机化、系统辨识和在线适配来解决这些问题。

## 二、部署流程

```
仿真训练 → 策略导出 → 域适配 → 真机部署 → 监控验证
```

### 2.1 策略导出

从 Booster Train 或 Booster GYM 导出的策略模型：

```python
from booster_deploy import DeployManager

deploy = DeployManager(robot_type="K1")

# 加载策略
deploy.load_policy("soccer_policy.pt")
```

### 2.2 域适配

在部署前进行域适配，缩小仿真与现实的差距：

```python
# 系统辨识
deploy.identify_system(
    calibration_motions=["walk", "stand", "squat"],
    duration_seconds=30
)

# 策略微调
deploy.fine_tune(
    target_metrics=["balance", "tracking_accuracy"],
    iterations=100
)
```

### 2.3 真机部署

```python
# 连接真机
deploy.connect(ip="192.168.1.100")

# 运行策略
deploy.run(
    max_duration=300,          # 最大运行时间（秒）
    safety_check_interval=0.01, # 安全检查间隔
    emergency_stop_threshold={
        "joint_velocity": 10.0,  # 关节速度上限
        "joint_torque": 50.0,    # 关节力矩上限
        "base_velocity": 2.0,    # 机身速度上限
    }
)

# 停止
deploy.stop()
```

## 三、安全机制

Booster Deploy 内置多层安全保护：

### 3.1 软件安全

```python
# 安全配置
safety_config = {
    "joint_limits": {
        "max_velocity": 10.0,    # rad/s
        "max_torque": 50.0,      # Nm
        "position_limits": True,  # 关节限位
    },
    "body_limits": {
        "max_linear_velocity": 2.0,   # m/s
        "max_angular_velocity": 3.0,  # rad/s
        "max_tilt_angle": 30.0,       # 度
    },
    "collision": {
        "auto_stop": True,
        "force_threshold": 100.0,  # N
    },
    "communication": {
        "watchdog_timeout": 0.1,  # 秒
    }
}
```

### 3.2 硬件安全

- 急停按钮（物理按键，最高优先级）
- 电流过载保护（硬件级）
- 通信中断自动停机
- 电池低压保护

## 四、监控与调试

### 4.1 实时监控

```python
from booster_deploy import Monitor

monitor = Monitor(robot_type="K1")
monitor.connect("192.168.1.100")

# 启动监控
monitor.start(track_metrics=[
    "joint_positions",
    "joint_velocities",
    "joint_torques",
    "base_velocity",
    "base_orientation",
    "battery_level",
    "motor_temperature",
])

# 获取实时数据
data = monitor.get_latest()
print(f"电量: {data.battery_level}%")
print(f"电机温度: {data.motor_temperature}°C")

# 记录数据
monitor.start_recording("deployment_log.hdf5")
monitor.stop_recording()
```

### 4.2 回放分析

```python
from booster_deploy import LogAnalyzer

analyzer = LogAnalyzer("deployment_log.hdf5")

# 分析跟踪精度
analyzer.plot_tracking_performance()

# 对比仿真与真实数据
analyzer.compare_sim_real("simulation_log.hdf5")

# 生成报告
analyzer.generate_report("deployment_report.html")
```

## 五、性能优化

### 5.1 推理优化

```python
# 使用 TensorRT 加速推理（NVIDIA Jetson）
deploy.optimize_inference(
    backend="tensorrt",
    precision="fp16"
)

# 或使用 ONNX Runtime
deploy.optimize_inference(
    backend="onnxruntime",
    precision="fp32"
)
```

### 5.2 控制频率

```python
# 设置控制频率
deploy.set_control_frequency(
    policy_freq=50,     # 策略推理频率 Hz
    control_freq=200,   # 底层控制频率 Hz
    interpolation="linear"
)
```

## 六、故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 策略表现差 | 仿真到真实差距大 | 增加域随机化、进行系统辨识 |
| 机器人抖动 | 控制频率不足或增益过高 | 降低控制频率、调整 PD 增益 |
| 通信延迟 | 网络问题 | 使用有线连接、优化数据包大小 |
| 电机过热 | 持续高负载 | 降低动作幅度、增加休息间隔 |
| 策略崩溃 | 遇到未训练的状态 | 增大训练数据分布、增加安全边界 |

## 七、最佳实践

1. **渐进部署**：先部署简单策略（站立），逐步增加复杂度
2. **安全第一**：始终有人在急停按钮旁
3. **数据记录**：每次部署都记录完整日志
4. **仿真对比**：部署前在仿真中充分测试
5. **回滚准备**：保留上一版本的可用策略作为回退
