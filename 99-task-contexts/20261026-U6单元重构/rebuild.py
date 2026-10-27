"""按用户指定的单元分工重建U6-L2～L4，并保留旧稿和输入基线。"""
from pathlib import Path
import ast
import copy
import hashlib
import json
import re
import shutil

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
NB = PROJ / 'notebooks'
LESSONS = {}


def lesson(key, filename, old_filename, generator, title):
    LESSONS[key] = {'filename': filename, 'old_filename': old_filename,
                    'generator': generator, 'title': title, 'cells': []}


def md(key, text):
    LESSONS[key]['cells'].append({'cell_type': 'markdown', 'metadata': {},
                                  'source': (text.strip() + '\n').splitlines(keepends=True)})


def code(key, text):
    text = text.strip() + '\n'
    ast.parse(text)
    LESSONS[key]['cells'].append({'cell_type': 'code', 'execution_count': None,
                                  'metadata': {}, 'outputs': [], 'source': text.splitlines(keepends=True)})


lesson('L2', 'U6-L2_动作录制与回放.ipynb', 'U6-L2_动作录制.ipynb', '_gen_L22.py', '动作录制与回放')
md('L2', '''# U6-L2：动作录制与回放

**课程目标**

1. 能完成一次拖动示教的录制、保存、读回和回放，记录轨迹文件与任务结果。
2. 能比较两次录制的停顿、动作节奏和回放表现，说明采集过程怎样影响轨迹。
3. 能在回放前退出示教上下文，并根据任务状态决定能否继续运行下一次。''')
md('L2', '''## 一、把自己录的动作做出来

L1读取了教师提供的轨迹。本课自己设计一段小幅动作，带动K1允许操作的部位完成示教，再让机器人回放。仅把文件保存成功，还不能确认它实际做出的动作符合设计。

任务采用“抬手—短暂停顿—回到起始姿态”等经教师确认的简单动作。第一次回放后，选择一个问题修改示教方式，重新录制并比较。

> **录制中的停顿、节奏和首尾姿态，会怎样影响机器人实际回放？**''')
md('L2', '''## 二、录制、文件与回放

拖动示教记录的是关节随时间变化的数据。可以把它与录像作对比：录像保存一帧帧画面，轨迹保存一个个时刻的关节记录。保存为`.btraj`后，`TrajectoryData.load()`能重新读取这些记录，`execute_trajectory()`将轨迹交给机器人执行。

这次实验没有训练新的动作策略。录制提供轨迹，回放使用已有执行能力；下一课的动作工坊还会把参考动作送入训练流程。

| 环节 | 接口或操作 | 得到什么 |
| --- | --- | --- |
| 进入示教上下文 | `with robot.hand_guiding_manager as hand_guiding` | 在这一段中使用示教管理器 |
| 开始与停止录制 | `start_recording()`、`stop_recording()` | 一条轨迹；无有效数据时可能返回`None` |
| 保存与读回 | `save()`、`TrajectoryData.load()` | 磁盘上的`.btraj`及重新读取的对象 |
| 回放 | `execute_trajectory()` | 运动任务句柄，用它等待并查询结果 |

`with`代码块退出后再回放。仅停止录制、仍留在示教上下文内时，不符合回放要求。''')
md('L2', '''## 三、先设计一段可比较的动作

画出起始姿态、关键动作与结束姿态，写下哪里需要停顿。动作由教师确认，优先采用双脚稳定、上身小幅运动的方案，不用力掰关节，不设计跳跃或失去支撑的动作。

本课录制两个版本。第二版只改变一个因素，例如缩短无意的停顿或放慢抬手，其他动作保持接近。两版分别保存，不能用第二版覆盖第一版。

| 版本 | 设计变化 | 文件名 |
| --- | --- | --- |
| v1 | 初次示教 | `my_action_v1.btraj` |
| v2 | 根据回放选择一项调整 | `my_action_v2.btraj` |''')
md('L2', '''## 四、实验：录制、保存并回放

⚠️ **安全**：本课包含手动示教和自动回放，全程由教师看护。只操作教师确认允许拖动的部位；回放前人员退出动作范围，确认机器人站稳、首姿态和周围空间适合该轨迹。模式切换使用实体按钮：先准备模式（PREP）并确认直立稳定，再进入行走模式（WALK）。严禁站立时从WALK直接切到阻尼模式（DAMP）。异常时由教师按设备操作规范中止；代码格停止运行不代表动作任务已停止。

📌 **前置**：L1的轨迹信息读取；开发环境能连接K1；教师已验证示教操作范围。使用K1开展本实验，T2的示教能力不能按本课直接套用。''')
md('L2', '''**STEP 01：** 连接机器人

本格只连接和读取信息。后面的录制与回放均要求当前模式为`"walk"`；先按上方要求完成模式准备。''')
code('L2', '''from pathlib import Path
from boosteros.robots.booster import BoosterRobot
from boosteros.types import TrajectoryData

robot = BoosterRobot()
print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())''')
md('L2', '''### 4.1 录制并保存第一版

输入当前Python环境可访问的文件名。程序检查文件是否已存在，防止覆盖已有版本。录制开始后，由一名同学完成示教，另一名同学在结束时按回车；键盘等待期间仍在录制，停顿也可能保留在轨迹中。

**STEP 02：** 录制一个版本并保存

<font color="red">提示：开始前应处于行走模式，机器人没有其他运动任务。教师确认允许操作的部位后再运行。完成示教后回车，程序停止录制并退出`with`，此时不会自动回放。</font>''')
code('L2', '''if robot.get_mode() != "walk":
    raise RuntimeError("请先按教师要求进入行走模式")
if robot.get_active_tasks(lambda info: info.group == "motion"):
    raise RuntimeError("仍有运动任务未结束，请先由教师检查")

same_data = False
verified_path = None
record_path = Path(input("本次文件名（默认 my_action_v1.btraj）：").strip() or "my_action_v1.btraj")
if record_path.suffix != ".btraj":
    raise ValueError("轨迹文件名应以 .btraj 结尾")
if record_path.exists():
    raise FileExistsError("文件已存在，请使用新的版本文件名")

traj = None
recording_seconds = 0.0
with robot.hand_guiding_manager as hand_guiding:
    hand_guiding.start_recording()
    try:
        input("按设计轻缓示教；完成后按回车停止录制：")
        recording_seconds = hand_guiding.get_recording_duration()
    finally:
        if hand_guiding.is_recording:
            traj = hand_guiding.stop_recording()

if traj is None or not traj.points:
    raise RuntimeError("未得到有效轨迹，本次不保存、不回放")
traj.save(record_path)
print("保存位置：", record_path.resolve())
print(f"停止前的录制计时：{recording_seconds:.2f} 秒")
print(f"轨迹时长：{traj.duration.seconds:.2f} 秒；采样点数：{len(traj.points)}")''')
md('L2', '''### 4.2 读回并核对

从磁盘加载刚才保存的文件，核对ID、关节名、采样点数和时长。停止前的录制计时与轨迹时长取值时刻不同，可能略有差异；读回对象应与保存对象对应。

信息一致只能说明文件读回核对通过，不能说明动作幅度、首姿态或实际回放效果合适。

**STEP 03：** 检查保存与读回的信息''')
code('L2', '''same_data = False
verified_path = None
traj_back = TrajectoryData.load(record_path)
same_data = (
    traj_back.id == traj.id
    and traj_back.joint_names == traj.joint_names
    and len(traj_back.points) == len(traj.points)
    and abs(traj_back.duration.seconds - traj.duration.seconds) < 0.001
)
print("轨迹 ID：", traj_back.id)
print("关节名：", traj_back.joint_names)
print("时长：", traj_back.duration.seconds, "秒")
print("采样点数：", len(traj_back.points))
print("读回核对：", "一致" if same_data else "不一致，请检查文件")
if not same_data:
    raise RuntimeError("读回核对未通过，本次不继续回放")
verified_path = record_path.resolve()''')
md('L2', '''### 4.3 回放并记录结果

`replay_task = robot.execute_trajectory(traj_back)`发起回放，并把任务句柄保存在`replay_task`中。`wait(timeout=...)`等待任务；超时可能返回仍在运行的状态，不会自动取消动作。

只有`SUCCEEDED`表示SDK报告执行成功；`FAILED`和`CANCELLED`表示其他结束结果。任务成功后还要观察动作是否符合设计，例如停顿是否过长、末姿态是否适合后续动作。

**STEP 04：** 经教师确认后回放

<font color="red">提示：确认已退出示教上下文、机器人处于行走模式、周围无人接触机器人，且教师认可起始姿态。状态仍未结束时保留句柄，不重复启动；超时由教师检查，不能把打印结束当作机器人已停止。</font>''')
code('L2', '''if not globals().get("same_data", False) or verified_path != record_path.resolve():
    raise RuntimeError("请先完成本次轨迹的保存和读回核对")
if traj_back.id != traj.id:
    raise RuntimeError("读回对象与本次录制不对应，请重新核对")
if "replay_task" in globals() and not replay_task.done():
    raise RuntimeError("上一回放任务仍未结束，保留原句柄，请教师检查")
if robot.get_mode() != "walk":
    raise RuntimeError("回放要求处于行走模式")
if robot.get_active_tasks(lambda info: info.group == "motion"):
    raise RuntimeError("有未结束的运动任务，本次不启动")
if input("教师已确认可以回放？输入“回放”继续：").strip() != "回放":
    raise RuntimeError("未启动回放")

replay_task = robot.execute_trajectory(traj_back)
status = replay_task.wait(timeout=max(15.0, traj_back.duration.seconds + 10.0))
print("任务状态：", status)
print("任务是否结束：", replay_task.done())
if not replay_task.done():
    print("等待时间已到，任务仍未结束；不重开，由教师检查")
elif status == "SUCCEEDED":
    print("SDK报告回放成功；请记录动作与设计的差异")
else:
    print("本次未成功完成，原因：", replay_task.error)''')
