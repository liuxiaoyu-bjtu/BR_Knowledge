# Chapter\_09\_动作学习综合项目：从动作数据到K1部署

# Chapter 09｜动作学习综合项目：从动作数据到 K1 部署

> Chapter 6 到 Chapter 8 分别讲解了动作数据、BeyondMimic（动作模仿训练框架）训练流程和模型部署机制。第 9 章把这些内容合并为一个完整项目：从一个已经完成 K1 重定向的动作 CSV 文件出发，完成 CSV 到 NPZ 的转换，创建新的训练任务，启动短轮次训练，查看 TensorBoard（训练可视化看板）数据，导出部署模型，再把模型部署到 MuJoCo（机器人动力学仿真器）和 K1 真机。
> 
> 

本章使用 `k1_walk_demo.csv` 作为基准动作文件。它不是一个已经完整注册好的训练项目，而是一份已经处在 K1 关节空间中的动作数据。这样做的目的，是让学习者从“一个动作文件”开始，亲自完成动作学习项目中最关键的工程连接过程，而不是只运行一个已经准备好的样例任务。

本章默认第 7 章所需的电脑硬件环境、显卡驱动、Python 3\.11、PyTorch（深度学习计算框架）、Isaac Sim（机器人仿真平台）、Isaac Lab（机器人强化学习训练框架）等基础环境已经具备。若这些环境尚未安装，应先完成 Chapter 7 中的环境准备，再进入本章。

## 9\.1 综合项目目标：跑通完整动作学习链路

动作学习项目不是单个脚本，也不是单个模型文件。它是一条数据和模型逐步变化的链路。

本章实践的链路如下：

```Plaintext
已重定向 K1 CSV
  -> CSV 转 NPZ
  -> 新建 BeyondMimic 训练 task
  -> PPO 短轮次训练
  -> TensorBoard 查看训练曲线
  -> checkpoint 导出 TorchScript
  -> 注册 booster_deploy 部署 task
  -> MuJoCo Sim-to-Sim
  -> K1 真机 Sim-to-Real
```

这里的每一步都有明确输入和输出。

|阶段|输入|输出|作用|
|---|---|---|---|
|重定向完成后的动作数据|人体动作或已有动作数据|K1 CSV|得到符合 K1 关节空间的轨迹|
|CSV 到 NPZ|`k1_walk_demo.csv`|`k1_walk_demo.npz`|补齐速度、身体部件位姿等训练字段|
|训练 task|NPZ、机器人模型、奖励配置|`Booster-K1-CH09_Walk_Demo-v0`|让 Isaac Lab 能创建训练环境|
|策略训练|训练 task|`model_*.pt` checkpoint|得到训练过程中的策略参数|
|模型导出|checkpoint|TorchScript / ONNX|得到部署侧可加载模型|
|部署 task|NPZ、TorchScript 模型|`k1_ch09_walk_demo`|让部署程序知道加载哪个动作和模型|
|MuJoCo 运行|部署 task|仿真动作效果|检查 Sim\-to\-Sim 执行效果|
|K1 真机运行|部署 task、网络接口|真机动作执行|完成 Sim\-to\-Real 链路|

`checkpoint` 是训练过程中保存的模型参数检查点；`TorchScript` 是 PyTorch 模型的可部署表示；`ONNX` 是 Open Neural Network Exchange（开放神经网络交换格式），用于在不同推理框架之间交换模型。本章部署侧主要使用 TorchScript 模型。

## 9\.2 动作数据从哪里来：重定向环节的前置理解

### 9\.2\.1 为什么动作数据需要重定向

人形机器人不能直接使用人体动作数据。人体动作和 K1 机器人动作之间至少存在四类差异。

第一，关节数量不同。人体骨骼数据可能包含脊柱、肩胛、手腕、手指等大量关节点，而 K1 的训练模型使用固定的 22 个关节。多出来的动作自由度需要被舍弃、合并或映射。

第二，关节方向不同。人体数据中的某个旋转轴，不一定对应 K1 某个关节的正方向。即使都是“肩部抬起”，人体骨骼坐标系、机器人 URDF（统一机器人描述格式）坐标系和训练环境坐标系也可能不同。

第三，身体比例不同。人体的腿长、臂长、躯干比例与 K1 不同。如果直接把人体末端位置复制给机器人，机器人可能无法到达，或者到达时关节角超过限制。

第四，物理约束不同。人类可以依靠肌肉和足底微调保持平衡，机器人必须满足电机力矩、关节限位、接触稳定性和控制频率等约束。一个在视觉上合理的人体动作，不一定能成为机器人可训练、可部署的动作。

因此，动作生成链路中的第一步通常是 retargeting（重定向）。重定向的作用，是把来源动作转换为 K1 机器人能够表达的根部位姿和关节角序列。

### 9\.2\.2 常见来源动作格式

