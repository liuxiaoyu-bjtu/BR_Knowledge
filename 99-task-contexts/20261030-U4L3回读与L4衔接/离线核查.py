from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import hashlib
import io
import json
import math
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)


def source(nb, number):
    return ''.join(nb['cells'][number - 1]['source'])


def run(text, namespace):
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(text, '<offline-notebook>', 'exec'), namespace)


nbs = {}
for lesson, name, count, codes in [('L3', 'U4-L3_跟住来宾.ipynb', 22, 8),
                                   ('L4', 'U4-L4_接待来宾.ipynb', 31, 13)]:
    rel = P / 'notebooks' / name
    nb = json.loads((ROOT / rel).read_text(encoding='utf-8'))
    before = json.loads((TASK / 'before' / rel).read_text(encoding='utf-8'))
    nbs[lesson] = nb
    check(lesson + '格数', len(nb['cells']) == count)
    check(lesson + '代码格数', sum(c['cell_type'] == 'code' for c in nb['cells']) == codes)
    check(lesson + '单元格ID及类型保留', [(c['id'], c['cell_type']) for c in nb['cells']] == [(c['id'], c['cell_type']) for c in before['cells']])
    check(lesson + 'Notebook元信息保留', nb['metadata'] == before['metadata'])
    import nbformat
    nbformat.validate(nbformat.from_dict(nb))
    checks.append(lesson + 'nbformat有效')
    for i, c in enumerate(nb['cells'], 1):
        if c['cell_type'] == 'code':
            compile(source(nb, i), str(rel) + ':' + str(i), 'exec')
            check(f'{lesson}第{i}格执行信息保留', c.get('execution_count') == before['cells'][i-1].get('execution_count') and c.get('outputs') == before['cells'][i-1].get('outputs'))
    changed_code = [i for i, (a, b) in enumerate(zip(before['cells'], nb['cells']), 1) if a['cell_type'] == 'code' and a['source'] != b['source']]
    check(lesson + '代码改动范围', changed_code == ([] if lesson == 'L3' else [7, 23]))
    steps = re.findall(r'\*\*STEP (\d+)：', '\n'.join(source(nb, i) for i in range(1, len(nb['cells'])+1) if nb['cells'][i-1]['cell_type'] == 'markdown'))
    check(lesson + 'STEP编号连续', steps == [f'{i:02d}' for i in range(1, (8 if lesson == 'L3' else 13)+1)])
    gen = '_gen_L15.py' if lesson == 'L3' else '_gen_L16.py'
    text = (ROOT / P / gen).read_text(encoding='utf-8')
    mirror = {}
    exec(compile(text, gen, 'exec'), {'__name__': 'offline_check', '__file__': str(ROOT / P / gen)}, mirror)
    check(lesson + '镜像内容完全一致', mirror['NOTEBOOK'] == nb)
    with tempfile.TemporaryDirectory(prefix='u4_mirror_') as folder:
        temp = Path(folder)
        (temp / 'notebooks').mkdir()
        run(text, {'__name__': '__main__', '__file__': str(temp / gen)})
        check(lesson + '生成器隔离重建一致', json.loads((temp / 'notebooks' / name).read_text(encoding='utf-8')) == nb)

for rel, digest in baseline['other_notebooks'].items():
    check('其他Notebook未改：' + Path(rel).name, hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest)


class Clock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        self.value += 0.01
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class Robot:
    def __init__(self):
        self.commands = []
        self.action_calls = []

    def get_mode(self):
        return 'walk'

    def set_velocity(self, *command):
        self.commands.append(command)

    def reset_odom(self):
        pass

    def get_odom(self):
        return SimpleNamespace(pose_2d=(0.1, 0.0, 0.0))

    def get_imu(self):
        return SimpleNamespace(angular_velocity=(0.0, 0.0, 0.0))

    def list_actions(self):
        return [SimpleNamespace(id=1)]

    def do_action(self, action):
        self.action_calls.append(action)
        return SimpleNamespace(done=lambda: True, wait=lambda timeout: 'SUCCEEDED')


def settings():
    return dict(STOP_RATIO=0.3, CENTER_PX=20, TURN_ONLY_PX=80, MAX_YAW=0.2,
                KP_YAW=0.001, FORWARD_SPEED=0.1, PULSE_SECONDS=0.2,
                READ_LIMIT=1.0, RUN_SECONDS=20.0, ARRIVAL_CHECKS=3,
                ACTION_WAIT=10, GREET_ID=1, robot=Robot(), time=Clock(), math=math)