md('L2', '''### 4.4 根据观察改录第二版

先记录第一版效果，选定一项调整。确认回放任务已结束、教师已恢复合适的起始姿态后，重新运行STEP 02～04；文件名改为`my_action_v2.btraj`。

如果第一版有一段无意停顿，第二版可减少这段等待；如果动作过急，第二版可放慢示教。比较两版轨迹时长及实际表现，保留文件和观察依据。不要只以时长更短判断动作更好。''')
md('L2', '''## 五、收尾

先确认回放任务已经进入终态，教师观察机器人状态。使用实体按钮退回准备模式（PREP），待站立稳定后，由教师支撑并按设备规范扶坐、进入阻尼模式（DAMP）；严禁从WALK直接切到DAMP。未结束或异常的任务交教师处理，不能靠关闭Notebook完成运动收尾。''')
md('L2', '''## 六、观察、记录与评价

### 6.1 两版比较

| 项目 | v1 | v2 |
| --- | --- | --- |
| 文件名、轨迹ID | | |
| 关节名、点数、轨迹时长 | | |
| 录制计时（秒） | | |
| 回放任务状态 | | |
| 停顿、节奏、首尾姿态的观察 | | |
| 本次调整与证据 | | |

未成功回放或任务未结束时如实记录，先处理任务和设备状态，不为填满表格重复启动。

### 6.2 检查点

- 能否从保存文件重新读出轨迹，并在本课完成一次成功回放。
- 能否用两版记录解释，示教中的哪一项变化影响了回放。
- 能否区分文件读回成功、任务执行成功和动作效果符合设计。

### 6.3 思考题

1. 录制时停了两秒，再继续动作，这段停顿可能怎样进入回放？
2. 为什么停止录制后还要退出`with`，才能执行回放？
3. 回放成功是否说明训练出了新的策略？请按本课实际操作说明。

### 6.4 学习评价

1. 按执行次序填写：开始录制→示教→停止录制→退出示教上下文→________→________→回放。
2. `wait(timeout=...)`返回`RUNNING`时，可以立即再发起一次动作吗？依据是什么？
3. 用本组第二版的观察，说明改动是否达到了原定目的。

> 参考答案（教师留存，PDF学生版删除）：1. 保存、读回核对；2. 不可，任务尚未进入终态，重复运动可能冲突；3. 结合实际记录，不能仅以时长变短判断。''')


