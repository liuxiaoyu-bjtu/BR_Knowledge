"""按v5生成本轮P1；不导入SDK、不运行机器人。复跑前须核对学生手改。"""
from pathlib import Path
import json
import textwrap
import hashlib
import pprint

ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
OUT = COURSE / 'notebooks'
LESSONS = []


def md(s):
    return {'cell_type':'markdown','metadata':{},'source':textwrap.dedent(s).strip().splitlines(keepends=True)}


def code(s):
    return {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],
            'source':textwrap.dedent(s).strip().splitlines(keepends=True)}


def lesson(number, name, cells):
    for i, cell in enumerate(cells):
        cell['id'] = hashlib.sha256((name+str(i)).encode()).hexdigest()[:10]
    LESSONS.append((number,name,{'cells':cells,'metadata':{
        'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python'},'x_course':{'outline':'v5','phase':'P1','confirmation_1':False,'confirmation_2':False}},
        'nbformat':4,'nbformat_minor':5}))


lesson(25,'U7-L1_多传感器订阅',[
md('''
# U7-L1：多传感器订阅

**课程目标**

1. 能为一个多路状态观察任务选择订阅方式，用短回调保存各路最近记录，并查看同一观察时刻下的数据值。
2. 能区分源时间戳与本地接收时间，依据缺失、接收后时长及时间戳比较条件判断数据是否适合联合使用。
3. 能比较有限队列的两种丢弃策略，说明选择依据，结束全部订阅，并区分多传感器融合与本课的联合检查。
'''),
md('''
## 一、任务：为场景运行准备状态观察窗

机器人准备执行一段讲解或踢球程序。操作者需要同时知道：相机有没有画面，机器人是否正在转动，里程计位置有没有变化。每隔一秒显示三路最近记录；某路没有更新时，应明确标出，不能把上一次记录当作刚收到的数据。

本课先做一个不驱动机器人的状态观察窗，再人为放慢图像处理，比较队列如何影响收到的记录。机器人保持固定姿态；可在镜头前缓慢移动彩色卡片观察画面数值变化，无需让机器人运动。

| 需要回答的问题 | 使用的信息 | 程序安排 |
| --- | --- | --- |
| 当前收到的画面是什么样 | 图像尺寸、中心像素、源时间戳 | 图像到达后更新最近记录 |
| 是否有转动读数 | IMU的z轴角速度 | IMU到达后更新数值 |
| 位置和朝向读数是什么 | 里程计x、y、yaw | 里程计到达后更新数值 |
| 这份记录多久没更新 | 本地接收时刻 | 主程序显示时计算经过时长 |

### 1.1 多传感器融合与多模态

**多传感器融合**是把多个传感器的信息结合起来，得到对环境或机器人状态的估计或判断。例如把IMU和里程计的信息用于估计姿态或位置；实际系统还需处理误差、坐标和时间关系。把几路数值打印在一起，只完成了联合观察，不等于已经得到融合定位结果。

**多模态**涉及视觉、语音、动作等不同的信息或表达方式。相机与IMU是不同传感器；视觉检测后播放介绍、执行动作，则涉及多种模态的协作。多传感器融合可以为这种协作提供信息，两者关注的对象不同。
'''),
md('''
## 二、建立三路订阅

### 2.1 按需读取与订阅

`get_imu()`由主程序主动读取最近可用值；`subscribe_imu(on_imu)`登记一个回调，SDK收到更新时调用它。**回调**就是预先交给SDK、等数据到达时再执行的函数。本课使用SDK已有的回调机制，不需要先创建自己的线程。

回调只提取需要的值，保存为一份新记录；显示、比较和慢处理放在主程序中。这样可减少回调等待。三路分别更新，显示时依次取得的最近记录仍可能来自不同采集时刻。

⚠️ **实验安全**：本课不发运动或模式切换指令。机器人保持坐稳或站稳，避免碰动机器人。若需调整站姿，先按既定模式与人工支撑流程操作，完成后再运行采集。

📌 **前置**：已连接机器人；旧订阅已退订；在Notebook所在目录运行。

**STEP 01：连接并查看模式。**
'''),
code('''
import time
from boosteros.robots.booster import BoosterRobot

robot = BoosterRobot()
print("机器人：", robot.robot_info.model, robot.robot_info.serial_number)
print("模式：", robot.get_mode())
'''),
md('''
### 2.2 同一观察时刻显示哪些值

`latest`中每路保存一份记录，包括数据值、源时间戳和本地接收时刻。`time.monotonic()`用于计算本程序中的时间间隔，不能与SDK源时间戳直接相减。

**STEP 02：订阅三路，每秒显示一次，共观察五次。** 回调每次替换完整记录；主程序取出后使用这份记录，不在同一次打印中反复读取正在更新的字段。`with`覆盖整个观察过程，正常结束或中断时退出并退订。

输出中的“接收后”表示这份记录被本程序接收后经过多久。它不包含传感器采集到回调开始前的传输和排队时间，因此不能直接当作完整延迟。
'''),
code('''
latest = {"图像": None, "IMU": None, "里程计": None}

def on_image(image):
    received = time.monotonic()
    pixels = image.to_numpy()
    latest["图像"] = {"source": image.header.timestamp, "received": received,
                      "value": f"{image.width}×{image.height}，中心像素{pixels[image.height//2, image.width//2].tolist()}"}

def on_imu(imu):
    latest["IMU"] = {"source": imu.timestamp, "received": time.monotonic(),
                     "value": f"z轴角速度={imu.angular_velocity[2]:.3f} rad/s"}

def on_odom(odom):
    x, y, yaw = odom.pose_2d
    latest["里程计"] = {"source": odom.timestamp, "received": time.monotonic(),
                        "value": f"x={x:.3f} m，y={y:.3f} m，yaw={yaw:.3f} rad"}

with robot.subscribe_image(on_image, queue_size=1, overflow="drop_oldest"), \\
     robot.subscribe_imu(on_imu, queue_size=1, overflow="drop_oldest"), \\
     robot.subscribe_odom(on_odom, queue_size=1, overflow="drop_oldest"):
    for number in range(5):
        time.sleep(1.0)
        snapshot = dict(latest)
        observed = time.monotonic()
        print(f"\\n观察{number+1}，本地时刻={observed:.3f}")
        for name in ["图像", "IMU", "里程计"]:
            record = snapshot[name]
            if record is None:
                print(name, "尚未收到")
            else:
                age = observed-record["received"]
                print(name, record["value"], "源时间戳=", record["source"],
                      f"接收后{age:.3f}秒")
print("三路观察已结束，订阅已退出")
'''),
md('''
记录一组完整快照。图像中心像素随卡片变化时，另外两路不一定发生明显变化；读数不变与没有更新要结合接收时刻判断。

| 观察编号 | 图像数值/接收后时长 | IMU数值/接收后时长 | 里程计数值/接收后时长 | 缺失或待查项 |
| --- | --- | --- | --- | --- |
| | | | | |

### 2.3 核对源时间戳

源时间戳描述数据对应的时刻。比较图像和IMU前，须核实单位及计时基准一致；同为一个数值类型不代表可以直接比较。若单位为秒且同源，图像－IMU为负，表示这份图像的时刻较早。各路最近记录的差值没有完成同步配对，也不表示当前数据年龄。

**STEP 03：检查最后一份快照的时间戳。** 未核实时保持`False`，记录原值即可。
'''),
code('''
TIMESTAMPS_VERIFIED = False  # 教师核实单位为秒且基准一致后修改
if not TIMESTAMPS_VERIFIED:
    print("本次仅保留源时间戳原值，单位与基准待核")
elif snapshot["图像"] is None or snapshot["IMU"] is None or snapshot["里程计"] is None:
    print("缺少记录，不能比较")
else:
    print("图像－IMU：", (snapshot["图像"]["source"]-snapshot["IMU"]["source"])*1000, "毫秒")
    print("图像－里程计：", (snapshot["图像"]["source"]-snapshot["里程计"]["source"])*1000, "毫秒")
'''),
md('''
## 三、处理跟不上时保留什么

队列保存等待回调处理的数据。传感器订阅`queue_size=0`表示不设容量上限；本课状态观察需要近期数据，因此显式设置有限容量。

| 队列满时的策略 | 处理 | 适用取舍 |
| --- | --- | --- |
| drop_oldest | 丢弃最旧的待处理项，留下新到的数据 | 优先了解近期状态，但会遗漏中间数据 |
| drop_newest | 丢弃新到的数据，保留正在等待的旧项 | 保留已排队项，收到的记录可能更旧 |
| block | 等待队列有空位 | 会产生等待，不能保证完整链路无损 |

### 3.1 用慢回调比较两种策略

**STEP 04：运行下面定义。** 这里特意把图像回调放慢到约0.3秒，用于暴露排队现象；实际状态观察应采用STEP 02的短回调。实验保持机器人和场景条件相近，分别记录两种策略。回调中只采集时间记录，实验结束后打印，减少打印对比较的干扰。
'''),
code('''
def queue_trial(policy):
    rows = []
    def slow_image(image):
        received = time.monotonic()
        time.sleep(0.3)
        rows.append((image.header.timestamp, received))
    with robot.subscribe_image(slow_image, queue_size=1, overflow=policy):
        time.sleep(3.0)
    print("策略：", policy, "已处理条数：", len(rows))
    for stamp, received in rows[-5:]:
        print("源时间戳：", stamp, "回调开始的本地时刻：", round(received, 3))
    return rows
'''),
md('''
**STEP 05：先运行drop_oldest，结束后再运行下一格。** 运行期间可以缓慢移动卡片，不碰机器人。
'''),code('''
oldest_rows = queue_trial("drop_oldest")
'''),md('''
**STEP 06：比较drop_newest。** 条数接近不表示保留了相同的数据。核实时间戳单位后，可比较相邻源时刻间隔与回调开始间隔；本实验没有记录全部原始消息，因此不能准确统计每条被丢弃的数据，也不能保证每次差异都明显。
'''),code('''
newest_rows = queue_trial("drop_newest")
'''),
md('''
### 3.2 为状态观察窗作选择

| 策略 | 已处理条数 | 末几条源时间戳与间隔 | 本次能确认什么 | 仍不能确认什么 |
| --- | --- | --- | --- | --- |
| drop_oldest | | | | |
| drop_newest | | | | |

状态观察窗关心近期读数，可以选择小队列和`drop_oldest`，同时显示接收后时长；若要保存全部采样用于离线分析，还需另行设计处理能力和存储，不能把本课设置当作无损采集方案。

本课实验结束时，各格的`with`均已退出，无需切换模式来证明退订。按教师安排保持当前安全姿态；需要关机时执行既定人工收尾流程。

## 四、学习检查

1. 在STEP 02某次观察中，三路数值分别是什么？哪路记录被接收得更早？这一结果能否说明采集顺序？
2. 某路“接收后”很短，但源数据已经排队很久，显示值能证明端到端延迟很小吗？说明还缺少什么信息。
3. 为当前状态窗选择队列策略，并结合本次记录解释代价；若两次实验差异不明显，应如实记录。
4. 说明多传感器融合、多路联合打印和视觉—语音—动作协作各关注什么。给出一个需要融合估计的例子，但不把本实验称为已实现定位融合。

**完成核对**：有数值的三路快照、源时间戳核实状态、队列记录和策略说明均已保存；全部订阅已退出。
''')])

