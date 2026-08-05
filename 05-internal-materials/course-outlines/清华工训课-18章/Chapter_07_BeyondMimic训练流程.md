# Chapter\_07\_BeyondMimic训练流程

# Chapter 07｜BeyondMimic 训练流程

Chapter 6 已经把动作学习的数据层讲清楚：动作可以来自动捕、遥操、示教、视频或已有数据集；来源动作经过重定向后得到 K1 CSV；CSV 再转换为 NPZ，成为训练系统可以读取的 motion file（动作文件）。进入 Chapter 7 后，问题变成：有了 NPZ 动作数据，如何训练出一个能够在仿真中跟踪动作的策略模型。

本章围绕 BeyondMimic（动作模仿训练框架）展开，在 Isaac Lab（机器人强化学习训练框架）中创建仿真环境，让机器人通过强化学习方式学习参考动作。训练完成后，系统会生成 checkpoint（检查点）文件，作为后续模型导出、MuJoCo 验证和真机部署的基础。

本章先解释为什么需要训练、BeyondMimic 是什么、训练需要什么、训练会产出什么；再进入实践流程：搭建电脑端训练环境，安装 Booster 动作学习工程，确认 MJ 动作 NPZ，使用 `MJ_Dance_002` 训练 task，启动 `train.py`，查看日志和 checkpoint。

模型导出、MuJoCo 中的 Sim\-to\-Sim（仿真到仿真验证）以及真机 Sim\-to\-Real（仿真到真实迁移）放到 Chapter 8 中。

## 7\.1 为什么需要训练

### 7\.1\.1 第 6 章得到的 NPZ 还不是控制策略

第 6 章中的 NPZ 文件是记录了参考动作的数据集合，它包含帧率、关节位置、关节速度、身体部件位置、身体部件姿态等字段。

NPZ 文件不是控制策略（模型），它无法指导机器人根据当前状态预测下一步对于各关节的控制参数是什么，也不会处理仿真中的扰动、身体偏差、接触变化和姿态误差。

对动作学习系统来说，我们需要的是一个基于 NPZ 数据文件训练的 policy（策略模型）。策略模型可以根据机器人当前 observation（观测），输出 action（动作输出）。这里的 action 是一组数值，这组数值即为机器人各关节的控制参数。

### 7\.1\.2 轨迹回放与策略控制的区别

**轨迹回放**和**策略控制**都能让机器人表现出动作，但它们的原理不同。

- 轨迹回放是按固定顺序播放已记录的关节状态。Chapter 5 的示教回放就是典型例子。

- 策略控制则是策略模型根据当前机器人状态对下一步控制量的预测。机器人当前姿态、速度、参考动作相位和身体偏差都会影响策略模型的输出。因此，策略模型不是“播放动作”，而是在仿真环境中学会了如何控制机器人持续做出动作。

可以用下面的方式区分两者：

```Plaintext
轨迹回放:
参考轨迹文件 -> 按时间顺序播放 -> 机器人执行

策略控制:
机器人当前状态 + 参考动作信息 -> 策略模型 -> 控制输出 -> 机器人状态更新
```

动作生成系统最终要得到的是能够参与部署链路的策略模型。

### 7\.1\.3 训练要解决的问题

训练要解决三个核心问题。

第一，如何让机器人动作接近参考动作。NPZ 提供了参考动作，训练过程会不断比较机器人当前状态与参考状态之间的误差，让策略模型的精度越来越高。

第二，如何让动作在物理仿真中可执行。人体动作或重定向轨迹在数据上看起来合理，不代表机器人在物理环境中一定能保持稳定。训练过程会在仿真中考虑重力、接触、关节限制、姿态变化等因素。

第三，如何得到可继续导出和部署的模型。训练过程会周期性保存 checkpoint。后续 Chapter 8 会使用 checkpoint 导出 TorchScript 或 ONNX 模型，并进入 MuJoCo 和真机执行流程。

因此，本章的训练目标可以概括为：

```Plaintext
输入: K1 NPZ 参考动作
过程: BeyondMimic 在 Isaac Lab 中训练策略
输出: checkpoint 策略参数
```

## 7\.2 BeyondMimic 框架是什么

### 7\.2\.1 BeyondMimic 在动作学习链路中的位置

BeyondMimic 是动作生成主线中的训练框架。它位于“动作数据已经准备好”和“模型可以部署执行”之间。

```Plaintext
K1 NPZ 动作数据
  ↓
BeyondMimic 训练
  ↓
checkpoint
  ↓
模型导出
  ↓
MuJoCo 仿真验证
  ↓
K1 真机执行
```

> 第 6 章关注 NPZ 是怎么来的，以及 NPZ 里有什么。第 7 章关注 BeyondMimic 如何读取 NPZ 并训练策略模型。第 8 章关注 checkpoint 如何导出并进入仿真和真机执行。
> 
> 

### 7\.2\.2 BeyondMimic 的核心思想

BeyondMimic 的核心思想是：用 Reinforcement Learning（强化学习）的训练流程，实现 Imitation Learning（模仿学习）的动作目标。

- 模仿学习强调“像参考动作”。如果机器人当前关节位置、身体部件位置和姿态越接近参考动作，训练目标就越好。

- 强化学习强调“在环境中反复尝试并根据奖励改进策略”。机器人在仿真环境中执行策略，环境根据动作跟踪效果、姿态稳定性、接触情况等计算 reward（奖励），训练算法再根据奖励更新策略模型。

- BeyondMimic 把这两件事结合起来：参考动作来自 NPZ，训练过程通过奖励函数鼓励机器人跟踪参考动作，同时利用仿真物理环境约束机器人动作，使训练结果更接近可执行策略。