lesson('L3', 'U6-L3_视频动作训练.ipynb', 'U6-L3_动作回放.ipynb', '_gen_L23.py', '视频动作训练（动作工坊）')
md('L3', '''# U6-L3：视频动作训练（动作工坊）

**课程目标**

1. 能按要求拍摄、检查并上传一段动作视频，创建面向K1的动作训练任务。
2. 能结合本次任务，说明视频提取骨架、重定向和强化学习训练分别处理什么，区分参考动作与训练策略。
3. 能记录任务进展，比较原视频与可查看的生成结果，指出动作保留、改变或未达到的部分，并提出有依据的改拍建议。''')
md('L3', '''## 一、从真人视频到机器人动作

上一课直接记录机器人关节轨迹并回放。这一课从人做动作的视频开始，在Booster Studio的动作工坊中创建训练任务，让生成的策略学习跟踪参考动作。

真人和K1的身形、关节及平衡条件不同。视频中的抬手、转身等动作，需要先转成可处理的运动数据，再适配K1，最后通过训练形成动作策略。

> **视频里看起来容易完成的动作，转成机器人动作时，哪些可以保留，哪些可能改变？**''')
md('L3', '''## 二、动作工坊中发生了什么

### 2.1 提取骨架动作

系统从视频中估计人体各部位的位置及其随时间的变化，形成骨架动作。它记录“人怎样动”，还不是能直接驱动K1的关节指令。

只有一个人完整出镜、光线清楚且无遮挡，系统才更容易持续判断同一身体部位。手臂交叉遮住身体、脚离开画面等情况，会使运动估计更困难。视频清楚也不能保证提取一定准确。''')
md('L3', '''### 2.2 重定向：把人体运动适配到K1

重定向根据K1的结构，把人体动作映射到机器人能够表达的运动。比如同一个抬手动作，人体与K1的关节数量、肢体比例和可转范围不同，不能直接照搬人的角度。

本功能使用imretarget完成这一步。这里需要辨认的是输入输出：输入为人体骨架动作，输出为适配机器人结构的参考动作。几何上能表达，还不等于机器人运动时能够保持稳定。''')
md('L3', '''### 2.3 强化学习训练：学习怎样跟踪参考动作

动作工坊把参考动作交给Booster Train的训练流程。与L1介绍的参考动作跟踪相同：参考动作说明希望做成什么样，策略在训练环境中尝试控制，训练程序依据动作跟踪等评分更新策略。

这条链可以写成：

```
真人视频 → 人体骨架动作 → 重定向后的参考动作 → 强化学习训练 → 动作策略
```

训练同时受最大时长和训练终止标准约束，满足任一条件就结束。到达最大时长不等于动作已经学得足够好；具体数值由平台设置。本课通过平台发起训练、观察结果，不需要编写训练算法。

与L2比较：L2读取和执行已有的关节轨迹，没有更新动作策略；本课新增了训练步骤。它是用强化学习完成参考动作模仿的应用，不应把上传视频直接称为行为克隆。''')
md('L3', '''## 三、准备可用的视频

### 3.1 视频要求

| 检查项 | 要求 | 本组检查 |
| --- | --- | --- |
| 文件 | MP4或MOV | |
| 分辨率与帧率 | 不低于720P、30帧/秒 | |
| 人物 | 单人、全身出镜 | |
| 清晰度与遮挡 | 画面清楚，避免肢体交叉遮挡和物体遮挡 | |
| 身体稳定 | 不跳跃、不踮脚、不设计单腿支撑动作 | |
| 动作难度 | 避免大幅弯腰、后仰和快速动作 | |

分辨率表示画面包含多少像素；帧率表示每秒记录多少帧。可以在手机、电脑的视频详情或教师指定工具中查看，不能只凭文件扩展名判断。拍摄时确认头、手和脚在整个动作过程中都没有离开画面。''')
md('L3', '''### 3.2 设计一段简短动作

选择面向接待或展示的小幅动作，例如双脚稳定的缓慢抬臂致意。先写清起始姿态、动作过程和结束姿态，经教师确认后再拍摄。动作短一些，便于逐段比较；实际上传时长限制以当前界面为准。

| 设计项 | 本组方案 |
| --- | --- |
| 动作用途与名称 | |
| 起始姿态 | |
| 关键运动与需要保留的停顿 | |
| 结束姿态 | |
| 预计最难适配的部位及原因 | |

最后一项先写预测。查看结果后回到此表，判断预测是否有观察依据。''')
md('L3', '''## 四、实践：创建与观察训练任务

📌 **前置**：Booster Studio已能使用动作工坊，账号及训练所需额度由教师准备。本课的上传和训练不要求机器人运动。教师另备一份已经完成、可供观察的K1样例，以免后台训练时间超过本节课。

⚠️ **设备运行**：训练完成页的预览可能只是策略运行的录制，观看预览不代表正在控制虚拟机器人或真机。只有教师确认当前动作可用、现场条件合适后，才进入部署运行；不能为了完成课堂记录跳过确认。''')
md('L3', '''**STEP 01：** 拍摄并检查输入视频

按第三节逐项填写检查结果。播放完整视频，检查动作全过程是否全身可见；不满足要求的片段先重拍。保留本组采用的版本及一项最主要的改拍理由。''')
md('L3', '''**STEP 02：** 在动作工坊创建动作

1. 打开Booster Studio的动作工坊，选择“创建动作”。
2. 输入能区分组别和版本的名称，例如“第三组_抬臂致意_v1”。
3. 选择K1对应的目标机型；若界面已由当前设备确定机型，核对显示是否正确。
4. 上传已检查的MP4或MOV，查看视频预览及界面显示的预计耗时、额度信息。
5. 经教师确认后提交，记录动作名称、提交时间和任务标识；没有显示标识时记录名称及截图，不自行编造。

修改视频后使用新版本名，保留原输入和任务记录，避免把不同任务的结果放在一起。''')
md('L3', '''**STEP 03：** 记录界面能观察到的进展

记录当前任务状态与界面提供的信息。若能查看提取骨架、重定向或训练阶段，写下阶段名称及看到了什么；界面未提供的中间结果填写“不可查看”，不要根据流程图补成实测。

| 记录时刻 | 当前任务状态或阶段 | 界面提供的画面/提示 | 本次可作出的判断 |
| --- | --- | --- | --- |
| 提交后 | | | |
| 课内再次查看 | | | |
| 完成或失败后 | | | |

正在处理与失败要分开记录。后台训练未完成时，保留任务，先用教师已完成样例开展下一步；本组任务在课后按同一表格补记。''')
md('L3', '''### 4.1 原视频与生成结果的比较

**STEP 04：** 查看可用结果，按动作片段比较

先注明比较对象：本组任务或教师样例。把原视频与生成结果按“起始—关键动作—结束”对应起来，观察抬臂方向、幅度、停顿、身体支撑与结束姿态。

| 动作片段 | 原视频表现 | 生成结果表现 | 保留/变化/无法判断 | 观察依据 |
| --- | --- | --- | --- | --- |
| 起始 | | | | |
| 关键动作 | | | | |
| 结束 | | | | |

相似外观不能证明动作一定能稳定上真机；训练显示结束，也不能代替结果检查。仅看预览时，把结论限定为预览观察。''')
md('L3', '''### 4.2 选择一项有依据的调整

**STEP 05：** 提出第二版方案

根据输入检查和结果，选一个最需要改变的因素。例如，原视频的手曾离开画面，可调整取景后重拍；动作过快，可放慢并保持其他条件接近。写出预期变化，以及将用哪一项观察判断。

生成结果与视频不同，也可能来自提取、机型适配或训练表现。没有中间证据时先记为待查，不把所有差异都归因于视频质量。第二次上传训练由教师按课堂条件安排；未再次训练时只提交方案，不写成已经改善。''')
md('L3', '''### 4.3 有条件的部署观察

教师确认可运行时，才在Studio中选择匹配机型的虚拟机器人或真机部署。真机动作开始后不能按普通视频的暂停来处理，必须按平台与设备要求完成运行确认；异常由教师处理。

部署前记录动作名、版本、机型和运行环境。先采用教师认可的验证环境，再决定是否上真机；预览、虚拟运行、真机运行分别记录。没有部署时写“未部署”，不影响对输入、训练流程与预览的学习记录。

本课产出的动作名称和版本会用于L4的作品设计；文件导出及程序调用由教师确认当前可用方式后再接入。''')
md('L3', '''## 五、整理作品材料

保留输入视频、动作名称与版本、任务进展记录、可用预览或部署观察、第二版建议。训练仍在处理时，另记补查时间；不要为结束课堂而删除任务或重复提交相同素材。

将本组动作在L4中承担的作用写清楚，并记录首尾姿态和运行条件。尚未完成的动作在作品清单中标为待验证，不能当作已经可执行的素材。''')
md('L3', '''## 六、检查与学习评价

### 6.1 检查点

- 能否说明所用视频的格式、分辨率、帧率和完整出镜情况。
- 能否把骨架提取、重定向、训练的输入输出分别说清楚。
- 能否用实际观察区分任务进展、训练结束、预览效果和部署结果。
- 能否提出一项对应观察证据的修改建议，并说明是否已经验证。

### 6.2 思考题

1. 已经把人体动作适配成K1参考动作，为什么还要训练策略？
2. 最大训练时长已经到达，可以直接判断动作合格吗？还需要什么证据？
3. 原视频手臂举得更高，生成动作举得较低，可以只凭成品判断是哪一步造成的吗？

### 6.3 学习评价

1. 给本组任务补全数据流程：视频→________→________→强化学习训练→________。
2. 用一项本课证据说明，它与L2直接回放`.btraj`相比增加了什么过程。
3. 提交一个动作片段的输入/结果对照和第二版建议，注明使用本组结果还是教师样例。

> 参考答案（教师留存，PDF学生版删除）：1. 人体骨架动作、重定向参考动作、动作策略；2. 新增策略训练，L2没有更新策略；3. 按来源、证据与条件评价，不要求所有训练当堂结束或所有动作都上真机。''')


