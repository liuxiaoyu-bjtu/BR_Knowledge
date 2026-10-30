from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import copy
import hashlib
import io
import json
import math
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
BASE = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)


def source(nb, number):
    return ''.join(nb['cells'][number - 1]['source'])


def execute(text, ns):
    # 离线运行学生代码前去掉time导入，注入不等待的时钟替身；不导入机器人SDK。
    tree = ast.parse(text)
    check('替身执行无SDK导入', not any(isinstance(node, (ast.Import, ast.ImportFrom)) and 'booster' in ast.unparse(node) for node in ast.walk(tree)))
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import)]
    with contextlib.redirect_stdout(io.StringIO()) as output:
        exec(compile(tree, '<offline-inputs>', 'exec'), ns)
    return output.getvalue()


nbs = {}
before_nbs = {}
for lesson, filename, count, code_count, generator in [
    ('L2', 'U4-L2_走近来宾.ipynb', 36, 10, '_gen_L14.py'),
    ('L3', 'U4-L3_跟住来宾.ipynb', 22, 8, '_gen_L15.py'),
    ('L4', 'U4-L4_接待来宾.ipynb', 29, 12, '_gen_L16.py')]:
    rel = P / 'notebooks' / filename
    nb = json.loads((ROOT / rel).read_text(encoding='utf-8'))
    old = json.loads((TASK / 'before' / rel).read_text(encoding='utf-8'))
    nbs[lesson], before_nbs[lesson] = nb, old
    check(lesson + '格数与代码数量', len(nb['cells']) == count and sum(c['cell_type'] == 'code' for c in nb['cells']) == code_count)
    check(lesson + '类型ID及元信息保留', [(c['id'], c['cell_type'], c['metadata']) for c in nb['cells']] == [(c['id'], c['cell_type'], c['metadata']) for c in old['cells']] and nb['metadata'] == old['metadata'])
    import nbformat
    nbformat.validate(nbformat.from_dict(nb))
    checks.append(lesson + 'nbformat有效')
    changed = [i for i, (a, b) in enumerate(zip(old['cells'], nb['cells']), 1) if a != b]
    check(lesson + '本轮改动范围', changed == {'L2': [15, 16, 18, 19], 'L3': [], 'L4': [21]}[lesson])
    for i, c in enumerate(nb['cells'], 1):
        if c['cell_type'] == 'code':
            compile(source(nb, i), str(rel) + ':' + str(i), 'exec')
            check(f'{lesson}第{i}格执行记录保留', c.get('execution_count') == old['cells'][i-1].get('execution_count') and c.get('outputs') == old['cells'][i-1].get('outputs'))
    gen_text = (ROOT / P / generator).read_text(encoding='utf-8')
    ns = {'__name__': 'offline_review', '__file__': str(ROOT / P / generator)}
    exec(compile(gen_text, generator, 'exec'), ns)
    check(lesson + '镜像完整一致', ns['NOTEBOOK'] == nb)
    with tempfile.TemporaryDirectory(prefix='u4_p2_') as folder:
        temp = Path(folder)
        (temp / 'notebooks').mkdir()
        exec(compile(gen_text, generator, 'exec'), {'__name__': '__main__', '__file__': str(temp / generator)})
        check(lesson + '生成器隔离重建一致', json.loads((temp / 'notebooks' / filename).read_text(encoding='utf-8')) == nb)

for rel, digest in BASE['other_notebooks'].items():
    check('其他学材未改：' + Path(rel).name, hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest)
check('L2第9格用户原文保留', source(nbs['L2'], 9) == source(before_nbs['L2'], 9))
check('L2自主编程位置保留', source(nbs['L2'], 35) == source(before_nbs['L2'], 35))
check('L3Notebook字节保留', (ROOT / P / 'notebooks/U4-L3_跟住来宾.ipynb').read_bytes() == (TASK / 'before' / P / 'notebooks/U4-L3_跟住来宾.ipynb').read_bytes())
check('L4仅更改旧STEP提示', source(nbs['L4'], 21) == source(before_nbs['L4'], 21).replace('旧致意任务未结束，请先执行STEP 11', '旧致意任务未结束，请先执行STEP 10'))


class StripReason(ast.NodeTransformer):
    def visit_Assign(self, node):
        if any(isinstance(target, ast.Name) and target.id == 'stop_reason' for target in node.targets):
            return None
        return node


for number in [16, 19]:
    old_tree = ast.parse(source(before_nbs['L2'], number))
    tree = ast.parse(source(nbs['L2'], number))
    old_loop = next(node for node in old_tree.body if isinstance(node, ast.For))
    protection = next(node for node in tree.body if isinstance(node, ast.Try))
    new_loop = next(node for node in protection.body if isinstance(node, ast.For))
    stripped = StripReason().visit(copy.deepcopy(new_loop))
    check(f'L2第{number}格原循环控制不变', ast.dump(old_loop, include_attributes=False) == ast.dump(stripped, include_attributes=False))
    check(f'L2第{number}格finally发零速度', len(protection.finalbody) == 1 and ast.unparse(protection.finalbody[0]) == 'robot.set_velocity(0, 0, 0)')
    calls = lambda value: [ast.unparse(node) for node in ast.walk(value) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id in ['robot', 'time']]
    check(f'L2第{number}格机器人与sleep调用集合不变', sorted(calls(old_tree)) == sorted(calls(tree)))


