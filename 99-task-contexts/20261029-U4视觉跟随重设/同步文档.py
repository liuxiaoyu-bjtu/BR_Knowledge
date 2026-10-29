from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = '05-internal-materials/vocational-planning/03_X课程项目/'
REPORT = '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md'
shared = []

def insert(text, note):
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith('# '):
            lines.insert(i + 1, '\n' + note + '\n')
            return ''.join(lines)
    raise ValueError('未找到主标题')

def update(rel, transform):
    file = ROOT / rel
    backup = TASK / 'before' / rel
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(file.read_bytes())
    current = file.read_text(encoding='utf-8-sig')
    changed = transform(current)
    assert changed != current, rel
    file.write_text(changed, encoding='utf-8')
    head = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT).decode('utf-8-sig')
    increment = transform(head)
    target = TASK / 'head-increment' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(increment.replace('\r\n', '\n').encode('utf-8'))
    shared.append(rel)

note = ('L3改为移动目标视觉跟随：水平偏差调方向，L2实测框高阈值控制跟进/暂停，近处继续观察；'
        'L4改为发现来宾、跟随、连续到位确认与致意。IMU/里程计另作运动记录，停稳后分析位移和朝向。'
        '两课25/31格、10/13代码格，生成器同步；新代码待①②，不登记阶段通过。L2含第9格原文保留。')
update('AGENTS.md', lambda s: insert(s, '> **U4视觉跟随重设（2026-10-29）**：' + note + '入口：`' + P + REPORT
    + '`。下方“静止来宾、odom控制行进量”的旧同步结论仅作历史记录。'))
update('INDEX.md', lambda s: insert(s, '> U4移动目标跟随 / 框高阈值 / 跟进与暂停 / 接待到位 / 机器人位移方向：['
    + 'L3/L4新稿与验证](' + P + REPORT + ')（2026-10-29；视觉控制、IMU/odom记录；新代码待①②）。'))
update('CHANGELOG.md', lambda s: insert(s, '## 2026-10-29 · U4-L3/L4改为视觉移动跟随\n\n'
    '- 按用户要求重写L3移动目标跟随，结合L1方向偏差与L2实测框高停止阈值；近处暂停前进、继续观察，远离后可再跟进。\n'
    '- L4改为发现单一来宾、跟随、连续到位、致意前新观测及任务退出；撤下预设行进量控制和0.35触发比例。\n'
    '- IMU/里程计改为运动观察记录；停稳后解释起终点直线位移、方向与机身朝向，不当作行走路程或安全诊断。\n'
    '- 两课25/31格、10/13代码格，镜像及大纲/进度/规则同步；旧稿与输出留档，新代码输出清空待验证。L2第9格等用户内容未改。\n'
    '- 仅做离线构造分支与格式核查，未运行机器人或新增确认；本地Git提交，推送由用户进行。'))
update('05-internal-materials/vocational-planning/README.md', lambda s: insert(s,
    '> **U4视觉跟随重设（2026-10-29）**：' + note + '[新稿与逐步验证](03_X课程项目/' + REPORT + ')。'))

