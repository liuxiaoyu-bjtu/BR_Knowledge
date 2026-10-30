from pathlib import Path
import copy
import hashlib
import json
import pprint

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = Path('05-internal-materials/vocational-planning/03_X课程项目')
BASE = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))


def replace_cell(nb, number, text):
    nb['cells'][number - 1]['source'] = (text.strip() + '\n').splitlines(keepends=True)


def replace_text(nb, number, old, new):
    text = ''.join(nb['cells'][number - 1]['source'])
    assert text.count(old) == 1, (number, old)
    replace_cell(nb, number, text.replace(old, new))


def checked_write(rel, payload):
    path = ROOT / rel
    before = path.read_bytes()
    assert hashlib.sha256(before).hexdigest() == BASE['files'][rel.as_posix()], rel
    assert path.read_bytes() == before, f'文件已被其他任务修改：{rel}'
    path.write_bytes(payload)


l3_rel = PROJECT / 'notebooks/U4-L3_跟住来宾.ipynb'
l4_rel = PROJECT / 'notebooks/U4-L4_接待来宾.ipynb'
l3 = json.loads((ROOT / l3_rel).read_text(encoding='utf-8'))
l4 = json.loads((ROOT / l4_rel).read_text(encoding='utf-8'))
old_l3 = copy.deepcopy(l3)

replace_text(l3, 4, '先完成静态判断，再分格进入运动模式；', '先完成静态判断，再按§4.1进入行走模式；')

replace_cell(l3, 6, '''
**STEP 02：设定初始化参数**

下格直接给变量赋值。`STOP_RATIO = 0.3`是示例占位，运行运动实验前必须替换为本组L2实测并核对的值。把目标、标定间距、头部角度和站姿记在本课§5.1的记录表中。

下表沿用“需要更改、可能更改、建议更改、可不改”的标注。先核对停止占比与目标，再参照L1、L2的记录调整运动参数；每次只改一个待研究参数。

| 参数 | 修改要求 | 含义与用法 |
| --- | --- | --- |
| `STOP_RATIO` | 需要更改 | L2实测的停止框高占比，取值在0与1之间；它不是像素数或置信度 |
| `TARGET_CLASS` | 可能更改 | 目标类别，如`person`、`bottle`；换目标时，一起检查STEP 01的检测模型、类别和停止占比。换回来宾后重新标定 |
| `FORWARD_SPEED` | 建议更改 | 前进速度，单位m/s；参考L2行走记录，数值过小也可能无法有效迈步 |
| `KP_YAW` | 建议更改 | 水平偏差换算为转向角速度的比例系数，单位rad/s/像素。沿用L1的`-KP_YAW × error`：右侧偏差为正，转向角速度为负 |
| `MAX_YAW` | 建议更改 | 转向角速度的绝对值上限，单位rad/s；限制比例计算得到的转向指令 |
| `CENTER_PX` | 可不改 | 水平偏差绝对值不超过这个像素数时，转向角速度取0，减少中心附近的小幅修正 |
| `TURN_ONLY_PX` | 建议更改 | 水平偏差绝对值超过这个像素数时，只转向、不前进；应大于`CENTER_PX` |
| `PULSE_SECONDS` | 建议更改 | 每次发送速度指令后的等待时长，单位秒。随后还要读取IMU和里程计，实际指令持续时间会更长 |
| `READ_LIMIT` | 建议更改 | 本次取图与检测允许的处理耗时，单位秒。接口返回后才检查，超限就放弃本次结果；它不能强制打断阻塞调用，也不代表图像从拍摄到使用的完整延迟 |
| `RUN_SECONDS` | 可不改 | 一轮跟随的观察时限，单位秒；程序在每轮开始时检查，正在执行的取图、检测或读状态不会被它强制打断 |

标为“可不改”的数值也是课堂初值；若静态分支或真机结果不合适，仍需调整并复测。
''')

replace_cell(l3, 8, '''
### 2.4 检查目标读数是否可用

`observe_target()`采集一张图像，检测目标，返回水平偏差、框高占比和读数说明。

- 找到唯一目标，且检测框未碰到画面边缘、处理耗时未超限时，返回偏差、占比和“可用”。
- 没有目标、检测到多个同类目标、检测框碰边或处理过慢时，前两项返回`None`，最后一项说明原因。后面的跟随程序据此结束本轮。

碰边检查只能发现一部分目标不完整的情况。物体遮挡、错误检测框等仍需结合画面核对，不能仅凭“可用”断定目标始终完整。

`choose_velocity()`根据偏差和占比计算前进速度、转向角速度及本轮决定；定义或调用这个函数本身都不会让机器人运动。

**STEP 03：定义取图检查与指令计算。**
''')