ns = settings()
run(source(nbs['L3'], 9), ns)
choose = ns['choose_velocity']
check('远且居中时前进', choose(0, 0.1)[:2] == (0.1, 0.0))
check('右侧大偏差先右转且限幅', choose(300, 0.1)[:2] == (0.0, -0.2))
check('左侧大偏差先左转且限幅', choose(-300, 0.1)[:2] == (0.0, 0.2))
check('阈值边界停止前进', choose(0, 0.3)[:2] == (0.0, 0.0))
check('近处仍可修正方向', choose(60, 0.4)[:2] == (0.0, -0.06))

observations = iter([(0, 0.1, '可用'), (0, 0.4, '可用'), (0, 0.1, '可用'), (None, None, '未检测到目标')])
ns['observe_target'] = lambda: next(observations)
body = source(nbs['L3'], 16)
run(body.replace('APPROVED = False', 'APPROVED = True', 1), ns)
check('L3到近处后继续观察并再次跟进', [row[-1] for row in ns['follow_rows']] == ['跟进', '已近，停止前进', '跟进'])
check('L3丢失目标退出且最后发零速度', ns['follow_reason'] == '未检测到目标' and ns['robot'].commands[-1] == (0, 0, 0))

ns = settings()
run(source(nbs['L4'], 19), ns)
observations = iter([(0, 0.4, '可用'), (0, 0.4, '可用'), (0, 0.1, '可用'), (0, 0.4, '可用'), (0, 0.4, '可用'), (0, 0.4, '可用')])
ns['observe_target'] = lambda: next(observations)
ns['choose_velocity'] = choose
with contextlib.redirect_stdout(io.StringIO()):
    result = ns['follow_to_guest']()
check('L4连续计数被中途不满足条件清零', result == '到位' and len(ns['motion_rows']) == 6)
check('L4到位后最后发零速度', ns['robot'].commands[-1] == (0, 0, 0))
ns['observe_target'] = lambda: (None, None, '检测到多个目标')
with contextlib.redirect_stdout(io.StringIO()):
    result = ns['follow_to_guest']()
check('L4多目标阻断跟随', result == '检测到多个目标' and ns['motion_rows'] == [])

body = source(nbs['L4'], 23)
ns = settings()
ns.update(greet_task=None, input=lambda _: (_ for _ in ()).throw(AssertionError('不应再询问重复启动口令')))
run(body, ns)
check('L4未批准不发运动指令', ns['robot'].commands == [])
ns['greet_task'] = SimpleNamespace(done=lambda: False)
run(body.replace('APPROVED = False', 'APPROVED = True', 1), ns)
check('L4旧任务未结束时不启动', ns['robot'].commands == [])
for wait_result, follow_result, expected in [(False, '到位', ['等待']), (True, '达到时限', ['等待', '跟随']), (True, '到位', ['等待', '跟随', '致意'])]:
    calls = []
    def wait():
        calls.append('等待')
        return wait_result
    def follow():
        calls.append('跟随')
        return follow_result
    def greet():
        calls.append('致意')
        return '致意任务成功'
    ns.update(greet_task=None, wait_for_guest=wait, follow_to_guest=follow, greet_guest=greet)
    run(body.replace('APPROVED = False', 'APPROVED = True', 1), ns)
    check('L4主流程交接：' + '/'.join(expected), calls == expected and ns['robot'].commands[-1] == (0, 0, 0))

ns = settings()
ns.update(greet_task=None, input=lambda _: '致意')
run(source(nbs['L4'], 21), ns)
for observation in [(None, None, '未检测到目标'), (0, 0.1, '可用'), (100, 0.4, '可用')]:
    ns['observe_target'] = lambda observation=observation: observation
    result = ns['greet_guest']()
    check('致意前新观测阻断：' + str(observation), ns['robot'].action_calls == [] and result != '致意任务成功')
ns['observe_target'] = lambda: (0, 0.4, '可用')
check('到位与确认满足才调用致意', ns['greet_guest']() == '致意任务成功' and ns['robot'].action_calls == [1])

summary = {'passed': len(checks), 'checks': checks,
           'robot_sdk_loaded': False, 'robot_connected': False,
           'note': '构造输入与替身对象核对控制分支；不能证明真机步态、间距、时延或动作终态。'}
(TASK / '离线核查结果.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(checks)}项离线核查通过；未导入机器人SDK，未连接机器人。')