lesson('L4', 'U6-L4_动作编排.ipynb', 'U6-L4_动作编排.ipynb', '_gen_L24.py', '动作编排')
md('L4', '''# U6-L4：动作编排

**课程目标**

1. 能围绕一个展示任务选择动作素材，标明来源、首尾姿态与使用条件，形成3～5步作品脚本。
2. 能把已验证的录制轨迹与内置动作按顺序编排，前一步成功后才进入下一步；未完成时停止启动后续动作并保留记录。
3. 能用一次试演记录找出衔接或表达问题，调整一个方案要素并说明复测结果或待验证事项。''')
md('L4', '''## 一、把动作组织成作品

L2保存并回放了自己的轨迹，L3用视频创建了训练任务。本课选择一个具体场景，例如“来宾面前的致意展示”，把已有动作组织成有开始、有内容、有结束的作品。

可以选择录制动作、动作工坊作品和系统内置动作。每个素材是否已经完成、能否在当前设备运行，以及前后姿态是否合适，都要先检查；不能只按动作名称排顺序。

> **怎样让不同来源的动作按预定次序执行，又能在某一步未完成时保留正确的结果？**''')
md('L4', '''## 二、素材来源与执行条件

| 来源 | 本课可使用的材料 | 调用或观察方式 | 编排前检查 |
| --- | --- | --- | --- |
| L2录制轨迹 | 本组已回放验证的`.btraj` | `TrajectoryData.load()`后交给`execute_trajectory()` | K1机型、文件、首尾姿态、单项回放 |
| 内置动作 | `list_actions()`实际列出的动作ID | `do_action(action_id)` | 型号与版本、幅度、时长、可打断性、单项执行 |
| L3动作工坊作品 | 已完成并验证的动作名称与版本 | 使用教师确认可用的部署或调用方式 | 训练/运行验证、机型、资源与首尾姿态 |

本课的Python脚本直接支持前两类素材。动作工坊作品先写入作品设计；程序入口由教师确认并提供后，再编入同一次程序试演。尚未接入的片段标为“待接入”，不可用打印动作名代替执行，也不能拿`.btraj`接口直接执行训练策略资源。

当前脚本不支持的片段若保留在程序清单中，会在开始前报错，不会先执行前面的动作。可以另存一份仅含已接入动作的基础版本，并说明它与完整作品设计的差别。''')
md('L4', '''### 2.1 顺序执行怎样衔接

`execute_trajectory()`和`do_action()`都会返回任务句柄。程序需要等待前一步进入终态，并检查状态是`SUCCEEDED`，再发起下一步。失败、取消或等待超时，都不能记作完成。

等待成功只解决了执行顺序，没有自动生成两个动作之间的过渡轨迹。上一动作的结束姿态、下一动作的起始姿态，以及动作间是否站稳，仍需单项验证和教师观察。

这些运动任务不同时启动。顺序编排也不等于把多个文件合并为一条轨迹，更不保证任意两个动作都能自然衔接。''')
md('L4', '''## 三、设计与检查作品

先写场景和希望观众看到的内容，再选择3～5步动作。至少包含一段本组录制轨迹和一个教师确认的内置动作；L3作品可列入完整方案，接入条件不足时保留为待验证片段。

| 步骤 | 动作作用 | 来源、文件或ID、版本 | 起始/结束姿态 | 前后衔接检查 | 已验证/待验证 |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

先分别检查素材，再检查相邻动作。需要改变录制动作的首尾姿态时，回到L2重新录制并另存版本，不在未验证的情况下直接改关节数据。''')
md('L4', '''## 四、实践：编排、试演与调整

⚠️ **安全**：作品会连续执行动作，全程由教师看护，人员退出动作范围。使用实体按钮完成准备模式（PREP）到行走模式（WALK）的准备，确认直立稳定后再运行。教师先检查单项动作和相邻衔接；异常时按设备规范中止，不能依赖Python等待超时来停止动作。站立时严禁WALK直接切到DAMP。

📌 **前置**：L2成功回放的文件；U1-L4的内置动作调用；已完成第三节作品设计。L3仍未完成或未接入的作品可保留在设计稿，不冒充本次程序执行成果。''')
md('L4', '''**STEP 01：** 连接设备并查看内置动作

先读取清单。选择教师确认可用的动作，保留清单实际返回的ID，不把整数编号或界面名称自行转换成SDK ID。''')
code('L4', '''import time
from pathlib import Path
from boosteros.robots.booster import BoosterRobot
from boosteros.types import TrajectoryData

robot = BoosterRobot()
actions = robot.list_actions()
action_by_id = {action.id: action for action in actions}
print("机器人：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())
for action in actions:
    print(action.id, action.type, action.duration, action.interruptible)''')