### 7\.2\.3 BeyondMimic 依赖哪些软件和框架

BeyondMimic 训练不是一个单独 Python 文件能完成的任务。它依赖一组软件和工程组件。

|名称|作用|
|---|---|
|Ubuntu|训练电脑的操作系统环境|
|NVIDIA Driver|NVIDIA 显卡驱动，让系统识别和调用 GPU|
|CUDA|GPU 并行计算平台，供 PyTorch 调用显卡算力|
|Conda|Python 环境隔离工具|
|uv|Python 项目依赖管理工具，常用于 `boostergmr`|
|PyTorch|深度学习计算框架，负责神经网络训练|
|Isaac Sim|NVIDIA 机器人仿真平台|
|Isaac Lab|基于 Isaac Sim 的机器人强化学习训练框架|
|PPO|Proximal Policy Optimization，近端策略优化算法|
|booster\_assets|K1 机器人模型、关节顺序和动作数据资源|
|booster\_train|K1 的 BeyondMimic 训练工程|
|booster\_deploy|后续 MuJoCo 和真机部署相关工程|
|boostergmr|动作重定向工程，用于将 BVH/SMPL\-X 等来源动作转换为机器人动作|
|TOOLs|CSV 清洗和格式整理工具|

这些组件分工明确。显卡驱动、CUDA、PyTorch 解决计算问题；Isaac Sim 和 Isaac Lab 解决仿真训练问题；Booster 相关工程解决 K1 模型、动作数据、训练任务和后续部署问题。

## 7\.3 训练需要什么

### 7\.3\.1 硬件条件

BeyondMimic 训练需要一台带 NVIDIA GPU 的 x86 电脑或工作站。训练通常不在 K1 机器人板载计算单元上完成，因为强化学习训练需要大量并行仿真和神经网络更新，计算负载远高于普通机器人控制程序。

推荐硬件条件如下：

|项目|建议配置|
|---|---|
|CPU 架构|x86\_64|
|操作系统|Ubuntu 桌面系统|
|GPU|NVIDIA GPU|
|推荐显卡|RTX 4090 级别显卡|
|显存|24 GB 级别更适合完整训练|
|磁盘空间|预留足够空间安装 Isaac Sim、Isaac Lab、工程包、日志和模型|

如果使用 NVIDIA 50 系显卡，需要额外确认 PyTorch、CUDA、Isaac Sim 和 Isaac Lab 版本是否支持对应显卡架构。显卡、驱动、CUDA 和 PyTorch 之间的版本匹配，是训练环境中最容易出问题的部分之一。

### 7\.3\.2 软件环境

本章目标训练环境采用以下软件组合：

|软件|本章目标版本或要求|
|---|---|
|Ubuntu|桌面系统|
|NVIDIA Driver|`nvidia-driver-595`|
|Python|3\.11|
|PyTorch|`torch==2.7.0`|
|torchvision|`torchvision==0.22.0`|
|CUDA wheel|`cu128`|
|Isaac Sim|`isaacsim[all,extscache]==5.1.0`|
|Isaac Lab|`isaaclab[isaacsim,all]`|

这些版本要整体理解，而不是孤立安装。PyTorch 的 CUDA 版本要能使用当前显卡驱动，Isaac Lab 又依赖 Isaac Sim 运行仿真训练。版本不匹配时，常见表现包括 CUDA 不可用、Isaac Sim 无法启动、训练脚本在导入阶段报错，或者训练开始后仿真异常退出。

### 7\.3\.3 训练工程

本章配套代码目录中已经整理出一个可用于训练实践的 BeyondMimic 工作区：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/
  training_environment_check.py
  check_beyondmimic_workspace.py
  beyondmimic_workspace/
    booster_assets/
    booster_train/
    booster_deploy/
    TOOLs/
```

训练实践从 `beyondmimic_workspace/` 进入。该工作区只保留 MJ 动作训练主线：

```Plaintext
beyondmimic_workspace/
  booster_assets/
    motions/K1/k1_mj2_seg1.npz
  booster_train/
    source/booster_train/booster_train/tasks/manager_based/beyond_mimic/robots/k1/mj_dance_002/
  booster_deploy/
    tasks/beyond_mimic/models/k1_mj_dance_002_2025-12-03_00-10-28.pt
  TOOLs/
```

`booster_assets` 存放 K1 机器人模型、关节顺序和动作资源。训练任务需要从这里读取机器人模型和 motion file。

`booster_train` 存放 BeyondMimic 训练任务、环境配置、奖励配置和训练脚本。`train.py` 就在这个工程中。

`booster_deploy` 用于后续部署和 MuJoCo 验证。本章保留了 MJ 动作对应的已训练 checkpoint，为 Chapter 8 做准备。

`boostergmr` 用于动作重定向，例如从 BVH 或 SMPL\-X 转换到 K1 机器人动作。它属于上游数据处理工具，本章训练实践不重新执行重定向，而是直接使用已经整理好的 MJ 动作 NPZ。

`TOOLs` 用于 CSV 清洗和格式整理，例如把重定向输出整理为 Booster 训练流程需要的 CSV。

### 7\.3\.4 动作数据

训练输入是第 6 章处理后的 `.npz` 文件，而不是原始 BVH，也不是还未整理的 CSV。本章实践只使用 MJ 动作：

```Plaintext
k1_mj2_seg1.npz
```

其他动作文件即使文件名相近，也不一定满足训练任务的字段、关节数量、身体部件数量和时间尺度要求。训练实践不要随意替换 motion file。

典型数据流程如下：

```Plaintext
BVH / SMPL-X / 其他来源动作
  ↓
boostergmr 重定向
  ↓
K1 CSV
  ↓
TOOLs 清洗 CSV
  ↓
