from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
RULE = Path('05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md')
REPORT = 'U4-L2-L3-L4_P2复核与定稿记录.md'
LINK = (P / '实验验证' / REPORT).as_posix()


def after_first_line(text, paragraph):
    first, rest = text.split('\n', 1)
    return first + '\n\n' + paragraph + '\n' + rest


def replace_row(text, prefix, row):
    lines = text.splitlines(keepends=True)
    found = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(found) == 1, prefix
    lines[found[0]] = row + '\n'
    return ''.join(lines)


brief = ('**U4后三课P2（2026-10-30）**：用户明确确认L2、L3、L4当前版本真机验证完成，'
         '①②依据已登记。L3、L4复核通过并登记③，可以进入P3；L2第16、19格按用户同意'
         '补最小try/finally及结束原因，待两格定向补验后再通过P2。三课36/22/29格、'
         '10/8/12代码，L4旧STEP提示已校正，正式镜像同步；未自动生成P3，未运行机器人。')


def transform(rel, text):
    if rel == Path('AGENTS.md'):
        return after_first_line(text, '> ' + brief + f' 审定与补验：`{LINK}`。下方“11课P1”等为历史统计，当前为8课P1、1课P2待补验、2课P2通过。')
    if rel == Path('INDEX.md'):
        return after_first_line(text, f'> U4-L2/L3/L4 P2 / 确认②③ / 行走中断停止 / 两格定向补验：[统一审定]({LINK})（2026-10-30；L3/L4通过，L2获批修订待补验）。')
    if rel == Path('CHANGELOG.md'):
        return after_first_line(text, f'''## 2026-10-30 · U4后三课真机确认与P2审定

- 用户明确确认三课当前版本真机验证均已完成，登记①②；L3、L4复核通过，③登记，可以进入P3。
- 回读L4用户29格/12代码稿，保留手动模式操作和简化说明，仅将旧任务提示由STEP 11校正为STEP 10；L2/L4正式生成器反向同步。
- L2第16、19格按用户确认加最小try/finally及结束原因，保留轮数、运动参数与判断；两格定向补验后再通过P2。第9格原文和学生自主程序保留。
- [目标覆盖、审定与补验]({LINK})、逐课进度和规则同步。当前4课有P5完成记录、17课P5待⑥、2课P2通过、1课P2待补验、8课P1待①②。
- 仅离线核对，未运行机器人、未生成P3；本地Git记录，推送由用户操作。
''')
    if rel == Path('05-internal-materials/vocational-planning/README.md'):
        return after_first_line(text, '> ' + brief + f' [审定与两格补验](03_X课程项目/实验验证/{REPORT})。')
    if rel == P / 'X课程当前进度.md':
        text = after_first_line(text, '> ' + brief + f' [审定及补验清单](实验验证/{REPORT})。本条覆盖下方此前“待①②”的U4记录。')
        text = replace_row(text, '| P1新稿/修订，待审或真机验证 |', '| P1新稿/修订，待审或真机验证 | 8 | U7/U8八课，待①② |\n| P2获批修订，待定向补验 | 1 | U4-L2第16、19格；两格补验后再登记③ |\n| P2审定通过，可进入P3 | 2 | U4-L3、L4；本轮未生成P3 |')
        for lesson, name, status, confirmation, next_step, note in [
            ('L2', '走近来宾', 'P2复核；获批修订已完成，待两格补验', '①通过；用户确认修订前现稿②；新增停止路径待补验，③未登记', '补验第16、19格正常退出及Notebook中断停止，再完成P2', '36格/10代码；原参数与控制判断保留，try/finally和结束原因已补；学生阈值作答格保留'),
            ('L3', '跟住来宾', 'P2审定通过，可以进入P3', '①②依据已登记，③通过（2026-10-30）', '按现稿编写P3教学设计，本轮未生成', '22格/8代码，STEP 01～08；本轮Notebook字节未改，视觉控制与运动记录分工明确'),
            ('L4', '接待来宾', 'P2审定通过，可以进入P3', '①②依据已登记，③通过（2026-10-30）', '按用户29格稿编写P3教学设计，本轮未生成', '29格/12代码，STEP 01～12；保留用户简化，旧任务提示仅改为STEP 10，不改运动行为')]:
            text = replace_row(text, f'| [U4-{lesson} ', f'| [U4-{lesson} {name}](notebooks/U4-{lesson}_{name}.ipynb) | {status} | {confirmation} | [审定与后续](实验验证/{REPORT})：{next_step} | {note} |')
        return text
    if rel == P / 'X课程开发计划-v4.md':
        text = after_first_line(text, '> ' + brief + f' [审定及补验](实验验证/{REPORT})。当前分布为4课P5完成记录、17课P5待⑥、2课P2通过、1课P2待补验、8课P1待①②；下方旧统计按历史阅读。')
        text = text.replace('4 notebook（L2～L4待确认②）', '4 notebook（L3/L4 P2通过，L2两格修订待补验）')
        updates = [
            ('L2', '走近来宾（距离估计与核对）', 'STEP04行走、STEP05速度比较、STEP06标定、STEP07独立核对、STEP08阈值自主程序；36格/10代码；①②有用户确认，第16/19格最小停止路径修订待补验，③未登记', '走近来宾'),
            ('L3', '跟住来宾（闭环与视觉伺服）', '移动目标视觉跟随，近处暂停、远离再跟进；IMU/odom记录，停稳后位移/方位分析；22格/8代码；①②③通过，可以进入P3', '跟住来宾'),
            ('L4', '接待来宾（视觉跟随与流程联调）', '发现来宾→跟随→连续到位→复核→致意及退出；29格/12代码，用户模式操作说明保留，旧STEP提示校正；①②③通过，可以进入P3', '接待来宾')]
        for lesson, title, note, name in updates:
            text = replace_row(text, f'| **U4** | **{lesson}** |', f'| **U4** | **{lesson}** | **{title}** | {note} | `U4-{lesson}_{name}` |')
        return text
    if rel == RULE:
        text = after_first_line(text, '> ' + brief + f' [当前审定](../03_X课程项目/实验验证/{REPORT})。本轮不改变通用P1～P6流程。')
        rows = [
            ('L2', '走近来宾', '🟡 **P2获批修订已完成，待第16/19格定向补验**', '**36格（26 md/10代码）**；用户确认当前稿①②。两格按获批方案加try/finally和结束原因，参数与判断保留；补验后再登记③。第9格用户原文及第35格学生作答保留，`_gen_L14.py`同步。'),
            ('L3', '跟住来宾', '🟢 **P2审定通过，①②③已登记，可进入P3（2026-10-30）**', '**22格（14 md/8代码）**，STEP 01～08；视觉方向/框高控制持续跟随，IMU/odom另作运动记录。用户简化稿本轮字节不变，`_gen_L15.py`一致；不沿用旧39格静止双对照或IMU差值停止口径。'),
            ('L4', '接待来宾', '🟢 **P2审定通过，①②③已登记，可进入P3（2026-10-30）**', '**29格（17 md/12代码）**，STEP 01～12；保留用户手动模式操作与简化文字。连续到位、致意前新观测及旧句柄检查完整，仅校正旧任务提示为STEP 10；`_gen_L16.py`同步，未改变运动行为。')]
        for lesson, name, status, note in rows:
            prefix = f'| `03_X课程项目/notebooks/U4-{lesson}_'
            row = f'| `03_X课程项目/notebooks/U4-{lesson}_{name}.ipynb` | U4·{lesson} | {status} | {note} |'
            if any(line.startswith(prefix) for line in text.splitlines()):
                text = replace_row(text, prefix, row)
            else:
                # HEAD的规则表尚无L3/L4；仅补入本轮当前审定，不带入工作区旧历史长行。
                anchor = f'| `03_X课程项目/notebooks/U4-L{int(lesson[1:]) - 1}_'
                lines = text.splitlines(keepends=True)
                index = next(i for i, line in enumerate(lines) if line.startswith(anchor))
                lines.insert(index + 1, row + '\n')
                text = ''.join(lines)
        return text
    if rel == P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md':
        text = after_first_line(text, f'> **2026-10-30 P2结果**：用户已确认三课现稿真机验证完成。L3（22格/8代码）与L4（29格/12代码）③通过，可以进入P3；L2两格停止路径获批修订，待定向补验。L4本节格号按用户最新稿更新，旧版本过程保留。详见[统一审定]({REPORT})。')
        start = text.index('### 4.3 L4逐步验证')
        end = text.index('## 5. 记录与后续阶段', start)
        text = text[:start] + '''### 4.3 L4当前格号与复核

用户已确认本版真机验证完成；下表用于后续P3覆盖与课堂复用，不另造新的实测结果。

| STEP / 代码格 | 内容 | 当前核对依据 |
| --- | --- | --- |
| 01、02 / 第5、7格 | 连接、动作列表及参数 | 保留首次初始化句柄，复用本组L3参数，动作ID来自本机 |
| 03、04 / 第9、11格 | 视觉规则和静态检查 | 与L3同样检查单一目标、碰边及耗时，额外显示是否满足到位条件 |
| 05 / 第13格 | 查看当前模式 | 文字给出已学模式操作，本格只打印；完整流程另检查walk |
| 06 / 第15格 | 定义有限等待 | 无目标有限等待，其他不可用原因退出 |
| 07 / 第17格 | 跟随与连续计数 | 不满足则清零，连续到位才返回“到位”；IMU/odom不参与到位条件 |
| 08 / 第19格 | 致意检查 | 输入后新取图，目标条件变化则跳过，动作与任务状态分别记录 |
| 09 / 第21格 | 完整一次接待 | APPROVED与walk检查、旧任务阻断、等待/跟随/致意交接；旧任务提示现为STEP 10 |
| 10 / 第23格 | 检查旧致意任务 | 保留句柄，必要时取消并等待；实际停稳另核对 |
| 11 / 第25格 | 最终运动报告 | 终点可能包含致意移动，位移、朝向和IMU采样分别说明 |
| 12 / 第27格 | 收尾 | 旧任务结束后才切prepare，继续既定人工支撑流程 |

''' + text[end:]
        return text
    raise ValueError(rel)


shared = [Path('AGENTS.md'), Path('INDEX.md'), Path('CHANGELOG.md'),
          Path('05-internal-materials/vocational-planning/README.md'), RULE,
          P / 'X课程当前进度.md', P / 'X课程开发计划-v4.md',
          P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md']

for rel in shared:
    path = ROOT / rel
    if (TASK / 'head-increment' / rel).exists():
        # 本轮前次运行已完成的共享文件，不重复插入。
        continue
    before = path.read_bytes()
    current = transform(rel, before.decode('utf-8').replace('\r\n', '\n'))
    head = subprocess.check_output(['git', 'show', 'HEAD:' + rel.as_posix()], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    isolated = transform(rel, head)
    assert path.read_bytes() == before, f'文件已有并发改动：{rel}'
    path.write_bytes(current.encode('utf-8'))
    dest = TASK / 'head-increment' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(isolated.encode('utf-8'))

(TASK / '共享文档清单.json').write_text(json.dumps([f.as_posix() for f in shared], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('8份阶段、规则与测试入口已同步；共享文件本轮增量另存，未暂存提交。')