动作数据可以来自不同来源。

`BVH` 是 Biovision Hierarchy（骨骼层级动作捕捉格式），常用于保存人体骨架结构和每一帧的关节旋转。

`FBX` 是 Filmbox（常见三维动画交换格式），常用于三维软件、动画资产和动作捕捉资产交换。

`SMPL-X` 是一种参数化人体模型格式，能够用少量参数表达身体、手部和面部姿态。

视频动作估计通常先从视频中提取人体关键点，再进一步恢复人体姿态或骨骼动作。它离机器人动作还有较远距离，仍然需要经过人体姿态估计、三维重建、重定向和动作清洗。

`GMR` 在动作学习资料中常用于指代面向机器人动作重定向的一组方法或工具链。若学习者后续希望从网络动作数据、动捕数据或视频动作中制作新动作，可以继续检索 `BVH to robot retargeting`、`SMPL-X retargeting`、`humanoid motion retargeting` 等关键词，重点关注“人体骨骼到机器人关节空间”的映射方法。

### 9\.2\.3 重定向的通用解决步骤

动作重定向的目标，是把人体动作转换成 K1 机器人能够表达和执行的根部位姿与关节角序列。一个通用的重定向流程通常包括以下步骤。

第一步，确认来源动作格式。来源数据可能是 `BVH`（骨骼层级动作捕捉格式）、`FBX`（三维动画交换格式）、`SMPL-X`（参数化人体模型）、视频姿态估计结果，或动捕系统导出的骨骼数据。不同格式保存的数据不同，有的直接包含骨骼旋转，有的只包含人体关键点位置。

第二步，建立人体模型与机器人模型的对应关系。人体骨骼中的髋部、膝部、踝部、肩部、肘部等节点，需要映射到 K1 的躯干、腿部、手臂和头部关节。这个过程不是一一复制，因为人体自由度通常多于机器人自由度，机器人关节方向、关节数量和运动范围也与人体不同。

第三步，统一坐标系、尺度和初始姿态。来源动作的坐标系可能与机器人仿真坐标系不同，人体身高比例也与 K1 不同。重定向前需要处理朝向、地面高度、身体比例、根部位置和初始站姿，否则导出的动作容易出现整体旋转错误、脚底漂浮、身体偏移或关节方向反转。

第四步，求解机器人关节轨迹。重定向算法会根据人体关键部位的位置和姿态，计算 K1 每一帧的根部位姿和关节角。常见做法包括 inverse kinematics（逆运动学求解）、关键点跟踪优化、关节角约束优化等。求解时需要限制关节角范围，避免生成机器人无法达到的姿态。

第五步，清洗和修正动作轨迹。初步重定向结果通常还需要滤波、去抖、裁剪异常帧、修正脚底接触、调整根部高度和速度。未经清洗的轨迹即使看起来能播放，也可能在训练中导致奖励异常、机器人快速摔倒或真机执行风险增大。

第六步，导出 K1 CSV。清洗后的轨迹需要保存为 K1 训练链路能够读取的 CSV 格式。每一行表示一帧，前 7 列是根部位置和四元数姿态，后续 22 列是 K1 关节角。只有得到这种结构稳定、关节顺序正确的 CSV 文件，才能继续进入本章的 `CSV -> NPZ -> 训练 -> 导出 -> 部署` 流程。

### 9\.2\.4 本章从已重定向 CSV 开始

本章不把 `boostergmr` 作为必须安装和运行的环节。原因是完整重定向需要额外准备原始动作文件、人体模型、机器人模型、坐标系映射和动作清洗流程，超出了本章的主任务。

本章采用更适合综合项目的起点：使用已经完成 K1 重定向的 CSV 文件 `k1_walk_demo.csv`。它已经不再是人体骨骼动作，而是 K1 机器人根部位姿和 22 个关节角随时间变化的轨迹。

这意味着本章的实践从以下位置开始：

```Plaintext
已重定向到 K1 的 CSV
  -> NPZ
  -> 训练
  -> 导出
  -> 部署
```

这种安排保留了重定向在完整链路中的概念位置，同时把实践重点放在训练和部署工程闭环上。

## 9\.3 基准动作文件：k1\_walk\_demo\.csv

### 9\.3\.1 文件位置

第 9 章配套代码目录为：

```Plaintext
CourseCode/chapter_09_end_to_end_motion_learning/
```

基准动作文件位于：

```Plaintext
CourseCode/chapter_09_end_to_end_motion_learning/
  beyondmimic_workspace/
    booster_assets/
      motions/
        K1/
          k1_walk_demo.csv
```

该 CSV 是已经重定向到 K1 关节空间的动作轨迹。本章不直接使用 MJ 动作，也不使用已有注册完成的训练项目，而是基于这份短动作文件创建新的训练任务。