def outline(s):
    s = insert(s, '> **U4最新主线（2026-10-29）**：L2实测框高停止阈值；L3跟随移动目标，视觉决定方向与跟进/暂停；'
        'L4加入连续到位、致意前复核和流程交接。IMU/里程计记录机身运动，结束后分析位移与朝向。['
        + '重设与验证](' + REPORT + ')；旧静止双对照和里程计到位方案不再用于新L3/L4。')
    s = s.replace('### U4：视觉引导自主接近（4课时）★ 综合实训', '### U4：视觉引导接近与跟随（4课时）★ 综合实训')
    s = s.replace('视觉引导自主接近', '视觉引导接近与跟随')
    s = s.replace('相机调方向、里程计估行进量、IMU 读数参与示例判断；L2 分别核对里程计行进、视觉估距与实测停止阈值',
        'L2核对位移与标定框高阈值；L3/L4视觉控制移动跟随与到位，IMU/odom记录位移、方向和朝向')
    s = s.replace('把 U1 的运动控制、U2 的传感器与状态读数、U3 的目标检测放进同一个接近任务，观察程序如何根据新读数调整动作，并比较不同来源的距离估计。',
        '把U1的运动控制、U2的状态读数、U3的目标检测用于转向、阈值停止和移动目标跟随；方向偏差和框高占比决定运动，IMU与里程计记录机身变化，停稳后核对实际位移与间距。')
    s = s.replace('跟住来宾（L3）：来宾站定，分别运行固定指令和带反馈的接近，记录两次停靠误差；单次对比只说明本次条件下的结果。',
        '跟住来宾（L3）：来宾缓慢移动；水平偏差调整方向，框高达到L2实测阈值后暂停前进，远离后可再次跟进；结束后读取位移与朝向。')
    s = s.replace('接待来宾（L4）：把检测、转向、接近和预定义致意动作接成一次流程，并逐项检查停止条件。',
        '接待来宾（L4）：发现单一来宾并视觉跟随，连续到位后复核目标和动作空间，再致意；未完成条件阻断后续。')
    s = s.replace('触发语音问候 + 手势致意（复用 U1/U6 动作）',
        '到位后执行教师确认的U1预定义致意动作，区分任务状态和现场效果；语音问候留待U5学习后的应用整合')
    s = s.replace('能说明视觉、里程计和 IMU 在接近流程中的分工，用构造读数检查停止分支，记录实际运行的停止原因；异常时由教师人工中止。',
        '能说明视觉的方向/框高反馈与IMU/里程计记录的分工；实际演示近处停止前进、目标远离后重新跟进，记录停止及流程阻断原因，停稳后报告位移与朝向；异常由教师人工中止。')
    lines = s.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| **3** | 跟住来宾'):
            lines[i] = '| **3** | 跟住来宾（闭环与视觉伺服） | 单一目标缓慢移动；L1方向反馈与L2框高阈值共同控制，近处暂停而继续观察；IMU/odom另作记录 | 静态分支→短步跟随；偏差大先转向，达到占比后vx=0，目标远离可再跟进；无效目标结束；finally零速度；停稳后算dx/dy、直线位移及方向 | **闭环(B09)**与**视觉伺服(B10)**；位移方向与机身朝向的区别 | — | ④ 跟进—暂停—再次跟进与小幅偏转；⑤ 停稳位移/方向、IMU记录及现场核对 |'
        elif line.startswith('| **4** | 接待来宾'):
            lines[i] = '| **4** | 接待来宾（视觉跟随与流程联调） | 单一来宾缓慢移动后停留，连续到位与致意交接；视觉控制，其他状态用于运动说明 | 等待→视觉跟随→连续3次到位→现场确认后新观测→预定义动作；函数返回、有限等待、保留旧句柄和退出；不输入起步间距规划总路程 | **多路信息联合使用**：不合成统一位置估计；函数返回和条件交接 | — | ⑥ 一次接待及失败阻断、致意终态与现场表现、停稳位移与朝向记录 |'
    s = '\n'.join(lines) + '\n'
    s = s.replace('里程计行走/速度比较、框高标定与阈值验证记录 + 开环/闭环对照记录',
        '里程计行走/速度比较、框高标定与阈值验证记录 + 移动跟随及位移/朝向记录')
    s = s.replace('3 m来宾触发及第3项语音问候仍是单元项目的待核实事项，本次不据此标记实现或验收通过。',
        '当前接待以单一可用来宾框开始，不设置3 m自动触发；第3项的语音能力留待U5后的应用整合，本轮不提前使用。')
    return s
update(P + 'X课程大纲-v5.md', outline)

def plan(s):
    s = insert(s, '> **U4新稿依据（2026-10-29）**：' + note + '[' + '重设与验证](' + REPORT
        + ')列出两课当前步骤；P2及后续产物按移动跟随新稿，不复用旧静止接近结论。')
    lines = s.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| **U4** | **L3**'):
            lines[i] = '| **U4** | **L3** | **跟住来宾（闭环与视觉伺服）** | 移动目标；L1偏差调方向，L2实测框高阈值控制跟进/暂停与再次跟进；IMU/odom记录，停稳后位移/方位分析；25格/10代码，待新稿①② | `U4-L3_跟住来宾` |'
        elif line.startswith('| **U4** | **L4**'):
            lines[i] = '| **U4** | **L4** | **接待来宾（视觉跟随与流程联调）** | 发现来宾→视觉跟随→连续到位→致意前复核→动作与退出；IMU/odom用于记录，不按预设里程到位；31格/13代码，待新稿①② | `U4-L4_接待来宾` |'
    return '\n'.join(lines) + '\n'
