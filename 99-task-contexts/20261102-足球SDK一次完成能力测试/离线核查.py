from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import ast
import contextlib
import hashlib
import importlib.metadata
import io
import json
import math
import os
import re
import tempfile
import time
import nbformat
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
NP = V / '足球测试_第4轮_完整能力验证.ipynb'
nb = nbformat.read(NP, as_version=4)
nbformat.validate(nb)
codes = [c.source for c in nb.cells if c.cell_type == 'code']
assert len(codes) == 9 and len(nb.cells) == 19
assert all(c.get('execution_count') is None and not c.get('outputs') for c in nb.cells if c.cell_type == 'code')
for source in codes:
    ast.parse(source)
assert codes[0] == (TASK / '公共代码.py').read_text(encoding='utf-8').strip()
base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))

def run_scenario(name, **cfg):
    events = []
    counters = {'start': 0, 'stop': 0, 'update_command': 0, 'update_ball': 0}
    clock = [0.0]
    active = [False]
    class Robot:
        def __init__(self, enable_tf_listener):
            events.append('connect')
            if cfg.get('connection_fail'):
                raise RuntimeError('stub connection failure')
            self.robot_info = 'offline stub'
            self.loco_client = SimpleNamespace(GetMode=self.raw_mode)
            self.ros_adapter = SimpleNamespace(get_transform=self.get_transform)
        def get_mode(self):
            if cfg.get('mode_fail'):
                raise RuntimeError('stub public mode failure')
            return 'walk'
        def raw_mode(self):
            if cfg.get('mode_fail'):
                raise RuntimeError('stub raw mode failure')
            return SimpleNamespace(mode='soccer' if active[0] else 'walk')
        def get_odom(self):
            if cfg.get('odom_fail'):
                raise RuntimeError('stub odom failure')
            x = 0.16 if cfg.get('movement_limit') and counters['update_ball'] > 1 and active[0] else 0.0
            return SimpleNamespace(pose_2d=[x, 0.0, 0.0])
        def get_transform(self, target_frame, source_frame):
            if cfg.get('tf_fail'):
                raise RuntimeError('stub TF time failure')
            return SimpleNamespace(source_frame=source_frame, target_frame=target_frame, to_matrix=lambda: np.eye(4))
    class Manager:
        def __init__(self, robot):
            events.append('construct')
            if cfg.get('construct_fail'):
                raise RuntimeError('stub constructor failure')
            self.robot = robot
            self.ball = None
            self.command = None
        def start(self):
            counters['start'] += 1
            events.append('start')
            if counters['start'] == cfg.get('start_fail_at'):
                raise RuntimeError('stub start failure')
            active[0] = True
        def stop(self):
            counters['stop'] += 1
            events.append('stop')
            if counters['stop'] == cfg.get('stop_fail_at'):
                raise RuntimeError('stub stop failure')
            self.ball = None
            self.command = None
            active[0] = False
        def update_command(self, direction, power):
            counters['update_command'] += 1
            events.append(('command', active[0], direction, power))
            if not 1 <= float(power) <= 10:
                raise ValueError('power out of range')
            self.robot.get_odom()
            self.command = [direction, power]
        def update_ball(self, x, y):
            counters['update_ball'] += 1
            events.append(('ball', active[0], x, y))
            if active[0] and cfg.get('active_ball_fail'):
                raise RuntimeError('stub active ball update failed')
            x, y = float(x), float(y)
            self.robot.get_odom()
            self.ball = [x, y]
    mods = {k: ModuleType(k) for k in ['boosteros', 'boosteros.robots', 'boosteros.robots.booster']}
    mods['boosteros.robots.booster'].BoosterRobot = Robot
    mods['boosteros.robots.booster'].SoccerKickManager = Manager
    def sleep(seconds):
        clock[0] += seconds
        if cfg.get('interrupt_continuous') and ns.get('report', {}).get('current_case') == '连续球位与活动中指令更新':
            raise KeyboardInterrupt('stub observation interrupted')
        if cfg.get('interrupt_kick') and ns.get('report', {}).get('current_case') in ['基线试踢', '改方向与重启', '改力度与重启']:
            raise KeyboardInterrupt('stub ball kicked, finish observation')
    def answer(prompt):
        return '' if cfg.get('decline') else ('启停' if '启停' in prompt else '执行')
    ns = {'__name__': '__offline__'}
    cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='soccer-complete-') as tmp:
        try:
            os.chdir(tmp)
            with patch.dict('sys.modules', mods), patch.object(importlib.metadata, 'version', return_value='stub-1.2.2'), \
                 patch.object(time, 'sleep', side_effect=sleep), patch.object(time, 'monotonic', side_effect=lambda: clock[0]), \
                 patch('builtins.input', side_effect=answer), contextlib.redirect_stdout(io.StringIO()):
                try:
                    exec(codes[0], ns)
                except RuntimeError:
                    assert cfg.get('connection_fail')
                    exec(codes[8], ns)
                else:
                    for i, source in enumerate(codes[1:], 1):
                        if i in [4, 5, 6, 7] and not cfg.get('unfilled'):
                            source = source.replace('BALL_X = None', 'BALL_X = ' + ('1.4' if i == 4 else '0.6'))
                            source = source.replace('BALL_Y = None', 'BALL_Y = 0.03')
                        exec(source, ns)
                report = ns['report']
                out = ns['OUTPUT']
                saved = json.loads((out / '原始记录.json').read_text(encoding='utf-8'))
                assert saved['test'] == '足球SDK完整能力验证_v2'
                summary = (out / '能力汇总.md').read_text(encoding='utf-8')
                assert '\n| 方法 |' in summary and all(m in summary for m in counters)
                for row in report['calls']:
                    if row['method'] in counters and row.get('returned'):
                        assert row['return_type'] == 'NoneType' and row['return_repr'] == 'None'
                # 已完成项重复执行不能再发运动指令；未填写或拒绝项仍须再次人工确认。
                if not cfg.get('connection_fail') and not cfg.get('unfilled') and not cfg.get('decline'):
                    before = dict(counters)
                    for i in range(8):
                        try:
                            exec(codes[i], ns)
                        except RuntimeError:
                            pass
                    assert counters == before, (name, '重复运行新增控制', before, counters)
        finally:
            os.chdir(cwd)
    if cfg.get('connection_fail'):
        assert not counters['start'] and not counters['update_ball']
    elif cfg.get('construct_fail'):
        assert not report['manager_created'] and all(v == 0 for v in counters.values())
    elif cfg.get('odom_fail'):
        assert counters['start'] == 1 and counters['stop'] == 2
        assert all('measured_pose' not in r for r in report['cases'].values())
    elif cfg.get('start_fail_at') == 1 or cfg.get('stop_fail_at') in [1, 2] or cfg.get('decline'):
        assert counters['start'] <= 1
    elif cfg.get('unfilled'):
        assert counters['start'] == 1
    elif cfg.get('interrupt_continuous'):
        assert counters['start'] == 5
        assert report['cases']['连续球位与活动中指令更新']['stop_returned']
        assert report['cases']['连续球位与活动中指令更新']['observation_interrupted']
    elif cfg.get('active_ball_fail'):
        assert counters['start'] == 2 and counters['stop'] == 3
        assert 'error' in report['cases']['连续球位与活动中指令更新']
    else:
        assert counters['start'] == 5 and counters['stop'] == 6, (name, counters)
        continuous = report['cases']['连续球位与活动中指令更新']
        if not cfg.get('movement_limit'):
            assert len(continuous['samples']) >= 2 and continuous['active_command_changed']
        for label in ['基线试踢', '改方向与重启', '改力度与重启']:
            assert len(report['cases'][label]['samples']) == 1
            assert report['cases'][label]['stop_returned']
        inactive = report['cases']['停用参数检查']
        assert all(r['expected_ValueError'] for r in inactive['checks'])
        assert not active[0]
    if cfg.get('stop_fail_at') in [1, 2]:
        assert report['control_uncertain'] and not report['active_tests_available']
    if cfg.get('tf_fail'):
        assert report['manager_created'] and 'transform_error' in report
    return {'scenario': name, 'passed': True, 'calls': counters}