### 9\.3\.2 CSV 行列结构

`k1_walk_demo.csv` 共 600 行，每一行表示一帧动作。每行 29 列，结构如下：

```Plaintext
x, y, z, qx, qy, qz, qw, joint_0, joint_1, ..., joint_21
```

前 7 列表示根部位姿：

|列|含义|
|---|---|
|`x, y, z`|根部在世界坐标系中的位置|
|`qx, qy, qz, qw`|根部朝向四元数|

后 22 列表示 K1 的 22 个关节角，单位是弧度。关节顺序需要与 `booster_assets.motions.K1_JOINT_NAMES` 一致：

```Plaintext
AAHead_yaw
Head_pitch
ALeft_Shoulder_Pitch
Left_Shoulder_Roll
Left_Elbow_Pitch
Left_Elbow_Yaw
ARight_Shoulder_Pitch
Right_Shoulder_Roll
Right_Elbow_Pitch
Right_Elbow_Yaw
Left_Hip_Pitch
Left_Hip_Roll
Left_Hip_Yaw
Left_Knee_Pitch
Left_Ankle_Pitch
Left_Ankle_Roll
Right_Hip_Pitch
Right_Hip_Roll
Right_Hip_Yaw
Right_Knee_Pitch
Right_Ankle_Pitch
Right_Ankle_Roll
```

如果列数不是 29，或者关节顺序不匹配，后续训练得到的动作会失真。常见现象包括关节方向错误、手臂和腿部动作错位、机器人一开始就摔倒，或者训练奖励长期无法上升。

### 9\.3\.3 检查动作文件

进入第 9 章代码目录：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning
```

运行检查脚本：

```Bash
python3 check_ch09_pipeline_resources.py
```

初始状态下，检查结果中会看到若干 `WARN`。这不是错误。`WARN` 表示后续流程还没有生成对应文件，例如：

```Plaintext
[WARN] 训练侧 k1_walk_demo.npz: 文件不存在
[WARN] 部署侧 ch09_walk_demo.pt: 文件不存在
```

第 9 章的目标正是生成这些文件。只要 CSV、训练 task 和部署 task 配置显示 `OK`，就可以进入下一步。

## 9\.4 准备本章工程目录

### 9\.4\.1 工作区结构

第 9 章配套目录包含以下内容：

```Plaintext
chapter_09_end_to_end_motion_learning/
├─ beyondmimic_workspace/
│  ├─ booster_assets/
│  ├─ booster_train/
│  ├─ booster_deploy/
│  └─ TOOLs/
├─ check_ch09_pipeline_resources.py
├─ prepare_ch09_deploy_files.py
└─ README.md
```

`booster_assets` 存放机器人模型和动作数据。`k1_walk_demo.csv` 放在 `booster_assets/motions/K1/` 下，后续生成的 `k1_walk_demo.npz` 也会放在同一目录。

`booster_train` 存放 BeyondMimic 训练代码和 Isaac Lab 训练 task。第 9 章新增的训练 task 位于：

```Plaintext
booster_train/source/booster_train/booster_train/
  tasks/manager_based/beyond_mimic/robots/k1/ch09_walk_demo/
```

`booster_deploy` 存放部署代码。第 9 章新增的部署 task 注册名为：

```Plaintext
k1_ch09_walk_demo
```

### 9\.4\.2 第 9 章新增文件的作用

`check_ch09_pipeline_resources.py` 用于检查第 9 章资源是否齐全。它不导入 Isaac Lab，不启动仿真，只检查文件结构、CSV 列数、训练 task 注册和部署 task 注册。

`prepare_ch09_deploy_files.py` 用于把训练阶段生成的 `k1_walk_demo.npz` 和导出的 TorchScript 模型复制到 `booster_deploy` 需要的位置。部署阶段不直接从训练目录读取模型，而是通过部署 task 中的 `motion_path` 和 `checkpoint_path` 加载文件。

## 9\.5 CSV 到 NPZ：生成训练动作包

### 9\.5\.1 为什么不能直接用 CSV 训练

CSV 只保存根部位姿和关节角。它适合人工检查，也适合保存基础轨迹，但不足以直接支撑 BeyondMimic 训练。

训练过程不仅需要知道“某一帧关节角是多少”，还需要知道身体部件在空间中的位置、姿态和速度。奖励函数会比较机器人当前状态与参考动作之间的误差，例如躯干姿态误差、脚部位置误差、手部位置误差和关节速度误差。

因此，CSV 需要转换成 NPZ。NPZ 中通常包含：

|字段|含义|
|---|---|
|`fps`|动作帧率|
|`joint_pos`|每一帧的关节位置|
|`joint_vel`|每一帧的关节速度|
|`body_pos_w`|身体部件在世界坐标系中的位置|
|`body_quat_w`|身体部件在世界坐标系中的姿态|
|`body_lin_vel_w`|身体部件线速度|
|`body_ang_vel_w`|身体部件角速度|

CSV 到 NPZ 的转换并不只是改文件后缀。转换脚本会在 Isaac 环境中重放动作，计算速度和身体部件位姿，并把训练所需数组打包保存。

### 9\.5\.2 运行转换命令

进入工作区：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace
```