lesson(26,'U7-L2_足球定位与自动踢球',[
md('''
# U7-L2：足球定位与自动踢球

**课程目标**

1. 能区分图像像素、机器人坐标与里程计坐标，用前向x、左向y及弧度方向解释球位置和踢球指令。
2. 能在固定相机与姿态条件下采集标定点，用独立卷尺点核对球坐标估计，说明误差和适用范围。
3. 能持续更新球坐标，使用自动踢球管理器进行有限时段的尝试，丢球或数据不可用时停止，并分别记录程序原因和实际踢球效果。
'''),
md('''
## 一、任务：把看见的球交给踢球控制

足球检测告诉程序球在画面的哪个位置。自动踢球管理器需要知道球相对机器人前方多远、左侧多远。若把“画面横坐标200”当作“前方200米”下发，数据形式都是数字，含义却完全不对。

本课先在机器人不移动时核对球坐标，再运行一次短时踢球尝试。球被踢出后，管理器接口没有返回本课可直接使用的“射门成功”；是否踢出、是否进入目标区由同学现场观察或录像记录。

### 1.1 三种坐标

| 坐标 | 原点和方向 | 本课用途 |
| --- | --- | --- |
| 图像(u,v) | 左上角；右为u正、下为v正；单位像素 | 检测框位置 |
| 机器人(x,y) | 按本机约定的机身参考原点；前为x正、左为y正；单位米 | update_ball的输入 |
| 里程计 | 相对建立/清零时的参考位置和朝向 | 描述机器人自身位移，不能单独给出未知球位置 |

球在前方0.8米、左侧0.2米，对应`x=0.8, y=0.2`。机器人原地转向后，即使球没动，相对坐标也会改变，因此运行中必须更新。`direction=0`表示相对机器人当前朝向向前踢，正角度朝左；不是世界坐标中的固定朝向。
'''),
md('''
## 二、先取得足球的图像位置

⚠️ **实验安全**：静态定位时机器人站稳并由同学保护，不发运动指令。踢球前单独确认平整场地、球和目标区，人员离开机器行进及出球方向；使用K1与已验证球型。异常时使用现场既定按钮流程切回准备模式，不能只依赖程序检查。

📌 **前置**：旧订阅、音频及运动任务已结束；`x_lab/`附件与Notebook在同一目录；教师已确认本机机身坐标原点和标定时头部、站姿。

**STEP 01：连接并查看模型。** `soccer`模型示例类别为`Ball`；以本机实际输出核对，不能直接取检测列表第一项。
'''),code('''
import time
import json
from pathlib import Path
from boosteros.robots.booster import BoosterRobot, SoccerKickManager
from boosteros.brain import Detection
from x_lab.ball_position import select_ball, ball_pixel, build_calibration, pixel_to_robot, verify_calibration

robot = BoosterRobot()
detector = Detection(model="soccer")
BALL_CLASS = "Ball"
soccer = SoccerKickManager(robot)  # 创建对象不等于开始踢球
kick_active = False              # 本格仅首次运行，不能覆盖仍在运行的管理器
print("机型：", robot.robot_info.model, "模式：", robot.get_mode())
'''),md('''
**STEP 02：静止观察。** 在前方放一只球，打印实际类别、评分及框下缘中点(u,v)。`to_numpy()`把SDK图像转为检测接口接受的数组。框下缘中点只是地面位置的近似线索，球轮廓下缘不等于精确接触点。
'''),code('''
image = robot.get_image(img_type="rgb")
results = detector.detect(image.to_numpy(), confidence=0.4)
for result in results:
    print(result.class_name, round(result.confidence, 3))
ball = select_ball(results, BALL_CLASS)
if ball is None:
    print("未检出足球；先核对类别、光照与球，不进行坐标计算")
else:
    u, v = ball_pixel(ball)
    print("分辨率：", image.width, image.height)
    print(f"球的图像线索：u={u:.1f}, v={v:.1f} 像素")
'''),md('''
## 三、标定与卷尺核对

### 3.1 用对应点建立近似换算

在已知地面位置放球，同时记录检测框线索。至少取四个不共线的点，覆盖准备使用的区域：既有远近差异，也有左右差异。横向坐标以机器人机身参考原点为基准测量，不能从一只脚随意起算。教师可课前完成标定，本组至少核对三个未参与拟合的点。

附件`x_lab/ball_position.py`根据对应点建立近似映射，本课不要求推导矩阵求解。输入是(u,v)像素，输出是(x,y)米；它不读取深度，也不能自动抵消头部转动、机身俯仰或步态带来的变化。

**STEP 03：填写实测样本。** 每次放球后重跑STEP 02记录一行。`samples`每行顺序为`[u, v, x米, y米]`；不能使用假设坐标启动运动。保留相机分辨率、头部角度、站姿与球型说明；改变这些条件后重新标定。
'''),code('''
samples = [
    # 在此填写至少四行实测值：[u, v, x米, y米]
]
SETUP_NOTE = ""  # 填写实际头部角度、站姿、坐标原点、地面与球型
calibration = None
if len(samples) < 4 or not SETUP_NOTE:
    print("等待填写标定点与姿态记录")
else:
    calibration = build_calibration(samples, [image.width, image.height], SETUP_NOTE)
    print("已建立映射，仍需独立卷尺核对，不能启动踢球")
'''),md('''
### 3.2 核对没有参与拟合的位置

**STEP 04：在标定区域内部另选至少三个点。** 重新测量(x,y)并运行STEP 02读取(u,v)，填写`check_points`。教师根据球大小、踢球动作和场地确定容许误差，不能把某个示例数值作为通用标准。超出标定区域时附件拒绝估计；不能直接删除范围检查来继续。
'''),code('''
check_points = [
    # 独立实测：[u, v, x米, y米]，不能重复拟合点
]
TOLERANCE_M = None  # 教师根据实机与球确定的容许误差（米）
if calibration is None or len(check_points) < 3 or TOLERANCE_M is None:
    print("标定或独立核对资料未齐")
else:
    errors = verify_calibration(calibration, check_points, TOLERANCE_M)
    for i in range(len(errors)):
        print(f"核对点{i+1}：平面位置误差{errors[i]:.3f}米")
    print("全部满足本次误差要求：", calibration["verified"])
    Path("ball_calibration.json").write_text(json.dumps(calibration, ensure_ascii=False, indent=2), encoding="utf-8")
'''),md('''
| 核对点 | 实测x/y（米） | 估计x/y（米） | 平面位置误差（米） | 是否可用于本次任务 |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

静止核对通过，只说明当前条件下的估计达到本次要求。机器人进入足球步态后相机姿态可能变化，教师还需在运动条件下检查可用范围；没有这项核查时停留在静态实验，不进入下一部分。

## 四、把新坐标交给自动踢球管理器

### 4.1 接口与控制权

| 调用 | 含义 |
| --- | --- |
| SoccerKickManager(robot) | 绑定机器人；T2目前不支持 |
| start() | 开启自动踢球控制，可能切换足球模式 |
| update_command(direction, power) | 设置相对当前机身的踢球方向(rad)与力度(1～10) |
| update_ball(x, y) | 持续提供当前机器人坐标系中的球位置(米) |
| stop() | 关闭控制，并清空球位置与踢球指令 |

这些调用返回`None`，没有可供`wait()`的踢球任务句柄。管理器已负责自动运动时，不再并发发送`set_velocity()`、`do_action()`或轨迹回放。`stop()`用于释放这段控制，现场还需观察是否停稳。

### 4.2 有限窗口内更新，不发送旧球位

**STEP 05：定义实验函数。** 每轮重新取图、检测并换算，未检出或超出范围就退出。记录取图前的本地时刻，检查本次取图与处理是否过慢；这不是完整图像采集延迟。下面0.8秒仅为待本机调试的上限，不能证明满足通用控制要求。
'''),code('''
def try_soccer():
    global kick_active
    if kick_active:
        print("旧管理器可能仍占用，请先执行STEP 07")
        return
    if calibration is None or not calibration["verified"]:
        print("独立标定核对未通过，不启动")
        return
    reason = "达到观察上限；踢球效果另记"
    rows = []
    try:
        kick_active = True
        soccer.start()
        soccer.update_command(direction=0.0, power=1.0)
        started = time.monotonic()
        last_source = None
        while time.monotonic()-started < 6.0:
            if not robot.get_fall_down_state().is_normal:
                reason = "机器人状态异常"
                break
            received = time.monotonic()
            img = robot.get_image(img_type="rgb")
            found = select_ball(detector.detect(img.to_numpy(), confidence=0.4), BALL_CLASS)
            if found is None:
                reason = "未检出足球"
                break
            if img.header.timestamp == last_source:
                reason = "图像源时间戳未更新"
                break
            last_source = img.header.timestamp
            u, v = ball_pixel(found)
            x, y = pixel_to_robot(calibration, u, v, [img.width, img.height])
            if time.monotonic()-received > 0.8:
                reason = "本次取图与处理超时"
                break
            soccer.update_ball(x, y)
            rows.append((x, y))
            time.sleep(0.1)
    except (RuntimeError, ValueError) as exc:
        reason = "调用或坐标不可用：" + str(exc)
    finally:
        soccer.stop()
        kick_active = False  # 只有stop返回后才清除
    print("停止原因：", reason, "下发坐标次数：", len(rows))
    print("最近坐标（米）：", rows[-5:])
'''),md('''
**STEP 06：现场批准后启动。** 确认标定姿态与当前画面一致，教师已验证足球步态下估计可用，旧任务已退出。先按按钮流程切到准备模式，等站稳，再按本机要求进入行走模式。管理器启动后由它控制足球行为。

<font color="red">球和人员位置已核对、出球方向无人、保护同学就位后，才运行下一格；不要连续“全部运行”。</font>
'''),code('''
APPROVED_FOR_MOTION = False  # 本次场地、动态标定和保护确认后由教师指导修改
if not APPROVED_FOR_MOTION or robot.get_mode() != "walk":
    print("尚未满足本次运动条件")
elif input("确认本次可试踢，输入“试踢”：").strip() == "试踢":
    try_soccer()
'''),md('''
**STEP 07：检查退出与现场效果。** 若上一格报停止异常，保留原管理器，不重建连接；先运行本格重试停止。停止返回后观察是否停稳，并按教师要求人工复位。
'''),code('''
soccer.stop()
kick_active = False
print("管理器stop已返回；请现场核对停稳、球是否踢出及实际方向")
'''),md('''
本次试验后先用按钮切回准备模式并等站稳。需要坐下时按约定人工支撑、切换阻尼并坐稳，严禁从行走模式直接切阻尼。

## 五、记录与学习检查

| 版本/姿态 | 方向rad/力度 | 程序停止原因 | 是否踢出 | 球实际去向/视频 | 待核查项 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

1. 画面u增大表示向右，机器人y为正表示向左。为什么不能直接把u当作y？
2. 球不动、机器人转向后，update_ball的x/y为何应变化？
3. 标定使用的头部姿态改变后，为什么独立核对结果不能继续沿用？
4. 程序达到六秒、管理器stop返回、球进入目标区，分别能证明什么？

**完成核对**：已有标定与独立误差记录；运动条件未获批准时如实填未运行；试踢记录区分调用结果、停稳及球的效果；旧管理器已停止。
''')])