md('L4', '''### 4.1 写出本次程序执行清单

每一行是“素材类型、对应文件或ID”。`trajectory`表示录制轨迹，`action`表示内置动作。先按本组方案替换示例；`hand_wave`、`bow`也要在本机清单中存在并经教师确认，才能使用。

**STEP 02：** 检查所有素材，再开始动作

下面只预载文件和检查清单，不执行运动。任何一步文件缺失、类型未接入或动作ID无效，都会在试演前提示。动作工坊片段的类型不能擅自写成`action`或`trajectory`来绕过检查。''')
code('L4', '''plan_ready = False
steps = [
    ("action", "hand_wave"),
    ("trajectory", "my_action_v1.btraj"),
    ("action", "bow"),
]

if not 3 <= len(steps) <= 5:
    raise ValueError("本次作品应为3～5步")
if not {"trajectory", "action"}.issubset({source for source, _ in steps}):
    raise ValueError("本次作品应同时包含录制轨迹与内置动作")
candidate_steps = []
for source, resource in steps:
    if source == "trajectory":
        path = Path(resource)
        if not path.is_file():
            raise FileNotFoundError(f"轨迹文件不存在：{resource}")
        data = TrajectoryData.load(path)
        if not data.points or data.duration.seconds <= 0:
            raise ValueError(f"轨迹没有有效时序数据：{resource}")
    elif source == "action":
        if resource not in action_by_id:
            raise ValueError(f"本机动作清单中没有：{resource}")
        data = resource
    else:
        raise ValueError(f"本次脚本未接入素材类型 {source}，整份清单检查未通过")
    candidate_steps.append((source, resource, data))
prepared_steps = candidate_steps
prepared_signature = tuple(steps)
plan_ready = True
print("素材检查通过，尚未发起运动：")
for number, (source, resource, _) in enumerate(prepared_steps, 1):
    print(number, source, resource)''')