进入训练工程：

```Bash
cd booster_train
```

运行 CSV 到 NPZ 转换：

```Bash
python scripts/csv_to_npz.py \
    --headless \
    --input_file ../booster_assets/motions/K1/k1_walk_demo.csv \
    --input_fps 30 \
    --output_name ../booster_assets/motions/K1/k1_walk_demo.npz \
    --output_fps 50
```

参数含义如下：

|参数|含义|
|---|---|
|`--headless`|无图形窗口运行 Isaac 应用|
|`--input_file`|输入 CSV 文件|
|`--input_fps 30`|输入动作按 30 FPS 理解|
|`--output_name`|输出 NPZ 文件路径|
|`--output_fps 50`|输出动作重采样为 50 FPS|

转换完成后，应生成：

```Plaintext
booster_assets/motions/K1/k1_walk_demo.npz
```

再次运行检查脚本：

```Bash
cd ..
python3 ../check_ch09_pipeline_resources.py
```

如果 NPZ 字段检查显示 `OK`，说明动作数据已经进入训练可读取的格式。

## 9\.6 新建训练 task：不要使用已有注册项目

### 9\.6\.1 task 的作用

在 BeyondMimic 中，动作文件和训练任务不是同一件事。

动作文件是 `k1_walk_demo.npz`，它告诉训练系统“参考动作是什么”。

训练 task 是 Isaac Lab 中的环境配置，它告诉训练系统：

- 使用哪个机器人模型；

- 读取哪个动作文件；

- 跟踪哪些身体部件；

- 使用哪些观测项；

- 使用哪些奖励项；

- 在什么地形和随机扰动下训练；

- 训练结果保存到哪个实验目录。

因此，只有 NPZ 文件还不能启动训练。还需要注册一个新的 task。

### 9\.6\.2 第 9 章 task 目录

第 9 章新增 task 目录为：

```Plaintext
booster_train/source/booster_train/booster_train/
  tasks/manager_based/beyond_mimic/robots/k1/ch09_walk_demo/
```

目录中包含：

```Plaintext
ch09_walk_demo/
├─ __init__.py
├─ env_cfg.py
├─ ppo_cfg.py
└─ tracking_env_cfg.py
```

`__init__.py` 负责把 task 注册到 Gymnasium（强化学习环境注册库）中。

`env_cfg.py` 负责绑定机器人模型、动作文件、参考身体部件和训练环境。

`ppo_cfg.py` 负责设置 PPO（Proximal Policy Optimization，近端策略优化）训练参数，例如最大训练轮数和实验名称。

`tracking_env_cfg.py` 复用已有的 BeyondMimic 跟踪奖励和观测定义。第 9 章的重点不是重新设计奖励函数，而是跑通完整工程链路。

### 9\.6\.3 注册 train task 和 play task

第 9 章注册两个 task：

```Plaintext
Booster-K1-CH09_Walk_Demo-v0
Booster-K1-CH09_Walk_Demo-v0-Play
```

第一个用于训练。它包含轻微地形变化和扰动，用于让策略在训练中接触更多状态。

第二个用于回放和导出。它使用更平稳的运行环境，适合加载 checkpoint 并导出部署模型。

这种 train task 与 play task 分离的设计很重要。训练时需要一定扰动来提高鲁棒性；导出和查看时则需要更可控的环境，便于判断模型是否能跟踪参考动作。

### 9\.6\.4 绑定 motion\_file

在 `env_cfg.py` 中，核心绑定关系是：

```Python
self.commands.motion.motion_file = f"{BOOSTER_ASSETS_DIR}/motions/K1/k1_walk_demo.npz"
```

这行代码决定训练环境读取哪一个参考动作。如果文件名写错，训练脚本会在创建环境或加载动作时失败。如果动作文件存在但字段不完整，训练可能在 `MotionLoader` 读取阶段报错。

### 9\.6\.5 设置 experiment\_name

在 `ppo_cfg.py` 中，第 9 章设置：

```Python
experiment_name = "ch09_walk_demo"
```

训练日志会保存到：

```Plaintext
booster_train/logs/rsl_rl/ch09_walk_demo/
```

后续查看 TensorBoard、寻找 checkpoint 和导出模型时，都要从这个目录进入。

## 9\.7 启动训练：设定几千轮跑通流程

### 9\.7\.1 查看 task 是否可见