csv_to_npz.py 转换
  ↓
K1 NPZ
  ↓
BeyondMimic 训练
```

NPZ 中的 `joint_pos`、`joint_vel`、`body_pos_w`、`body_quat_w` 等字段会作为参考动作被训练任务读取。

### 7\.3\.5 训练任务配置

BeyondMimic 训练还需要 task（训练任务）配置。task 不是普通文件名，而是 Isaac Lab 中注册的训练环境 ID。一个 task 会把机器人模型、动作文件、观测项、奖励项、仿真环境和 PPO 参数组织到一起。

一个可训练 task 至少需要明确：

- 使用哪个机器人模型；

- 加载哪个 NPZ motion file；

- 跟踪哪些身体部件；

- 使用哪些 observation；

- 使用哪些 reward；

- 训练多少 iterations；

- 日志和 checkpoint 存在哪里。

## 7\.4 训练会产出什么

### 7\.4\.1 checkpoint

训练最重要的产物是 checkpoint。checkpoint 通常是 `model_*.pt` 文件，保存策略网络在某个训练阶段的参数。

例如：

```Plaintext
model_9999.pt
model_19999.pt
model_29999.pt
```

编号通常表示训练迭代进度。编号越大，代表训练轮次越靠后，但不一定绝对代表效果最好。后续仍然需要结合训练曲线和动作执行效果判断。

### 7\.4\.2 训练日志

训练日志通常保存在：

```Plaintext
booster_train/logs/rsl_rl/<experiment_name>/<timestamp>/
```

其中 `<experiment_name>` 来自 `ppo_cfg.py` 中的 `experiment_name`，`<timestamp>` 是启动训练时生成的时间戳目录。

日志中会保存训练配置、运行信息和 checkpoint。训练时终端也会持续输出 iteration（迭代次数）、reward（奖励）、episode length（回合长度）、loss（损失）等信息。

### 7\.4\.3 导出模型

checkpoint 还不是最终部署格式。训练完成后，需要使用 `play.py` 加载 checkpoint，并导出 TorchScript 或 ONNX 模型。

TorchScript 是 PyTorch 模型的可部署表示；ONNX 是 Open Neural Network Exchange 的缩写，通常译为开放神经网络交换格式。它们的详细作用和导出过程放到 Chapter 8。

### 7\.4\.4 训练结果与真机执行的关系

checkpoint 不等于真机可直接执行的动作。完整链路还需要：

```Plaintext
checkpoint
  ↓
导出模型
  ↓
MuJoCo Sim-to-Sim 验证
  ↓
真机 Sim-to-Real 执行
```

因此，第 7 章的完成标准不是“机器人已经在真机上动起来”，而是完成从 NPZ 到 checkpoint 的训练闭环。

## 7\.5 实践总览：从环境到训练结果

### 7\.5\.1 本章实践流程

本章实践按下面顺序展开：

```Plaintext
搭建电脑训练环境
  ↓
安装 Booster 动作学习工程
  ↓
确认 MJ 动作 NPZ
  ↓
确认 MJ_Dance_002 训练 task
  ↓
运行 train.py
  ↓
查看 logs 和 checkpoint
```

这条流程中，环境搭建是基础，MJ 动作 NPZ 是训练输入，`Booster-K1-MJ_Dance_002-v0` 是训练 task，`train.py` 是训练入口，checkpoint 是本章输出。

### 7\.5\.2 实践完成标准

完成本章实践后，应达到以下状态：

- `nvidia-smi` 能识别 NVIDIA GPU；

- Conda 训练环境已经创建并激活；

- Python 版本为 3\.11；

- PyTorch 能检测到 CUDA；

- Isaac Sim 和 Isaac Lab 可导入；

- `booster_assets` 和 `booster_train` 已安装；

- `check_beyondmimic_workspace.py` 能确认 MJ 动作训练资源齐全；

- `list_envs.py` 能列出 `Booster-K1-MJ_Dance_002-v0`；

- `train.py` 能启动训练；

- `logs/rsl_rl/...` 中生成 `model_*.pt` checkpoint。

## 7\.6 电脑训练环境搭建

### 7\.6\.1 安装 NVIDIA 显卡驱动

在 Ubuntu 电脑上先安装 NVIDIA 显卡驱动。本章目标环境使用：

```Bash
sudo apt update
sudo apt install nvidia-driver-595
sudo reboot
```

重启后验证：

```Bash
nvidia-smi
```

如果命令能够显示显卡型号、驱动版本和显存信息，说明驱动基本可用。如果提示命令不存在或无法连接驱动，需要先处理显卡驱动问题，再继续安装 PyTorch 和 Isaac Lab。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzRlMGI1M2NkMDM3MWU5YmRlMWEwNjM0ZDU2NDdlNTJfNGQxZTdiZDI4MWViMzgwZTFkYTY0ZDhhMjhmMjc3MjFfSUQ6NzY2MjIwNTQ1MjEzMDU4NTU2NF8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.6\.2 安装 Miniconda

Miniconda 用于创建独立 Python 环境，避免把训练依赖安装到系统 Python 中。

下载安装脚本：

```Bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

添加执行权限并安装：

```Bash
chmod +x Miniconda3-latest-Linux-x86_64.sh
bash ./Miniconda3-latest-Linux-x86_64.sh
```

安装完成后重新加载 shell 配置：

```Bash
source ~/.bashrc
```

验证：

```Bash
conda --version
```

如果 `conda` 命令不存在，需要检查 Miniconda 安装目录是否加入 `PATH`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2M1NWFjYWQ2MzNjOWNmNTU0ODgwMWMzMWQxYWVmYWFfMmMxODQ3ZTgyNWY5MTA2N2E5NjI1YzZjMzQyMWU1ZGVfSUQ6NzY2MjIwNTU5NDY2MDQ5MDIxMl8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.6\.3 安装 uv