md('L4', '''### 4.2 试演并记录每一步

`active_motion`保存当前任务句柄。上一轮任务尚未结束时，程序保留这个句柄并拒绝重开。每步成功才继续；失败、取消或超时则停止启动后续动作。

`WAIT_LIMIT`是每一步等待的时间上限，由教师结合动作时长确认。超时不会自动停止机器人；仍在运行的任务交教师处理。记录的用时从接口调用前到等待返回，包含调用和等待开销，不等同于纯关节运动时长。

**STEP 03：** 经教师检查后试演

<font color="red">提示：当前应为行走模式，教师确认清单顺序、动作衔接与周围空间。代码等待时间不作为安全限时；如果本次异常中断，先核对`active_motion`和设备状态，不能直接重跑。</font>''')
code('L4', '''if not globals().get("plan_ready", False):
    raise RuntimeError("请先完成整份素材清单检查")
if tuple(steps) != prepared_signature:
    raise RuntimeError("动作清单已改动，请重新运行STEP 02检查")
if "active_motion" in globals() and not active_motion.done():
    raise RuntimeError("上一任务未结束，保留句柄，不启动新的编排")
if robot.get_mode() != "walk":
    raise RuntimeError("请先按教师要求进入行走模式")
if robot.get_active_tasks(lambda info: info.group == "motion"):
    raise RuntimeError("存在未结束的运动任务，请教师检查")
if input("教师已确认可以试演？输入“试演”继续：").strip() != "试演":
    raise RuntimeError("未开始试演")

WAIT_LIMIT = 45.0  # 单步等待上限（秒），由教师结合所选动作确认
run_log = []
for number, (source, resource, data) in enumerate(prepared_steps, 1):
    if robot.get_active_tasks(lambda info: info.group == "motion"):
        print("发现未结束运动任务，不启动下一步")
        break
    started = time.monotonic()
    try:
        if source == "trajectory":
            active_motion = robot.execute_trajectory(data)
        else:
            active_motion = robot.do_action(data)
        status = active_motion.wait(timeout=WAIT_LIMIT)
    except Exception as exc:
        run_log.append((number, source, resource, "调用或等待异常", time.monotonic() - started, str(exc)))
        print("本步发生异常，不启动后续动作：", exc)
        break
    elapsed = time.monotonic() - started
    run_log.append((number, source, resource, status, elapsed, str(active_motion.error)))
    print(number, resource, status, f"{elapsed:.2f} 秒")
    if not active_motion.done():
        print("等待超时，任务仍未结束；保留句柄，由教师处理")
        break
    if status != "SUCCEEDED":
        print("本步未成功，不启动后续动作")
        break

print(f"本次获得{len(run_log)}步记录；清单共有{len(prepared_steps)}步，请逐项核对")''')
md('L4', '''**STEP 04：** 读日志，补充现场观察

程序日志记录已调用步骤和任务结果。没执行的步骤不会自动出现，应在作品记录中标为“未执行”。即使所有任务状态都是成功，也要另看节奏、首尾姿态和动作间过渡是否符合设计。''')
code('L4', '''print("步骤 | 来源 | 素材 | 任务结果 | 调用及等待用时（秒） | 错误信息")
for number, source, resource, status, seconds, error in run_log:
    print(number, source, resource, status, f"{seconds:.2f}", error, sep=" | ")''')