update(P + 'X课程开发计划-v4.md', plan)

def progress(s):
    s = insert(s, '> **U4移动跟随新稿（2026-10-29）**：' + note + '[测试入口](' + REPORT + ')。')
    lines = s.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| [U4-L3 '):
            lines[i] = '| [U4-L3 跟住来宾](notebooks/U4-L3_跟住来宾.ipynb) | P1重设稿；移动目标视觉跟随 | 新稿①待审、②待验证；未进P2 | 按[新验证清单](' + REPORT + ')核对静态、移动与退出 | 25格/10代码；视觉控制跟进/暂停，IMU/odom记录位移与朝向；旧静止双对照已撤下 |'
        elif line.startswith('| [U4-L4 '):
            lines[i] = '| [U4-L4 接待来宾](notebooks/U4-L4_接待来宾.ipynb) | P1重设稿；跟随与接待流程联调 | 新稿①待审、②待验证；未进P2 | 按[新验证清单](' + REPORT + ')核对连续到位、致意和旧任务退出 | 31格/13代码；不再用起步间距/odom控制到位，无0.35触发阈值；动作终态须真机核对 |'
    return '\n'.join(lines) + '\n'
update(P + 'X课程当前进度.md', progress)
update('05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md', lambda s:
    insert(s, '> **U4当前口径（2026-10-29）**：L3/L4已按用户要求改为移动视觉跟随；历史“静止来宾、odom控制到位、IMU差值停止”不再适用新稿。['
        + '新稿与验证](../03_X课程项目/' + REPORT + ')。')
    + '\n\n## U4-L3/L4移动跟随重设（2026-10-29）\n\n'
    + '- L3：25格/10代码；L1水平偏差与L2实测框高阈值决定转向及前进，近处暂停后继续观察，目标远离可再跟进。\n'
    + '- L4：31格/13代码；发现来宾、跟随、连续到位、致意前新观测和动作退出，函数返回决定交接。\n'
    + '- IMU/里程计仅作运动记录，停稳后报告直线位移、位移方向和机身朝向；不把净位移当作路程或安全诊断。\n'
    + '- 新代码清空旧执行输出，旧两课与生成器留在本轮任务基线；`_gen_L15.py`、`_gen_L16.py`完整同步。\n'
    + '- L2用户原稿及第9格不改；新L3/L4仍待①②，不继承旧代码验证。P2～P5依据当前移动跟随版。\n')

for name in ['U4-L3-L4_承接新版L2的同步审查.md', 'U4-L2-L4_距离实验复评与文字校对.md']:
    update(P + '实验验证/' + name, lambda s: insert(s,
        '> **历史方案已更新（2026-10-29）**：用户明确L3应跟随移动目标、L4对应联调。['
        + '视觉移动跟随新稿](U4-L3-L4_视觉移动跟随重设与验证.md)已替换静止接近与预设行进量控制；本文件保留此前审查范围，不据此生成当前L3/L4材料。'))
update(P + '实验验证/U4-L2_重开发回读与第五部分同步.md', lambda s: insert(s,
    '> **L3/L4最新承接（2026-10-29）**：['
    + '视觉移动跟随重设](U4-L3-L4_视觉移动跟随重设与验证.md)已落实方向偏差与L2实测框高阈值控制，IMU/odom另作运动记录。L2含第9格原文保留；旧“后续课不接视觉停止”的结论已由用户新要求替代。'))
(TASK / '共享文档清单.json').write_text(json.dumps(shared, ensure_ascii=False, indent=2), encoding='utf-8')
print('已同步', len(shared), '份阶段依据与导航；HEAD增量另存。')