`uv` 是 Python 项目依赖管理工具。本章中，`boostergmr` 的依赖同步和命令运行会用到它。

安装：

```Bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装后重新加载 shell，或按终端提示加载 `uv` 的环境脚本。验证：

```Bash
uv --version
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTdmOWQ0NWU3NTE3NGMxNTkxYWRlMGRjYzRhZDZlZDhfZWI4ODgyMmM0MDRlZWQ4NjM1NDU5NWUzOWFkYWUyMzdfSUQ6NzY2MjIwNjA2MDI0NTg0NzI1OF8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.6\.4 创建 Python 3\.11 环境

创建并激活训练环境：

```Bash
conda create -n booster_train python=3.11
conda init
source ~/.bashrc
conda activate booster_train
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MmM3NzUwMzIwMmM5OTQ0ZTcxOWFmMTlmMzFiNDQxYjVfYzdiY2E2MTFkNWVkMTRlMzg2YjE4YTdhYzBlMWNhODBfSUQ6NzY2MjIwNjk4MjQxODQ1MTcyOF8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MGQxNzU4MjgzNmU5YWM0MTA2NGRmNGQzOTEwZDM0MDVfYjBjNjI0NDg5OWU4OTgzYTc5NWI5OTBlMzYyZDczMzhfSUQ6NzY2MjIwNzE1NzcyNzQ4MTA5N18xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

后续 PyTorch、Isaac Sim、Isaac Lab、Booster 训练工程都在这个环境中安装和运行。每次重新打开终端后，都需要先执行：

```Bash
conda activate booster_train
```

### 7\.6\.5 安装 PyTorch

安装 PyTorch 和 torchvision：

```Bash
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

验证 PyTorch 和 CUDA：

```Bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

如果输出中 `torch.cuda.is_available()` 为 `True`，说明 PyTorch 能调用 GPU。如果为 `False`，需要检查显卡驱动、PyTorch CUDA wheel 和当前 Conda 环境。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWFiNzc4MWZiODllMzMzNmQ5MWIzZmEwYWVkMzIwYzVfZGQzYTU0MWQ4YTcwNmM1ZDYxMWVmODA5YjAyZTFjZWNfSUQ6NzY2MjIwNzY5MTA2MjIxODAyOF8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.6\.6 安装 Isaac Sim 与 Isaac Lab

安装 Isaac Sim：

```Bash
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com
```

安装 Isaac Lab：

```Bash
pip install isaaclab[isaacsim,all] --extra-index-url https://pypi.nvidia.com
```

验证导入：

```Bash
python -c "import isaacsim; import isaaclab; print('isaac ok')"
```

Isaac Sim 和 Isaac Lab 体积较大，安装时间可能较长。安装过程中如果网络中断或依赖失败，需要先解决 Python 包安装问题，再继续训练工程安装。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTY4ZTMxMzE4NzkyNDlmNmJmYmU0NTQ4MGQ0NDFiNGVfMDg0Nzg4OTJkYzFiM2YyYTlkZDYwYmQ1ZWVjYzMzYTlfSUQ6NzY2MjIwOTM4MzE1ODAwOTA5N18xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.6\.7 验证环境

在继续安装 Booster 工程前，可以先做一次基础检查：

```Bash
python --version
conda info --envs
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
python -c "import isaacsim; import isaaclab; print('ok')"
```

这些命令通过后，说明电脑端训练基础环境已经具备。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yjk1NTFmNGRhNWIzNGRmZTUwYzg3NWJmNjkyNThjNGFfMzMzNmJjNTBkM2Y5Y2MyMDQ0MzUxMzk5MWI0NWQ5MTVfSUQ6NzY2MjIwOTYyMzA0NDI3OTUwMV8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzNiOGU5NGI1YjgzN2ZlZmQzOTZhMTEyNzU2NWQxZTBfMjIwMGVmMjc4MmJhYjk0NmQxOWQ4NTU0MzY3OWRhNzBfSUQ6NzY2MjIwOTkwMjUyNjEwNjU3NV8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZmI3Y2VmNGYzYjI5MjM3ZWI1ODQ0YmIyNzk0MTZiZjdfMTk4Y2I0MDA5MmNmMmZkNGNkMzM1ODc3MzQ0MmRlOGVfSUQ6NzY2MjIwOTk4ODExOTYyOTA5Ml8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

## 7\.7 安装 Booster 动作学习工程

本章训练工程已经放在：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/
```

后续命令都从这个工作区进入。每次打开新终端后，先激活训练环境，再进入本章工作区：

```Bash
conda activate booster_train
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace
```

### 7\.7\.1 安装 booster\_assets

`booster_assets` 存放机器人模型、K1 关节顺序和动作资源。训练任务需要通过它找到 K1 的机器人模型和 motion file。

进入工程目录并安装：

```Bash
cd booster_assets
python -m pip install -e .
```

`-e` 表示 editable install，即可编辑安装。这样在工程目录中修改资源或 Python 包后，当前环境可以直接使用更新后的内容。

### 7\.7\.2 安装 booster\_train

`booster_train` 是本章训练的核心工程，包含 Isaac Lab 训练任务、BeyondMimic 配置、PPO 配置和训练脚本。

安装：

```Bash
cd ../booster_train
python -m pip install -e source/booster_train
```

验证：

```Bash
cd ..
python -c "import booster_train; print('booster_train ok')"
```