replace_cell(l3, 14, '''
## 四、实训：目标移动，机器人跟随

### 4.1 场地和模式

在地面标出起点、目标缓慢移动的短路线和终点停留区。先让目标在机器人正前方逐渐远离并停留，再按场地条件测试小幅偏左或偏右。

目标保持直立、完整可见，避免走向机器人或急转弯。路线内不安排其他人员穿行、遮挡，也不放置其他同类目标。更换目标或改变拍摄姿态后，重新核对L2停止占比。

模式切换沿用已学操作：进入`prepare`，由人工支撑并用STAND使机器人站起，确认站稳后再进入`walk`。头部保持标定时的固定角度。进入行走模式后，可重跑STEP 04核对当前画面中的判断；该格只打印，不发送运动指令。
''')

replace_text(l3, 15, '**STEP 08：现场确认后运行**', '**STEP 06：现场确认后运行**')
replace_text(l3, 15, '最外层`finally`保证本格正常退出或可处理的异常、中断时需要发送零速度；', '最外层`finally`在本格正常退出或可处理的异常、中断时尝试发送零速度；')
replace_text(l3, 15, '> 由人工支撑机器人站起，确认站稳、空间和路线均满足要求，再运行下一格。头部保持标定时的固定角度。', '> 已按§4.1进入`walk`，并确认机器人站稳、头部角度及路线符合要求后，再运行下一格。')
replace_text(l3, 17, '**STEP 09：确认机器人停稳后读取终点**', '**STEP 07：确认机器人停稳后读取终点**')
replace_text(l3, 19, '**STEP 10：结束运动，回到准备姿态。**', '**STEP 08：结束运动，回到准备姿态。**')

# 用户的8格代码、执行次数及输出保持原样。
assert [c for c in l3['cells'] if c['cell_type'] == 'code'] == [c for c in old_l3['cells'] if c['cell_type'] == 'code']

replace_text(l4, 1, '停稳后读取IMU和里程计记录，解释机器人位移与朝向。', '结合跟随中的IMU记录和停稳后的里程计读数，解释机器人位移与朝向。')
replace_cell(l4, 2, '''
## 一、跟随结束后的接待任务

展厅来宾进入指定通道，机器人发现来宾后调整方向并缓慢接近。来宾沿标记路线移动，随后在接待点停留，机器人停稳后执行一次致意动作。

L3达到框高阈值后仍继续观察，来宾远离时还能重新跟进。本课需要确定什么时候结束跟随、交给致意环节：连续几次都达到停止占比且基本对准，才结束跟随；随后确认来宾位置与动作空间，再执行致意。连续满足条件用于减少一次检测波动带来的误触发，仍需现场确认来宾和机器人已经停稳。

接待流程为`发现单一来宾 → 视觉跟随 → 连续到位确认 → 再次检查 → 致意 → 结束`。方向和远近判断沿用L3，新增的是各步骤的交接与退出条件。IMU和里程计继续记录机器人运动，不用于决定来宾是否到位。
''')

replace_cell(l4, 6, '''
### 3.1 复用已经核对的参数

**STEP 02：填写停止占比、跟随参数及致意动作。**

下格直接赋值。将`STOP_RATIO = 0.3`替换为本组L2实测值；其余跟随参数逐项采用L3已经核对的设置，不要因重新打开一课而照抄回示例值。尚未完成L3真机测试时，先完成L3测试。把目标、标定间距、头部角度和站姿填入§5.1记录表。若换用瓶子等目标，检测模型、`TARGET_CLASS`与标定值需一起调整；瓶子测试只用于核对程序分支。

跟随参数的含义与L3 STEP 02相同。本课新增：

| 参数 | 用途 |
| --- | --- |
| `GREET_ID` | 运行本格时输入STEP 01本机列表中、由教师确认的致意动作ID；不能输入列表序号。当前按整数ID读取，本机类型不同时先核对后调整 |
| `ARRIVAL_CHECKS` | 连续满足到位条件的次数，初值为3。它是观察次数，不是3秒，也不能证明来宾完全静止 |
| `ACTION_WAIT` | 致意任务的等待上限，单位秒；结合所选动作的实际时长由教师核对 |

本格最后初始化运动记录。重复接待时从STEP 10开始；需要改参数时可重跑本格，保留STEP 01中的`greet_task`原句柄。
''')