lesson(27,'U7-L3_多线程协作',[
md('''
# U7-L3：多线程协作

**课程目标**

1. 能解释视觉处理与语音播放的等待关系，用一个工作线程让检测继续更新。
2. 能用同一把锁交接完整检测记录，区分结果处理耗时、接收后时长与源时间戳。
3. 能发出停止请求并核查线程与音频任务是否结束，在未结束时保留原对象、不重复启动。
'''),md('''
## 一、任务：播报时继续观察目标

机器人发现目标后开始介绍。主程序等待播放结束时，如果检测也写在同一个顺序循环中，下一次检测要等播报结束才会开始。目标在这段时间可能移动，播报前的结果不能直接用于之后的行动。

本课让一个工作线程持续检测，主线程负责有限播报与显示。机器人保持静止；同学缓慢移动目标，比较播报前后结果。这里处理执行关系，不增加自动接近和踢球运动。

### 1.1 线程与SDK回调

**线程**是同一程序的一条执行路径。`Thread(target=detect_loop)`先登记函数，`start()`才开始运行。原来的Notebook程序是主线程，本课再创建一个检测工作线程。

L1把回调交给SDK，由SDK的工作机制在收到数据时调用。本课则自己安排一段反复“取图—检测—更新”的工作。两种方式都可能在主程序等待时继续工作，但不保证同时完成，也不保证相机数据没有延迟。

| 执行位置 | 工作 | 等待位置 |
| --- | --- | --- |
| 检测工作线程 | 取图、推理、保存结果 | 图像/推理调用和短暂间隔 |
| 主线程 | 发起播报，等待并查看结果 | 合成及播放任务等待 |
'''),md('''
## 二、建立可交接的检测记录

⚠️ **实验安全**：本课不发运动指令；机器人保持固定姿态，同学只移动检测目标。语音音量适中，远离出球和机器人运动实验。

📌 **前置**：旧管理器已stop；旧线程、订阅、识别或chat任务已结束；`x_lab/`附件可导入。

**STEP 01：首次连接，保存线程与音频任务。** 本格只在首次准备时运行。重复实验先检查旧对象，不能靠重跑本格抹掉句柄。
'''),code('''
import time
import threading
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech
from x_lab.ball_position import select_ball
from x_lab.flows import new_session, say, idle, cleanup

robot = BoosterRobot()
speech = Speech(robot)
detector = Detection(model="soccer")
TARGET_CLASS = "Ball"  # 也可统一改模型与类别，用person观察来宾
vision_thread = None
session = new_session(robot, speech)
print("模式：", robot.get_mode())
'''),md('''
### 2.1 锁与完整记录

检测结果包括“检出与否、位置、时间、编号”。如果读取到新编号配旧位置，主程序会误判。**锁**用于让一份记录的更新和复制按次序进行；读写双方都使用同一把锁。

`with lock:`内只做短暂赋值或复制，不能把取图、推理或播放放进去。`Event`提供停止标志：`set()`请求结束，`is_set()`读取请求；工作函数到检查位置才会响应。

**STEP 02：确认旧线程与音频都结束，再初始化。**
'''),code('''
if vision_thread is not None and vision_thread.is_alive():
    raise RuntimeError("旧检测线程仍在运行，先执行STEP 07")
if not idle(session):
    raise RuntimeError("旧音频任务未结束，先执行STEP 07")

lock = threading.Lock()
STOP = threading.Event()
shared = {"number": 0, "found": False, "u": None, "v": None,
          "received": None, "finished": None, "source": None, "error": None}
'''),md('''
**STEP 03：定义检测线程。** `received`从取图前开始计时，`finished`在推理结束后记录；两者之差含本次取图和处理。主线程读取后还要考虑记录已经放了多久。源时间戳另存，未核实时不与本地时钟相减。
'''),code('''
def detect_loop():
    try:
        while not STOP.is_set():
            received = time.monotonic()
            image = robot.get_image(img_type="rgb")
            target = select_ball(detector.detect(image.to_numpy()), TARGET_CLASS)
            u, v = None, None
            if target is not None:
                u, v = target.bbox.center_x, target.bbox.center_y
            finished = time.monotonic()
            with lock:
                shared.update(number=shared["number"]+1, found=target is not None,
                              u=u, v=v, received=received, finished=finished,
                              source=image.header.timestamp)
            time.sleep(0.1)
    except Exception as exc:
        with lock:
            shared["error"] = str(exc)
        STOP.set()

def read_observation():
    with lock:
        return dict(shared)
'''),md('''
## 三、比较播报前后的更新

**STEP 04：启动、观察和停止写在同一个格内。** 避免启动工作线程后停在人工等待格，留下不受当前实验管理的后台任务。播报时同学缓慢移动球；不要遮挡镜头或碰动机器人。

`say()`附件按U5有限文本任务的用法先合成再播放，并保存任务句柄；等待超限会取消并保留实际状态。播报未成功也要核查线程和句柄。
'''),code('''
before = None
after = None
if STOP.is_set() or (vision_thread is not None and vision_thread.is_alive()):
    raise RuntimeError("请先收尾，再从STEP 02开始")
vision_thread = threading.Thread(target=detect_loop, daemon=True)
try:
    vision_thread.start()
    time.sleep(1.0)
    before = read_observation()
    print("播报前：", before)
    result = say(session, "我正在介绍这个场景。请同学缓慢移动目标，观察检测是否仍在更新。")
    after = read_observation()
    print("播报结果：", result)
    print("播报后：", after)
finally:
    STOP.set()
    vision_thread.join(timeout=3.0)
print("检测线程仍在运行：", vision_thread.is_alive())
'''),md('''
### 3.1 哪些结果还能用

**STEP 05：检查记录编号和时长。** 编号增大表示期间又完成了检测，不能单独证明球识别正确。`None`表示没有结果，不能替换成“球在中心”。一秒上限是本次观察练习的待调参数，不是运动安全保证。
'''),code('''
if before is None or after is None or after["received"] is None:
    print("本次没有完整比较记录")
else:
    print("期间完成检测次数：", after["number"]-before["number"])
    processing = after["finished"]-after["received"]
    stored = time.monotonic()-after["finished"]
    print(f"本次取图和处理{processing:.3f}秒，处理后又经过{stored:.3f}秒")
    usable = after["found"] and time.monotonic()-after["received"] <= 1.0
    print("按本次条件是否仍可使用：", usable)
'''),md('''
**STEP 06：停留约两秒后再次运行上一格。** 原来的`after`变量不会因为线程曾运行过就自动更新。说明此时“可使用”判断为何可能变化。若要比较目标变化，应先完整收尾，再从STEP 02开始新一轮，不能把已结束线程的旧记录当作实时检测。

## 四、退出与重复运行

**STEP 07：分别核查线程和SDK任务。** `join(timeout=3)`返回不保证线程已退出，仍需看`is_alive()`；SDK任务也需检查自身终态。没有全部结束前保留原对象，不重建连接或重新绑定STOP。
'''),code('''
STOP.set()
if vision_thread is not None:
    vision_thread.join(timeout=3.0)
    print("线程仍在运行：", vision_thread.is_alive())
print("音频待处理项：", cleanup(session))
print("音频任务均已结束：", idle(session))
print("检测错误：", read_observation()["error"])
'''),md('''
本课没有运动，无需额外切换模式。确认后台资源结束，按教师安排保持姿态或执行既定人工关机流程。

## 五、记录与学习检查

| 轮次 | 播报前/后编号 | 目标与坐标变化 | 处理时长/存放时长 | 播报状态 | 线程与音频退出 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

1. 同一格中，主线程在等待播放，检测编号仍可能增大的原因是什么？
2. 为什么取图或播报不应放在`with lock:`中？锁能保证各传感器采集时刻一致吗？
3. STOP已置位而线程仍存活时，为什么不应重新创建STOP并启动另一个线程？
4. 播报结束后直接使用播报前的球位置有什么问题？给出可执行的更新与拒用条件。

**完成核对**：有播报前后记录及时间含义说明；线程与音频任务分开核查；重复实验至少完整执行一轮退出检查。
''')])

