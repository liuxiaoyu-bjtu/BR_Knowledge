# Chapter\_08\_模型部署与执行

# Chapter 08｜模型部署与执行

> Chapter 7 完成了 BeyondMimic（动作模仿训练框架）的训练流程：动作数据以 NPZ 形式进入训练环境，训练过程生成策略参数。
> 
> 本章继续处理动作生成系统的下一步：如何把已经训练好的 MJ 动作模型放入部署工程，并在 MuJoCo（多关节接触动力学仿真器）中执行。
> 
> 

建议：本章不要把第 7 章短训练得到的 checkpoint 作为输入。短训练主要用于确认训练环境和 task 能跑通，训练质量通常不足以展示稳定动作。本章直接使用已经提供的 MJ 动作部署模型：

```Plaintext
k1_mj_dance_002_2025-12-03_00-10-28.pt
```

这个 `.pt` 文件位于 `booster_deploy` 的模型目录中，会被部署侧代码通过 `torch.jit.load` 加载。它更接近部署阶段使用的 TorchScript（PyTorch 脚本化模型），不是让读者从短训练结果中临时挑选的训练 checkpoint。这样可以把第 8 章的重点放在部署链路本身：模型文件如何被加载，动作文件如何被读取，部署 task 如何注册，MuJoCo 如何运行，以及同一个部署任务如何切换到 K1 真机执行。

## 8\.1 从训练结果到部署执行

### 8\.1\.1 checkpoint 与部署模型不是同一层概念

在动作学习链路中，经常会看到 `.pt` 文件。需要先区分两类 `.pt`。

第一类是训练侧 checkpoint（检查点）。它通常出现在：

```Plaintext
booster_train/logs/rsl_rl/<experiment_name>/<timestamp>/model_*.pt
```

这类文件保存训练过程中策略网络的参数状态，可用于继续训练、在 Isaac Lab 中播放，或通过导出脚本转换为部署格式。它依赖训练工程中的 task 配置、观测维度、动作维度、归一化器和训练器结构。

第二类是部署侧 TorchScript 模型。它通常放在：

```Plaintext
booster_deploy/tasks/beyond_mimic/models/
```

部署侧代码通过 `torch.jit.load` 加载它。TorchScript 是 PyTorch 模型的一种可执行表示，包含模型计算图和参数，适合在部署程序中直接推理。第 8 章使用的 MJ `.pt` 就属于这个部署侧模型。

可以用下面的链路理解二者关系：

```Plaintext
训练侧 checkpoint
  ↓
play.py 导出
  ↓
TorchScript / ONNX
  ↓
booster_deploy 加载执行
```

本章不要求重新训练，也不要求从短训练结果导出模型，而是直接使用已经提供的 MJ TorchScript 模型。

### 8\.1\.2 为什么部署前要先做 Sim\-to\-Sim

Sim\-to\-Sim 是 Simulation\-to\-Simulation 的缩写，通常译为仿真到仿真验证。这里的两个仿真环境分别是 Isaac Lab 和 MuJoCo。

Isaac Lab 负责训练。它提供并行仿真环境、强化学习接口、奖励函数和训练器。策略模型最初是在 Isaac Lab 中学习动作跟踪能力。

MuJoCo 负责部署前验证。它是另一个物理仿真环境，运行方式、控制循环和模型加载方式都与 Isaac Lab 不同。模型能在 MuJoCo 中执行，说明它不只是“在训练环境中能跑”，而是能够进入更接近部署侧的控制链路。

真机执行风险最高。真机有真实电机、地面接触、姿态偏差、电源限制和安全边界。一个动作模型即使在训练环境中看起来可用，也不应直接上真机。先经过 MuJoCo Sim\-to\-Sim，可以提前发现模型加载、动作文件、关节映射、控制频率和姿态稳定性问题。

因此，本章的执行顺序是先部署到 MuJoCo，再部署到 K1 真机：