md('L4', '''### 4.3 根据试演修改一个要素

选择顺序、素材或某个录制动作的首尾姿态中的一项修改，写出原因。确认上一轮运动任务已结束、教师恢复合适姿态后，重新检查整份素材清单，再试演。

复测使用新版本名并保留原记录。若新增动作工坊片段尚未有可用的程序入口，记录待接入条件；可以在Studio中单独演示该素材，但必须注明“单独运行”，不能说它已经进入这次SDK连续编排。''')
md('L4', '''## 五、顺序、状态与更复杂的组织

本课用列表和循环确定动作顺序，用任务结果决定继续或停止。动作素材可以来自学习算法，运行顺序仍由人编写的规则决定。

U5-L4用“待机、会话已发起、停止请求已发出”描述应用状态。作品若要等待来宾、根据条件选择动作，也可先设计相应状态与转换。行为树则把动作与判断组织为可组合节点，是另一种组织方式。本课不要求实现新的状态机或行为树；作品设计、两类动作混合执行与结果复核是本次实践任务。''')
md('L4', '''## 六、收尾与交付

教师确认运动任务已结束、机器人状态适合收尾后，使用实体按钮退回准备模式（PREP）；待直立稳定，再支撑机器人并按设备规范扶坐、进入阻尼模式（DAMP）。严禁WALK直接切到DAMP。

交付作品脚本、素材清单、试演日志、现场观察及修改说明。演示视频由教师按课堂条件安排，画面注明执行的是基础版本、完整版本还是单独素材，不混用三种成果。''')
md('L4', '''## 七、作品记录与学习评价

### 7.1 试演记录

| 步骤 | 素材与版本 | 任务状态/未执行 | 现场效果 | 需要调整什么 |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

分别填写本组录制动作、内置动作，以及有条件使用的动作工坊作品。未完成训练、未接入程序或未部署时如实标明。

### 7.2 检查点

- 作品是否有明确场景、3～5步设计和可追溯的素材来源。
- 基础程序是否实际包含录制轨迹与内置动作，且每步成功后才继续。
- 记录能否区分任务成功、动作衔接效果与未执行步骤。
- 修改建议是否对应试演证据；未复测的改动是否标明待验证。

### 7.3 思考题

1. 第一条轨迹结束姿态与下一动作起始姿态不同，单纯`wait()`能否自动解决？
2. 等待返回`RUNNING`与返回`FAILED`时，下一步都不启动，但两者分别需要处理什么？
3. 动作由强化学习训练得到，整个作品的顺序是否也由模型决定？依据是什么？

### 7.4 学习评价

1. 提交一份至少包含两类可执行素材的作品及试演记录。
2. 指出脚本中保存当前句柄、等待任务和判断成功的代码位置，解释各自作用。
3. 说明一个本次修改及其结果；未复测时说明还缺哪项验证。

> 参考答案（教师留存，PDF学生版删除）：1. 以实际文件、ID和记录核对，不将待接入素材当执行成果；2. `active_motion`、`wait()`、`done()`及`SUCCEEDED`判断；3. 根据观察评价。状态机/行为树不作本课必达技能。''')


