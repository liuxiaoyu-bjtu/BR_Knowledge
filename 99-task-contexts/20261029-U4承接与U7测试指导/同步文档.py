from pathlib import Path
import subprocess
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = '05-internal-materials/vocational-planning/03_X课程项目/'
REPORT = '实验验证/U4-L3-L4_承接新版L2的同步审查.md'
GUIDE = '实验验证/U7_逐课真机测试指导.md'
shared = []

def update(rel, transform):
    path = ROOT / rel
    original = path.read_text(encoding='utf-8-sig')
    before = TASK / 'before' / rel
    if not before.exists():
        before.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(path.read_bytes())
    changed = transform(original)
    assert changed != original, rel
    path.write_text(changed, encoding='utf-8')
    head = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT).decode('utf-8-sig')
    increment = transform(head)
    target = TASK / 'head-increment' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(increment, encoding='utf-8')
    shared.append(rel)

def insert_after_heading(text, entry):
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith('# '):
            lines.insert(i + 1, '\n' + entry + '\n')
            return ''.join(lines)
    raise ValueError('未找到主标题')

summary = ('U4-L3/L4已同步新版L2的课间分工、对照条件与分组记录，区分启动触发和视觉停止阈值；'
           '两课代码不变，真机②仍待完成。U7补齐L1/L2两处情境备忘，四课测试指导已整理；未新增①②或推进Phase。')
update('AGENTS.md', lambda s: insert_after_heading(s, '> **U4承接与U7测试准备（2026-10-29）**：' + summary
    + '入口：`' + P + REPORT + '`、`' + P + GUIDE + '`。'))
update('INDEX.md', lambda s: insert_after_heading(s, '> U4课间承接 / 框高启动与停止阈值：['
    + 'L3/L4同步审查](' + P + REPORT + ')；U7逐格真机测试 / 足球动态标定 / 线程退出：['
    + '四课测试指导](' + P + GUIDE + ')（2026-10-29；未新增确认）。'))
update('CHANGELOG.md', lambda s: insert_after_heading(s, '## 2026-10-29 · U4课间承接与U7真机测试准备\n\n'
    '- 回读U4-L3/L4，修订课间承接、开闭环比较条件和L2分组记录引用；区分接待触发与视觉停止阈值，保留控制代码。\n'
    '- 搜寻U7四课主稿，落实L1/L2两处`<sss>`情境备忘；保留用户现有修改，反向同步相关生成器。\n'
    '- 新增按格号/STEP组织的四课真机指导，说明静态及动态标定、播报期间检测、任务状态与物理效果、退出重跑和未测项。\n'
    '- 更新大纲说明、阶段依据和导航；只做离线检查，不新增确认或真机结果。本地Git提交，推送由用户手动进行。'))
update('05-internal-materials/vocational-planning/README.md', lambda s: insert_after_heading(s,
    '> **U4承接与U7测试准备（2026-10-29）**：' + summary + '[U4同步审查](03_X课程项目/'
    + REPORT + ')、[U7逐格真机测试](03_X课程项目/' + GUIDE + ')。'))

def outline(s):
    s = insert_after_heading(s, '> **U4后续课同步（2026-10-29）**：L3明确方向反馈与行进量同循环，记录比较条件；'
        'L4通过函数返回连接流程，框高仅作启动触发，未接入L2视觉停止程序。L2三组记录分别引用，触发位置另行标定。['
        + '同步审查](' + REPORT + ')；控制代码和确认状态不变。')
    s = s.replace('相机偏差用于调方向，里程计估计行进量，IMU z 轴角速度参与示例停止分支；',
        '相机偏差用于调方向，里程计估计行进量（未接入L2框高停止），IMU z 轴角速度参与示例停止分支；')
    s = s.replace('并引用 L2 的距离对照记录', '并分别引用 L2 行走、标定与阈值记录；启动触发比例另行核对')
    return s
update(P + 'X课程大纲-v5.md', outline)

def progress(s):
    s = insert_after_heading(s, '> **本轮衔接与测试准备（2026-10-29）**：' + summary + '['
        + 'U4同步审查](' + REPORT + ')、[U7逐课真机测试指导](' + GUIDE + ')。')
    s = s.replace('P1修订稿；文字校对完成 | ②未完成；无新确认 | 复核与L2的衔接，再真机②及P2',
        'P1修订稿；已同步新版L2承接与对照条件 | ②未完成；无新确认 | 按同步审查真机②，再P2')
    s = s.replace('P1修订稿；文字校对完成 | ②未完成；无新确认 | 与L2/L3统一任务后真机②及P2',
        'P1修订稿；触发阈值与L2分组记录已同步 | ②未完成；无新确认 | 按同步审查真机②，再P2')
    lines = s.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| [U7-L'):
            lines[i] = line.replace('按[验证清单](实验验证/U7_U8_v5重构与验证清单.md)逐格审阅/验证',
                '按[真机指导](' + GUIDE + ')逐格验证，保留未测项')
    return '\n'.join(lines) + '\n'
update(P + 'X课程当前进度.md', progress)
update(P + 'X课程开发计划-v4.md', lambda s: insert_after_heading(s,
    '> **后续阶段依据（2026-10-29）**：U4-L3/L4按新版L2同步承接、对照条件与记录，['
    + '审查](' + REPORT + ')列出P2待验及P3～P5注意事项。U7两处情境已补齐，['
    + '真机指导](' + GUIDE + ')按当前60格/24代码安排测试；阶段及确认状态不变。'))
update('05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md', lambda s:
    s + '\n\n## U4承接与U7测试准备（2026-10-29）\n\n'
    '- U4-L3/L4保留运动代码，同步新版L2的分组记录与课间分工；L4启动触发阈值不直接沿用L2停止阈值。后续设计依据['
    + '同步审查](../03_X课程项目/' + REPORT + ')，不再强制同一次停靠取得三项距离。\n'
    '- U7主稿两处`<sss>`情境备忘已落实；保留用户已有正文、代码与执行记录，并同步生成器。['
    + '四课测试指导](../03_X课程项目/' + GUIDE + ')按当前STEP及格号核查。\n'
    '- 本轮仅离线检查；动态标定、状态及退出依赖用户真机验证。未新增①②或P2通过；Git仅本地提交。\n')
update(P + '实验验证/U7_U8_v5重构与验证清单.md', lambda s: insert_after_heading(s,
    '> **U7测试入口更新（2026-10-29）**：L1/L2情境备忘已补齐，当前四课60格/24代码。['
    + '逐课真机测试指导](U7_逐课真机测试指导.md)细化STEP、格号、预期、未测项和退出；下列历史离线检查不替代当前真机验证。'))
update(P + '实验验证/U4-L2_重开发回读与第五部分同步.md', lambda s: insert_after_heading(s,
    '> **后续课已同步（2026-10-29）**：['
    + 'L3/L4承接审查](U4-L3-L4_承接新版L2的同步审查.md)已落实课间分工、比较条件及分组记录；L2本轮未再改动，后续课控制代码保留。'))

(TASK / '共享文档清单.json').write_text(json.dumps(shared, ensure_ascii=False, indent=2), encoding='utf-8')
print('已同步', len(shared), '份文档，并保存仅含本轮增量的HEAD版本')