进入训练工程：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace/booster_train
```

列出可用训练环境：

```Bash
python scripts/list_envs.py
```

输出中应包含：

```Plaintext
Booster-K1-CH09_Walk_Demo-v0
Booster-K1-CH09_Walk_Demo-v0-Play
```

如果看不到这两个 task，说明 `ch09_walk_demo` 目录没有被正确放入训练工程，或者 `__init__.py` 中的注册代码没有被导入。

### 9\.7\.2 启动短轮次训练

运行训练命令：

```Bash
python scripts/rsl_rl/train.py \
    --task Booster-K1-CH09_Walk_Demo-v0 \
    --headless \
    --device cuda:0 \
    --max_iterations 5000 \
    --logger tensorboard \
    --run_name ch09_5000
```

参数含义如下：

|参数|含义|
|---|---|
|`--task`|指定训练 task|
|`--headless`|无图形界面训练|
|`--device cuda:0`|使用第 0 块 NVIDIA GPU|
|`--max_iterations 5000`|覆盖默认训练轮数，训练 5000 次迭代|
|`--logger tensorboard`|使用 TensorBoard 记录训练曲线|
|`--run_name ch09_5000`|给本次训练目录增加可读名称|

5000 次迭代适合本章跑通完整流程。它不等于最终高质量动作模型。强化学习训练结果受动作难度、奖励函数、随机种子、训练轮数、仿真设置等因素影响。若要得到更稳定的动作，通常需要更长训练、更细致的奖励设计和多次对比。

### 9\.7\.3 训练过程中的终端信息

训练启动后，终端会持续输出 iteration（迭代次数）、reward（奖励）、episode length（回合长度）、loss（损失）等信息。

早期训练中，机器人可能很快失稳，奖励较低，回合长度较短。这是正常现象。策略一开始并不知道如何根据观测输出合适动作，需要在仿真中反复尝试，通过奖励函数逐步靠近参考动作。

如果训练刚启动就报错，应优先检查：

- `k1_walk_demo.npz` 是否存在；

- NPZ 是否包含 `joint_pos`、`body_pos_w` 等字段；

- task ID 是否拼写正确；

- `--device cuda:0` 对应的 GPU 是否可用；

- Isaac Sim 和 Isaac Lab 是否能正常导入。

## 9\.8 查看 TensorBoard 看板数据

### 9\.8\.1 启动 TensorBoard

训练日志目录为：

```Plaintext
booster_train/logs/rsl_rl/ch09_walk_demo/
```

在 `booster_train` 目录下运行：

```Bash
tensorboard --logdir logs/rsl_rl/ch09_walk_demo --port 6006
```

浏览器打开：

```Plaintext
http://localhost:6006
```

TensorBoard 是训练过程的可视化工具。它可以显示奖励、损失、学习率、回合长度等曲线。仅看终端输出容易错过趋势，看板能够帮助判断训练是否在朝合理方向变化。

### 9\.8\.2 重点观察哪些曲线

本章重点关注三类曲线。

第一类是 reward（奖励）。奖励曲线如果长期停留在很低水平，说明策略没有有效学会跟踪动作。奖励有波动是正常的，因为强化学习训练带有随机探索和批量更新。

第二类是 episode length（回合长度）。如果回合长度极短，通常说明机器人很快触发终止条件，例如摔倒、姿态偏差过大或动作跟踪失败。随着训练推进，回合长度通常应有一定改善。

第三类是 loss（损失）。损失曲线用于观察策略网络和价值网络更新是否稳定。损失不是越低越好，重点是看是否出现持续异常发散。

### 9\.8\.3 checkpoint 保存位置

训练过程会按间隔保存 checkpoint。第 9 章的实验名称是 `ch09_walk_demo`，训练目录通常形如：

```Plaintext
logs/rsl_rl/ch09_walk_demo/2026-xx-xx_xx-xx-xx_ch09_5000/
```

目录中会出现：

```Plaintext
model_1000.pt
model_2000.pt
model_3000.pt
model_4000.pt
model_5000.pt
params/
```

如果训练被中断，最后一个 checkpoint 编号可能小于 5000。后续导出模型时，选择实际存在的 `model_*.pt` 文件。

## 9\.9 使用 play\.py 导出模型

### 9\.9\.1 checkpoint 与导出模型的区别

训练产生的 `model_5000.pt` 是 checkpoint。它保存的是训练框架中的策略参数和训练状态，主要用于继续训练、回放或导出。

部署侧需要的是 TorchScript 模型。TorchScript 模型是把策略网络和归一化处理固化后的推理模型，部署程序可以直接用 `torch.jit.load` 加载。

因此，训练结束后必须执行导出步骤，不能把训练 checkpoint 直接当作部署模型使用。

### 9\.9\.2 运行 play\.py

进入 `booster_train` 目录：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace/booster_train
```

执行导出命令。将 `<RUN_DIR>` 替换为实际训练目录名称：