results = [run_scenario('正常完成全部方法和活动场景'),
           run_scenario('模式读取失败仍完成构造与控制', mode_fail=True),
           run_scenario('TF报错不阻断完整控制', tf_fail=True),
           run_scenario('构造失败保留错误且后续运动跳过', construct_fail=True),
           run_scenario('start报错仍尝试stop', start_fail_at=1),
           run_scenario('无球位stop失败后续控制被挡住', stop_fail_at=1),
           run_scenario('参数清理stop失败后续控制被挡住', stop_fail_at=2),
           run_scenario('odom不可读记录为能力缺口', odom_fail=True),
           run_scenario('未填写真实球位只运行无球位启停', unfilled=True),
           run_scenario('未人工启动不发运动指令', decline=True),
           run_scenario('人工结束连续观察后stop并可继续独立试踢', interrupt_continuous=True),
           run_scenario('看到球踢动后中断观察仍可继续方向力度试验', interrupt_kick=True),
           run_scenario('活动中球位调用异常后stop并跳过后续活动', active_ball_fail=True),
           run_scenario('行进边界到达提前停止', movement_limit=True),
           run_scenario('连接失败仍可保存汇总', connection_fail=True)]

# 与管理器源码同一平面位姿约定；只验证测试工具的数学一致性。
scope = {}
tree = ast.parse(codes[0])
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'ball_at_current_frame')
exec(compile(ast.Module(body=[function], type_ignores=[]), '<geometry>', 'exec'), {'math': math}, scope)
calc = scope['ball_at_current_frame']
assert np.allclose(calc([1.4, .2], [0, 0, 0], [.1, 0, 0]), [1.3, .2])
assert np.allclose(calc([1., 0], [0, 0, 0], [0, 0, math.pi/2]), [0, -1.])