```Plaintext
MJ TorchScript 模型
  ↓
booster_deploy task
  ↓
MuJoCo Sim-to-Sim
  ↓
K1 真机执行
```

### 8\.1\.3 本章使用的 MJ 部署资源

第 8 章使用第 7 章已经整理好的 BeyondMimic 工作区：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/
```

其中与本章直接相关的资源如下：

|资源|路径|作用|
|---|---|---|
|MJ 动作 NPZ|`booster_deploy/tasks/beyond_mimic/motions/k1_mj2_seg1.npz`|部署侧参考动作|
|MJ TorchScript 模型|`booster_deploy/tasks/beyond_mimic/models/k1_mj_dance_002_2025-12-03_00-10-28.pt`|部署侧策略模型|
|部署 task|`booster_deploy/tasks/beyond_mimic/__init__.py`|注册 `k1_mj2`|
|策略执行逻辑|`booster_deploy/tasks/beyond_mimic/beyond_mimic.py`|构造 observation 并调用模型推理|
|MuJoCo 入口|`booster_deploy/scripts/deploy.py`|运行部署任务|
|K1 MuJoCo 模型|`booster_assets/robots/K1/K1_22dof.xml`|MuJoCo 中的 K1 机器人模型|

第 8 章的配套代码目录为：

```Plaintext
CourseCode/chapter_08_model_deployment/
```

该目录不重复复制大模型和机器人资源，只提供检查脚本，统一指向第 7 章中已经整理好的 MJ 工作区。

## 8\.2 模型文件与导出格式

### 8\.2\.1 训练侧 checkpoint 保存了什么

训练侧 checkpoint 保存的是策略网络在某个训练阶段的参数。它通常与训练器、优化器、归一化器和 task 配置绑定。

训练侧 checkpoint 的典型文件名是：

```Plaintext
model_9999.pt
model_19999.pt
model_29999.pt
```

编号表示训练迭代过程中的保存节点。编号越大，通常表示训练越靠后，但不一定表示动作效果最好。如果训练后期发散，后期 checkpoint 的动作反而可能更差。因此，训练侧 checkpoint 需要结合日志和执行效果选择。

部署时不能只看文件后缀。即使同样是 `.pt`，训练侧 checkpoint 与部署侧 TorchScript 模型的内部结构也不同。训练侧 checkpoint 通常由训练框架加载，部署侧 TorchScript 模型则由 `torch.jit.load` 加载。

### 8\.2\.2 TorchScript 与 ONNX

TorchScript 是 PyTorch 的模型部署格式之一。它把模型计算逻辑和参数保存成可执行对象，使部署程序可以不依赖完整训练流程，直接进行模型推理。

ONNX 是 Open Neural Network Exchange 的缩写，通常译为开放神经网络交换格式。它是一种跨框架模型表示方式，便于在不同推理引擎之间交换模型。

在 BeyondMimic 训练工程中，`play.py` 会尝试导出两类文件：

```Plaintext
exported/*.pt
exported/*.onnx
```

其中 `*.pt` 是 TorchScript 模型，`*.onnx` 是 ONNX 模型。当前 `booster_deploy` 的 MJ 执行逻辑使用的是 TorchScript `.pt` 文件，因为 `BeyondMimicPolicy` 中通过 `torch.jit.load` 加载模型。

### 8\.2\.3 play\.py 的作用

训练工程中的导出入口是：

```Plaintext
booster_train/scripts/rsl_rl/play.py
```

它的作用不是继续训练，而是加载训练侧 checkpoint，创建 play task 对应的环境，取出策略网络，再导出 TorchScript 和 ONNX。

如果具备训练侧 checkpoint，可以使用类似命令导出：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_train
python scripts/rsl_rl/play.py --task=Booster-K1-MJ_Dance_002-v0-Play --checkpoint=<TRAINING_CHECKPOINT_PATH> --headless
```

`--task` 必须使用 play task：

```Plaintext
Booster-K1-MJ_Dance_002-v0-Play
```

不能随意换成其他 task。`--task` 决定环境配置、观测维度、动作维度和归一化器加载方式。如果 task 与 checkpoint 不匹配，常见结果是模型加载时报 shape mismatch（张量形状不匹配），或者模型能加载但动作表现异常。

本章默认不执行这条导出命令。原因是第 8 章已经提供了可用于部署的 MJ TorchScript 模型，实践重点是部署执行。

### 8\.2\.4 实践案例：检查 MJ 部署模型结构

本实践检查第 8 章使用的部署资源是否完整。

进入本章代码目录：

```Bash
cd CourseCode/chapter_08_model_deployment
```

运行：

```Bash
python3 check_mj_deployment_resources.py
```

脚本会检查：

- `beyondmimic_workspace` 是否存在；

- `booster_deploy/scripts/deploy.py` 是否存在；

- `k1_mj2_seg1.npz` 是否存在并包含核心字段；

- `k1_mj_dance_002_2025-12-03_00-10-28.pt` 是否具备 TorchScript 归档结构；

- `k1_mj2` 是否在部署 task 中注册；

- `K1_22dof.xml` 是否存在。

这个脚本不导入 `torch`，不启动 MuJoCo，也不打开仿真窗口。它适合在正式部署前先做资源层检查。

## 8\.3 部署侧模型加载机制

### 8\.3\.1 booster\_deploy 的作用

`booster_train` 负责训练，`booster_deploy` 负责执行。二者不能混在一起理解。

`booster_train` 中的核心问题是：如何在 Isaac Lab 中训练策略，让策略学会跟踪参考动作。

`booster_deploy` 中的核心问题是：如何把动作文件、策略模型、机器人模型、控制器和执行入口组织成一个可以运行的 task。

第 8 章使用的部署工程位于：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_deploy/
```

其中，部署入口是：

```Plaintext
scripts/deploy.py
```

`deploy.py` 通过 `--task` 参数选择要运行的部署任务，通过 `--mujoco` 参数决定在 MuJoCo 中运行。

### 8\.3\.2 k1\_mj2 部署任务

MJ 动作的部署 task 名称是：

```Plaintext
k1_mj2
```

它在 `tasks/beyond_mimic/__init__.py` 中注册。核心配置包括：

```Python
self.policy.motion_path = "motions/k1_mj2_seg1.npz"
self.policy.checkpoint_path = "models/k1_mj_dance_002_2025-12-03_00-10-28.pt"
```

这两行把“参考动作”和“策略模型”绑定到同一个部署 task 中。

`motion_path` 指向 MJ 动作 NPZ。部署运行时，策略会读取这个动作文件，得到每一帧的参考关节位置、参考关节速度和参考身体姿态。

`checkpoint_path` 指向 MJ TorchScript 模型。部署运行时，策略会读取机器人当前状态和参考动作目标，构造 observation（观测），再调用模型输出 action（动作输出）。

部署 task 还会配置关节刚度、阻尼和力矩限制。这些参数会影响 MuJoCo 中动作执行的稳定性，也会影响真机部署时的安全边界。

### 8\.3\.3 BeyondMimicPolicy 的执行逻辑

`tasks/beyond_mimic/beyond_mimic.py` 中的 `BeyondMimicPolicy` 是部署侧策略类。它的执行逻辑可以概括为四步。

第一，加载 TorchScript 模型：

```Python
self._model = torch.jit.load(f"{self.task_path}/{self.cfg.checkpoint_path}")
```

第二，加载动作文件：

```Python
self.motion = MotionLoader(
    motion_file=f"{self.task_path}/{self.cfg.motion_path}",
    ...
)
```

第三，构造 observation。部署侧会读取当前机器人状态，包括根部姿态、角速度、关节位置、关节速度和上一帧 action；同时读取参考动作当前帧的关节位置、关节速度和躯干姿态。

第四，执行模型推理：

```Python
action = self._model(obs).flatten()
```

模型输出的 action 会经过关节顺序映射、缩放和默认关节位置叠加，最终成为关节目标。

这说明部署模型不是“播放动作文件”。动作文件提供参考目标，策略模型根据当前状态实时计算控制输出。MuJoCo 中看到的机器人动作，是策略闭环控制的结果。

### 8\.3\.4 MuJoCo 控制器的作用

`MujocoController` 负责在 MuJoCo 中运行 K1 模型。它会加载：

```Plaintext
booster_assets/robots/K1/K1_22dof.xml
```

这个 XML 是 K1 的 MuJoCo 模型。控制器会创建 MuJoCo 仿真数据，设置初始姿态，然后进入控制循环。

每个控制循环中，控制器会执行：

```Plaintext
update_state()
  ↓
policy_step()
  ↓
ctrl_step()
  ↓
viewer.sync()
```

`update_state()` 从 MuJoCo 中读取机器人当前关节和根部状态。

`policy_step()` 调用 `BeyondMimicPolicy`，得到下一步 action。

`ctrl_step()` 把 action 转成关节 PD 控制目标，并推进 MuJoCo 物理仿真。

`viewer.sync()` 更新 MuJoCo 窗口显示。

当前 MuJoCo 控制器还支持 reference ghost（参考虚影）。虚影表示参考动作轨迹，实体机器人表示策略控制下的实际执行结果。两者越接近，说明动作跟踪效果越好。

## 8\.4 MuJoCo 仿真执行

### 8\.4\.1 安装部署依赖

如果第 7 章已经完成环境和工程安装，可以继续使用同一个 Conda 环境。每次打开新终端后，先激活训练环境：

```Bash
conda activate booster_train
```

安装或确认 `booster_assets`：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_assets
python -m pip install -e .
```

安装 `booster_deploy` 依赖：

```Bash
cd ../booster_deploy
python -m pip install -r requirements.txt
```

`requirements.txt` 中包含 `torch`、`mujoco`、`scipy`、`evdev` 等依赖。MuJoCo 运行需要图形显示环境。如果通过远程桌面或无显示服务器运行，需要先确认图形界面和 OpenGL 支持可用。

### 8\.4\.2 列出部署任务

进入部署工程：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_deploy
```

列出已注册任务：

```Bash
python scripts/deploy.py -l
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yjk2YzI2MDg0NmM4MDE4N2RmZjMwOGM0ZjcwMGQwMTVfMWQ5ZGY1ZjIyYjBiYTVjZmZlNmZjYzhhZDBiZmEyMWFfSUQ6NzY2MjIxOTU5OTUwMTY5MTg2MV8xNzg1ODM5NDY1OjE3ODU5MjU4NjVfVjM)

正常情况下，输出中应包含：

```Plaintext
k1_mj2
```

如果没有 `k1_mj2`，说明部署 task 没有被正确注册，或者当前运行目录不对。`deploy.py` 会递归导入 `tasks/` 下的模块，只有模块被成功导入，`register_task("k1_mj2", ...)` 才会生效。

### 8\.4\.3 实践案例：运行 MJ 动作 MuJoCo 仿真

确认资源检查通过、部署依赖安装完成、`k1_mj2` 能列出后，运行：

```Bash
python scripts/deploy.py --task k1_mj2 --mujoco --device cpu
```

参数含义如下：

|参数|含义|
|---|---|
|`--task k1_mj2`|选择 MJ 动作部署任务|
|`--mujoco`|使用 MuJoCo 仿真执行，不连接真机|
|`--device cpu`|模型推理使用 CPU|

如果电脑具备可用 CUDA 环境，也可以将 `--device cpu` 改为 `--device cuda`。但 MuJoCo 仿真本身仍需要本机图形环境支持。

运行后会打开 MuJoCo 窗口。窗口中通常会看到实体 K1 机器人和半透明参考虚影。参考虚影来自动作 NPZ，实体机器人由策略模型控制。观察时重点看三点：

1. 实体机器人是否能持续执行 MJ 动作，而不是启动后立刻摔倒；

2. 实体机器人躯干、手臂和腿部是否大致跟随参考虚影；

3. 动作过程中是否出现明显抖动、脚底滑动或姿态快速发散。

本章使用的是已经提供的 MJ 部署模型，运行效果应比临时短训练结果更稳定。短训练只适合检查流程，不适合作为稳定部署效果展示。

### 8\.4\.4 MuJoCo 运行现象的含义

MuJoCo 中的动作效果不是简单动画播放。实体机器人每一帧都会经过如下计算：

```Plaintext
当前机器人状态 + 当前参考动作帧
  ↓
TorchScript 策略模型
  ↓
关节 action
  ↓
PD 控制与 MuJoCo 物理推进
  ↓
下一帧机器人状态
```

如果实体机器人与参考虚影接近，说明策略能够根据状态闭环跟踪动作。如果实体机器人明显偏离参考虚影，可能是策略模型质量不足、动作数据与模型不匹配、关节映射不一致、初始姿态不合适，或者控制参数不合适。

Sim\-to\-Sim 的价值正在这里：它让部署侧的问题在仿真中暴露出来，而不是直接把风险带到真机。

## 8\.5 真机执行接口与安全前置

### 8\.5\.1 真机执行与 MuJoCo 执行的区别

MuJoCo 执行发生在本机仿真环境中。即使动作失败，影响也只停留在软件仿真中。

真机执行会把策略输出发送到 K1 机器人控制链路。真实机器人有重量、惯性、电机力矩、地面摩擦和跌倒风险，因此真机执行必须更谨慎。

`deploy.py` 在不加 `--mujoco` 时，会尝试通过机器人 SDK 连接真实机器人：

```Bash
python scripts/deploy.py --task k1_mj2 --net <NETWORK_INTERFACE>
```

`<NETWORK_INTERFACE>` 需要按实际机器人网络配置填写。真机部署还需要 `booster_robotics_sdk_python` 等依赖可用。

从命令结构看，部署到 MuJoCo 和部署到真机的差别主要是运行参数不同：带 `--mujoco` 时进入 MuJoCo 仿真，不带 `--mujoco` 时进入真机控制链路。真机执行必须在安全条件、场地和机器人状态都满足时进行。

### 8\.5\.2 真机执行前必须确认的条件

执行动作模型前，至少确认以下条件：

- K1 机器人电量充足，机身无明显机械异常；

- 机器人双脚着地，周围留出足够空间，地面平整、防滑、无障碍物；

- 机器人已经处于可控站立状态；

- 执行动作前已经在 MuJoCo 中确认 `k1_mj2` 可以运行；

- 机器人网络连接稳定，`--net` 参数与实际网络接口一致；

- 部署环境已安装机器人 SDK 和 Python 依赖；

- 操作人员站在机器人侧后方安全位置，避免站在机器人正前方或腿部摆动范围内；

- 出现异常姿态、动作发散或失稳趋势时，立即按机器人背部 STAND 按钮，让机器人退出当前动作并回到站立控制状态。

对于动作模型部署，安全条件本身就是运行步骤的一部分。不要把 MuJoCo 中能运行等同于真机一定能运行。

### 8\.5\.3 真机执行常见风险

真机执行时常见风险包括：

|风险|可能原因|
|---|---|
|动作启动后马上失稳|初始姿态与模型预期不一致，或地面条件不合适|
|关节抖动明显|控制参数、模型输出或状态反馈异常|
|动作幅度过大|策略输出与真机关节限制不匹配|
|无法连接机器人|网络接口、SDK 环境或机器人端服务异常|
|执行一段时间后偏离|Sim\-to\-Real 误差累积，真实接触条件与仿真不同|

这些问题不能只靠命令行排查。真机部署需要结合机器人状态、场地、动作幅度和安全干预手段一起判断。

## 8\.6 实践案例：MJ 动作模型部署闭环

### 8\.6\.1 实践目标

本实践完成 MJ 动作模型的部署侧闭环：

```Plaintext
检查部署资源
  ↓
确认 k1_mj2 task 注册
  ↓
加载 MJ TorchScript 模型
  ↓
部署到 MuJoCo 仿真
  ↓
观察实体机器人与参考虚影
  ↓
部署到 K1 真机
  ↓
观察真机 MJ 动作执行效果
```

实践输入是已经提供的 MJ TorchScript 模型，不使用第 7 章短训练得到的 checkpoint。

### 8\.6\.2 文件目录

第 8 章配套代码位于：

```Plaintext
CourseCode/chapter_08_model_deployment/
```

目录中包含：

|文件|作用|
|---|---|
|`check_mj_deployment_resources.py`|检查 MJ 部署资源是否齐全|
|`README.md`|说明本章运行方式|

本章部署资源位于第 7 章工作区：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/
```

这样可以避免重复复制同一套 MJ 模型、动作文件和机器人模型。

### 8\.6\.3 运行资源检查

进入第 8 章代码目录：

```Bash
cd CourseCode/chapter_08_model_deployment
```

运行：

```Bash
python3 check_mj_deployment_resources.py
```

如果检查通过，会看到 MJ 部署资源齐全的提示。若出现 FAIL 项，先处理缺失文件或 task 注册问题，再运行 MuJoCo。

### 8\.6\.4 部署到 MuJoCo 仿真

进入部署工程：

```Bash
cd ../chapter_07_beyondmimic_training/beyondmimic_workspace/booster_deploy
```

列出任务：

```Bash
python scripts/deploy.py -l
```

确认输出中包含：

```Plaintext
k1_mj2
```

先部署到 MuJoCo：

```Bash
python scripts/deploy.py --task k1_mj2 --mujoco --device cpu
```

看到 MuJoCo 窗口打开，并且 K1 实体机器人开始跟随 MJ 参考虚影运动，说明部署侧模型加载、动作读取和 MuJoCo 控制链路已经打通。

> 视频占位 8\-1：MJ 模型部署到 MuJoCo 仿真的运行效果。

> （此处补充视频：\_\_\_\_\_\_\_\_\_\_）

\[录屏 2026\-07\-13 13\-59\-40\.webm\]

### 8\.6\.5 部署到 K1 真机

MuJoCo 运行正常后，再进入真机执行。真机执行使用同一个 `k1_mj2` task，不再添加 `--mujoco` 参数，而是通过 `--net` 指定机器人网络接口。

执行前确认机器人处于可控站立状态，周围留出足够空间，操作人员站在机器人侧后方安全位置。出现异常姿态、动作发散或失稳趋势时，立即按机器人背部 STAND 按钮，让机器人退出当前动作并回到站立控制状态。

真机执行命令如下：

```Bash
python scripts/deploy.py --task k1_mj2 --net <NETWORK_INTERFACE> --device cpu
```

其中：

|参数|含义|
|---|---|
|`--task k1_mj2`|选择 MJ 动作部署任务|
|`--net <NETWORK_INTERFACE>`|指定与机器人通信的网络接口或地址|
|`--device cpu`|模型推理使用 CPU|

如果真机部署环境使用 CUDA 推理，也可以将 `--device cpu` 改为 `--device cuda`。真机运行时重点观察机器人是否能稳定进入动作、躯干是否明显失稳、手臂和腿部是否出现异常抖动，以及动作结束后是否仍能保持可控状态。

> 视频占位 8\-2：MJ 模型部署到 K1 真机后的运行效果。

> （此处补充视频：\_\_\_\_\_\_\_\_\_\_）

\[03a08356ff21ab2fb0d483d16f97b92b\.mp4\]

### 8\.6\.6 常见问题排查

问题 1：`python scripts/deploy.py -l` 看不到 `k1_mj2`。

确认当前目录是：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_deploy
```

再检查 `tasks/beyond_mimic/__init__.py` 中是否存在：

```Python
register_task("k1_mj2", K1MJ2ControllerCfg())
```

问题 2：提示 `No module named booster_assets`。

需要先安装 `booster_assets`：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_assets
python -m pip install -e .
```

问题 3：提示 `No module named mujoco`。

需要在当前 Conda 环境中安装 `booster_deploy` 依赖：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_deploy
python -m pip install -r requirements.txt
```

问题 4：`torch.jit.load` 加载模型失败。

检查 `tasks/beyond_mimic/models/` 下是否存在：

```Plaintext
k1_mj_dance_002_2025-12-03_00-10-28.pt
```

如果误把训练侧 `model_*.pt` 放到这里，部署侧可能无法用 `torch.jit.load` 读取。部署侧需要 TorchScript 模型。

问题 5：找不到 `k1_mj2_seg1.npz`。

检查 `tasks/beyond_mimic/__init__.py` 中的 `motion_path`，以及文件是否位于：

```Plaintext
booster_deploy/tasks/beyond_mimic/motions/k1_mj2_seg1.npz
```

问题 6：MuJoCo 窗口无法打开。

检查是否有可用图形界面。远程服务器、无显示器主机或 SSH 终端可能缺少显示环境。需要使用支持图形显示的桌面环境或远程桌面。

问题 7：实体机器人与参考虚影差距很大。

先确认使用的是 `k1_mj2` task、MJ 动作 NPZ 和 MJ TorchScript 模型。动作文件、模型文件和 task 配置必须来自同一条训练链路。若三者不匹配，即使程序能启动，动作效果也可能明显异常。

问题 8：实体机器人启动后很快倒下。

优先检查模型与动作是否匹配、机器人初始姿态是否合理、MuJoCo 模型是否加载正确、关节刚度和阻尼是否被修改。不要把这种状态直接迁移到真机执行。

问题 9：真机执行时提示 `booster_robotics_sdk_python` 未安装。

这说明当前环境缺少机器人 SDK 的 Python 绑定。MuJoCo 仿真不需要该依赖，但真机执行需要通过 SDK 与机器人通信。需要先在真机部署环境中安装对应 SDK，再运行不带 `--mujoco` 的部署命令。

问题 10：真机执行时无法连接机器人。

先检查 `--net <NETWORK_INTERFACE>` 是否填写正确，再检查机器人与部署电脑是否在同一网络中。网络连接正常后，再确认机器人端服务已经启动、机器人处于可控站立状态。若动作启动后出现异常姿态、动作发散或失稳趋势，立即按机器人背部 STAND 按钮退出当前动作。

## 8\.7 本章小结

### 8\.7\.1 本章完成的部署链路

本章完成了动作生成系统中的部署执行环节。第 7 章关注训练流程，第 8 章关注如何把已经提供的 MJ 部署模型放入 `booster_deploy`，并分别部署到 MuJoCo 和 K1 真机。

本章讲清楚了训练侧 checkpoint 与部署侧 TorchScript 模型的区别，说明了 `play.py` 的导出作用，也解释了 `booster_deploy` 如何通过 `k1_mj2` task 绑定动作文件和模型文件。通过资源检查、task 列表、MuJoCo 运行和真机运行命令，可以确认 MJ 模型从仿真部署到真机部署的完整链路。

### 8\.7\.2 进入第 9 章

进入 Chapter 9 后，动作生成系统将进入综合项目阶段。第 9 章会把前面几章串联起来，形成从动作数据、训练理解、模型部署、MuJoCo 验证到真机执行的完整项目流程。