replace_cell(l4, 7, '''
STOP_RATIO = 0.3         # 示例占位，必须替换为本组L2实测并核对的停止占比
TARGET_CLASS = "person"  # 更换目标时，检测模型、类别和阈值一起修改
FORWARD_SPEED = 0.10     # m/s，采用L3核对后的设置
KP_YAW = 0.001           # rad/s/像素，沿用L1、L3的偏差方向约定
MAX_YAW = 0.20           # rad/s，采用L3核对后的设置
CENTER_PX = 20           # 基本对准的像素范围
TURN_ONLY_PX = 80        # 偏差较大时只转向，不前进
PULSE_SECONDS = 0.20     # 秒，读IMU和里程计会增加指令持续时间
READ_LIMIT = 1.0         # 秒，取图与检测返回后检查，不能打断阻塞调用
RUN_SECONDS = 20.0       # 秒，一轮跟随的观察时限
print("停止占比：", STOP_RATIO)

GREET_ID = int(input("输入教师确认可用的致意动作ID："))
ARRIVAL_CHECKS = 3   # 连续满足次数，真机核对后可调整
ACTION_WAIT = 10.0  # 致意等待上限，按动作实际时长由教师核对
motion_rows = []
start_pose = None
end_pose = None
''')

replace_cell(l4, 8, '''
### 3.2 复用视觉观察与指令计算

`observe_target()`先取图并检查目标，再返回水平偏差、框高占比和说明；`choose_velocity()`据此返回前进速度、转向角速度和决定。方向符号、框高阈值、近时停止前进及偏差大时先转向，都沿用L3。

本格还保留了联调中的检测框数值检查：`math.isfinite()`判断数值是否为有限数，`all(...)`检查列出的各项是否都满足；宽、高还需大于0。这些检查会拒用异常框，不能识别人物身份或判断目标是否被遮挡。

定义这两个函数不会启动运动。先运行STEP 04核对静态分支，再连接后续流程。

**STEP 03：定义视觉观察与指令计算。**
''')

replace_cell(l4, 18, '''
### 4.2 跟随与连续到位确认

**STEP 08：定义跟随函数。** 函数的取图、计算指令和短步运动沿用L3。本课增加`arrived_count`，记录已经连续满足多少次到位条件。

一次到位条件是`ratio >= STOP_RATIO and abs(error) <= CENTER_PX`：框高达到停止占比，同时水平方向基本对准。两项都满足时发送零速度，计数加1；任一项不满足就把计数清零，按L3规则继续跟随。目标不可用则直接结束。到位确认期间只观察，不发送前进或转向指令。

例如，四轮检查依次为“满足、满足、不满足、满足”，计数依次为`1、2、0、1`，还不能进入致意。只有连续达到`ARRIVAL_CHECKS`次，函数才返回“到位”；达到观察时限仍未满足时，返回未完成原因。

IMU和里程计继续写入`motion_rows`，不参与到位判定。确认期间在零速度指令下读取，其他轮在短步末尾读取；发送零速度不等于已经物理停稳，停稳情况由现场核对。这里只定义函数，STEP 10才调用它开始运动。
''')

replace_cell(l4, 22, '''
### 4.4 运行完整流程

**STEP 10：现场确认后执行一次接待。** 本格会调用前面的函数，实际转向、前进并可能致意。教师核对目标、阈值、路线、动作范围和模式后，将`APPROVED`改为`True`再运行；每次重复测试都要重新确认现场条件。

程序先等待单一可用来宾，再跟随；只有跟随函数返回“到位”，才进入致意前检查。到位后机器人保持零速度，教师确认停稳与空间并输入“致意”，程序再用新画面检查一次。这里的确认对应跟随转入动作的交接，仍需保留。

旧致意句柄未结束时不启动新一轮。其他连接的旧任务需事先人工核查，本程序的句柄检查不能覆盖它们。重复接待前先运行STEP 11确认旧任务结束，再恢复起点与现场条件；若已切回`prepare`，按STEP 05、06重新进入`walk`。

`finally`在正常退出或可处理的异常、中断时尝试发送零速度。若中断发生在动作等待期间，还需运行STEP 11检查动作句柄；零速度不能代替取消动作。断网或强制终止内核时按现场按钮流程处置。
''')
replace_text(l4, 23, 'elif input("本轮可接待？输入“接待”：").strip() == "接待":', 'else:')

for rel, nb, gen in [(l3_rel, l3, '_gen_L15.py'), (l4_rel, l4, '_gen_L16.py')]:
    checked_write(rel, (json.dumps(nb, ensure_ascii=False, indent=1) + '\n').encode('utf-8'))
    content = ('# -*- coding: utf-8 -*-\n'
               '"""U4学生Notebook完整镜像；按2026-10-30回读稿同步，真机确认状态另见进度表。"""\n'
               'import json\nfrom pathlib import Path\n'
               'NOTEBOOK = ' + pprint.pformat(nb, width=110, sort_dicts=False) + '\n'
               'if __name__ in ("__main__", "__gen__"):\n'
               '    path = Path(__file__).parent / "notebooks" / ' + repr(rel.name) + '\n'
               '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
    checked_write(PROJECT / gen, content.encode('utf-8'))

print('L3：22格/8代码，代码与执行信息不变；L4：31格/13代码，仅参数与重复启动确认两格代码调整。')