```Bash
python scripts/rsl_rl/play.py \
    --task Booster-K1-CH09_Walk_Demo-v0-Play \
    --checkpoint logs/rsl_rl/ch09_walk_demo/<RUN_DIR>/model_5000.pt \
    --headless
```

如果实际只训练到 `model_3000.pt`，则把命令中的 `model_5000.pt` 改为实际存在的 checkpoint。

### 9\.9\.3 导出文件位置

导出完成后，模型位于：

```Plaintext
logs/rsl_rl/ch09_walk_demo/<RUN_DIR>/exported/
```

目录中通常会出现：

```Plaintext
ch09_walk_demo_<RUN_DIR>.pt
ch09_walk_demo_<RUN_DIR>.onnx
```

其中 `.pt` 文件是 TorchScript 模型，后续部署使用它。`.onnx` 文件可以作为模型交换格式保留，但本章部署命令使用 TorchScript。

## 9\.10 注册部署 task

### 9\.10\.1 部署侧需要哪些文件

部署侧至少需要两个文件。

第一个是动作 NPZ：

```Plaintext
booster_deploy/tasks/beyond_mimic/motions/k1_walk_demo.npz
```

第二个是导出的 TorchScript 模型：

```Plaintext
booster_deploy/tasks/beyond_mimic/models/ch09_walk_demo.pt
```

训练侧和部署侧都需要动作 NPZ，但它们处于不同工程目录中。训练侧 NPZ 用于创建训练环境，部署侧 NPZ 用于在 MuJoCo 或真机执行时提供参考动作。

### 9\.10\.2 准备部署文件

回到第 9 章工作区：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace
```

执行部署文件准备脚本。将 `<RUN_DIR>` 和 `<MODEL>` 替换为实际导出目录和模型名：

```Bash
python3 ../prepare_ch09_deploy_files.py \
    --exported_model booster_train/logs/rsl_rl/ch09_walk_demo/<RUN_DIR>/exported/<MODEL>.pt
```

脚本会完成两件事：

```Plaintext
booster_assets/motions/K1/k1_walk_demo.npz
  -> booster_deploy/tasks/beyond_mimic/motions/k1_walk_demo.npz

exported/<MODEL>.pt
  -> booster_deploy/tasks/beyond_mimic/models/ch09_walk_demo.pt
```

复制完成后，再次运行检查脚本：

```Bash
cd ..
python3 check_ch09_pipeline_resources.py
```

如果部署侧 NPZ 和模型都显示 `OK`，说明部署文件已经准备完成。

### 9\.10\.3 部署 task 配置

第 9 章部署 task 注册名为：

```Plaintext
k1_ch09_walk_demo
```

它在 `booster_deploy/tasks/beyond_mimic/__init__.py` 中注册。核心配置包括：

```Python
self.policy.motion_path = "motions/k1_walk_demo.npz"
self.policy.checkpoint_path = "models/ch09_walk_demo.pt"
```

`motion_path` 告诉部署程序读取哪个参考动作。`checkpoint_path` 告诉部署程序读取哪个 TorchScript 策略模型。

部署 task 还包含关节刚度、阻尼和力矩限制设置。这些参数会影响动作执行的刚柔程度和安全边界。第 9 章沿用适合 K1 BeyondMimic 动作部署的基础参数，不在本章展开调参。

### 9\.10\.4 列出部署 task

进入部署工程：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace/booster_deploy
```

列出部署 task：

```Bash
python scripts/deploy.py -l
```

输出中应包含：

```Plaintext
k1_ch09_walk_demo
```

如果看不到该任务，说明 `register_task("k1_ch09_walk_demo", ...)` 没有被正确加载。

## 9\.11 部署到 MuJoCo 仿真

### 9\.11\.1 为什么先部署到 MuJoCo

MuJoCo 是机器人动力学仿真器。它与 Isaac Lab 使用不同的仿真和执行链路。训练在 Isaac Lab 中完成，部署先在 MuJoCo 中运行，属于 Sim\-to\-Sim（仿真到仿真）检查。

Sim\-to\-Sim 的价值在于：如果策略只在训练环境中表现正常，但换到部署侧仿真后立刻失稳，说明模型、动作文件、观测构造或控制参数之间可能存在不一致。先在 MuJoCo 中运行，可以在不接触真机的情况下发现这类问题。

### 9\.11\.2 运行 MuJoCo