def backup(path):
    dest = TASK / 'before' / path.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(path.read_bytes())


def generator_text(item):
    doc = f'''U6-{item['key']} {item['title']} —— Notebook的反向同步镜像。
以 notebooks/{item['filename']} 为单一源文件，2026-10-26按用户指令重构。
状态：P1新修订稿，待设计确认及受影响部分真机验证；不把静态检查记为验证通过。
模式切换在Markdown中按实体按钮要求说明，不用代码set_mode。
动作工坊的新SDK接口测试中，不写入可执行代码；正式两类动作只按成功状态顺序执行。'''
    parts = ['# -*- coding: utf-8 -*-\n', repr(doc) + '\n', 'import json, os\n',
             f'OUT = os.path.join(os.path.dirname(__file__), "notebooks", {item["filename"]!r})\n',
             'cells = []\n']
    for cell in item['cells']:
        parts.append('cells.append(' + repr(cell) + ')\n')
    parts.append('nb = ' + repr({k: v for k, v in item['doc'].items() if k != 'cells'}) + '\n')
    parts.append('nb["cells"] = cells\nwith open(OUT, "w", encoding="utf-8") as output:\n    json.dump(nb, output, ensure_ascii=False, indent=1)\nprint("wrote", OUT, "cells=", len(cells))\n')
    result = ''.join(parts)
    ast.parse(result)
    return result


def main():
    assert not (TASK / '重构清单.json').exists(), '已执行，不覆盖输入基线'
    shared = ['AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
              '05-internal-materials/vocational-planning/README.md',
              '01-booster-kb/07-tech-platform/motion-creator.md',
              '01-booster-kb/07-tech-platform/_index.md',
              '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md']
    for name in ['X课程大纲-v4.md', 'X课程开发计划-v4.md', '_regen_from_nb.py', '_diffcheck_u2.py']:
        shared.append((PROJ / name).relative_to(ROOT).as_posix())
    for rel in shared:
        backup(ROOT / rel)
    l1 = NB / 'U6-L1_动作的来源.ipynb'
    manifest = {'date': '2026-10-26', 'shared': shared, 'lessons': [],
                'l1_preserved_sha256': hashlib.sha256(l1.read_bytes()).hexdigest()}
    for key, item in LESSONS.items():
        item['key'] = key
        old_path = NB / item['old_filename']
        gen_path = PROJ / item['generator']
        backup(old_path)
        backup(gen_path)
        before_bytes = old_path.read_bytes()
        old_doc = json.loads(before_bytes)
        doc = copy.deepcopy(old_doc)
        doc['cells'] = item['cells']
        for number, cell in enumerate(doc['cells'], 1):
            cell['id'] = f'u6-{key.lower()}-{number:02d}'
        item['doc'] = doc
        new_path = NB / item['filename']
        if old_path != new_path:
            assert not new_path.exists(), new_path
            archive = TASK / '旧稿' / item['old_filename']
            archive.parent.mkdir(parents=True, exist_ok=True)
            # 归档旧文件，确保notebooks中只有新的当前课稿。
            shutil.move(str(old_path), str(archive))
        new_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        gen_path.write_text(generator_text(item), encoding='utf-8', newline='\n')
        manifest['lessons'].append({'lesson': key, 'old_path': old_path.relative_to(ROOT).as_posix(),
                                    'path': new_path.relative_to(ROOT).as_posix(),
                                    'generator': gen_path.relative_to(ROOT).as_posix(),
                                    'before_sha256': hashlib.sha256(before_bytes).hexdigest(),
                                    'after_sha256': hashlib.sha256(new_path.read_bytes()).hexdigest(),
                                    'old_cells': len(old_doc['cells']), 'cells': len(doc['cells']),
                                    'code_cells': sum(c['cell_type'] == 'code' for c in doc['cells'])})
    (TASK / '重构清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps([{k: x[k] for k in ['lesson', 'old_cells', 'cells', 'code_cells']} for x in manifest['lessons']], ensure_ascii=False))


if __name__ == '__main__':
    main()
