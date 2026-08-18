---
title: BoosterOS SDK V1.0
module: 07-tech-platform
status: completed
created: 2026-07-16
updated: 2026-08-06
source: BoosterOS 开发者接口文档 - V1.0 (Booster Robotics 官方文档)
version: V1.0
---

# BoosterOS SDK V1.0

> **定位**: BoosterOS 是面向机器人应用开发的**主 SDK**（Python），提供连接机器人、读取传感器、下发控制指令、语音交互、视觉检测等全部接口。一套代码可同时操作 K1/T1 真机和 Booster Studio 虚拟仿真环境。
>
> **适用版本**: Python >= 3.10 | 机器人固件 >= v1.7 | 当前仅支持 Booster 真机或 Booster Studio 虚拟仿真环境

---

## 目录

- [一、快速上手](#一快速上手)
- [二、BoosterRobot — 核心类](#二boosterrobot--核心类)
  - [2.1 构造与连接](#21-构造与连接)
  - [2.2 信息与状态获取](#22-信息与状态获取)
  - [2.3 传感器与状态快照](#23-传感器与状态快照)
  - [2.4 传感器订阅](#24-传感器订阅)
  - [2.5 运动控制](#25-运动控制)
  - [2.6 高级任务](#26-高级任务)
  - [2.7 音频管理器](#27-音频管理器)
  - [2.8 示教管理器](#28-示教管理器)
  - [2.9 自动踢球管理器](#29-自动踢球管理器)
- [三、视觉与语音](#三视觉与语音)
  - [3.1 Speech — 语音能力](#31-speech--语音能力)
  - [3.2 Detection — 视觉检测](#32-detection--视觉检测)
- [四、公共数据类型](#四公共数据类型)
  - [4.1 基础类型（Time / Duration / Header）](#41-基础类型)
  - [4.2 感知与状态数据](#42-感知与状态数据)
  - [4.3 关节相关数据](#43-关节相关数据)
  - [4.4 机器人元信息](#44-机器人元信息)
  - [4.5 任务与订阅](#45-任务与订阅)
  - [4.6 轨迹数据](#46-轨迹数据)
- [五、枚举与字面量类型](#五枚举与字面量类型)
- [六、API 速查总表](#六api-速查总表)
- [七、常见问题与调试](#七常见问题与调试)

---

## 一、快速上手

### 1.1 安装

```bash
# 基础包（机器人连接、状态读取、运动控制）
python3 -m pip install boosteros

# brain 可选包（包含 Speech 语音 + Detection 视觉依赖）
python3 -m pip install "boosteros[brain]"
```

### 1.2 连通性检查

```python
from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()

info = robot.robot_info
print(f"{info.manufacturer}, {info.model}, {info.serial_number}")
# Booster Robotics, Booster K1, rivt9

mode = robot.get_mode()
print(f"mode={mode}")
# mode=prepare

joints = robot.list_joints()
print(f"joints={len(joints)}")
# joints=22
```

### 1.3 第一次读取数据

```python
robot = BoosterRobot()

# 关节状态
joint_states = robot.get_joint_states()
print(joint_states.names[:5])
# ['AAHead_Yaw', 'Head_Pitch', 'ALeft_Shoulder_Pitch', 'Left_Shoulder_Roll', 'Left_Elbow_Pitch']

# IMU
imu = robot.get_imu()
print(imu.rpy)

# 图像
img = robot.get_image(img_type="rgb")
img.save("quickstart_rgb.jpg")
```

---

## 二、BoosterRobot — 核心类

`BoosterRobot` 是所有操作的入口类。**同一台机器人应只创建并复用一个实例**——每个实例独立建立 ROS 节点、数据订阅和底层控制通道，重复创建可能导致指令冲突。

### 2.1 构造与连接

```python
BoosterRobot(
    network_interface: str = "",
    virtual_robot_name: str = "",
    *,
    timeout: float = 5.0,
    callback_workers: int = 4,
    enable_tf_listener: bool = True,
    **kwargs: Any,
) -> BoosterRobot
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `network_interface` | `str` | `""` | 保留参数，当前固定使用默认值 |
| `virtual_robot_name` | `str` | `""` | 虚拟机器人名称，仅多虚拟机器人模式下需要 |
| `timeout` | `float` | `5.0` | 初始化和服务发现超时（秒） |
| `callback_workers` | `int` | `4` | 传感器回调工作线程数（>=1），高频订阅可调大 |
| `enable_tf_listener` | `bool` | `True` | 是否启动 TF 监听，关闭后 `get_transform()` 不可用 |
| `**kwargs` | — | — | 高级选项：`domain_id`（ROS_DOMAIN_ID，多机器人隔离）、`dds_profile`（FastRTPS DDS XML 配置） |

**异常**: `ValueError`（callback_workers < 1）、`LocoClientInitError`（超时未发现运动控制服务）

### 2.2 信息与状态获取

| 方法 | 返回类型 | 功能 |
|---|---|---|
| `robot_info` (属性) | `RobotInfo` | 获取名称、型号、序列号、固件版本等元信息 |
| `get_mode()` | `RobotModeName` | 获取当前模式（`"damping"` / `"prepare"` / `"walk"` / `"custom"`） |
| `list_gaits()` | `list[RobotGaitName]` | 获取 walk 模式可用步态（如 `["default", "soccer"]`） |
| `get_gait()` | `RobotGaitName` | 获取当前步态（默认 `"default"`） |
| `list_frames()` | `list[str]` | 获取可查询的坐标系名称列表 |
| `list_joints()` | `list[JointInfo]` | 获取当前机型支持的关节列表（含限位、最大力矩/速度） |
| `list_actions()` | `list[ActionInfo]` | 获取预定义动作列表（10 个动作 ID，见 [ActionInfo](#actioninfo)） |

### 2.3 传感器与状态快照

> 快照类接口获取的是**最近一帧**缓存数据，调用时不会阻塞等待新数据。超时时间内无数据则抛 `DataNotReadyError`。

| 方法 | 返回类型 | 功能 |
|---|---|---|
| `get_image(camera_id="", img_type="rgb")` | `AnyImage` | 获取最近一帧 RGB 或深度图像 |
| `get_camera_info(camera_id="")` | `CameraInfo` | 获取相机内参（K/D/R/P 矩阵）和标定信息 |
| `get_imu(imu_id="")` | `IMUState` | 获取 IMU：线加速度、角速度、姿态四元数、RPY |
| `get_odom()` | `OdomState` | 获取里程计：位置、姿态、线速度、角速度、pose_2d |
| `get_joint_states()` | `JointStates` | 获取所有关节的位置、速度、力矩 |
| `get_battery()` | `BatteryState` | 获取电池百分比、电压、电流、温度、充放电状态 |
| `get_fall_down_state()` | `FallDownState` | 获取摔倒状态（normal / falling / fallen / getting_up） |
| `get_transform(target_frame, source_frame)` | `Transform` | 查询坐标系变换（需 `enable_tf_listener=True`） |

### 2.4 传感器订阅

> 订阅类接口提供**持续回调**机制，返回 `SensorSubscription` 句柄（支持 `with` 上下文和 `.unsubscribe()` 手动取消）。

| 方法 | 回调参数类型 | 功能 |
|---|---|---|
| `subscribe_image(callback, *, camera_id, img_type, queue_size, overflow)` | `AnyImage` | 订阅图像流 |
| `subscribe_imu(callback, *, imu_id, queue_size, overflow)` | `IMUState` | 订阅 IMU 数据流 |
| `subscribe_odom(callback, *, queue_size, overflow)` | `OdomState` | 订阅里程计数据流 |
| `subscribe_battery(callback, *, queue_size, overflow)` | `BatteryState` | 订阅电池状态更新 |
| `subscribe_fall_down_state(callback, *, queue_size, overflow)` | `FallDownState` | 订阅摔倒状态更新 |

**通用参数**: `queue_size`（回调队列大小，0=不限制）、`overflow`（队列满策略：`"block"` / `"drop_oldest"` / `"drop_newest"`）

### 2.5 运动控制

> ⚠️ **安全提示**: 真机上调用运动控制前，确认空间充足、机器人姿态正常、急停手段就绪。

| 方法 | 返回 | 功能 |
|---|---|---|
| `set_mode(mode_name)` | `None` | 切换模式（damping→prepare→walk→custom），等待切换完成 |
| `set_gait(gait)` | `None` | 设置 walk 模式步态（`"default"` / `"soccer"`） |
| `set_velocity(vx, vy, vyaw)` | `None` | 发送平面速度控制命令（持续运动，调用 `set_velocity(0,0,0)` 停止） |
| `upper_body_control(enable)` | `None` | walk 模式下启用/关闭上半身自定义控制 |
| `set_joints(joint_commands)` | `None` | 批量下发关节控制命令（position/velocity/effort + kp/kd/weight） |
| `set_head_angle(pitch, yaw)` | `None` | walk 模式下控制头部俯仰和偏航角度（°） |
| `reset_odom()` | `None` | 将里程计重置到零位 |

**`set_velocity` 参数**:

| 参数 | 类型 | 说明 |
|---|---|---|
| `vx` | `float` | 前进线速度（m/s），正=前进 |
| `vy` | `float` | 横向线速度（m/s），正=左移 |
| `vyaw` | `float` | 偏航角速度（rad/s），正=左转 |

**`set_joints` 参数**: 接受 `list[JointCommand]`，每个 `JointCommand` 包含 `name`（关节名）+ 可选 `position` / `velocity` / `effort` / `acceleration` / `kp` / `kd` / `weight`。

### 2.6 高级任务

> 高级任务接口均为**异步执行**，返回 `TaskHandle[None]`。通过 `TaskHandle.wait()` 等待完成、`TaskHandle.cancel()` 取消。

| 方法 | 返回 | 功能 |
|---|---|---|
| `get_active_tasks(filter)` | `list[TaskHandle[None]]` | 获取当前未进入终态的任务列表 |
| `do_action(action_id, *, on_done, on_status_change)` | `TaskHandle[None]` | 异步执行预定义动作（hand_shake / kick / dance 等 10 个） |
| `get_up(*, on_done, on_status_change)` | `TaskHandle[None]` | 异步触发机器人起身任务 |
| `execute_trajectory(trajectory, *, on_done, on_status_change)` | `TaskHandle[None]` | 异步回放示教轨迹（`TrajectoryData`） |
| `play_sound(audio, *, volume, on_done, on_status_change)` | `TaskHandle[None]` | 异步播放音频（`AudioData` 或文件路径） |

### 2.7 音频管理器

通过 `robot.audio_manager` 访问（`BoosterAudioManager` 实例）。

| 方法 | 返回 | 功能 |
|---|---|---|
| `get_system_volume()` | `float` | 查询系统输出音量（0.0-1.0） |
| `set_system_volume(volume)` | `None` | 设置系统输出音量 |
| `start_recording(sample_rate, channels, sample_format, *, use_naec)` | `None` | 开始内存录音会话（单次会话，不可并发） |
| `stop_recording()` | `AudioData` | 停止录音并返回合并后的音频数据 |
| `is_recording()` | `bool` | 查询是否存在进行中的录音会话 |
| `get_recording_duration()` | `float` | 获取当前已采集音频时长（秒） |
| `record_stream(sample_rate, channels, sample_format, *, use_naec, chunk_bytes, stop_event)` | `Iterator[AudioData]` | 以生成器形式流式读取麦克风音频 |
| `play_stream(*, sample_rate, channels, sample_format, volume, queue_size, overflow)` | `AudioPlaybackStreamHandle` | 打开可写入的 PCM 播放流 |

**播放流用法**:
```python
stream = robot.audio_manager.play_stream(sample_rate=16000, channels=1, sample_format="S16LE")
stream.write(audio_bytes)
stream.close()
```

### 2.8 示教管理器

通过 `robot.hand_guiding_manager` 访问（`BoosterHandGuidingManager` 实例），支持 `with` 上下文自动停止录制。

| 方法/属性 | 返回 | 功能 |
|---|---|---|
| `start_recording()` | `None` | 开始录制拖动示教轨迹（零力矩模式） |
| `stop_recording()` | `TrajectoryData \| None` | 停止录制并返回轨迹数据 |
| `is_recording` (属性) | `bool` | 查询是否正在录制 |
| `get_recording_duration()` | `float` | 获取当前录制持续时间（秒） |

**用法示例**:
```python
with robot.hand_guiding_manager as mgr:
    mgr.start_recording()
    time.sleep(5.0)  # 此期间拖拽机器人演示动作
    trajectory = mgr.stop_recording()

# 保存轨迹
trajectory.save("my_action.traj")

# 回放轨迹
robot.execute_trajectory(trajectory).wait()
```

### 2.9 自动踢球管理器

独立构造 `SoccerKickManager(robot)`。

| 方法 | 返回 | 功能 |
|---|---|---|
| `start()` | `None` | 开启自动踢球控制 |
| `update_command(direction, power)` | `None` | 设置踢球方向（rad）和力度（0-10） |
| `update_ball(x, y)` | `None` | 更新足球在机器人坐标系下的位置（m） |
| `stop()` | `None` | 关闭自动踢球控制 |

---

## 三、视觉与语音

> 从 `boosteros.brain` 导入，需安装 `boosteros[brain]`。

### 3.1 Speech — 语音能力

```python
from boosteros.brain import Speech
speech = Speech(robot)
```

| 方法 | 返回 | 功能 |
|---|---|---|
| `recognize_stream(*, on_result, **kwargs)` | `TaskHandle[None]` | 流式语音识别（ASR），通过 `on_result(text, is_final)` 回调接收结果 |
| `chat(*, config, **kwargs)` | `TaskHandle[None]` | 启动语音对话任务（ASR→LLM→TTS 闭环） |
| `list_voices()` | `list[dict[str, Any]]` | 获取可用音色列表 |

**`ChatConfig` 配置项**:

| 参数 | 类型 | 说明 |
|---|---|---|
| `system_prompt` | `str` | 系统提示词——定义 Agent 人设的核心配置 |
| `voice` | `str` | 音色 ID（从 `list_voices()` 获取） |
| `volume` | `float` | 音量（0.0-1.0） |
| `max_tokens` | `int` | 最大回复 token 数 |

**语音对话示例**:
```python
from boosteros.brain import Speech
from boosteros.brain.speech import ChatConfig

speech = Speech(robot)
config = ChatConfig(
    system_prompt="你是一个热情专业的足球解说员，用激情四射的语气解说每一场比赛。",
    voice="zh_female_1",
    volume=0.8,
)
speech.chat(config=config)
```

### 3.2 Detection — 视觉检测

```python
from boosteros.brain import Detection
detector = Detection(model="default", backend="onnx")
```

| 方法 | 返回 | 功能 |
|---|---|---|
| `list_models()` (类方法) | `list[dict[str, Any]]` | 获取可用检测模型列表 |
| `load_model(model)` | `None` | 切换当前检测模型 |
| `detect(image, confidence, iou_threshold)` | `list[DetectionResult]` | 执行目标检测 |
| `plot(image, results, as_image)` | `Image \| np.ndarray` | 在图像上绘制检测框和类别标签 |

**`detect` 参数**:

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `image` | `AnyImage \| np.ndarray` | 必填 | 输入图像 |
| `confidence` | `float` | `0.5` | 置信度阈值（0-1），低于此值的检测结果被丢弃 |
| `iou_threshold` | `float` | `0.45` | NMS IoU 阈值 |

### 3.3 可用检测模型与类别能力

`list_models()` 返回当前环境可用的检测模型（字段：`id` / `name` / `type` / `backend`）。实测（2026-08-14）环境共 3 个模型，后端均支持 `cloud` / `local`：

| 模型 ID | 名称 | 识别目标 | 类别来源 |
|---|---|---|---|
| `default` | 通用物体检测（快速） | **COCO 80 类**通用物体（人/车/动物/家具/食物/电子设备等） | 从 ONNX 模型导出，见下方完整清单 |
| `person` | 人物检测 | 人（单一类别） | 专用模型 |
| `soccer` | robocup 检测 | 足球/球门/队友对手/场线等 RoboCup 场景目标 | 专用模型，见 [robocup-demo.md](robocup-demo.md) |

#### default 模型 — COCO 80 类完整清单

`default` 模型为 COCO 数据集 80 类目标检测（YOLO 系），`DetectionResult.class_id` 即下表索引。课程视觉实验可直接据此设计（如"找杯子""避让行人""识别课桌"）。

| ID | 类别 | ID | 类别 | ID | 类别 | ID | 类别 |
|---|---|---|---|---|---|---|---|
| 0 | person | 1 | bicycle | 2 | car | 3 | motorcycle |
| 4 | airplane | 5 | bus | 6 | train | 7 | truck |
| 8 | boat | 9 | traffic light | 10 | fire hydrant | 11 | stop sign |
| 12 | parking meter | 13 | bench | 14 | bird | 15 | cat |
| 16 | dog | 17 | horse | 18 | sheep | 19 | cow |
| 20 | elephant | 21 | bear | 22 | zebra | 23 | giraffe |
| 24 | backpack | 25 | umbrella | 26 | handbag | 27 | tie |
| 28 | suitcase | 29 | frisbee | 30 | skis | 31 | snowboard |
| 32 | sports ball | 33 | kite | 34 | baseball bat | 35 | baseball glove |
| 36 | skateboard | 37 | surfboard | 38 | tennis racket | 39 | bottle |
| 40 | wine glass | 41 | cup | 42 | fork | 43 | knife |
| 44 | spoon | 45 | bowl | 46 | banana | 47 | apple |
| 48 | sandwich | 49 | orange | 50 | broccoli | 51 | carrot |
| 52 | hot dog | 53 | pizza | 54 | donut | 55 | cake |
| 56 | chair | 57 | couch | 58 | potted plant | 59 | bed |
| 60 | dining table | 61 | toilet | 62 | tv | 63 | laptop |
| 64 | mouse | 65 | remote | 66 | keyboard | 67 | cell phone |
| 68 | microwave | 69 | oven | 70 | toaster | 71 | sink |
| 72 | refrigerator | 73 | book | 74 | clock | 75 | vase |
| 76 | scissors | 77 | teddy bear | 78 | hair drier | 79 | toothbrush |

**课程应用提示**：
- 实验室常见可识别目标：人(0)、杯子(41)、瓶子(39)、手机(67)、椅子(56)、桌子(60)、球(32)、书本(73)、背包(24)、键盘(66)、鼠标(64)、显示器 tv(62)、盆栽(58) 等
- 无人机/交通类（5/6/7/9/11）与动物类（14-23）适合通识课拓展演示，实验室场景较少见
- 通过 `confidence` 阈值调节灵敏度：降低到 0.3 可在复杂场景捕获更多目标

---

## 四、公共数据类型

> 所有类型从 `boosteros.types` 导入。

### 4.1 基础类型

| 类型 | 关键属性/方法 | 说明 |
|---|---|---|
| `Time` | `nanoseconds` (int); 只读: `seconds`, `sec`, `nanosec` | 高精度时间点。方法: `now()` (类方法), `to_datetime()`, `from_datetime()` |
| `Duration` | `nanoseconds` (int); 只读: `seconds` | 时间段长度 |
| `Header` | `stamp` (Time), `frame_id` (str); 只读: `timestamp`, `sec`, `nanosec` | 数据对象时间戳和坐标系。方法: `from_sec()` (类方法) |

### 4.2 感知与状态数据

| 类型 | 关键属性 | 说明 |
|---|---|---|
| `AnyImage` (= `Image \| CompressedImage`) | `header`, `width`, `height` | 图像联合类型。方法: `to_numpy()`, `to_pil()`, `to_bytes()`, `size()`, `save(path)`, `resize(w,h)`, `show()` |
| `Image` | 继承 ImageBase + `encoding` (str) | 原始像素图像 |
| `CompressedImage` | 继承 ImageBase + `format` (str) | 压缩图像（JPEG/PNG） |
| `BoundingBox2D` | `x`, `y`, `width`, `height`; 只读: `center_x`, `center_y`, `area` | 2D 检测框。方法: `to_dict()` |
| `DetectionResult` | `class_name`, `class_id`, `confidence`, `bbox` (BoundingBox2D), `mask`, `keypoints`, `distance_m` | 检测结果。方法: `to_dict()` |
| `CameraInfo` | `header`, `width`, `height`, `k` (3x3), `d`, `r`, `p`, `distortion_model`, `binning_x`, `binning_y`, `roi` | 相机内参和标定。方法: `to_dict()` |
| `RegionOfInterest` | `x_offset`, `y_offset`, `height`, `width`, `do_rectify` | ROI 区域。方法: `to_dict()` |
| `IMUState` | `header`; 只读: `linear_acceleration` (3,), `angular_velocity` (3,), `orientation` (4,), `rpy` (3,) | IMU 状态。方法: `to_numpy()` |
| `OdomState` | `header`; 只读: `position` (3,), `orientation` (4,), `linear_velocity`, `angular_velocity`, `rpy`, `pose_2d` (3,) | 里程计位姿和速度。方法: `to_numpy()` |
| `Transform` | `header`; 只读: `translation` (3,), `rotation` (4,), `source_frame`, `target_frame`, `rpy` (3,) | 坐标系变换。方法: `inverse()`, `to_matrix()`, `to_numpy()` |
| `BatteryState` | `header`, `temperature`, `charge`, `capacity`, `serial_number`; 只读: `percentage`, `voltage`, `current`, `status_code`, `is_charging`, `is_low`, `is_critical` | 电池状态。方法: `to_numpy()` |
| `FallDownState` | `header`, `state` (str), `recoverable` (bool); 只读: `is_normal`, `is_falling`, `has_fallen`, `is_getting_up` | 摔倒状态（从 `boosteros.robots.booster` 导入） |
| `AudioData` | `header`, `channels`, `sample_rate`, `coding_format`, `sample_format`, `bitrate`; 只读: `data`, `format`, `bit_depth`, `duration` | 音频数据。方法: `save(path)`, `with_data(bytes)`, `concat([...])` (类方法), `to_numpy()` |

### 4.3 关节相关数据

| 类型 | 关键属性 | 说明 |
|---|---|---|
| `JointState` | `name`, `position`, `velocity`, `effort`, `extra` | 单个关节状态 |
| `JointStates` | `header`; 只读: `joints`, `names` | 一帧关节状态快照。方法: `get_joint(name)`, `to_numpy()`，支持 `[]` 和迭代 |
| `JointCommand` | `name`, `position`, `velocity`, `effort`, `acceleration`, `kp`, `kd`, `weight` | 单个关节控制命令（所有控制量字段可选） |

### 4.4 机器人元信息

| 类型 | 关键属性 | 说明 |
|---|---|---|
| `RobotInfo` | `manufacturer`, `model`, `name`, `serial_number`, `firmware_version`, `extra` | 机器人基础元信息 |
| `JointLimits` | `min`, `max` | 关节物理限位（rad） |
| `JointInfo` | `name`, `limits` (JointLimits), `max_torque`, `max_velocity`, `extra` | 关节静态元信息 |
| `ActionInfo` | `id`, `type`, `duration`, `interruptible` | 预定义动作信息 |

**预定义动作 ID 列表**（共 10 个）:

| 动作 ID | 说明 | 动作 ID | 说明 |
|---|---|---|---|
| `hand_shake` | 握手 | `hand_wave` | 挥手 |
| `dance_new_year` | 新年舞蹈 | `dance_rock_rolling` | 摇滚舞蹈 |
| `dance_towards_future` | 走向未来舞蹈 | `gesture_dabing` | 大兵手势 |
| `gesture_ultraman` | 奥特曼手势 | `bow` | 鞠躬 |
| `cheer` | 欢呼 | `lucky_cat` | 招财猫 |

### 4.5 任务与订阅

| 类型 | 关键属性/方法 | 说明 |
|---|---|---|
| `TaskHandle[T]` | `trace_id`, `task_id`, `type`, `group`; 只读: `status`, `error` | 异步任务句柄。方法: `wait(timeout)`, `cancel()`, `done()`, `running()`, `task_info()`, `add_done_callback()`, `add_status_change_callback()` |
| `TaskInfo` | `trace_id`, `task_id`, `type`, `group`, `status` | 任务身份与状态不可变快照 |
| `SensorSubscription` | — | 传感器订阅句柄。方法: `unsubscribe()`，支持 `with` 上下文 |
| `AudioPlaybackStreamHandle` | — | PCM 播放流句柄。方法: `write(data)`, `close()`, `is_playing()`, `has_pending_audio()`, `wait()`, `cancel()` |

**TaskHandle 使用示例**:
```python
# 异步执行动作并等待完成
handle = robot.do_action("hand_wave")
handle.wait(timeout=10.0)
print(handle.status)  # SUCCEEDED

# 取消任务
handle2 = robot.do_action("dance_rock_rolling")
handle2.cancel()
```

### 4.6 轨迹数据

| 类型 | 关键属性 | 说明 |
|---|---|---|
| `TrajectoryMeta` | `id`, `duration`, `sample_interval`, `manufacturer`, `model`, `firmware_version`, `boosteros_version` | 轨迹元数据。方法: `to_dict()` |
| `JointTrajectoryPoint` | `time_from_start` (Duration), `joints` (list[JointState]); 只读: `joint_names` | 轨迹中的一帧关节数据。方法: `get_joint(name)`, `to_dict()` |
| `TrajectoryData` | `meta` (TrajectoryMeta), `points` (list[JointTrajectoryPoint]); 只读: `id`, `joint_names`, `duration` | 通用轨迹。方法: `save(path)`, `load(path)` (类方法), `to_numpy()` |

---

## 五、枚举与字面量类型

| 类型 | 取值 | 说明 |
|---|---|---|
| `ImageType` | `"rgb"`, `"depth"` | 图像类型 |
| `PcmSampleFormat` | `"S16LE"` | PCM 采样格式（16bit 有符号小端） |
| `RobotModeName` | `"damping"`, `"prepare"`, `"walk"`, `"custom"` | 机器人模式：阻尼→准备→行走→自定义 |
| `RobotGaitName` | `"default"`, `"soccer"` | 机器人步态 |
| `TaskStatus` | `"PENDING"`, `"RUNNING"`, `"CANCELLING"`, `"SUCCEEDED"`, `"FAILED"`, `"CANCELLED"` | 任务状态（前三非终态，后三终态） |
| `OverflowPolicy` | `"block"`, `"drop_oldest"`, `"drop_newest"` | 队列溢出策略 |

**模式切换流程**: `damping` → `set_mode("prepare")` → `set_mode("walk")` → `set_velocity(...)`。从 walk 回到 damping 可直接切换。`custom` 模式用于 BeyondMimic 等自定义控制场景。

---

## 六、API 速查总表

### BoosterRobot 全部接口（41 个）

| 分类 | 接口 | 类型 |
|---|---|---|
| 构造 | `BoosterRobot(...)` | 构造函数 |
| 属性 | `robot_info`, `audio_manager`, `hand_guiding_manager` | 属性（3 个） |
| 信息查询 | `get_mode()`, `list_gaits()`, `get_gait()`, `list_frames()`, `list_joints()`, `list_actions()` | 方法（6 个） |
| 传感器快照 | `get_image()`, `get_camera_info()`, `get_imu()`, `get_odom()`, `get_joint_states()`, `get_battery()`, `get_fall_down_state()`, `get_transform()` | 方法（8 个） |
| 传感器订阅 | `subscribe_image()`, `subscribe_imu()`, `subscribe_odom()`, `subscribe_battery()`, `subscribe_fall_down_state()` | 方法（5 个） |
| 运动控制 | `set_mode()`, `set_gait()`, `set_velocity()`, `upper_body_control()`, `set_joints()`, `set_head_angle()`, `reset_odom()` | 方法（7 个） |
| 高级任务 | `get_active_tasks()`, `do_action()`, `get_up()`, `execute_trajectory()`, `play_sound()` | 方法（5 个） |
| 音频管理 | `audio_manager.get_system_volume()`, `.set_system_volume()`, `.start_recording()`, `.stop_recording()`, `.is_recording()`, `.get_recording_duration()`, `.record_stream()`, `.play_stream()` | 方法（8 个） |
| 示教管理 | `hand_guiding_manager.start_recording()`, `.stop_recording()`, `.is_recording`, `.get_recording_duration()` | 方法+属性（4 个） |
| 踢球管理 | `SoccerKickManager(robot).start()`, `.update_command()`, `.update_ball()`, `.stop()` | 方法（4 个） |

### 独立模块接口

| 模块 | 导入路径 | 接口 |
|---|---|---|
| Speech | `boosteros.brain.Speech` | `recognize_stream()`, `chat()`, `list_voices()` |
| Detection | `boosteros.brain.Detection` | `list_models()` (类方法), `load_model()`, `detect()`, `plot()` |

### 数据类型（22 个）

`Time`, `Duration`, `Header`, `AnyImage`, `Image`, `CompressedImage`, `BoundingBox2D`, `DetectionResult`, `CameraInfo`, `RegionOfInterest`, `IMUState`, `OdomState`, `Transform`, `BatteryState`, `FallDownState`, `AudioData`, `JointState`, `JointStates`, `JointCommand`, `RobotInfo`, `JointLimits`, `JointInfo`, `ActionInfo`, `TaskHandle`, `TaskInfo`, `SensorSubscription`, `AudioPlaybackStreamHandle`, `TrajectoryMeta`, `JointTrajectoryPoint`, `TrajectoryData`

---

## 七、常见问题与调试

### 7.1 模式切换

**Q: `set_mode("walk")` 后多久能调用 `set_velocity()`？**
A: `set_mode()` 是同步调用，返回即表示切换完成，可以立即调用运动控制接口。

**Q: 如何在程序结束时安全停止机器人？**
```python
robot.set_velocity(0, 0, 0)  # 停止运动
robot.set_mode("damping")     # 回到阻尼模式
```

### 7.2 数据获取

**Q: `get_image()` 一直抛 `DataNotReadyError`？**
A: 检查相机话题是否正常发布——在机器人终端执行 `ros2 topic hz /boostercamera/head/raw/rgb`。

**Q: 快照和订阅的区别？**
A: 快照（`get_*`）返回最近一帧缓存数据，适合低频读取。订阅（`subscribe_*`）通过回调持续接收数据，适合高频处理。

### 7.3 关节控制

**Q: `set_joints()` 和 `set_head_angle()` 的区别？**
A: `set_joints()` 是通用关节控制接口（批量，任意关节），`set_head_angle()` 是专门针对头部俯仰和偏航的快捷接口（仅 walk 模式）。

### 7.4 调试建议：增益优化

关节控制中的 `kp`（比例增益）和 `kd`（微分增益）需要根据实际负载调优：
- `kp` 过大 → 关节抖动/过冲
- `kp` 过小 → 响应迟钝、不到位
- `kd` 用于抑制振荡，一般设为 kp 的 1/10 ~ 1/5
- 建议从低 kp 开始逐步增大，直到响应满意且无振荡

### 7.5 提取示例代码

原始文档中的示例代码可通过以下命令批量提取：
```bash
python3 -c "
import re, sys
text = open('BoosterOS 开发者接口文档 - V1.0.md').read()
for i, m in enumerate(re.finditer(r'\`\`\`python\n(.*?)\`\`\`', text, re.DOTALL)):
    with open(f'example_{i+1:03d}.py', 'w') as f:
        f.write(m.group(1))
    print(f'Written example_{i+1:03d}.py')
"
```

---

## 版本更新说明

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-08-06 | V1.0 录入 | 基于官方 BoosterOS 开发者接口文档 V1.0 完整录入，覆盖 BoosterRobot 全部 41 个接口 + Speech/Detection 独立模块 + 22 个数据类型 + 6 个枚举 |

> **原始文档**: `/root/uploads/1785830408754983913-BoosterOS 开发者接口文档 - V1.0.md`（5,780 行，Booster Robotics 官方）
>
> **后续更新**: 当收到 V1.x / Vx 更新版本文档时，将更新本文档并记录版本变更历史。