进入部署工程：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace/booster_deploy
```

运行：

```Bash
python scripts/deploy.py --task k1_ch09_walk_demo --mujoco --device cpu
```

如果模型质量有限，MuJoCo 中可能出现跟踪不稳定、步态变形或很快停止。这并不一定表示工程链路错误。第 9 章的训练轮数较少，主要目标是跑通项目流程。要提升动作质量，需要增加训练轮数、调整奖励权重、检查动作数据质量，并比较不同 checkpoint。

### 9\.11\.3 MuJoCo 中应观察什么

MuJoCo 运行时，重点观察：

- 机器人是否能够正常加载；

- 是否同时出现参考动作和策略执行动作；

- 策略执行动作是否大致跟随参考动作节奏；

- 是否一开始就发生姿态发散；

- 是否出现模型文件或 NPZ 字段读取错误；

- 动作失败时，是模型质量问题还是工程配置问题。

若运行报错 `Unknown task`，先执行 `python scripts/deploy.py -l` 确认任务是否注册。

若报错找不到 `ch09_walk_demo.pt`，说明导出的模型还没有复制到 `booster_deploy/tasks/beyond_mimic/models/`。

若报错找不到 `k1_walk_demo.npz`，说明动作文件还没有复制到 `booster_deploy/tasks/beyond_mimic/motions/`。

> 视频占位 9\-1：k1\_walk\_demo 部署到 MuJoCo 仿真的运行效果。

> （此处补充视频：\_\_\_\_\_\_\_\_\_\_）

## 9\.12 部署到 K1 真机

### 9\.12\.1 真机部署与 MuJoCo 的参数差异

同一个部署 task 可以运行在 MuJoCo，也可以运行在真机上。两者主要区别在命令参数。

MuJoCo 使用：

```Bash
python scripts/deploy.py --task k1_ch09_walk_demo --mujoco --device cpu
```

真机不加 `--mujoco`，而是通过 `--net` 指定 SDK 通信使用的网络接口：

```Bash
python scripts/deploy.py --task k1_ch09_walk_demo --net <NETWORK_INTERFACE> --device cpu
```

`<NETWORK_INTERFACE>` 需要替换为实际网络接口，例如有线网卡、机器人控制网络对应的接口名或 IP 配置中使用的接口参数。部署程序会通过 Booster SDK 与机器人通信。

### 9\.12\.2 真机运行前检查

真机运行前必须确认以下条件：

- K1 机器人电量充足；

- 机器人周围留出足够空间；

- 机器人已经处于可控站立状态；

- 部署电脑与机器人网络连通；

- 部署环境中可以导入 `booster_robotics_sdk_python`；

- 当前部署 task 已在 MuJoCo 中至少运行过一次；

- 操作者站在机器人侧后方，避免站在机器人正前方或腿部摆动路径上；

- 手可以直接触达机器人背部 `STAND` 按钮。

如果出现姿态异常、动作明显发散、脚底打滑、上身快速倾倒或机器人进入不可控动作趋势，应立即按机器人背部 `STAND` 按钮退出当前动作状态。

### 9\.12\.3 运行真机部署

进入部署工程：

```Bash
cd CourseCode/chapter_09_end_to_end_motion_learning/beyondmimic_workspace/booster_deploy
```

运行：

```Bash
python scripts/deploy.py --task k1_ch09_walk_demo --net <NETWORK_INTERFACE> --device cpu
```

真机部署时，终端可能提示等待机器人状态、初始化控制器或加载模型。确认没有报错后，再观察机器人动作。

如果终端报错 `booster_robotics_sdk_python is not installed`，说明当前环境缺少 Booster SDK 的 Python 绑定。真机部署必须在安装了 SDK Python 绑定的环境中运行。

如果机器人无响应，优先检查网络接口参数、机器人与电脑的网络连接、SDK 通信是否正常。

> 视频占位 9\-2：k1\_walk\_demo 部署到 K1 真机后的运行效果。

> （此处补充视频：\_\_\_\_\_\_\_\_\_\_）

## 9\.13 常见问题排查

### 9\.13\.1 没有 boostergmr，是否还能完成本章

可以完成。本章从已经重定向到 K1 的 `k1_walk_demo.csv` 开始。`boostergmr` 属于上游动作制作工具链，用于把 BVH、FBX、SMPL\-X 或其他人体动作数据映射到机器人关节空间。

如果需要制作全新动作，应先完成重定向，再进入本章的 CSV 到 NPZ、训练、导出和部署流程。

### 9\.13\.2 CSV 列数不对

K1 CSV 应为 29 列：

```Plaintext
7 个根部位姿字段 + 22 个 K1 关节字段
```

如果列数不对，CSV 可能不是 K1 22\-DoF 数据，或者带有 header、额外时间列、额外关节列。先用检查脚本确认列数，再进入 CSV 到 NPZ 转换。

### 9\.13\.3 CSV 转 NPZ 失败

优先检查：

- 是否在 `booster_train` 目录下运行；

- `--input_file` 是否指向真实存在的 CSV；

- `--input_fps` 是否写成了合理帧率；

- Isaac Sim 和 Isaac Lab 是否能正常启动；

- `booster_assets` 是否已安装到当前 Python 环境。

如果错误出现在导入阶段，通常是 Python 环境或 Isaac Lab 安装问题。

### 9\.13\.4 task 列表中看不到 CH09\_Walk\_Demo

检查目录是否存在：

```Plaintext
booster_train/source/booster_train/booster_train/
  tasks/manager_based/beyond_mimic/robots/k1/ch09_walk_demo/