如果无法导入，通常是当前 Conda 环境不对，或者安装命令没有在 `booster_train` 工程目录下执行。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTg1ODg2NTQxZjZlNDE1ZWI3NTM4OTA3NzE0OGUyNTdfNmU3OGQyNGM1MTAzNjE0NGMyYjAxZTZkMTdkMmI1ZThfSUQ6NzY2MjIxMDU0MTY1NDMzMDM0OV8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.7\.3 安装 booster\_deploy

`booster_deploy` 用于 Chapter 8 的 MuJoCo 验证和真机部署。本章先完成依赖安装，后续再使用。

安装：

```Bash
cd booster_deploy
python -m pip install -r requirements.txt
```

### 7\.7\.4 检查本章 MJ 训练资源

本章配套代码提供了资源检查脚本，用于确认 `beyondmimic_workspace` 中的 MJ 动作文件、训练 task 和后续章节使用的 checkpoint 是否齐全。

回到本章代码目录：

```Bash
cd ../..
python3 check_beyondmimic_workspace.py
```

检查通过时，会看到 MJ 动作训练资源齐全的提示。该脚本不会导入 Isaac Lab，也不会启动训练，因此可以在正式训练前快速排查缺文件问题。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGNjMGUwODgxZjYwMzZiZDA5NjA1OTQ0ODA5MzY1N2VfMDFkMWRhMDk0MzRhNDI2NGU4NGE2OWNhZDE0NzQ2YjJfSUQ6NzY2MjIxMTA0NTAwODAwMjMzM18xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.7\.5 准备 TOOLs

`TOOLs` 用于清洗和转换重定向输出的 CSV，使其符合 Booster 训练流程需要的格式。本章训练实践直接使用已经准备好的 `k1_mj2_seg1.npz`，不需要重新从 BVH 开始重定向；`TOOLs` 保留为动作数据处理工具，便于理解 CSV 到 NPZ 的上游流程。

### 7\.7\.6 play\.py 已知兼容性修改

后续 Chapter 8 会使用 `booster_train/scripts/rsl_rl/play.py` 加载 checkpoint 并导出模型。部分工程版本中，`play.py` 的预训练 checkpoint 分支可能影响显式 `--checkpoint` 的使用。如果后续导出阶段出现 checkpoint 读取异常，需要让 `play.py` 以显式传入的 `--checkpoint` 为准，避免进入预训练 checkpoint 分支。

第 7 章只记录这个注意点，不展开模型导出。模型导出属于 Chapter 8。

安装完成后，工作区中的关键文件应保持如下位置：

```Plaintext
beyondmimic_workspace/
  booster_assets/motions/K1/k1_mj2_seg1.npz
  booster_train/source/booster_train/booster_train/tasks/manager_based/beyond_mimic/robots/k1/mj_dance_002/
  booster_deploy/tasks/beyond_mimic/models/k1_mj_dance_002_2025-12-03_00-10-28.pt
```

## 7\.8 训练数据准备

### 7\.8\.1 本章只使用 MJ 动作 NPZ

本章训练实践只使用一个动作文件：

```Plaintext
beyondmimic_workspace/booster_assets/motions/K1/k1_mj2_seg1.npz
```

这个文件已经完成从来源动作到 K1 训练数据的处理，可以直接被 `mj_dance_002` task 加载。很多动作文件虽然同样是 `.npz` 后缀，但并不一定满足 K1 训练任务要求，例如字段不全、关节数量不一致、身体部件数量不一致、帧率不匹配或重定向结果不稳定。因此，本章不要把其他动作文件替换到 `motion_file` 中。

MJ 动作对应的训练任务是：

```Plaintext
Booster-K1-MJ_Dance_002-v0
```

它在 `env_cfg.py` 中引用的动作文件是：

```Python
self.commands.motion.motion_file = f"{BOOSTER_ASSETS_DIR}/motions/K1/k1_mj2_seg1.npz"
```

这条引用关系非常重要。`train.py` 并不是直接读取命令行中的 NPZ 文件名，而是通过 task 配置间接找到 motion file。

### 7\.8\.2 MJ 动作 NPZ 是怎么来的

从完整动作学习流程看，MJ 动作 NPZ 的上游处理仍然遵循 Chapter 6 中介绍的数据链路：

```Plaintext
来源动作
  ↓
重定向到 K1
  ↓
K1 CSV
  ↓
CSV 清洗与关节顺序整理
  ↓
CSV 转 NPZ
  ↓
k1_mj2_seg1.npz
```

重定向的意义是把人体或其他来源动作映射到 K1 的身体比例、关节自由度和关节顺序上。CSV 清洗的意义是让数据列顺序、根部位姿和关节角格式符合 K1 训练流程。CSV 转 NPZ 的意义是把逐帧表格数据转换为训练环境可快速读取的数组结构。

本章实践不重新执行这些上游步骤。训练重点是理解 BeyondMimic 如何加载一个已经准备好的 K1 NPZ，并训练出 checkpoint。

### 7\.8\.3 检查 MJ 动作 NPZ

可以使用 Chapter 6 的检查脚本查看 MJ 动作 NPZ：

```Bash
python3 CourseCode/chapter_06_motion_data/inspect_motion_data.py CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_assets/motions/K1/k1_mj2_seg1.npz
```

至少要确认 NPZ 包含：

- `fps`;

- `joint_pos`;

- `joint_vel`;

- `body_pos_w`;

- `body_quat_w`;

- `body_lin_vel_w`;

- `body_ang_vel_w`。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MTliZjFhZjRmMzNjOGI0NWQwNDFlNjY4NDE3NTMyZWJfZDg5MmQxNTBlZjZjZjM1NmU4NmRiN2FmODJmMzM5NjVfSUQ6NzY2MjIxMzI0MDExMDc0Njg1NF8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

在本章代码目录中，也可以运行：