class Robot:
    def __init__(self, reads=(), repeat=0.0):
        self.reads = iter(reads)
        self.repeat = repeat
        self.commands = []

    def reset_odom(self):
        pass

    def get_odom(self):
        value = next(self.reads, self.repeat)
        if isinstance(value, BaseException):
            raise value
        return SimpleNamespace(pose_2d=(value, 0, 0))

    def set_velocity(self, *values):
        self.commands.append(values)

    def get_mode(self):
        return 'walk'

    def get_imu(self):
        return SimpleNamespace(angular_velocity=(0, 0, 0))


for number in [16, 19]:
    for label, reads, expected_exception, expected_reason in [
        ('到原阈值', [0, 0.4, 0.79], None, '里程计读数已接近计划行进量'),
        ('200轮耗尽', [], None, '达到轮数上限，尚未确认计划行进量'),
        ('读取异常', [0, RuntimeError('构造读数异常')], RuntimeError, '执行中断或异常，未完成本次行进'),
        ('Notebook中断', [0, KeyboardInterrupt()], KeyboardInterrupt, '执行中断或异常，未完成本次行进')]:
        robot = Robot(reads)
        ns = dict(robot=robot, time=SimpleNamespace(sleep=lambda seconds: None))
        caught = None
        try:
            output = execute(source(nbs['L2'], number), ns)
        except BaseException as error:
            caught = type(error)
        check(f'L2第{number}格{label}异常传播', caught is expected_exception)
        check(f'L2第{number}格{label}末次零速度', robot.commands[-1] == (0, 0, 0))
        check(f'L2第{number}格{label}结束原因', ns['stop_reason'] == expected_reason)
        check(f'L2第{number}格{label}原运动速度保留', all(command in [(0.3, 0, 0), (0, 0, 0)] for command in robot.commands))


class Clock:
    value = 0.0

    def monotonic(self):
        self.value += 0.01
        return self.value

    def sleep(self, seconds):
        self.value += seconds


ns = dict(math=math, time=Clock(), robot=Robot(), STOP_RATIO=0.3, CENTER_PX=20,
          TURN_ONLY_PX=80, MAX_YAW=0.2, KP_YAW=0.001, FORWARD_SPEED=0.1,
          PULSE_SECONDS=0.2, READ_LIMIT=1, RUN_SECONDS=20, ARRIVAL_CHECKS=3)
execute(source(nbs['L4'], 9), ns)
check('L4方向与远近分支', ns['choose_velocity'](300, 0.1)[:2] == (0, -0.2) and ns['choose_velocity'](0, 0.4)[:2] == (0, 0))
execute(source(nbs['L4'], 17), ns)
readings = iter([(0, 0.4, '可用'), (0, 0.4, '可用'), (0, 0.1, '可用'), (0, 0.4, '可用'), (0, 0.4, '可用'), (0, 0.4, '可用')])
ns['observe_target'] = lambda: next(readings)
with contextlib.redirect_stdout(io.StringIO()):
    result = ns['follow_to_guest']()
check('L4中途不满足时清零后再连续到位', result == '到位' and len(ns['motion_rows']) == 6)
check('L4交接前末次零速度', ns['robot'].commands[-1] == (0, 0, 0))
ns.update(greet_task=None)
execute(source(nbs['L4'], 21), ns)
check('L4默认未批准不进入运动', ns['flow_reason'] == '本轮未运行')
ns['greet_task'] = SimpleNamespace(done=lambda: False)
output = execute(source(nbs['L4'], 21).replace('APPROVED = False', 'APPROVED = True', 1), ns)
check('L4旧任务提示指向实际清理步骤', 'STEP 10' in output and 'STEP 11' not in output)

for lesson, maximum in [('L3', 8), ('L4', 12)]:
    titles = re.findall(r'\*\*STEP (\d+)：', '\n'.join(''.join(c['source']) for c in nbs[lesson]['cells'] if c['cell_type'] == 'markdown'))
    check(lesson + 'STEP连续', titles == [f'{i:02d}' for i in range(1, maximum+1)])

report = ROOT / P / '实验验证/U4-L2-L3-L4_P2复核与定稿记录.md'
for link in re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
    check('审定报告链接：' + link, (report.parent / link).exists())
progress = (ROOT / P / 'X课程当前进度.md').read_text(encoding='utf-8')
check('阶段分布更新', '| P2获批修订，待定向补验 | 1 |' in progress and '| P2审定通过，可进入P3 | 2 |' in progress and '| P1新稿/修订，待审或真机验证 | 8 |' in progress)
result = {'passed': len(checks), 'checks': checks, 'robot_sdk_loaded': False,
          'robot_connected': False, 'L2_P2_passed': False,
          'L3_L4_P2_passed': True, 'note': '运动异常与中断使用构造输入；两格实际停止效果待用户真机补验。'}
(TASK / '离线核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(checks)}项离线核对通过；L3/L4可进入P3，L2仍待两格真机补验。')