lesson(28,'U7-L4_多模态流程衔接',[
md('''
# U7-L4：多模态流程衔接

**课程目标**

1. 能为感知、播报和行为片段写出交接条件，说明播报之后为何需要新观测。
2. 能分别运行导览和足球的局部参考片段，按所用接口管理任务句柄或自动踢球控制。
3. 能记录程序返回原因、SDK状态和现场表现，未完成时停止后续操作，并核查重复运行条件。
'''),md('''
## 一、任务：一句播报之后还能按原计划行动吗

定点导览发现来宾后准备介绍并致意；足球场景发现球后准备说明并试踢。两者都需要视觉、语音和行为衔接，但播报结束时目标可能已经移动或离开。

本课比较两个局部片段：`确认目标 → 播报 → 重新确认 → 一次行为`。只运行这个交接过程，记录在哪里结束。导览暂不增加路线，足球不增加比赛策略。

| 交接点 | 导览 | 足球 |
| --- | --- | --- |
| 首次确认 | 单名来宾可见 | 足球在已核对的标定范围 |
| 播报后新观测 | 仍有来宾才致意 | 球坐标仍可用才进入管理器 |
| 行为结束 | 检查动作句柄实际状态及现场表现 | stop返回，并现场记录球的效果 |

### 1.1 多模态协作不要求所有步骤同时运行

L3展示了播报期间继续检测的方式。若片段只需在播报结束后重新确认，顺序程序就能满足需求；若要求期间持续观察，才增加工作线程和退出管理。本课先用顺序片段把交接条件核对清楚。多模态指信息与行为方式的协作，不等于必须多线程。
'''),md('''
## 二、准备功能片段

⚠️ **实验安全**：致意和踢球均可能带动机身。两类片段分开运行，先清理上一类任务，再核对各自场地。踢球场地、标定与保护要求同L2；不在踢球管理器运行时另发速度、轨迹或动作指令。

📌 **前置**：L3线程与音频已结束；拟用动作已验证模式、时长和范围；踢球需有`ball_calibration.json`及足球步态下的教师验证。

**STEP 01：首次连接并保存会话记录。** `session`附件记录当前音频、动作及踢球管理器，重试前用它检查旧任务，不重跑连接格覆盖它。
'''),code('''
import json
from pathlib import Path
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech
from x_lab.flows import new_session, idle, observe_guest, observe_ball, say, greet, kick_window, cleanup
import time

robot = BoosterRobot()
speech = Speech(robot)
guest_detector = Detection(model="person")
ball_detector = Detection(model="soccer")
session = new_session(robot, speech)
calibration = None
if Path("ball_calibration.json").exists():
    calibration = json.loads(Path("ball_calibration.json").read_text(encoding="utf-8"))
for action in robot.list_actions():
    print(action.id, action.type, action.duration)
'''),md('''
### 2.1 用返回原因决定交接

每个片段返回“完成”或具体停止原因。有限文本合成、播放、动作有任务句柄；自动踢球管理器的四个控制调用返回`None`。不能给所有接口套上相同的`wait()`。

附件`x_lab/flows.py`提供已学功能片段：`say()`合成与播放，`greet()`等待动作，`kick_window()`持续检测并更新球位。它们保存旧句柄、限制等待、必要时取消或停止，供本课和应用项目复用。可打开附件核对实际SDK调用，不把附件名称当作SDK接口。

`greet()`仅在`SUCCEEDED`时返回“完成”；超时取消会返回实际原因。某些已实测动作采用等待后取消时，应分别记录现场动作与取消终态，不把`CANCELLED`改写为成功；本次未获成功状态则结束片段，待教师审定该动作的具体交接约定。

**STEP 02：定义导览局部片段。** 来宾在通道外站定；本片段不驱动接近，不判断人物身份。首次及播报后的观察都检查本次取图与处理时长，0.8秒是待本机核对的练习参数；取得新源图像后才进入行为。
'''),code('''
GREET_ID = ""  # 从实际动作清单填写已验证的ID

def guide_segment():
    first = observe_guest(robot, guest_detector)
    if not first["found"]:
        return "首次未检出来宾"
    if time.monotonic()-first["received"] > 0.8:
        return "首次取图与处理过慢"
    result = say(session, "欢迎参观。请在指定区域观看机器人的致意动作。")
    if result != "完成":
        return "播报：" + result
    current = observe_guest(robot, guest_detector)
    if not current["found"]:
        return "播报后未检出来宾"
    if time.monotonic()-current["received"] > 0.8:
        return "播报后取图与处理过慢"
    if current["source_stamp"] == first["source_stamp"]:
        return "播报后尚无新图像"
    return greet(session, GREET_ID)
'''),md('''
**STEP 03：定义足球局部片段。** 播报时管理器尚未开始；之后重新核对球位，管理器启动后仍需逐轮取新坐标。这里只设六秒观察窗口，不保证六秒内踢出或进球。
'''),code('''
def soccer_segment():
    if calibration is None or not calibration.get("verified", False):
        return "没有通过独立核对的标定"
    first = observe_ball(robot, ball_detector, calibration)
    if not first["found"]:
        return first["reason"]
    if time.monotonic()-first["received"] > 0.8:
        return "首次取图与处理过慢"
    result = say(session, "准备进行短时试踢，请留在场地外观看。")
    if result != "完成":
        return "播报：" + result
    current = observe_ball(robot, ball_detector, calibration)
    if not current["found"]:
        return "播报后：" + current["reason"]
    if time.monotonic()-current["received"] > 0.8:
        return "播报后取图与处理过慢"
    if current["source_stamp"] == first["source_stamp"]:
        return "播报后尚无新图像"
    reason, rows = kick_window(session, ball_detector, calibration, seconds=6.0, power=1.0)
    print("球坐标更新条数：", len(rows))
    return reason
'''),md('''
## 三、一次只验证一类交接

**STEP 04：先选导览，再按条件安排足球。** 定义格不会运动；执行格会发起实际任务。按按钮流程先进入准备模式、等站稳，再进入本机实验要求的行走模式。动作ID和模式应在现场复核。

<font color="red">导览确认动作范围；足球另确认标定姿态、动态适用范围、球位与出球方向。旧任务未结束时不试演。</font>
'''),code('''
SCENE = "导览"  # 另一选项为“踢球”
APPROVED = False  # 每次实际条件确认后修改
if not APPROVED or robot.get_mode() != "walk":
    print("尚未满足本次运行条件")
elif not idle(session):
    print("旧任务尚未结束")
elif SCENE not in ["导览", "踢球"]:
    print("请填写导览或踢球")
elif input("本次可运行，输入“运行”：").strip() == "运行":
    try:
        if SCENE == "导览":
            reason = guide_segment()
        else:
            reason = soccer_segment()
        print("片段返回：", reason)
    finally:
        print("收尾待处理项：", cleanup(session))
'''),md('''
**STEP 05：核查后再重试。** 返回原因表示程序条件，实际动作、来宾反应和球的去向另行记录。未确认结束时保留session，稍后重跑核查格；全部退出、人工恢复站位后才可重试。
'''),code('''
print("待处理项：", cleanup(session))
print("资源全部结束：", idle(session))
for key in ["audio_task", "motion_task"]:
    task = session[key]
    if task is not None:
        print(key, task.status, "done=", task.done())
print("踢球控制仍被本程序标为活动：", session["kick_active"])
'''),md('''
本次结束先切准备模式并等站稳；需要坐下时按人工支撑、切阻尼、坐稳的既定流程处理，不能从行走模式直接切阻尼。

## 四、记录与学习检查

| 片段 | 首次观测 | 播报结果 | 播报后新观测 | 返回原因/任务状态 | 现场行为 | 退出 |
| --- | --- | --- | --- | --- | --- | --- |
| 导览 | | | | | | |
| 踢球 | | | | | | |

1. 播报成功而目标已离开时，后续程序应怎样处理？指出两种片段中的对应行。
2. 什么需求值得增加L3工作线程？仅在播报后检查目标时，顺序程序能否完成任务？
3. 致意返回CANCELLED、踢球窗口达到上限，分别应怎样记录？为什么都不能直接填“表演成功”？
4. 若修改为一段完整应用，仍需确定哪些对象、场地、模块交接和验收要求？列出本组实际需要解决的项目问题。

**完成核对**：至少完成可用片段的交接记录，另一类按设备安排验证；未运行项明确标记。没有留下活动管理器、音频或动作任务。
''')])