```Bash
cd CourseCode/chapter_07_beyondmimic_training
python3 check_beyondmimic_workspace.py
```

这个脚本会检查 MJ 动作 NPZ 的核心字段、`mj_dance_002` task 配置和后续章节使用的已训练 checkpoint。

## 7\.9 确认 MJ\_Dance\_002 训练任务

### 7\.9\.1 task 是什么

task 是 Isaac Lab 中注册的训练环境 ID。训练命令中的 `--task` 必须与注册 ID 完全一致。

本章使用的 train task 是：

```Plaintext
Booster-K1-MJ_Dance_002-v0
```

对应的 play task 是：

```Plaintext
Booster-K1-MJ_Dance_002-v0-Play
```

train task 用于训练，play task 用于后续播放、检查或导出。第 7 章执行训练时使用 train task，不使用 play task。

### 7\.9\.2 MJ task 目录

MJ 动作的 BeyondMimic 训练任务配置位于：

```Plaintext
booster_train/source/booster_train/booster_train/tasks/manager_based/beyond_mimic/robots/k1/mj_dance_002/
```

一个任务目录通常包含：

```Plaintext
__init__.py
env_cfg.py
ppo_cfg.py
tracking_env_cfg.py
```

本章重点关注前三个文件。

### 7\.9\.3 查看 `__init__.py`

`__init__.py` 负责注册 task。一个任务通常注册两个 ID：训练用 ID 和 play 用 ID。

MJ 动作的注册结构如下：

```Python
gym.register(
    id="Booster-K1-MJ_Dance_002-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:RoughWoStateEstimationEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.ppo_cfg:PPORunnerCfg",
    },
)

gym.register(
    id="Booster-K1-MJ_Dance_002-v0-Play",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:PlayFlatWoStateEstimationEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.ppo_cfg:PPORunnerCfg",
    },
)
```

训练命令使用第一个 ID，后续导出或播放时使用第二个 ID。两个名称必须记录清楚，并在命令中保持一致。

### 7\.9\.4 查看 `env_cfg.py`

`env_cfg.py` 负责训练环境配置。关键字段包括：

```Python
self.scene.robot = ROBOT_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
self.actions.joint_pos.scale = K1_ACTION_SCALE
self.commands.motion.motion_file = f"{BOOSTER_ASSETS_DIR}/motions/K1/k1_mj2_seg1.npz"
self.commands.motion.anchor_body_name = "Trunk"
self.commands.motion.body_names = [
    "Trunk",
    "Head_2",
    "Left_Hip_Roll",
    "Left_Shank",
    "left_foot_link",
    "Right_Hip_Roll",
    "Right_Shank",
    "right_foot_link",
    "Left_Arm_2",
    "Left_Arm_3",
    "left_hand_link",
    "Right_Arm_2",
    "Right_Arm_3",
    "right_hand_link",
]
```

其中：

- `ROBOT_CFG` 指定 K1 机器人模型；

- `K1_ACTION_SCALE` 指定动作输出缩放；

- `motion_file` 指向本章唯一使用的 MJ 动作 NPZ；

- `anchor_body_name` 指定动作跟踪的锚定身体部件，常用 `Trunk`；

- `body_names` 指定参与动作跟踪的身体部件。

如果 `motion_file` 路径错误，训练任务启动时会找不到动作文件。如果 `body_names` 与机器人模型中的身体部件名称不一致，训练环境也可能创建失败。

### 7\.9\.5 查看 `ppo_cfg.py`

`ppo_cfg.py` 负责 PPO 训练配置。常见结构如下：

```Python
from isaaclab.utils import configclass
from booster_train.tasks.manager_based.beyond_mimic.agents.rsl_rl_ppo_cfg import BasePPORunnerCfg


@configclass
class PPORunnerCfg(BasePPORunnerCfg):
    max_iterations = 30000
    experiment_name = "k1_mj_dance_002"
```

其中：

- `max_iterations` 是最大训练迭代次数；

- `experiment_name` 是实验名称，也会影响日志目录名称。

完整训练可能需要数万次迭代。第一次检查环境和 task 是否能跑通时，可以通过训练命令临时覆盖较小迭代次数，例如 `--max_iterations 10`。确认流程正常后，再执行完整训练。

### 7\.9\.6 train task 与 play task 的区别

train task 通常使用更适合训练的环境配置，例如粗糙地形、随机扰动或更完整的训练设置。play task 通常用于播放、检查和后续导出，环境更接近平坦展示或部署前验证。

第 7 章训练命令使用 train task：

```Plaintext
Booster-K1-MJ_Dance_002-v0
```

Chapter 8 导出模型时使用 play task：

```Plaintext
Booster-K1-MJ_Dance_002-v0-Play
```

不要把两者混用。task 不一致可能导致观测维度、动作维度或归一化参数不匹配。

## 7\.10 启动训练

### 7\.10\.1 查看可用任务