```

检查 `__init__.py` 中是否注册：

```Plaintext
Booster-K1-CH09_Walk_Demo-v0
Booster-K1-CH09_Walk_Demo-v0-Play
```

如果 task 目录存在但仍然看不到，可能是 Python 包没有以 editable（可编辑安装）方式安装，或当前运行环境没有加载到本工作区中的 `booster_train`。

### 9\.13\.5 训练启动后马上报 motion\_file 错误

检查 `env_cfg.py` 中是否引用：

```Plaintext
k1_walk_demo.npz
```

同时确认文件已经生成在：

```Plaintext
booster_assets/motions/K1/k1_walk_demo.npz
```

CSV 文件存在不代表 NPZ 已经存在。训练读取的是 NPZ，不是 CSV。

### 9\.13\.6 TensorBoard 没有曲线

确认训练命令中包含：

```Bash
--logger tensorboard
```

确认 TensorBoard 指向正确目录：

```Bash
tensorboard --logdir logs/rsl_rl/ch09_walk_demo --port 6006
```

如果刚启动训练不久，曲线可能还没有写入足够数据。等待训练运行一段时间后刷新页面。

### 9\.13\.7 找不到 checkpoint

checkpoint 位于：

```Plaintext
booster_train/logs/rsl_rl/ch09_walk_demo/<RUN_DIR>/
```

如果训练未达到保存间隔，可能还没有生成 `model_*.pt`。第 9 章默认配置按一定间隔保存模型，训练到 5000 轮通常应出现 `model_5000.pt`。

### 9\.13\.8 exported 目录没有生成

确认执行的是 `play.py`，不是 `train.py`。

确认 `--checkpoint` 指向真实存在的 checkpoint 文件。

确认 `--task` 使用的是 play task：

```Plaintext
Booster-K1-CH09_Walk_Demo-v0-Play
```

如果使用训练 task 导出，可能会受到训练环境扰动影响，不利于稳定回放和导出。

### 9\.13\.9 deploy\.py 看不到 k1\_ch09\_walk\_demo

进入 `booster_deploy` 后运行：

```Bash
python scripts/deploy.py -l
```

如果列表中没有 `k1_ch09_walk_demo`，检查 `booster_deploy/tasks/beyond_mimic/__init__.py` 中是否调用：

```Python
register_task("k1_ch09_walk_demo", K1CH09WalkDemoControllerCfg())
```

部署 task 注册成功后，`deploy.py -l` 才能列出它。

### 9\.13\.10 真机部署缺少 SDK

如果真机部署时报错：

```Plaintext
booster_robotics_sdk_python is not installed
```

说明当前环境没有安装 Booster SDK 的 Python 绑定。MuJoCo 仿真不需要该绑定，但真机部署必须安装。

### 9\.13\.11 真机运行时动作不稳定

动作不稳定不一定是部署命令错误。常见原因包括：

- 训练轮数过少；

- 动作数据本身不适合 K1 稳定执行；

- reward（奖励）权重不适合该动作；

- checkpoint 选择过早；

- MuJoCo 中已经表现出明显不稳定；

- 真机地面摩擦、初始姿态、电池电量和通信延迟影响执行。

如果动作在 MuJoCo 中已经明显失败，不应直接上真机。若真机执行时出现失稳趋势，按机器人背部 `STAND` 按钮退出当前动作状态。

## 9\.14 本章小结

本章完成了动作生成模块的综合项目闭环。学习者从一个已经完成 K1 重定向的 CSV 文件开始，依次完成 CSV 到 NPZ 转换、新建 BeyondMimic 训练 task、启动短轮次训练、查看 TensorBoard 看板、使用 checkpoint 导出 TorchScript 模型、注册部署 task、运行 MuJoCo 仿真和进入 K1 真机部署。

这条链路体现了动作学习项目的核心工程逻辑：动作数据必须先进入机器人关节空间，再转换为训练系统需要的多数组格式；训练 task 把机器人模型、动作文件、观测、奖励和 PPO 配置组织在一起；训练结果不能直接部署，需要通过 play\.py 导出；部署侧还需要把动作文件和导出模型重新注册到执行框架中。

第 6 章解决“动作数据是什么”，第 7 章解决“为什么要训练以及如何训练”，第 8 章解决“模型如何部署执行”，第 9 章则把这些步骤组合成一个可运行的动作学习项目。完成本章后，学习者已经具备从一个 K1 动作文件出发，构建完整动作学习与部署流程的工程理解。