lesson(29,'U8-L1_选题与任务拆解',[
md('''
# U8-L1：选题与任务拆解

**课程目标**

1. 能从导览或踢球委托中确定本组对象、场地和核心功能，写出可观察的验收条件。
2. 能拆分功能模块，约定输入、返回结果、未完成处理及责任人。
3. 能根据已验证能力、设备和时间取舍任务，形成开发与首轮测试计划。
'''),md('''
## 一、选择本组委托

请在下面两项委托中选择一项，先明确使用场景，再编写本组程序。现场作品不超过两分钟；无需为了增加时长重复动作。

| 委托 | 使用者需要什么 | 本组需要确定什么 |
| --- | --- | --- |
| A 导览 | 来宾在指定接待点获得准确、清楚的介绍，并看到适合场景的致意 | 介绍对象与内容、来宾站位、是否移动、动作与停止条件 |
| B 踢球 | 观众看到机器人识别足球并向指定方向尝试踢球，能够核对实际效果 | 球型、起点、目标区、标定范围、方向力度及停止条件 |

导览可以定点完成。若增加短距离移动，只使用已验证的片段，写明活动范围、来宾位置与停止条件；本任务不要求自动导航或返回起点。踢球使用U7管理器，不同时安排速度控制或预定义踢球动作。

### 1.1 从描述变为可核对的要求

“热情迎宾”“踢得准”还不足以验收。应写明运行前条件、机器人要做的行为、观察依据以及未完成时怎样退出。

**示例**：单名来宾站在指定区域，画面内无遮挡；机器人检出来宾后播放本组核对过的介绍。播放成功且来宾仍可见时再致意；未检出则说明原因并结束。现场分别记录是否听到完整介绍、动作表现及SDK状态。

这个示例没有承诺持续识别同一个人，也没有把播放等待返回等同于所有内容正确。要求越具体，后面的测试越容易安排。
'''),md('''
## 二、写需求与验收条件

**任务01（约9分钟）：选题并填写本组要求。** 每组确定一个核心流程，至少写一个可安全测试的未完成情况。不要把需要新模型、复杂算法或未验证硬件的功能列为本次必达项。

| 编号 | 对象与场地 | 运行前条件 | 机器人行为 | 完成的证据 | 未完成时处理 |
| --- | --- | --- | --- | --- | --- |
| R1核心功能 | | | | | |
| R2未完成处理 | | | | | |
| R3选做功能 | | | | | |

踢球作品中，“管理器stop已返回”是控制退出证据；“球进入目标区”要用现场位置或视频证明，两项分别记录。一次进球也不足以证明每次都能进球。

### 2.1 核查现成能力

| 能力 | 来源 | 本机已经验证到哪一步 | 本组需要调整/补测 |
| --- | --- | --- | --- |
| 视觉与类别筛选 | U3、U7 | | |
| 播报或会话 | U5 | | |
| 动作或踢球 | U6、U7 | | |
| 位置、移动或数据检查 | U4、U7 | | |

持续chat不是有限文本播报，不能从`result()`取得一轮聊天文字来判定回答结束。基础作品可用已学的有限文本合成与播放；需要持续对话时明确会话启停和任务退出条件。
'''),md('''
## 三、拆分模块并约定交接

**模块**是可单独说明和检查的一段功能。**接口约定**要写清调用前提供什么、结束后返回什么、后续程序据此如何处理。它既包括数据，也包括谁拥有任务句柄、谁负责取消或停止。

| 示例模块 | 输入/前提 | 输出 | 谁接着处理 | 未完成处理 |
| --- | --- | --- | --- | --- |
| 单次目标观察 | 图像、类别、标定（足球） | 有效目标信息或具体原因 | 主流程决定播报或结束 | 未检出、超时、超范围均不发运动 |
| 有限播报 | 已核对文本、空闲音频 | 播放任务结果 | 主流程安排新观测 | 保存句柄并收尾，终态未确认不重开 |

**任务02（约11分钟）：画流程，填写本组接口。** 可沿用普通函数返回原因的方式，不要求额外创建类或复杂状态机。若任务确需等候、重试或多轮，须同时写上限、复位与旧任务检查。

| 模块/负责人 | 输入及单位 | 调用前条件 | 返回值/状态 | 下一模块如何使用 | 退出责任 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |

流程草图：________。播报之后是否重新观测：________。哪段拥有机器人运动控制：________。
'''),md('''
## 四、安排分工与第一轮测试

**任务03（约9分钟）：分配代码、资料、测试与演示职责。** 人数少时可兼任；每名成员都应能解释本组核心流程。代码可分工并行，同一机器人只由一名操作员按约定运行。

| 成员 | 本课职责/文件 | 交给谁 | 完成检查方式 |
| --- | --- | --- | --- |
| | | | |

| 素材或条件 | 实际位置/编号 | 是否齐备 | 待补责任人 |
| --- | --- | --- | --- |
| 已验证动作ID或球标定 | | | |
| 介绍内容、目标区与场地 | | | |
| x_lab附件、图像/语音环境 | | | |

**任务04（约9分钟）：与另一组互读。** 另一组只按表格回答：能否知道程序要完成什么、怎样测试、失败如何结束？修改读者需要猜测的地方，形成第一轮用例。

| 用例 | 对应需求 | 测试前条件 | 操作 | 预期程序结果 | 要记录的现场现象 |
| --- | --- | --- | --- | --- | --- |
| 正常流程 | | | | | |
| 未完成情况 | | | | | |

本课先完成纸面与文件核查，不启动机器人。需要真机的测试由教师统一安排，不同时抢占同一台机器人。

## 五、提交与学习检查

本课45分钟建议：理解委托7分钟，需求9分钟，接口11分钟，分工9分钟，互读与检查9分钟。

提交本组主题、需求验收表、流程、接口与分工、素材清单及两类测试用例。

1. 指出本组一条含糊要求，并把它改成能用现场记录核对的条件。
2. 若一个模块返回“未检出”，下一模块会怎样处理？若只返回空白，会使谁无法判断？
3. 说明本组必须保留的一项功能和主动放弃的一项功能，依据是时间、场地还是已有能力？

**完成核对**：主流程、单位、退出责任和验收证据明确；无需读者猜测；没有把未验证能力写成现成条件。
''')])