进入 `booster_train`：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_train
```

查看已注册任务：

```Bash
python scripts/list_envs.py
```

确认 `Booster-K1-MJ_Dance_002-v0` 已经出现在输出中。如果任务没有出现，优先检查：

- 任务目录是否放在正确位置；

- `__init__.py` 是否注册了 task；

- Python 包是否重新安装或可被当前环境发现；

- task 名称是否拼写正确。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzUyZGUwMmI1Y2I5ZGUyYmZmZjYzMjhkY2Q2NDA1ZmJfMmJiMThhNzgzY2UyZGNmYmYzYzdiMmRkZjNmNzYyN2ZfSUQ6NzY2MjIxNDExNjE5NTMzOTU1Nl8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.10\.2 运行训练命令

启动训练：

```Bash
python scripts/rsl_rl/train.py --task=Booster-K1-MJ_Dance_002-v0 --device cuda:0 --headless
```

如果只是检查训练能否启动，可以先限制迭代次数：

```Bash
python scripts/rsl_rl/train.py --task=Booster-K1-MJ_Dance_002-v0 --device cuda:0 --headless --max_iterations 10
```

短训练只能验证流程能否跑通，不能代表动作已经训练完成。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NWE5YjA1MTcxOTYwM2Q1ZTk2MTZkZGE0ZjhjMGYxNGNfMjQxYjZjZjM1ZTNiNzMyMThmZDcwODQ3MWY0MWE2Y2FfSUQ6NzY2MjIxNDYyMTQwMTAyNTcxNV8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.10\.3 参数含义

`--task` 指定训练任务 ID。它必须与 `__init__.py` 中注册的 train task 完全一致。

`--device cuda:0` 指定使用第 0 块 NVIDIA GPU。如果电脑有多块显卡，可以使用 `cuda:1`、`cuda:2` 等编号。

`--headless` 表示不打开图形界面。训练通常耗时较长，关闭图形界面可以减少显示开销，提高训练效率。

`--max_iterations` 用于覆盖 `ppo_cfg.py` 中的最大训练迭代次数，适合做短流程检查。

### 7\.10\.4 训练过程会看到什么

训练启动后，Isaac Lab 会创建仿真环境，RSL\-RL 会创建策略训练器。终端会持续输出训练信息。

常见指标包括：

|指标|含义|
|---|---|
|`iteration`|当前训练迭代次数|
|`reward`|奖励，反映策略表现|
|`episode length`|回合长度，反映机器人能维持动作的时间|
|`loss`|神经网络训练损失|
|`time`|训练耗时|

训练初期机器人可能很快摔倒，reward 低、episode length 短，这是正常现象。随着训练推进，如果配置和数据合理，策略会逐渐学会跟踪参考动作。

完整训练可能持续数小时到 24 小时甚至更久。训练过程中系统出现轻度卡顿，通常是 CPU 和 GPU 资源被训练任务占用导致。只要终端仍持续输出迭代信息，通常不需要中断。

## 7\.11 查看训练结果

### 7\.11\.1 logs 目录

训练结果会写入：

```Plaintext
booster_train/logs/rsl_rl/<experiment_name>/<timestamp>/
```

其中 `<experiment_name>` 来自 `ppo_cfg.py`，`<timestamp>` 是训练启动时间。

目录中通常包含：

```Plaintext
params/
model_*.pt
```

`params/` 保存训练配置，`model_*.pt` 是 checkpoint。

### 7\.11\.2 checkpoint 文件

checkpoint 是策略模型训练过程中的参数快照。它保存了当前策略网络的权重，使训练结果可以被继续训练、播放或导出。

常见文件名如下：

```Plaintext
model_9999.pt
model_19999.pt
model_29999.pt
```

训练完成后，通常会选择编号较大的 checkpoint 进入后续处理。但如果训练后期发散，编号最大的 checkpoint 不一定效果最好，需要结合训练日志和后续动作验证判断。

本章配套资源中已经保留了 MJ 动作对应的已训练 checkpoint：

```Plaintext
beyondmimic_workspace/booster_deploy/tasks/beyond_mimic/models/k1_mj_dance_002_2025-12-03_00-10-28.pt
```

它用于后续 Chapter 8 的模型导出、MuJoCo Sim\-to\-Sim（仿真到仿真验证）和真机部署链路。第 7 章中的短训练主要用于确认环境和 task 能跑通，不要求短训练结果达到可部署质量。

### 7\.11\.3 如何初步判断训练是否正常

可以先观察四点。

第一，训练是否持续输出 iteration。如果训练在创建环境阶段就退出，说明 task、依赖或动作文件可能有问题。

第二，reward 是否长期完全没有变化。如果 reward 长时间异常，可能是参考动作、奖励配置或机器人状态异常。

第三，episode length 是否一直非常短。如果机器人每次很快失败，可能是动作太难、初始姿态不合理、重定向结果不稳定或奖励配置需要调整。

第四，是否生成 checkpoint。如果没有 `model_*.pt`，说明训练没有进入正常保存阶段，或训练迭代次数太少。

### 7\.11\.4 如何选择后续使用的 checkpoint

选择 checkpoint 时不要只看编号。更稳妥的顺序是：

1. 先确认训练没有报错；

2. 查看 reward 和 episode length 是否有改善；

3. 选择后期但未明显发散的 checkpoint；

4. 在 Chapter 8 中通过 play 和 MuJoCo 验证动作效果。

第 7 章只完成 checkpoint 生成和初步判断。真正的动作效果验证放到第 8 章。

## 7\.12 实践案例：启动一次 BeyondMimic 训练

### 7\.12\.1 实践目标

本实践完成一次训练流程启动和结果检查。目标不是立刻得到高质量动作，而是确认训练环境、训练数据和 task 配置能够形成闭环。

完成后应能确认：

- 当前电脑训练环境是否可用；

- `Booster-K1-MJ_Dance_002-v0` 训练 task 是否已经注册；

- `k1_mj2_seg1.npz` 是否位于 `booster_assets` 的动作目录中；

- `train.py` 是否能启动；

- `logs/rsl_rl/` 下是否生成训练目录；

- 是否出现 `model_*.pt` checkpoint。

### 7\.12\.2 文件目录

本章配套代码位于：

```Plaintext
CourseCode/chapter_07_beyondmimic_training/
```

目录中包含：

|路径|作用|
|---|---|
|`training_environment_check.py`|检查 Python、Conda、GPU、PyTorch、Isaac Lab 和 Booster 包是否可用|
|`check_beyondmimic_workspace.py`|检查 MJ 动作训练资源、task 配置和已训练 checkpoint|
|`beyondmimic_workspace/booster_assets/`|K1 机器人模型与 `k1_mj2_seg1.npz`|
|`beyondmimic_workspace/booster_train/`|BeyondMimic 训练工程与 `MJ_Dance_002` task|
|`beyondmimic_workspace/booster_deploy/`|后续章节使用的部署资源与已训练 checkpoint|
|`beyondmimic_workspace/TOOLs/`|CSV 清洗和动作数据整理工具|
|`README.md`|说明本章代码资源和运行方式|

### 7\.12\.3 资源检查脚本

进入本章代码目录：

```Bash
cd CourseCode/chapter_07_beyondmimic_training
```

先检查本章 BeyondMimic 工作区资源：

```Bash
python3 check_beyondmimic_workspace.py
```

该脚本会检查：

- MJ 动作 NPZ 是否存在；

- NPZ 是否包含训练所需核心字段；

- `Booster-K1-MJ_Dance_002-v0` 是否已经注册；

- `env_cfg.py` 是否引用 `k1_mj2_seg1.npz`；

- 后续章节使用的 MJ checkpoint 是否存在。

### 7\.12\.4 环境检查脚本

运行：

```Bash
python3 training_environment_check.py
```

脚本会检查：

- Python 是否为 3\.11；

- 当前是否处于 Conda 环境；

- `nvidia-smi` 是否可用；

- PyTorch 是否安装；

- PyTorch CUDA 是否可用；

- Isaac Sim 和 Isaac Lab 是否可导入；

- `booster_assets` 和 `booster_train` 是否可导入。

如果出现 FAIL 项，先处理环境问题，再启动训练。该脚本不启动训练，不打开 Isaac Sim，也不加载机器人模型。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjcxNDQ2YTYwMmE3NDc0NTI3NGZjZjVjZmRhM2JjMmFfY2E0MzU2OWY0M2Q0ZTNhYjFkYmZiYzVkOGZjMzJhODRfSUQ6NzY2MjIxNzcyOTMxOTYxOTg1MV8xNzg1ODM5NDU1OjE3ODU5MjU4NTVfVjM)

### 7\.12\.5 运行训练

完成资源检查、环境检查和工程安装后，进入 `booster_train`：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_train
```

