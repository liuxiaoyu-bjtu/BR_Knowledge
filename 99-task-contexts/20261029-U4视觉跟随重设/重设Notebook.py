from pathlib import Path
import json
import pprint
import textwrap

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'

OBSERVE = '''
def observe_target():
    started = time.monotonic()
    image = robot.get_image(img_type="rgb")
    results = detector.detect(image.to_numpy())
    targets = []
    for result in results:
        if result.class_name == TARGET_CLASS:
            targets.append(result)
    if not targets:
        return None, None, "未检测到目标"
    if len(targets) != 1:
        return None, None, "检测到多个目标"

    box = targets[0].bbox
    values = [box.center_x, box.center_y, box.width, box.height]
    if not all(math.isfinite(value) for value in values):
        return None, None, "检测框包含无效数值"
    if box.width <= 0 or box.height <= 0:
        return None, None, "检测框大小无效"
    left = box.center_x - box.width / 2
    right = box.center_x + box.width / 2
    top = box.center_y - box.height / 2
    bottom = box.center_y + box.height / 2
    if left <= 2 or top <= 2 or right >= image.width - 2 or bottom >= image.height - 2:
        return None, None, "检测框碰到画面边缘，先检查目标是否完整"
    if time.monotonic() - started > READ_LIMIT:
        return None, None, "本次取图与检测过慢"
    error = box.center_x - image.width / 2
    ratio = box.height / image.height
    return error, ratio, "可用"


def choose_velocity(error, ratio):
    yaw_rate = 0.0
    if abs(error) > CENTER_PX:
        yaw_rate = max(-MAX_YAW, min(MAX_YAW, -KP_YAW * error))
    if ratio >= STOP_RATIO:
        return 0.0, yaw_rate, "已近，停止前进"
    if abs(error) > TURN_ONLY_PX:
        return 0.0, yaw_rate, "先原地对准"
    return FORWARD_SPEED, yaw_rate, "跟进"
'''

PARAMETERS = '''
STOP_RATIO = float(input("输入L2实测并核对的停止框高占比："))
SETUP_NOTE = input("填写本次目标、标定间距、头部角度和站姿：").strip()
if not math.isfinite(STOP_RATIO) or not 0 < STOP_RATIO < 1 or not SETUP_NOTE:
    raise ValueError("占比需在0与1之间，并保留标定条件说明")

TARGET_CLASS = "person"  # 更换目标时，检测模型、类别和阈值一起修改
FORWARD_SPEED = 0.10    # m/s，待教师结合L2记录确认；小速度也可能不产生有效行走
KP_YAW = 0.001          # rad/s/像素，沿用L1的偏差方向约定
MAX_YAW = 0.20          # rad/s，待真机核对
CENTER_PX = 20          # 认为基本对准的像素范围
TURN_ONLY_PX = 80       # 偏差较大时只转向，不前进；待本机调试
PULSE_SECONDS = 0.20    # 一次短步等待，读状态还会增加实际指令持续时间
READ_LIMIT = 1.0        # 本次取图与检测耗时上限，不能当作完整图像延迟
RUN_SECONDS = 20.0      # 一轮观察窗口，接口阻塞时不能保证到点立即退出
print("停止占比：", STOP_RATIO, "条件：", SETUP_NOTE)
'''

SUMMARY = '''
def report_motion(start_pose, end_pose, rows):
    dx = end_pose[0] - start_pose[0]
    dy = end_pose[1] - start_pose[1]
    displacement = math.hypot(dx, dy)
    print(f"参考坐标变化：dx={dx:+.3f} m，dy={dy:+.3f} m")
    print(f"起终点直线位移估计：{displacement:.3f} m（不是沿途路程）")
    if displacement >= 0.05:
        bearing = math.degrees(math.atan2(dy, dx))
        print(f"位移方向：相对里程计参考x轴{bearing:+.1f}°，正角朝参考y轴方向")
    else:
        print("位移较小，不解释方向角；0.05 m只是本次显示条件")
    print(f"起始/结束机身朝向：{start_pose[2]:+.3f}/{end_pose[2]:+.3f} rad")
    if rows:
        peak_wz = max(abs(row[5]) for row in rows)
        print(f"已记录{len(rows)}轮；采样中最大|z轴角速度|={peak_wz:.3f} rad/s")
'''

def clean(source):
    return textwrap.dedent(source).strip() + '\n'