lesson(30,'U8-L2_分主题开发模板',[
md('''
# U8-L2：核心模块开发

**课程目标**

1. 能按本组接口约定选择和修改功能片段，组织一个最小可运行流程。
2. 能先核对配置与单个模块，再进行整体验证，并记录返回原因和现场表现。
3. 能保存跨课使用的本组程序与版本，核查任务退出后再重试。
'''),md('''
## 一、任务：让本组接口真正接起来

使用上一课的需求表作为依据。代码中的模块名称、参数单位和返回原因应与接口表相符；若实现中发现接口不合适，先修改约定，再同步代码。

本课提供`u8_team_template.py`和`x_lab/`功能参考。前者包含普通函数和待填写配置，后者复用已经学过的视觉、播报、动作与足球代码。参考流程用于建立可运行起点，最终作品还需按本组需求完成修改和测试，不能只改组名后提交。

45分钟建议：核对5分钟，分工修改13分钟，模块测试10分钟，整体验证11分钟，保存收尾6分钟。未轮到设备时进行代码、资料与接口核查；不要把“计划测试”填成“真机通过”。
'''),md('''
## 二、保存和加载本组文件

**STEP 01：确认Notebook工作目录，再首次复制模板。** 本组程序保存在`u8_team.py`；文件已有内容时保留，避免覆盖同学修改。直接打开该文件修改Python代码，保存后再回到Notebook。
'''),code('''
from pathlib import Path
import shutil

print("工作目录：", Path.cwd())
if not Path("u8_team_template.py").exists() or not Path("x_lab").is_dir():
    raise RuntimeError("请把Notebook、模板及x_lab文件夹放在同一目录")
if not Path("u8_team.py").exists():
    shutil.copyfile("u8_team_template.py", "u8_team.py")
    print("已复制本组文件，请打开u8_team.py修改")
else:
    print("已有u8_team.py，保留原内容")
'''),md('''
### 2.1 填写流程与参数

打开本组文件，修改以下配置：

| 配置 | 要填写的内容 |
| --- | --- |
| VERSION | 本组版本标记，修改后递增，如team2-v1 |
| THEME | 只选导览或踢球 |
| STEPS | 按接口安排观察、介绍、再观察、致意或试踢 |
| INTRODUCTION | 本组核对事实后的介绍或试踢说明 |
| GREET_ID | 导览实际使用、已验证的动作ID |
| KICK_SECONDS/DIRECTION/POWER | 踢球观察上限、相对方向rad、力度1～10 |

起始片段的导览顺序示例为`["观察", "介绍", "再观察", "致意"]`；踢球把最后一项改成`"试踢"`。据本组需求选择内容、条件与参数，补充或修改相应函数，写明验收方式。若增加模块，还须同步`validate()`与接口表，不能只在列表填一个程序不认识的名字。

**STEP 02：加载并检查。** `import`首次加载文件；`reload()`让本次使用刚保存的版本，避免继续使用内存中的旧定义。只在机器人任务已退出时重新加载，不在运行中改写模块。
'''),code('''
import importlib
import u8_team

importlib.reload(u8_team)
print("版本：", u8_team.VERSION, "主题：", u8_team.THEME)
print("流程：", u8_team.STEPS)
print("配置问题：", u8_team.validate())
'''),md('''
## 三、先核查模块

⚠️ **实验安全**：导览动作、移动或踢球前按各模块的场地与模式要求检查。踢球时只有管理器控制运动。人员离开运动与出球方向；异常使用现场按钮流程，不仅依赖代码。不要对本Notebook执行无人核查的“全部运行”。

📌 **前置**：主题、动作和材料已审阅；U7线程、管理器、音频及运动任务均已结束；踢球标定已通过静态和运动条件核查。下格首次运行，重试保留session。

**STEP 03：连接并保存本次任务记录。**
'''),code('''
import json
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech
from x_lab.flows import new_session, idle, say, cleanup

robot = BoosterRobot()
speech = Speech(robot)
session = new_session(robot, speech)
detectors = {u8_team.THEME: Detection(model="person" if u8_team.THEME == "导览" else "soccer")}
calibration = None
if Path("ball_calibration.json").exists():
    calibration = json.loads(Path("ball_calibration.json").read_text(encoding="utf-8"))
print("模式：", robot.get_mode())
'''),md('''
**STEP 04：先测试只观察的模块。** 此格不发运动指令，检查未检出、类别和处理耗时等实际返回。改变主题后需在旧任务结束的条件下重新准备对应检测器；不能只改文字标签。
'''),code('''
if u8_team.THEME not in detectors:
    print("检测器与本组主题不一致，请先按新主题重新准备")
else:
    print("观察模块：", u8_team.observe(session, detectors, calibration))
'''),md('''
**STEP 05：单独核对本组介绍。** 运行前检查文本事实、读音和现场音量。这个模块成功不代表整套作品成功；播放未成功则先检查句柄，不继续动作。
'''),code('''
if not u8_team.INTRODUCTION.strip():
    print("先在本组文件填介绍并保存，任务退出后重跑STEP 02")
elif not idle(session):
    print("旧任务未结束，先执行STEP 07")
else:
    print("播报模块：", say(session, u8_team.INTRODUCTION))
'''),md('''
| 模块/版本 | 输入与前提 | 实际返回/状态 | 现场现象 | 接口是否需改 |
| --- | --- | --- | --- | --- |
| 观察 | | | | |
| 介绍 | | | | |
| 动作/足球（按教师轮换） | | | | |

动作或踢球独立检查沿用U7对应Notebook已验证的操作；不要为测试另建一套会互相抢占的管理器。其结果必须在本组整合代码中再次核对。

## 四、连接并验证最小流程

**STEP 06：按本组需求运行一次。** 运行前核对L1接口表与当前版本。按按钮流程切准备模式并等站稳，再进入本机要求的行走模式；只执行本组审核过的动作与参数。运行记录每步的原因和含等待的用时，不能直接当作物理运动时长。

<font color="red">本次场地、标定或动作条件获教师确认，旧任务退出，操作员和保护同学就位后，再启用运行。</font>
'''),code('''
APPROVED = False
run_log = []
if not APPROVED or robot.get_mode() != "walk":
    print("本次运行条件未确认")
elif u8_team.validate() or not idle(session) or u8_team.THEME not in detectors:
    print("配置、主题或旧任务仍有问题")
elif input("确认可运行，输入“运行”：").strip() == "运行":
    try:
        u8_team.run_project(session, detectors, calibration, run_log)
        for row in run_log:
            print(row)
    finally:
        print("收尾：", cleanup(session))
'''),md('''
**STEP 07：退出核查并保存记录。** 若仍有活动任务，保留session和本组文件，先处理它们，不重新连接或重载程序。
'''),code('''
print("待处理：", cleanup(session))
print("资源全部结束：", idle(session))
if run_log:
    evidence = {"version": u8_team.VERSION, "theme": u8_team.THEME, "log": run_log}
    Path("u8_module_run.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已保存u8_module_run.json；现场表现仍需另填")
'''),md('''
先切准备模式并等站稳；如需坐下，按人工支撑、切阻尼、坐稳流程处理。下一轮先确认旧任务退出、人工复位，再按需重载本组文件。

## 五、提交与学习检查

提交`u8_team.py`、版本、模块测试、更新后的接口表、一次整体运行记录及未解决项。记录文件不含完整现场现象，须与本组表格或视频相互核对。

1. 找出本组一处返回原因，解释主流程接到它后做什么。
2. 播报后再次观察具体使用了哪一行？去掉会产生什么问题？
3. 本组复用了哪些功能，又改了什么？这些改动对应哪条需求和测试？

**完成核对**：文件可跨课重载，版本与记录一致；代码职责和控制权明确；未测试模块标记待测；所有任务退出。
''')])