查看任务：

```Bash
python scripts/list_envs.py
```

短训练检查：

```Bash
python scripts/rsl_rl/train.py --task=Booster-K1-MJ_Dance_002-v0 --device cuda:0 --headless --max_iterations 10
```

确认短训练能启动后，再进行完整训练：

```Bash
python scripts/rsl_rl/train.py --task=Booster-K1-MJ_Dance_002-v0 --device cuda:0 --headless
```

### 7\.12\.6 常见问题排查

问题 1：`nvidia-smi` 看不到显卡。

先检查显卡驱动是否安装成功。驱动不可用时，PyTorch 和 Isaac Lab 都无法正常使用 GPU。

问题 2：`torch.cuda.is_available()` 返回 `False`。

检查当前是否激活了正确 Conda 环境，PyTorch 是否安装了 CUDA 版本，显卡驱动是否与 CUDA wheel 兼容。

问题 3：Isaac Sim 或 Isaac Lab 无法导入。

检查是否在 Python 3\.11 环境中安装，安装命令是否执行完整，是否使用了 `--extra-index-url https://pypi.nvidia.com`。

问题 4：`booster_train` 无法导入。

确认已经执行：

```Bash
cd CourseCode/chapter_07_beyondmimic_training/beyondmimic_workspace/booster_train
python -m pip install -e source/booster_train
```

并确认当前终端仍在同一个 Conda 环境中。

问题 5：`task` 名称不存在。

检查 `__init__.py` 中注册的 ID，确认训练命令中的 `--task` 与注册 ID 完全一致。

问题 6：找不到 NPZ 文件。

检查 `env_cfg.py` 中 `self.commands.motion.motion_file` 的路径。该路径必须指向真实存在的 NPZ 文件。

问题 7：训练开始时报 shape 不匹配。

常见原因是 task 配置、motion file、机器人模型或 play/train 配置不一致。先确认 NPZ 的关节数量、机器人模型和 task 配置匹配。

问题 8：显存不足。

可以减少并行环境数量，或关闭图形界面。训练命令中使用 `--headless` 可以降低显示开销。

问题 9：checkpoint 没有生成。

检查训练是否真的进入迭代阶段，以及训练迭代次数是否足够。短训练只用于检查流程，可能不会生成完整可用 checkpoint。

问题 10：reward 长时间不变化。

检查动作数据是否合理、重定向是否稳定、奖励配置是否正确、机器人是否很快失败，以及 task 是否加载了正确 NPZ。

## 7\.13 本章小结

### 7\.13\.1 本章完成的训练闭环

本章完成了动作生成系统中的训练环节。第 6 章得到的 NPZ 是参考动作数据，而 BeyondMimic 训练的目标是把参考动作转化为策略模型的 checkpoint。

本章先解释了为什么需要训练，说明了轨迹回放和策略控制的区别；随后介绍了 BeyondMimic、Isaac Sim、Isaac Lab、PyTorch、PPO、booster\_assets、booster\_train 等组件在训练链路中的作用；最后给出了从电脑环境搭建、工程安装、数据准备、task 创建、训练启动到 checkpoint 查看的一整套流程。

### 7\.13\.2 进入第 8 章

进入 Chapter 8 后，课程将继续处理第 7 章生成的 checkpoint。下一章会讲解如何使用 `play.py` 导出模型，如何在 MuJoCo 中进行 Sim\-to\-Sim 验证，以及如何进入 K1 真机执行链路。

