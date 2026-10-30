from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
REPORT = 'U4-L3_回读审查与L4同步.md'
LINK = f'{P.as_posix()}/实验验证/{REPORT}'


def after_title(text, paragraph):
    first, rest = text.split('\n', 1)
    return first + '\n\n' + paragraph + '\n' + rest


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


brief = ('**U4-L3回读与L4同步（2026-10-30）**：保留用户简化后的L3八格代码及执行信息，'
         '补齐参数、实际检查范围和模式操作说明，STEP重排为01～08。L3现22格/8代码；'
         'L4仍31格/13代码，直接设置参数并复用L3验证值，删除重复启动口令，补清连续到位与致意交接。'
         '两份生成器同步；仅离线核对，仍为P1待①②，未进入P2。')


def transform(rel, text):
    if rel == Path('AGENTS.md'):
        return after_title(text, '> ' + brief + f' 入口：`{LINK}`。')
    if rel == Path('INDEX.md'):
        return after_title(text, f'> U4-L3用户简化稿 / 跟随参数 / STEP重排 / L4连续到位与致意交接：[回读与同步]({LINK})（2026-10-30；22/31格、8/13代码；P1待①②）。')
    if rel == Path('CHANGELOG.md'):
        return after_title(text, f'''## 2026-10-30 · 回读U4-L3用户修订稿并适度同步L4

- 保留L3当前22格、8格代码及执行信息，补齐参数含义、取图耗时检查范围和模式操作，STEP连续编号为01～08。
- L4维持31格/13代码及连续到位、致意前新观测和旧句柄检查；参数改为直接赋值，删除重复“接待”口令，保留动作交接确认。
- 两份生成器、L3测试格号及进度入口同步。[回读与后续验证依据]({LINK})；仅做离线检查，未运行机器人，未新增阶段确认。
- 仅本地Git记录，推送由用户操作。
''')
    if rel == Path('05-internal-materials/vocational-planning/README.md'):
        return after_title(text, '> ' + brief + f' [回读与验证依据](03_X课程项目/实验验证/{REPORT})。')
    if rel == P / 'X课程开发计划-v4.md':
        text = after_title(text, '> ' + brief + f' [逐项审查](实验验证/{REPORT})。下方25格/10代码为L3此前版本统计。')
        text = replace_once(text,
            'IMU/odom记录，停稳后位移/方位分析；25格/10代码，待新稿①②',
            'IMU/odom记录，停稳后位移/方位分析；用户简化稿22格/8代码，STEP 01～08，待①②')
        return replace_once(text,
            '31格/13代码，待新稿①② | `U4-L4_接待来宾`',
            '31格/13代码；同步L3直接参数写法，保留到位/动作交接，待①② | `U4-L4_接待来宾`')
    if rel == P / 'X课程当前进度.md':
        text = after_title(text, '> ' + brief + f' [当前步骤与待验项](实验验证/{REPORT})。下方25格/10代码为L3此前版本统计。')
        text = replace_once(text,
            '| [U4-L3 跟住来宾](notebooks/U4-L3_跟住来宾.ipynb) | P1重设稿；移动目标视觉跟随 | 新稿①待审、②待验证；未进P2 | 按[新验证清单](实验验证/U4-L3-L4_视觉移动跟随重设与验证.md)核对静态、移动与退出 | 25格/10代码；视觉控制跟进/暂停，IMU/odom记录位移与朝向；旧静止双对照已撤下 |',
            f'| [U4-L3 跟住来宾](notebooks/U4-L3_跟住来宾.ipynb) | P1用户简化稿；回读说明已补齐 | ①②未新增确认；未进P2 | 按[当前格号](实验验证/{REPORT})核对静态、移动与退出 | 22格/8代码，STEP 01～08；用户代码与执行信息保留，IMU/odom用于运动记录 |')
        return replace_once(text,
            '| [U4-L4 接待来宾](notebooks/U4-L4_接待来宾.ipynb) | P1重设稿；跟随与接待流程联调 | 新稿①待审、②待验证；未进P2 | 按[新验证清单](实验验证/U4-L3-L4_视觉移动跟随重设与验证.md)核对连续到位、致意和旧任务退出 | 31格/13代码；不再用起步间距/odom控制到位，无0.35触发阈值；动作终态须真机核对 |',
            f'| [U4-L4 接待来宾](notebooks/U4-L4_接待来宾.ipynb) | P1重设稿；已同步L3简化参数写法 | 新稿①待审、②待验证；未进P2 | 按[同步与待验项](实验验证/{REPORT})核对连续到位、致意和旧任务退出 | 31格/13代码；参数与完整流程两格代码调整，保留连续到位及动作交接确认；动作终态待真机核对 |')
    if rel == P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md':
        text = after_title(text, f'> **2026-10-30现稿**：L3经用户简化后为22格/8代码，八格代码及执行信息保留；L4为31格/13代码，直接参数与重复启动确认已调整。第4.2节按当前L3格号更新，第2节仍记录2026-10-29的重设过程。详见[回读与L4同步]({REPORT})。未新增①②确认，未进入P2。')
        start = text.index('### 4.2 L3逐步验证')
        end = text.index('### 4.3 L4逐步验证')
        text = text[:start] + '''### 4.2 L3逐步验证

| STEP / 代码格 | 测什么 | 应看到什么 |
| --- | --- | --- |
| 01 / 第5格 | 首次连接、检测模型 | 机型/编号/模式正确，模型与目标匹配，未发运动指令 |
| 02 / 第7格 | 直接填写L2实测停止占比与L1/L2参数 | 0.3只作示例占位；采用本组标定值，目标、姿态与参数在记录表保留 |
| 03、04 / 第9、11格 | 定义与静态决定 | 远且对准时跟进，偏差大时先转向；达到阈值后vx=0，仍可能原地修正；无目标、多目标、碰边或处理过慢时拒用 |
| 05 / 第13格 | IMU/odom字段 | x/y为米、yaw和角速度分别为rad与rad/s；不触发运动或诊断 |
| §4.1 / 第14格文字 | 模式与人工确认 | 按已学操作先prepare、人工支撑/STAND站起、确认站稳再walk；保持标定时姿态 |
| 06 / 第16格 | 静止目标接近，再缓慢远离—停留、小幅侧移 | 输出跟进、已近、先对准；已近后继续观察，远离后再次跟进；异常退出尝试零速度 |
| 07 / 第18格 | 停稳后的终点 | 有效起终点、直线位移及方向、机身朝向；区分位移与路程 |
| 08 / 第20格 | 收尾与重复运行 | 先零速度再prepare；人工支撑与阻尼流程扶坐，下一轮重新布置并确认 |

先用静止目标核对靠近后停止前进，再增加移动。不为制造失败让人突然穿入行走路线。`READ_LIMIT`只在接口返回后检查耗时，不能打断阻塞调用；读IMU和odom可能延长速度指令持续时间，这些都须现场测量。波动导致频繁启停时记录框高与决定，再逐项评估阈值、短步和速度。

''' + text[end:]
        text = replace_once(text,
            'ID及类型来自本机；`greet_task`仅首次初始化，重复测试保留原句柄',
            '参数直接采用L3调试值，动作ID及类型来自本机；`greet_task`仅首次初始化，重复测试保留原句柄')
        return replace_once(text,
            '等待→跟随→到位→人工确认/新观测→致意；未到位跳过致意，不按预计里程触发',
            '现场核对后设APPROVED=True；等待→跟随→到位→人工确认/新观测→致意；无重复“接待”口令，未到位跳过致意')
    raise ValueError(rel)


shared = [Path('AGENTS.md'), Path('INDEX.md'), Path('CHANGELOG.md'),
          Path('05-internal-materials/vocational-planning/README.md'),
          P / 'X课程开发计划-v4.md', P / 'X课程当前进度.md',
          P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md']

for rel in shared:
    path = ROOT / rel
    before = path.read_bytes()
    current = before.decode('utf-8').replace('\r\n', '\n')
    updated = transform(rel, current)
    assert path.read_bytes() == before, f'文件已被其他任务修改：{rel}'
    path.write_bytes(updated.encode('utf-8'))
    head = subprocess.check_output(['git', 'show', 'HEAD:' + rel.as_posix()], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    isolated = transform(rel, head)
    dest = TASK / 'head-increment' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(isolated.encode('utf-8'))

(TASK / '共享文档清单.json').write_text(json.dumps([p.as_posix() for p in shared], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('已同步7份共享文档；仅本轮增量另存，未暂存或提交。')