def write_notebook(prefix, sections, gen_number):
    path = next((P / 'notebooks').glob(prefix + '_*.ipynb'))
    current = json.loads(path.read_text(encoding='utf-8'))
    cells = []
    for index, (kind, source) in enumerate(sections, 1):
        cell = {'cell_type': kind, 'id': f'{prefix.lower()}-follow-{index:02}',
                'metadata': {}, 'source': clean(source).splitlines(keepends=True)}
        if kind == 'code':
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    current['cells'] = cells
    current['nbformat'] = 4
    current['nbformat_minor'] = 5
    path.write_text(json.dumps(current, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gen = P / f'_gen_L{gen_number}.py'
    source = ('# -*- coding: utf-8 -*-\n'
              '"""视觉跟随P1修订稿完整镜像；代码有改动，须逐格真机验证。"""\n'
              'import json\nfrom pathlib import Path\nNOTEBOOK = '
              + pprint.pformat(current, width=110, sort_dicts=False)
              + '\nif __name__ in ("__main__", "__gen__"):\n'
              + '    path = Path(__file__).parent / "notebooks" / ' + repr(path.name) + '\n'
              + '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
    gen.write_text(source, encoding='utf-8')
    print(path.name, len(cells), '格/', sum(c['cell_type'] == 'code' for c in cells), '代码格')

M = 'markdown'
C = 'code'

L3 = [
(M, '''
# U4-L3：跟住来宾（闭环与视觉伺服）

**课程目标**

1. 能把L1的水平方向偏差与L2的实测框高停止阈值放入同一循环，使机器人在受控场地中短时跟随单一移动目标。
2. 能解释“远时跟进、近时停止前进、偏差大时先对准、目标不可用时结束”，并根据静态分支及真机结果调整参数。
3. 能在跟随过程中记录IMU和里程计，结束后说明机器人位移的方向、大小与机身朝向，区分直线位移和行走路程。
'''),
(M, '''
## 一、来宾移动后，机器人怎样继续跟上

L1让机器人朝向目标，L2在指定间距处测得框高占比：同一目标、完整可见且拍摄条件相近时，框高占比达到这个数值，可作为停止前进的条件。

现在，来宾缓慢向前走，并在标记处短暂停留。机器人不能只按起步时的一段距离走完就结束，而要重新看画面：目标偏向哪里，是否又远了一些，是否已经足够近？本课将方向和远近两个判断连接起来，在一轮有限时间内持续观察。

先用单一目标做静态判断，再由教师看护安排缓慢移动。来宾保持直立、尽量面向相机，不安排遮挡、突然折返或多人穿行。目标已近时机器人不再前进，目标远离后可以重新跟进；本课不自动后退，也没有人物身份跟踪功能。
'''),
(M, '''
## 二、从一次走近到连续跟随

### 2.1 每轮都要回答两个问题

| 观察量 | 含义 | 对指令的影响 |
| --- | --- | --- |
| 框中心x − 图像宽度的一半 | 目标在画面左侧还是右侧 | 决定转向角速度；右侧偏差为正，发负角速度向右转 |
| 框高 ÷ 图像高度 | 与L2停止阈值相比是偏远还是已近 | 小于阈值时可跟进；达到阈值后不再前进 |

框高达到阈值不会结束整个L3实验。程序停住前进后仍继续观察，如果来宾再次远离、框高占比减小，就重新判断是否跟进。若方向偏差很大，先原地转向，暂不前进。

### 2.2 闭环与视觉伺服

先给固定速度和时长、执行期间不根据目标变化修改指令，是本任务中的开环做法。反复读取目标位置并改变下一条指令，是闭环做法。用图像中的框位置和大小作为反馈调整运动，称为**视觉伺服**。

本课每次只走一个短步，随后停住、重新取图。跟随会有间歇，不能保证始终保持精确间距。地面、检测波动和更新间隔都会影响实际结果，需要边看输出边核对现场。
'''),
(M, '''
### 2.3 准备检测和标定参数

⚠️ **实验安全**：本课会转向和前进，必须有教师看护并清空路线。目标缓慢移动，看护人员留在侧方。先完成静态判断，再分格进入运动模式；不要“全部运行”。出现碰撞风险或异常运动时按既定按钮流程人工中止，不能等待视觉条件或IMU读数保证安全。

📌 **前置**：已完成L1方向调节和L2框高阈值核对；旧动作、轨迹和其他运动任务已结束。保持与标定相同的目标、头部角度和站姿，跟随时不再单独转头，以免改变框高对应关系。

**STEP 01：连接机器人并加载检测模型。**
'''),
(C, '''
import math
import time
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection

robot = BoosterRobot()
detector = Detection(model="person")
print("已连接：", robot.robot_info.model, robot.robot_info.serial_number)
print("当前模式：", robot.get_mode())
'''),
(M, '''
**STEP 02：带入L2实测的停止占比。** `STOP_RATIO`表示在本次目标间距处核对过的框高比例，不是像素数，也不是置信度。若在L2改用了瓶子等目标，本课仍需使用同一个目标及匹配模型；换回来宾时先重做标定。

速度、像素范围和短步时长是待调参数。`TURN_ONLY_PX`大于`CENTER_PX`：前者限制何时可以边走边转，后者用于减少画面中心附近的小幅转动。
'''),
(C, PARAMETERS),
(M, '''
### 2.4 先检查目标读数能不能使用

`observe_target()`返回三个值：水平偏差、框高占比和读数说明。目标数量不是1、框碰到画面边缘或数据无效时，前两项返回`None`，后续程序结束本轮。碰边检查只能发现一部分截断问题；身体被物体挡住、检测框错误等仍需现场观察，不能由这个检查证明目标始终完整。

`choose_velocity()`只计算，不运动。它返回前进速度、转向角速度和本轮决定。先静态检查这些结果，才能运行运动循环。

**STEP 03：定义取图检查与指令计算。**
'''),
(C, OBSERVE),
(M, '''
**STEP 04：机器人保持不动，改变目标位置检查分支。** 分别观察目标在左侧、右侧、较远和达到阈值时的输出；另做一次没有目标的检查。一次只保留一个目标，移动物体不碰机器人。

下面只打印拟发送的指令。记录画面中的目标位置是否与输出一致；若方向相反或目标不完整，先检查模型、头部朝向、标定和偏差符号。
'''),
(C, '''
error, ratio, note = observe_target()
if error is None:
    print("本轮不能运动：", note)
else:
    vx, yaw_rate, decision = choose_velocity(error, ratio)
    print(f"方向偏差={error:+.1f} px，框高占比={ratio:.3f}")
    print(f"决定：{decision}；拟发vx={vx:.2f} m/s，vyaw={yaw_rate:+.3f} rad/s")
'''),
(M, '''
## 三、跟随时另外记录机器人怎样移动

相机的偏差和框高决定本课运动；里程计与IMU用于留下这段运动的观察记录。目标移动了多少，不能由机器人的里程计单独得出。

| 记录量 | 本课用途 |
| --- | --- |
| 里程计x、y | 查看机器人在参考平面中的位置变化 |
| 里程计yaw | 查看机身朝向；与位移方向分开记录 |
| IMU z轴角速度 | 观察采样时绕身体竖直方向转动的快慢，单位rad/s |

正常转向也会产生角速度，本课不再用“与静止样本相差0.5”作为结束跟随的理由。IMU角速度不是倾斜角，也不直接表示侧倾或打滑。

**STEP 05：静止读一次，核对字段和单位。** 此格不清零、不运动。
'''),
(C, '''
odom = robot.get_odom()
imu = robot.get_imu()
print("里程计x/y/yaw：", odom.pose_2d, "单位：m、m、rad")
print("三轴角速度：", imu.angular_velocity, "rad/s")
print("三轴线加速度：", imu.linear_acceleration, "m/s²")
'''),
(M, '''
## 四、实训：目标移动，机器人跟随

### 4.1 场地和模式

标出起点、目标缓慢移动的短路线及终点停留区。先做正前方远离—停留，再按场地条件做小幅偏左或偏右；不让来宾走向机器人，不做急转弯。保持目标完整可见，路线内不安排其他人员。改变目标或拍摄姿态后，先重新核对L2停止阈值。

**STEP 06：进入准备姿态。**
'''),
(C, '''
robot.set_mode("prepare")
print("当前模式：", robot.get_mode())
'''),
(M, '''
> 由人工支撑机器人站起，确认站稳、空间和路线均满足要求，再运行下一格。头部保持标定时的固定角度。

**STEP 07：进入行走模式。**
'''),
(C, '''
robot.set_mode("walk")
print("当前模式：", robot.get_mode())
'''),
(M, '''
### 4.2 运行一轮跟随

**STEP 08：现场确认后运行。** 本格在`walk`下清零里程计并保存实际起始读数。清零只改变参考，不使机器人回到起点；实际读数不必恰好为零。

每轮先取图决定指令，短步末尾读取IMU和里程计，再发送零速度。记录里的三路信息是顺序读取的，不保证来自同一时刻。读状态会增加这次指令持续时间，0.2秒不能理解为精确运动时长。最外层`finally`保证本格正常退出或可处理的异常、中断时尝试发送零速度；通信中断或内核被强制终止时仍须现场人工处置。

“已近”只停止前进，仍可小幅原地修正方向；整个循环继续观察。目标不可用时结束本轮，不重新寻找别的目标。
'''),
(C, '''
APPROVED = False  # 每次由教师检查目标、标定、场地与参数后修改
follow_rows = []
start_pose = None
end_pose = None
follow_reason = "本轮未运行"
if APPROVED and robot.get_mode() == "walk" and input("可跟随？输入“跟随”：").strip() == "跟随":
    try:
        robot.set_velocity(0, 0, 0)
        robot.reset_odom()
        start_pose = list(robot.get_odom().pose_2d)
        started = time.monotonic()
        follow_reason = "达到本轮观察时限"
        while time.monotonic() - started < RUN_SECONDS:
            error, ratio, note = observe_target()
            if error is None:
                follow_reason = note
                break
            vx, yaw_rate, decision = choose_velocity(error, ratio)
            try:
                robot.set_velocity(vx, 0, yaw_rate)
                time.sleep(PULSE_SECONDS)
                wz = robot.get_imu().angular_velocity[2]
                x, y, yaw = robot.get_odom().pose_2d
            finally:
                robot.set_velocity(0, 0, 0)
            follow_rows.append([x, y, yaw, error, ratio, wz, decision])
            print(f"{decision}：偏差{error:+.0f}px，占比{ratio:.3f}；x/y={x:+.2f}/{y:+.2f}m，yaw={yaw:+.2f}rad，wz={wz:+.2f}rad/s")
    except (Exception, KeyboardInterrupt):
        follow_reason = "执行异常或中断，请保留报错和本轮记录"
        raise
    finally:
        robot.set_velocity(0, 0, 0)
    print("本轮结束：", follow_reason)
else:
    print("本轮未启动，请检查现场批准、模式和输入")
'''),
(M, '''
### 4.3 停稳后查看方位与距离

**STEP 09：教师确认已经停稳后读取终点。** 若本轮没有启动，就不计算。终点读数在这里重新读取，不能把最后一轮运动中的位置自动当作停稳位置。

`dx、dy`是起点到终点的坐标变化，`hypot(dx,dy)`给出两点间的直线位移估计。机器人转弯或绕路时，沿途走过的路程可能更长。`atan2(dy,dx)`给出位移方向；它与机器人最后朝向是两回事。此处角度相对里程计参考x轴，不是相对教室正北。
'''),
(C, SUMMARY + '''

if start_pose is None:
    print("本轮没有起始记录")
else:
    end_pose = list(robot.get_odom().pose_2d)
    report_motion(start_pose, end_pose, follow_rows)
    print("结束原因：", follow_reason)
'''),
(M, '''
### 4.4 重复测试与收尾

第一轮先检查“靠近后不再前进”。条件满足后，重新布置路线，再测试“目标远离后重新跟进”和“小幅偏转后调整方向”。每轮恢复标记起点、核对姿态和参数，并重新给予批准。目标丢失、截断、多目标等退出原因必须单独记录，不能写成跟随完成。

**STEP 10：结束运动，回到准备姿态。**
'''),
(C, '''
robot.set_velocity(0, 0, 0)
robot.set_mode("prepare")
print("当前模式：", robot.get_mode())
'''),
(M, '''
> 再按已经验证的人工支撑和阻尼流程扶坐，禁止从行走模式直接切阻尼。收尾不代替对线程、动作等旧任务的检查，本课不创建这些任务。

## 五、观察、记录与检查

### 5.1 视觉跟随记录

| 轮次/版本 | 目标及拍摄条件 | 停止占比/速度/短步时长 | 目标怎样移动 | 出现过的跟随决定 | 结束原因 | 最终卷尺间距 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | |
| 2 | | | | | | |

用输出或录像指出：哪次框高达到阈值后前进速度变为0，哪次目标再次远离后恢复跟进；方向偏差较大时是否先转向。最终间距应在目标和机器人都停稳后测量。使用来宾并以1.2米标定时，核对是否处于本组要求的间距；其他目标使用各自的实测间距。

### 5.2 机器人运动记录

| 起始x/y/yaw | 停稳x/y/yaw | dx/dy | 直线位移估计 | 位移方向/参考轴 | 采样最大角速度 | 卷尺或地面标记核对 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

说明机器人最终朝向与位移方向是否相同。IMU和里程计提供估计及采样记录，不能证明机器人准确走过某条真实轨迹，不能由最大角速度判定“安全”或“打滑”。

### 5.3 检查点与思考

- 能从代码指出决定前进和转向的图像量，说明为何不再输入起步间距来规划跟随总路程。
- 能说明“达到停止占比”在L2结束走近、在L3暂停前进而继续观察的区别。
- 能区分目标相对机器人的远近、机器人自身位移、机身朝向及IMU角速度。
- 如果目标只转身、弯腰或被遮挡，框高变化还能说明距离变化吗？应怎样处理？
- 框高在阈值两侧来回波动时，输出为何可能反复切换？先怎样检查采样、阈值和速度？
- 为什么从起点走出一条弯线后，`hypot(dx,dy)`不能当成整段行走路程？
'''),
(M, '''
## 六、扩展阅读：跟随的适用条件

本课按每轮检测框控制一个当前可见目标，没有识别人物身份。场景中出现第二个人时直接结束；即使始终只有一个检测框，也不能证明它始终属于同一个人。课堂应保持单一目标和清楚的路线。

框高占比是实测条件下的近距离线索，人体侧身、步态摆动或画面截断会破坏原来的对应关系。因此先安排缓慢、直立、无遮挡的演示。真实服务中的人员跟随还需处理身份、遮挡、动态测距和障碍物，本课尚未实现这些能力。

如果参数调整后仍反复启停，先固定目标与姿态、记录同一位置的波动，再决定是否设置分开的停止和重新前进阈值。新增判断后需要重新验证，不能只靠让动作看上去更流畅就认定间距准确。
'''),
]

L4 = [
(M, '''
# U4-L4：接待来宾（视觉跟随与流程联调）

**课程目标**

1. 能将发现来宾、视觉跟随、到位确认与致意连接为一次接待流程，说明每一步的继续和退出条件。
2. 能复用L1的方向偏差、L2的实测框高阈值和L3的移动跟随，在来宾缓慢移动并停留后确认到位；目标不可用时阻断致意。
3. 能分别记录程序结束原因、致意任务状态及现场效果，停稳后读取IMU和里程计记录，解释机器人位移与朝向。
'''),
(M, '''
## 一、把跟随接到一次接待中

展厅来宾进入指定通道，机器人发现这位来宾后调整方向并缓慢接近。来宾可以在标记路线内移动，随后在接待点短暂停留。机器人不能按最初的一段行进量走完就致意，而要用新画面持续检查方向和远近。

L3达到框高阈值后继续观察，来宾远离还能重新跟进。本课要完成一次接待，因此增加一个交接条件：连续几次都达到停止占比且基本对准，先结束跟随，再重新确认目标和动作空间，执行一次致意。连续满足条件用于减少一次检测波动带来的误触发，不能证明来宾身体已经静止。

本课流程是`发现单一来宾 → 视觉跟随 → 连续到位确认 → 再次检查 → 致意 → 结束`。IMU和里程计记录机器人怎样移动，不以预设路程或某个角速度差触发到位。
'''),
(M, '''
## 二、每一步怎样交接

| 步骤 | 继续条件 | 未满足时怎样处理 |
| --- | --- | --- |
| 等待来宾 | 有且只有一个可用目标框 | 无目标时有限等待；多目标、截断或处理异常则结束 |
| 跟随 | 每轮目标可用 | 远时跟进，偏差大时先转向，近时停止前进；目标不可用即结束 |
| 到位确认 | 连续3次达到停止占比且水平偏差不超过中心范围 | 任一次不满足，计数回到0；继续观察至本轮上限 |
| 致意前检查 | 来宾仍可用且到位，现场确认动作空间合适 | 不调用动作，记录具体原因 |
| 致意后收尾 | 查看句柄实际状态、核对物理动作 | 未成功不写成完成；保留未结束句柄，先处理旧任务 |

等待阶段不再另设“框高0.35就是3米”的触发比例。有一个可用来宾框即可进入跟随；用于到位的仍是L2实测停止占比，不由里程计推算来宾位置。

函数通过返回文字把结果交给主程序。调用者只有收到“到位”，才进入致意前检查。函数运行结束也可能是超时或目标无效，不能将所有返回都写成完成。
'''),
(M, '''
## 三、准备和静态联调

⚠️ **实验安全**：一位来宾按标记路线缓慢移动，面向相机、保持直立，随后短暂停留；不靠近机器人、不急转弯，不安排其他人员穿行。教师在侧方保护。转向、短步行走与致意都须事先核对空间，出现风险由人工立即中止。

📌 **前置**：L1～L3对应程序及阈值已核对；选择已验证的低幅度预定义动作；旧运动任务已结束。头部保持标定时角度，不同时启动语音、其他动作或跟随程序。

**STEP 01：首次连接，查看可用动作。** `greet_task`保存致意句柄，重复测试不重跑本格清掉旧句柄。
'''),
(C, '''
import math
import time
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection

robot = BoosterRobot()
detector = Detection(model="person")
greet_task = None
for action in robot.list_actions():
    print(action.id, action.type, action.duration)
print("模式：", robot.get_mode())
'''),
(M, '''
### 3.1 复用已经核对的参数

**STEP 02：填写停止占比及选定动作。** 拍摄条件、目标、速度和转向参数与L3对应。动作ID从本机列表中选择，不能将序号当作ID。当前输入按本课原有整数ID使用；若本机ID类型不同，先按实际列表调整后再运行。
'''),
(C, PARAMETERS + '''
GREET_ID = int(input("输入教师确认可用的致意动作ID："))
ARRIVAL_CHECKS = 3   # 连续满足次数，真机核对后可调整
ACTION_WAIT = 10.0  # 本次致意的等待上限，按动作实际时长由教师核对
motion_rows = []
start_pose = None
end_pose = None
'''),
(M, '''
### 3.2 在原有控制上定义可交接的片段

下面两个函数沿用L3：取图后检查目标是否可用，再根据方向偏差和框高计算指令。`observe_target()`返回偏差、占比、说明；`choose_velocity()`返回前进速度、转向角速度、决定。定义函数不会启动运动。

**STEP 03：定义视觉观察与指令计算。**
'''),
(C, OBSERVE),
(M, '''
**STEP 04：只读图，检查当前条件会怎样影响流程。** 让来宾分别在较远、偏左/右和接待间距处站定，记录拟发送的指令。未出现可用目标时不会进入跟随；已经到位仍需后续连续确认，不能只凭这一格就启动致意。
'''),
(C, '''
error, ratio, note = observe_target()
if error is None:
    print("不能进入跟随：", note)
else:
    vx, yaw_rate, decision = choose_velocity(error, ratio)
    print(f"偏差={error:+.0f}px，占比={ratio:.3f}；{decision}")
    print(f"拟发vx={vx:.2f}m/s，vyaw={yaw_rate:+.3f}rad/s")
    print("本次是否满足到位条件：", ratio >= STOP_RATIO and abs(error) <= CENTER_PX)
'''),
(M, '''
### 3.3 场地与模式准备

标出起点、来宾移动路线和接待停留区，保持地面平整、目标完整可见。使用来宾并以1.2米标定时，最终停稳后用卷尺核对本组要求的间距。里程计会记录机器人经过的位置，不再输入卷尺起步间距来决定应该走多远。

**STEP 05：进入准备姿态。**
'''),
(C, '''
robot.set_mode("prepare")
print("当前模式：", robot.get_mode())
'''),
(M, '''
> 人工支撑站起并确认站稳，核对头部角度、路线和动作范围后再继续。

**STEP 06：进入行走模式。**
'''),
(C, '''
robot.set_mode("walk")
print("当前模式：", robot.get_mode())
'''),
(M, '''
## 四、连接接待流程

### 4.1 等待单一来宾

**STEP 07：定义有限等待。** `True`表示已出现可用来宾；程序结束或读数不可用时返回`False`。没有目标可以继续等，但多目标、截断或处理过慢需要先处理，不能随意选一个框继续。
'''),
(C, '''
def wait_for_guest(seconds=10.0):
    started = time.monotonic()
    while time.monotonic() - started < seconds:
        error, ratio, note = observe_target()
        if error is not None:
            print("发现可用来宾，占比：", round(ratio, 3))
            return True
        if note != "未检测到目标":
            print("等待结束：", note)
            return False
        time.sleep(0.2)
    print("等待结束：规定时间内没有单一可用来宾")
    return False
'''),
(M, '''
### 4.2 跟随，直到可以交给致意环节

**STEP 08：定义跟随函数。** 每轮重新取图，L1方向偏差决定转向，L2框高阈值决定是否继续前进。满足到位条件先发零速度并累计次数；任一轮不满足就清零计数。到位后返回“到位”，读数无效或达到时限则返回原因。

IMU和里程计与L3相同，记录在`motion_rows`中。到位确认期间记录静止读数，其他轮在短步末尾采样；这些值不用于判断来宾是否已经到位，也不作为侧倾或打滑诊断。
'''),
(C, '''
def follow_to_guest():
    global motion_rows, start_pose
    motion_rows = []
    robot.reset_odom()
    start_pose = list(robot.get_odom().pose_2d)
    arrived_count = 0
    started = time.monotonic()
    try:
        while time.monotonic() - started < RUN_SECONDS:
            error, ratio, note = observe_target()
            if error is None:
                return note
            vx, yaw_rate, decision = choose_velocity(error, ratio)
            at_goal = ratio >= STOP_RATIO and abs(error) <= CENTER_PX
            if at_goal:
                robot.set_velocity(0, 0, 0)
                arrived_count += 1
                decision = "到位确认"
            else:
                arrived_count = 0
                robot.set_velocity(vx, 0, yaw_rate)
            try:
                time.sleep(PULSE_SECONDS)
                wz = robot.get_imu().angular_velocity[2]
                x, y, yaw = robot.get_odom().pose_2d
            finally:
                robot.set_velocity(0, 0, 0)
            motion_rows.append([x, y, yaw, error, ratio, wz, decision])
            print(f"{decision}：偏差{error:+.0f}px，占比{ratio:.3f}，确认{arrived_count}/{ARRIVAL_CHECKS}")
            if arrived_count >= ARRIVAL_CHECKS:
                return "到位"
        return "跟随达到观察时限，未完成连续到位确认"
    finally:
        robot.set_velocity(0, 0, 0)
'''),
(M, '''
### 4.3 致意前再次确认

跟随返回“到位”后，先停止速度，再由教师确认停稳及动作空间。输入确认期间来宾仍可能移动，所以确认后重新取图；目标不可用、偏离中心或再次变远时跳过致意，不使用确认前的旧画面。

**STEP 09：定义致意检查与调用。** 只有实际状态`SUCCEEDED`才返回“致意任务成功”。等待超时会请求取消，并保留当前状态；是否已完整做出动作仍要现场记录。若本机动作采用等待后取消才释放占用，先记录实际行为和取消终态，交教师审定，不将`CANCELLED`自动改写成成功。
'''),
(C, '''
def greet_guest():
    global greet_task
    if greet_task is not None and not greet_task.done():
        return "旧致意任务仍未结束"
    if input("已停稳且动作空间合适？输入“致意”：").strip() != "致意":
        return "未确认致意"
    if robot.get_mode() != "walk":
        return "当前模式不满足致意条件"
    error, ratio, note = observe_target()
    if error is None:
        return "致意前目标不可用：" + note
    if ratio < STOP_RATIO or abs(error) > CENTER_PX:
        return "来宾位置已改变，跳过致意"
    if GREET_ID not in [action.id for action in robot.list_actions()]:
        return "致意动作ID不在当前列表"
    greet_task = robot.do_action(GREET_ID)
    status = greet_task.wait(timeout=ACTION_WAIT)
    if not greet_task.done():
        greet_task.cancel()
        greet_task.wait(timeout=3.0)
        return "致意等待超时，取消后状态：" + str(greet_task.status)
    if status == "SUCCEEDED":
        return "致意任务成功"
    return "致意任务状态：" + str(status)
'''),
(M, '''
### 4.4 运行完整流程

**STEP 10：本轮批准后执行一次。** 本格调用前面的函数，实际转向、前进并可能致意。来宾缓慢移动后停留，教师全程看护。旧致意句柄未结束时不启动新一轮；其他连接的旧任务也需事先人工核查，本句柄检查不能覆盖它们。

`finally`用于正常退出或可处理的异常、中断时尝试发送零速度。若中断发生在动作等待期间，还需运行STEP 11检查动作句柄；零速度不能代替取消动作。断网或强制终止内核时按现场按钮流程处置。
'''),
(C, '''
APPROVED = False
flow_reason = "本轮未运行"
motion_rows = []
start_pose = None
end_pose = None
if not APPROVED or robot.get_mode() != "walk":
    print("现场或模式条件未满足")
elif greet_task is not None and not greet_task.done():
    print("旧致意任务未结束，请先执行STEP 11")
elif input("本轮可接待？输入“接待”：").strip() == "接待":
    flow_reason = "执行中断或异常，请核对报错与旧任务"
    try:
        robot.set_velocity(0, 0, 0)
        if wait_for_guest():
            flow_reason = follow_to_guest()
            print("跟随结果：", flow_reason)
            if flow_reason == "到位":
                flow_reason = greet_guest()
        else:
            flow_reason = "等待未获得单一可用来宾"
    finally:
        robot.set_velocity(0, 0, 0)
    print("本次接待结束：", flow_reason)
'''),
(M, '''
### 4.5 检查任务、记录终点，再收尾

**STEP 11：检查并结束仍活动的致意任务。** 保留原句柄；请求取消后仍未结束时，先由教师处理，不启动下一轮。发送停止指令、得到取消终态和机器人实际停稳是需要分别核对的事情。
'''),
(C, '''
robot.set_velocity(0, 0, 0)
if greet_task is None:
    print("本轮没有致意句柄")
else:
    if not greet_task.done():
        greet_task.cancel()
        greet_task.wait(timeout=3.0)
    print("致意状态：", greet_task.status, "任务已结束：", greet_task.done())
print("请现场确认机器人已经停稳")
'''),
(M, '''
**STEP 12：停稳后读取最终位移与朝向。** `dx、dy`和方向角相对清零后里程计的参考轴；方向角表示起点到终点的方向，yaw表示机身朝向，两者可以不同。直线位移不等于沿途路程。这里的终点包括本轮致意可能产生的位置变化，不能全算作跟随运动。
'''),
(C, SUMMARY + '''

if start_pose is None:
    print("本轮未进入跟随，没有起点记录")
else:
    end_pose = list(robot.get_odom().pose_2d)
    report_motion(start_pose, end_pose, motion_rows)
    print("本次结束原因：", flow_reason)
'''),
(M, '''
**STEP 13：回到准备姿态。** 先确认STEP 11任务已结束，再运行此格；未确认时先处理旧任务。随后按既定人工支撑与阻尼流程扶坐，禁止行走模式直接切阻尼。
'''),
(C, '''
if greet_task is not None and not greet_task.done():
    print("致意任务尚未结束，请教师先处理")
else:
    robot.set_velocity(0, 0, 0)
    robot.set_mode("prepare")
    print("当前模式：", robot.get_mode())
'''),
(M, '''
## 五、接待记录与学习检查

### 5.1 按步骤核对

| 轮次/版本 | 来宾路线与标定条件 | 停止占比/速度/确认次数 | 等待结果 | 跟随结束原因 | 致意状态与现场表现 | 最终卷尺间距 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | |
| 2 | | | | | | |

正常接待之外，再安排一次来宾未出现或在开始前移出画面的测试；不能进入后续跟随或致意。运动中自然发生丢失、截断或多目标时保存输出，不为凑测试让人员突然穿进路线。

| 起始x/y/yaw | 终点x/y/yaw | 直线位移/方向 | 采样IMU角速度 | 当前任务是否结束 | 待改项 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

### 5.2 引用前三课的依据

- L1：记录用于本课的方向偏差符号、比例系数及转向上限；若方向不对，先处理再行走。
- L2：带入同一目标及拍摄条件的停止占比，引用静态采样与实测间距；里程计/卷尺实验用于理解位移估计误差。
- L3：引用移动目标的跟进、近处暂停、再次远离和小幅偏转记录；本课增加连续到位及致意交接，不重新证明身份跟踪或融合定位。

### 5.3 检查点与思考

1. 哪两项图像量决定跟随？为什么移动目标的接近不再由“起步间距减去1.2米”控制？
2. 连续到位计数什么时候增加、什么时候清零？连续3次满足能证明来宾完全静止吗？
3. 教师输入“致意”后为何还要再取图？来宾已经远离时函数会返回什么？
4. 里程计终点位移和IMU角速度能说明什么，为什么不能单独用它们证明已走到来宾跟前？
5. 任务返回`CANCELLED`，但现场看见动作完成，记录应怎样写？还需核对什么才能再次接待？

**本课完成依据**：一份真实接待记录、至少一项未满足条件时的阻断记录、停稳后的位移/朝向说明，以及旧任务退出记录。没有执行的步骤写明“未执行”。
'''),
(M, '''
## 六、扩展阅读：从课堂接待到应用

当前程序限定单一来宾、短路线和稳定拍摄条件，没有人物身份关联、障碍物识别或路线导航。来宾走动会改变身形和框大小，所以应从缓慢、面向相机的场景逐步验证，不能把一轮接待结果推广为任意人群中的自主服务。

相机控制方向和接近，IMU与里程计记录机身运动，信息在流程中有不同用途；当前没有将它们合成为统一的位置估计。后续U7再专门讨论多路信息的更新与多模态衔接，本课不提前引入订阅、线程或语音。

每次复测先固定目标、头部姿态、路线和参数，只改变一个待研究条件。若框高阈值附近反复切换，先检查检测波动与动作节奏；如果目标不完整或状态不可确认，应结束并重新检查，不能为完成接待而删掉条件。
'''),
]

write_notebook('U4-L3', L3, 15)
write_notebook('U4-L4', L4, 16)
