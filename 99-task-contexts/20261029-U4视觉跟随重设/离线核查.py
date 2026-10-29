from pathlib import Path
from types import SimpleNamespace as NS
import ast
import contextlib
import hashlib
import io
import json
import math
import re
import runpy
import tempfile
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
BASE = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
checks = []

def check(name, condition):
    assert condition, name
    checks.append(name)

def code_cells(prefix):
    path = next((P / 'notebooks').glob(prefix + '_*.ipynb'))
    nb = json.loads(path.read_text(encoding='utf-8'))
    return nb, [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']

class Clock:
    def __init__(self):
        self.now = 0.0
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds

class Task:
    def __init__(self, status='SUCCEEDED', active=False):
        self.status = status
        self.active = active
        self.cancelled = False
    def done(self):
        return not self.active
    def wait(self, timeout):
        return self.status
    def cancel(self):
        self.cancelled = True
        self.active = False
        self.status = 'CANCELLED'

class Robot:
    def __init__(self):
        self.commands = []
        self.pose = [0.0, 0.0, 0.0]
        self.task = Task()
        self.action_calls = 0
        self.imu_fault = None
    def get_mode(self):
        return 'walk'
    def set_velocity(self, vx, vy, yaw):
        self.commands.append((vx, vy, yaw))
    def reset_odom(self):
        self.pose = [0.0, 0.0, 0.0]
    def get_odom(self):
        return NS(pose_2d=list(self.pose))
    def get_imu(self):
        if self.imu_fault:
            raise self.imu_fault
        return NS(angular_velocity=[0, 0, .2])
    def list_actions(self):
        return [NS(id=7)]
    def do_action(self, action_id):
        self.action_calls += 1
        return self.task

def environment():
    clock = Clock()
    return {'math': math, 'time': clock, 'robot': Robot(),
            'STOP_RATIO': .6, 'CENTER_PX': 20, 'TURN_ONLY_PX': 80,
            'FORWARD_SPEED': .1, 'KP_YAW': .001, 'MAX_YAW': .2,
            'PULSE_SECONDS': .2, 'READ_LIMIT': 1.0, 'RUN_SECONDS': 2.0,
            'TARGET_CLASS': 'person', 'APPROVED': True,
            'greet_task': None, 'GREET_ID': 7, 'ARRIVAL_CHECKS': 3, 'ACTION_WAIT': 10,
            'input': lambda _: '致意'}

def sequence(values):
    iterator = iter(values)
    return lambda: next(iterator)

def run(source, env):
    with contextlib.redirect_stdout(io.StringIO()):
        exec(source, env)

L3, c3 = code_cells('U4-L3')
L4, c4 = code_cells('U4-L4')
visual3 = next(s for s in c3 if 'def observe_target()' in s)
visual4 = next(s for s in c4 if 'def observe_target()' in s)
check('两课视觉判断与指令计算一致', visual3 == visual4)

env = environment()
run(visual3, env)
choose = env['choose_velocity']
check('远且对准可以前进', choose(0, .4)[0] == .1)
check('达到阈值停止前进', choose(0, .6)[0] == 0)
check('超过阈值不后退不前进', choose(0, .8)[0] == 0)
check('大偏差先原地对准', choose(100, .4)[0] == 0)
check('目标右偏发负yaw', choose(50, .4)[1] < 0)
check('目标左偏发正yaw', choose(-50, .4)[1] > 0)
check('中心范围不来回微调', choose(10, .4)[1] == 0)
check('转向角速度受限', abs(choose(1000, .4)[1]) == .2)

box = NS(center_x=320., center_y=240., width=100., height=200.)
target = NS(class_name='person', bbox=box)
env['robot'].get_image = lambda **_: NS(width=640, height=480, to_numpy=lambda: None)
env['detector'] = NS(detect=lambda _: [target])
error, ratio, note = env['observe_target']()
check('合法目标返回偏差与高度占比', error == 0 and math.isclose(ratio, 200/480) and note == '可用')
env['detector'].detect = lambda _: []
check('无目标拒用', env['observe_target']() == (None, None, '未检测到目标'))
env['detector'].detect = lambda _: [target, target]
check('多目标拒用', env['observe_target']()[2] == '检测到多个目标')
env['detector'].detect = lambda _: [target]
box.center_x = 30
check('边缘框拒用', env['observe_target']()[0] is None)
box.center_x = math.nan
check('非有限框拒用', env['observe_target']()[0] is None)
box.center_x = 320
def slow(_):
    env['time'].sleep(1.1)
    return [target]
env['detector'].detect = slow
check('取图检测过慢拒用', env['observe_target']()[2] == '本次取图与检测过慢')

follow3 = next(s for s in c3 if s.startswith('APPROVED ='))
env = environment()
run(visual3, env)
env['input'] = lambda _: '跟随'
env['observe_target'] = sequence([(0,.3,'可用'),(0,.6,'可用'),(0,.3,'可用'),(100,.3,'可用'),(None,None,'未检测到目标')])
run(follow3.replace('APPROVED = False', 'APPROVED = True', 1), env)
decisions = [r[6] for r in env['follow_rows']]
check('L3跟进近处暂停并能再次跟进', decisions[:3] == ['跟进','已近，停止前进','跟进'])
check('L3大偏差只转向', decisions[3] == '先原地对准')
check('L3丢目标结束且最终零速度', env['follow_reason'] == '未检测到目标' and env['robot'].commands[-1] == (0,0,0))

for fault in [RuntimeError('模拟读取失败'), KeyboardInterrupt()]:
    env = environment()
    run(visual3, env)
    env['input'] = lambda _: '跟随'
    env['observe_target'] = lambda: (0,.3,'可用')
    env['robot'].imu_fault = fault
    try:
        run(follow3.replace('APPROVED = False', 'APPROVED = True', 1), env)
    except (RuntimeError, KeyboardInterrupt):
        pass
    check('L3' + type(fault).__name__ + '退出清零并保留异常原因', env['robot'].commands[-1] == (0,0,0) and '异常或中断' in env['follow_reason'])

follow4 = next(s for s in c4 if s.startswith('def follow_to_guest'))
wait4 = next(s for s in c4 if s.startswith('def wait_for_guest'))
greet4 = next(s for s in c4 if s.startswith('def greet_guest'))
env = environment()
run(visual4, env)
run(follow4, env)
env['observe_target'] = sequence([(0,.6,'可用'),(0,.3,'可用'),(0,.6,'可用'),(0,.6,'可用'),(0,.6,'可用')])
with contextlib.redirect_stdout(io.StringIO()):
    result = env['follow_to_guest']()
check('L4到位中断后重计连续次数', result == '到位' and len(env['motion_rows']) == 5)
check('L4到位后已发零速度', env['robot'].commands[-1] == (0,0,0))
env = environment()
run(visual4, env)
run(follow4, env)
env['observe_target'] = lambda: (None,None,'检测到多个目标')
check('L4跟随多目标退出', env['follow_to_guest']() == '检测到多个目标' and not env['motion_rows'])
run(wait4, env)
with contextlib.redirect_stdout(io.StringIO()):
    result = env['wait_for_guest']()
check('L4等待多目标立即阻断', result is False and env['time'].now == 0)
env['observe_target'] = lambda: (None,None,'未检测到目标')
with contextlib.redirect_stdout(io.StringIO()):
    result = env['wait_for_guest'](.5)
check('L4无目标只有限等待', result is False and env['time'].now >= .5)

env = environment()
run(greet4, env)
env['observe_target'] = lambda: (0,.3,'可用')
check('L4确认后目标远离不致意', '改变' in env['greet_guest']() and env['robot'].action_calls == 0)
env['observe_target'] = lambda: (None,None,'未检测到目标')
check('L4致意前丢目标阻断', '不可用' in env['greet_guest']() and env['robot'].action_calls == 0)
env['observe_target'] = lambda: (0,.6,'可用')
env['greet_task'] = Task('RUNNING', active=True)
check('L4旧任务未结束不启动新动作', '旧致意' in env['greet_guest']() and env['robot'].action_calls == 0)
env['greet_task'] = None
check('L4有效到位可以致意并按成功状态记录', env['greet_guest']() == '致意任务成功' and env['robot'].action_calls == 1)
env['greet_task'] = None
env['robot'].task = Task('RUNNING', active=True)
result = env['greet_guest']()
check('L4超时取消不改写成成功', 'CANCELLED' in result and '超时' in result and env['robot'].task.cancelled)
env['robot'].get_mode = lambda: 'prepare'
check('L4人工确认后复核模式', '模式' in env['greet_guest']())

main4 = next(s for s in c4 if s.startswith('APPROVED ='))
env = environment()
env['input'] = lambda _: '接待'
env['wait_for_guest'] = lambda: True
env['follow_to_guest'] = lambda: '未检测到目标'
env['greet_guest'] = lambda: (_ for _ in ()).throw(AssertionError('不应致意'))
run(main4.replace('APPROVED = False', 'APPROVED = True', 1), env)
check('L4完整流程未到位跳过致意并停止', env['flow_reason'] == '未检测到目标' and env['robot'].commands[-1] == (0,0,0))
env = environment()
env['input'] = lambda _: '接待'
env['wait_for_guest'] = lambda: True
env['follow_to_guest'] = lambda: '到位'
env['greet_guest'] = lambda: '致意任务成功'
run(main4.replace('APPROVED = False', 'APPROVED = True', 1), env)
check('L4完整流程只在到位后交接致意', env['flow_reason'] == '致意任务成功' and env['robot'].commands[-1] == (0,0,0))
env['follow_to_guest'] = lambda: (_ for _ in ()).throw(RuntimeError('模拟跟随读取异常'))
try:
    run(main4.replace('APPROVED = False', 'APPROVED = True', 1), env)
except RuntimeError:
    pass
check('L4执行异常仍清零并保留异常说明', env['robot'].commands[-1] == (0,0,0) and '异常' in env['flow_reason'])

stats = next(s for s in c3 if s.startswith('def report_motion'))
run(stats, env)
out = io.StringIO()
with contextlib.redirect_stdout(out):
    env['report_motion']([0,0,0], [3,4,.7], [[0,0,0,0,.5,.2,'跟进']])
check('位移汇总区分5米净位移和机身朝向', '5.000' in out.getvalue() and '53.1' in out.getvalue() and '0.700' in out.getvalue())

formats = []
regen = runpy.run_path(str(P / '_regen_from_nb.py'), run_name='maintenance_check')
for number, prefix in [(15, 'U4-L3'), (16, 'U4-L4')]:
    path = next((P / 'notebooks').glob(prefix + '_*.ipynb'))
    raw = path.read_bytes()
    nb = json.loads(raw)
    nbformat.validate(nbformat.from_dict(nb))
    check(prefix + 'cell ID不重复', len({c['id'] for c in nb['cells']}) == len(nb['cells']))
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            ast.parse(''.join(cell['source']))
            check(prefix + '代码输出未冒用旧结果-' + cell['id'], cell['execution_count'] is None and cell['outputs'] == [])
    gen = P / f'_gen_L{number}.py'
    with tempfile.TemporaryDirectory(prefix='u4follow-') as tmp:
        sandbox = Path(tmp)
        (sandbox / 'notebooks').mkdir()
        copied = sandbox / gen.name
        copied.write_bytes(gen.read_bytes())
        runpy.run_path(str(copied), run_name='__gen__')
        output = sandbox / 'notebooks' / path.name
        check(prefix + '正向镜像一致', json.loads(output.read_text(encoding='utf-8')) == nb)
        regen['build'](str(copied), str(output), '完整镜像核查')
        runpy.run_path(str(copied), run_name='__gen__')
        check(prefix + '反向再生成一致', json.loads(output.read_text(encoding='utf-8')) == nb)
    check(prefix + '检查未覆盖源文件', raw == path.read_bytes())
    formats.append({'file': path.name, 'cells': len(nb['cells']), 'code_cells': sum(c['cell_type'] == 'code' for c in nb['cells'])})

for rel, digest in BASE['protected'].items():
    check('范围外Notebook保留-' + Path(rel).name, hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest)
guide = P / '实验验证/U4-L3-L4_视觉移动跟随重设与验证.md'
for target in re.findall(r'\[[^\]]*\]\(([^\n)]+)\)', guide.read_text(encoding='utf-8')):
    if not target.startswith(('https:', 'http:', '#')):
        check('报告链接-' + target, (guide.parent / target).exists())
result = {'passed': len(checks), 'checks': checks, 'notebooks': formats,
          'other_notebooks_preserved': len(BASE['protected']), 'robot_executed': False}
(TASK / '离线核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('离线核查通过', len(checks), '项。未调用SDK、未运行机器人；构造分支不替代真机结果。')