lesson(31,'U8-L3_联调模板',[
md('''
# U8-L3：真机彩排与联调

**课程目标**

1. 能按本组需求和用例进行彩排，分别记录程序结果、现场表现及未完成项。
2. 能依据记录选择一项修改，在相同或注明差异的条件下复测，并说明结果。
3. 能保存可交付版本，核查退出与人工复位后的重跑条件，整理展演证据。
'''),md('''
## 一、任务：这次成功能否按相同条件复现

上次运行完成了某个步骤，并不说明本组全部需求已经满足。彩排要先确定起点、目标、环境和版本，再把程序原因与现场结果对应起来。发现问题后选择一个要素修改，避免同时改许多参数而无法解释效果。

| 证据 | 能回答的问题 | 不能直接推出的结论 |
| --- | --- | --- |
| 每步日志 | 执行到哪里、返回了什么原因 | 没有记录的幕内细节 |
| SDK任务状态 | 指定任务是否成功、失败或取消 | 所有物理动作都符合预期 |
| 现场或视频 | 听到什么、机器人和球怎样运动 | 每次运行都会相同 |

45分钟建议：核查5分钟，基线11分钟，分析修改7分钟，复测11分钟，交付7分钟，收尾4分钟。
'''),md('''
## 二、固定条件与版本

**任务01：填写本轮用例。** 正常流程之外，选择一个可安全开展的未完成情况，如启动前没有目标、静态检查发现无效动作ID或未核对标定。不得通过推倒、碰撞或同时启动运动来制造故障。

| 用例/需求编号 | 版本 | 起点/目标/姿态 | 环境与参数 | 预期程序处理 | 需观察的现象 |
| --- | --- | --- | --- | --- | --- |
| 正常 | | | | | |
| 未完成 | | | | | |

**STEP 01：加载上一课同一份本组文件。** 保持工作目录、`u8_team.py`和`x_lab/`一致。不要重新复制模板覆盖作品。
'''),code('''
from pathlib import Path
import importlib
import json
import time
if not Path("u8_team.py").exists():
    raise RuntimeError("请先保留并带入上一课的u8_team.py")
import u8_team
importlib.reload(u8_team)
print("本轮版本：", u8_team.VERSION, "主题：", u8_team.THEME)
print("配置问题：", u8_team.validate())
'''),md('''
⚠️ **实验安全**：沿用本组已审定的场地、模式、标定和保护要求。管理器与速度/动作控制互斥；不为测试临时加入未验证动作。程序检查不能替代保护同学和按钮处置。

📌 **前置**：其他Notebook的线程、订阅、音频和运动已结束；上一课的连接不在后台运行。下格在本Notebook首次准备时运行一次，后续彩排保留session。

**STEP 02：连接并恢复本组资源。**
'''),code('''
from boosteros.robots.booster import BoosterRobot
from boosteros.brain import Detection, Speech
from x_lab.flows import new_session, idle, cleanup

robot = BoosterRobot()
session = new_session(robot, Speech(robot))
detectors = {u8_team.THEME: Detection(model="person" if u8_team.THEME == "导览" else "soccer")}
calibration = None
if Path("ball_calibration.json").exists():
    calibration = json.loads(Path("ball_calibration.json").read_text(encoding="utf-8"))
trials = []
print("模式：", robot.get_mode())
'''),md('''
## 三、执行基线并留下原始记录

**STEP 03：一次只执行一个用例。** 填写用例名称，按批准的条件人工恢复起点；先切准备模式站稳，再进入本机要求的行走模式。导览与踢球不在同一轮中混合控制。

<font color="red">本轮条件确认后才运行；未满足条件时只进行静态检查并登记，不把它填作真机彩排。</font>
'''),code('''
CASE_NAME = "正常-基线"
APPROVED = False
if not APPROVED or robot.get_mode() != "walk":
    print("运行条件待确认")
elif u8_team.validate() or not idle(session) or u8_team.THEME not in detectors:
    print("配置、主题或旧任务未处理")
elif input("本用例可运行，输入“彩排”：").strip() == "彩排":
    log = []
    try:
        u8_team.run_project(session, detectors, calibration, log)
    finally:
        pending = cleanup(session)
        trials.append({"case":CASE_NAME, "version":u8_team.VERSION,
                       "theme":u8_team.THEME, "log":log, "pending":pending})
        print("本轮记录：", trials[-1])
'''),md('''
**任务02：把现场现象补在表中。** 程序异常中断时也保留部分日志；如果只知道某幕异常，幕内位置填“待查”，不根据猜测补造原因。

| 用例 | 实际程序结果/状态 | 现场表现/视频片段 | 是否满足该需求 | 未执行部分 | 待查信息 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 四、依据问题修改一个要素

**任务03：选择问题和证据，先写预期变化，再改代码或参数。** 球位置超出标定范围时，应核查点位和姿态，不删除范围检查；动作超时应核查实测时长与终态，不直接把取消改成成功。

| 问题 | 依据 | 修改项 | 预期变化 | 保持不变的条件 |
| --- | --- | --- | --- | --- |
| | | | | |

**STEP 04：旧任务全部结束后，保存新版本并重载。** 修改`u8_team.py`中的VERSION。若改变主题、标定或检测模型，需按新条件准备资源，不能只重载本组模块。
'''),code('''
print("收尾检查：", cleanup(session))
if not idle(session):
    print("资源未结束，不重载")
else:
    importlib.reload(u8_team)
    print("新版本：", u8_team.VERSION, "配置问题：", u8_team.validate())
'''),md('''
**STEP 05：复测。** 人工恢复相同起点、目标和环境，重跑STEP 03，修改`CASE_NAME`为对应复测名。若条件不同，在表中说明；复测没完成就填待补，不能把预期写成结果。

| 基线版本/结果 | 修改版本/结果 | 条件差异 | 能支持的判断 | 仍未验证的内容 |
| --- | --- | --- | --- | --- |
| | | | | |

## 五、保存交付证据

**STEP 06：退出核查并导出本次记录。** 文件名含时间，避免覆盖上一轮证据。记录文件只含程序数据，现场表和视频另存。
'''),code('''
print("待处理：", cleanup(session))
print("资源全部结束：", idle(session))
filename = "u8_rehearsal_" + time.strftime("%Y%m%d_%H%M%S") + ".json"
Path(filename).write_text(json.dumps(trials, ensure_ascii=False, indent=2), encoding="utf-8")
print("已保存：", filename, "用例数：", len(trials))
'''),md('''
退出后先切准备模式等站稳；按教师安排人工坐下或保留安全姿态。需要再次演示时先核对旧任务退出，再人工复位，不能假定程序会自动返回起点。

## 六、学习检查与提交

提交当前本组程序、版本、正常与未完成用例、修改前后记录、视频或现场证据及待解决项。作品实际运行不超过两分钟，演示说明和复位另计。

1. 本组哪条需求尚未有充分证据？需要补什么测试？
2. 本次修改与复测能支持什么判断？哪些条件变化使结论受限？
3. 指出重复运行前的任务检查和人工复位步骤；它们分别解决什么问题？

**完成核对**：原始基线没有覆盖；版本与记录一致；解释来自实际证据；未测、失败和取消均如实标记。
''')])