for name, expected in base['protected'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, '保护文件被改：' + name
for name in base['link_only']:
    old = (TASK / 'before' / name).read_text(encoding='utf-8-sig')
    new = (ROOT / name).read_text(encoding='utf-8-sig')
    assert old.replace('足球测试_第4轮_管理器创建与启停.ipynb', '足球测试_第4轮_完整能力验证.ipynb') == new

assert not (V / '足球测试_第4轮_管理器创建与启停.ipynb').exists()
links_checked = 0
for p in [ROOT / name for name in base['shared']] + [V / '足球测试_第4轮_操作与记录.md', NP]:
    text = p.read_text(encoding='utf-8-sig') if p.suffix == '.md' else '\n'.join(c.source for c in nb.cells)
    assert '足球测试_第4轮_管理器创建与启停.ipynb' not in text
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith('http') or '足球测试_第4轮_' not in target:
            continue
        assert (p.parent / target).exists(), (p, target)
        links_checked += 1

generated_source = (TASK / '生成完整测试.py').read_text(encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='soccer-generate-') as tmp:
    source = generated_source.replace("V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'", 'V = Path(' + repr(tmp) + ')')
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, str(TASK / '生成完整测试.py'), 'exec'), {'__file__': str(TASK / '生成完整测试.py')})
    regenerated = nbformat.read(Path(tmp) / NP.name, as_version=4)
    assert [c.source for c in regenerated.cells] == [c.source for c in nb.cells]
    assert (Path(tmp) / '足球测试_第4轮_操作与记录.md').read_text(encoding='utf-8') == (V / '足球测试_第4轮_操作与记录.md').read_text(encoding='utf-8')

out = {'nbformat_ast': True, 'cells': len(nb.cells), 'code_cells': len(codes),
       'scenarios': results, 'geometry_consistency': True, 'hardware_executed': False,
       'protected_unchanged': len(base['protected']), 'round3_only_link_changed': True,
       'current_links_checked': links_checked, 'generator_matches_delivery': True}
(TASK / '离线核查结果.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=2))