lesson(32,'U8-L4_展示评分表',[
md('''
# U8-L4：成果展演与答辩

**课程目标**

1. 能对照本组需求演示导览或踢球作品，用程序与现场证据说明完成情况。
2. 能结合实际代码或彩排现象解释两个本组用到的概念，并说明模块交接和修改依据。
3. 能根据评价指出作品的使用条件、未解决项及下一步可验证的改进。
'''),md('''
## 一、任务：交付一项可以说明使用条件的应用

观众需要知道作品服务谁、怎样使用、已经验证了什么。演示时说明条件和局限，可以帮助使用者判断作品是否适合当前场景。不要把尚未测试的功能作为已经完成的能力展示。

每组时段为五分钟演示和三分钟答辩。五分钟包含场景说明、作品运行、结果证据及必要复位，机器人实际片段原则上不超过两分钟。答辩从本组确实使用的概念中抽两个，结合代码或记录说明。

### 1.1 展演安排

单场45分钟按四组准备：开场与核查5分钟，四组各8分钟共32分钟，评价5分钟，收尾3分钟。组数更多时由教师分场；有足够设备与指导人员时可分站并统一评分，不把六组48分钟硬塞进一个课时。
'''),md('''
## 二、展演前核对

**任务01：逐项确认提交材料。**

| 材料/条件 | 实际文件、版本或安排 | 是否齐备 |
| --- | --- | --- |
| 主题、需求和验收表 | | |
| 本组程序、接口和分工 | | |
| 标定/动作/场地等使用条件 | | |
| 基线、修改与复测证据 | | |
| 已知未解决项 | | |
| 操作员、保护同学和复位步骤 | | |

实际展演使用已验证版本，不在候场时临时加入未测试动作。导览与足球分别检查活动及出球方向；同一机器人一次由一名操作员控制。演示代码沿用本组L3定稿，不另抄一套难以核对的新程序。
'''),md('''
## 三、演示与结果说明

**任务02：按下面顺序准备讲解。**

1. 说明对象、场地和一条核心需求，给出运行前条件。
2. 指出本组使用的模块和交接，不逐行朗读全部代码。
3. 运行本组定稿，展示实际结果；出现未完成时按既定流程退出，说明记录到了什么。
4. 展示一项修改及复测证据，区分当前达到与尚未达到的要求。

| 需求编号 | 本次程序结果 | 本次现场表现 | 彩排证据 | 验收判断/未完成项 |
| --- | --- | --- | --- | --- |
| | | | | |

致意取消、踢球观察窗口结束、球进入目标区属于不同结果，按实际记录。程序在限定时间内退出不自动代表作品功能完成；现场未成功也应保留真实记录供解释。

### 3.1 答辩准备

| 本组使用的概念 | 在哪段代码或哪个现象中 | 它解决什么问题 | 使用条件与局限 |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

可选本组实际用到的坐标变换、反馈控制、订阅、融合、队列、线程、任务状态或行为编排等。没有实现融合估计的作品，不把“同时显示几路数据”解释为已经完成融合定位。

回答时用具体代码或记录说明。例如“播报后重新取图”对应哪一行、当时目标变化是什么；“球坐标以米为单位”来自怎样的标定和误差核对。只复述术语不足以解释本组实现。
'''),md('''
## 四、评价与反馈

**任务03：根据同一组证据评分。** 满分100，按以下四项记录。动作复杂、幅度大或使用更多API不单独加分。

| 维度 | 分值 | 依据 |
| --- | --- | --- |
| 功能完成度 | 30 | 对照已确定需求的实际运行、未完成处理和退出情况 |
| 概念理解 | 20 | 两个实际使用概念的解释，能联系代码和现象说明条件 |
| 工程组织 | 20 | 接口与分工、版本、模块测试、修改及复测证据 |
| 演示表达 | 30 | 需求和操作说明、演示顺序、结果证据、答辩及局限说明 |

评分等级建议：依据充分且符合本组要求可给该项高分；部分达成时按证据给相应分；没有证据的项目不按口头承诺给满分。教师与观众应注明支撑判断的材料或现象。

| 小组 | 功能/30 | 概念/20 | 组织/20 | 表达/30 | 合计 | 一项证据与改进建议 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

观众反馈：我能确认的一个功能是________，依据是________；还希望补测________，因为________。
'''),md('''
## 五、个人说明与交付核查

**任务04：每人填写。**

1. 我负责的模块或证据是什么？它交给哪个模块使用？
2. 我能解释的一处代码或一次修改是什么？依据哪条运行记录？
3. 当前作品适合什么条件？离开这些条件，首先需要重新验证什么？

展演后核对后台线程、音频、运动与踢球管理器退出；先切准备模式并等站稳，再按教师安排人工支撑坐下或关机。不因演示时段结束就覆盖未结束任务的句柄。

最终提交：本组可运行文件与版本、依赖和素材、需求与接口表、测试复测记录、演示证据、评价反馈与个人说明。视频仅作为证据补充；替代现场演示须由教师明确安排，不能把历史视频标为本次真机结果。

**完成核对**：所有成果能对应本组需求；事实、运行结果和后续计划分开；文件可交接，现场资源已结束。
''')])


def write_all():
    for number, name, notebook in LESSONS:
        target = OUT / (name+'.ipynb')
        target.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        # 生成器只含当前Notebook数据，离线运行时重建同一源内容。
        payload = pprint.pformat(notebook, width=110, sort_dicts=False)
        source = ('# -*- coding: utf-8 -*-\n'
                  '"""v5 P1反向同步生成器；运行会覆盖Notebook，先核对用户手改。"""\n'
                  'import json\nfrom pathlib import Path\n'
                  'NOTEBOOK = '+payload+'\n'
                  'if __name__ in ("__main__", "__gen__"):\n'
                  f'    path = Path(__file__).parent / "notebooks" / {repr(name+".ipynb")}\n'
                  '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
        (COURSE/f'_gen_L{number}.py').write_text(source,encoding='utf-8')
        print(name, len(notebook['cells']), '格/',sum(c['cell_type']=='code' for c in notebook['cells']),'代码格')


if __name__ == '__main__':
    write_all()
