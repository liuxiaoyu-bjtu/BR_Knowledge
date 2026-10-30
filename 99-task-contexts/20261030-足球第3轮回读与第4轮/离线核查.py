from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import ast
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import tempfile
import time
import nbformat
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
NBPATH = V / '足球测试_第4轮_管理器创建与启停.ipynb'
nb = nbformat.read(NBPATH, as_version=4)
nbformat.validate(nb)
codes = [c.source for c in nb.cells if c.cell_type == 'code']
assert len(nb.cells) == 13 and len(codes) == 6
trees = [ast.parse(s) for s in codes]
calls = [n.func.attr for t in trees for n in ast.walk(t)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
assert 'update_ball' not in calls and 'update_command' not in calls
assert calls.count('start') == 1 and calls.count('stop') == 1
assert all(not c.get('outputs') and c.get('execution_count') is None for c in nb.cells if c.cell_type == 'code')

def scenario(name, **config):
    events = []
    counters = {'tf': 0, 'start': 0, 'stop': 0}

    class FakeAdapter:
        def get_transform(self, target_frame, source_frame):
            return None

    class FakeRobot:
        def __init__(self, enable_tf_listener):
            events.append('connect')
            assert enable_tf_listener is True
            if config.get('connect_fail'):
                raise RuntimeError('stub connection failed')
            self.ros_adapter = FakeAdapter()
            self.loco_client = SimpleNamespace(GetMode=self.raw_mode)
            self.robot_info = 'stub K1, no hardware'

        def get_mode(self):
            events.append('public_mode')
            if config.get('mode_fail'):
                raise RuntimeError('stub public mode failed')
            return 'walk'

        def raw_mode(self):
            events.append('raw_mode')
            if config.get('mode_fail'):
                raise RuntimeError('stub raw mode failed')
            return SimpleNamespace(mode=SimpleNamespace(value=1))

        def _get_model(self):
            return 'stub K1'

        def list_frames(self):
            return ['head_color_optical_frame', 'trunk']

        def get_transform(self, target_frame, source_frame):
            counters['tf'] += 1
            events.append('tf')
            if counters['tf'] <= config.get('tf_failures', 0):
                raise RuntimeError('stub TF extrapolation')
            assert target_frame == 'trunk' and source_frame == 'head_color_optical_frame'
            return SimpleNamespace(source_frame=source_frame, target_frame=target_frame,
                header='stub', translation=np.array([0., 0., 1.]),
                rotation=np.array([0., 0., 0., 1.]), to_matrix=lambda: np.eye(4))

    class FakeManager:
        def __init__(self, robot):
            events.append('construct')
            if config.get('construct_fail'):
                raise RuntimeError('stub actual constructor failed')

        def start(self):
            counters['start'] += 1
            events.append('start')
            if counters['start'] == config.get('start_fail_at'):
                raise RuntimeError('stub start failed')

        def stop(self):
            counters['stop'] += 1
            events.append('stop')
            if counters['stop'] == config.get('stop_fail_at'):
                raise RuntimeError('stub stop failed')

    mods = {key: ModuleType(key) for key in ['boosteros', 'boosteros.robots', 'boosteros.robots.booster']}
    mods['boosteros.robots.booster'].BoosterRobot = FakeRobot
    mods['boosteros.robots.booster'].SoccerKickManager = FakeManager
    answers = iter(['', ''] if config.get('skip') else ['启停', '重启'])
    def fake_sleep(seconds):
        if seconds == 3.0 and config.get('interrupt_observation'):
            raise KeyboardInterrupt('stub interrupt')

    ns = {'__name__': '__offline_test__'}
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='soccer-round4-') as tmp:
        try:
            os.chdir(tmp)
            with patch.dict('sys.modules', mods), patch.object(importlib.metadata, 'version', return_value='stub-1.2.2'), \
                 patch.object(time, 'sleep', side_effect=fake_sleep), patch('builtins.input', side_effect=lambda _: next(answers)), \
                 contextlib.redirect_stdout(io.StringIO()):
                if config.get('connect_fail'):
                    try:
                        exec(codes[0], ns)
                    except RuntimeError:
                        pass
                    else:
                        raise AssertionError('expected connection exception')
                    exec(codes[5], ns)
                else:
                    for source in codes:
                        exec(source, ns)
                report = ns['report']
                saved = json.loads((ns['OUTPUT'] / '原始记录.json').read_text(encoding='utf-8'))
                assert saved == json.loads(json.dumps(report, default=str))
                summary = (ns['OUTPUT'] / '能力汇总.md').read_text(encoding='utf-8')
                assert '\n| 检查项 |' in summary
                if not config.get('connect_fail'):
                    # 重跑初始化、构造、两次启停格不能新增构造或控制调用。
                    before = list(events)
                    directory = ns['OUTPUT']
                    report_id = id(ns['report'])
                    for i in [0, 2, 3, 4]:
                        try:
                            exec(codes[i], ns)
                        except RuntimeError:
                            pass
                    assert events == before, (name, 'duplicate execution added calls', events)
                    assert ns['OUTPUT'] == directory and id(ns['report']) == report_id
        finally:
            os.chdir(original_cwd)

    if config.get('connect_fail'):
        assert 'construct' not in events and counters['start'] == counters['stop'] == 0
    elif config.get('construct_fail'):
        assert events.count('construct') == 1 and counters['start'] == counters['stop'] == 0
        assert report['capabilities']['实际创建管理器'] == '失败'
        assert any(e['stage'] == 'SoccerKickManager构造' and 'FakeManager' not in e['error']
                   and '__init__' in e['traceback'] for e in report['errors'])
    else:
        assert report['capabilities']['实际创建管理器'] == '成功'
        assert events.count('construct') == 1
        expected = 0 if config.get('skip') else (1 if config.get('start_fail_at') == 1
            or config.get('stop_fail_at') == 1 or config.get('interrupt_observation') else 2)
        assert counters['start'] == counters['stop'] == expected, (name, counters)
        if expected:
            control = [x for x in events if x in ('start', 'stop')]
            assert control == ['start', 'stop'] * expected
        if config.get('mode_fail'):
            assert report['capabilities']['机器人连接'] == '成功'
        if config.get('stop_fail_at') == 1:
            assert report['control_uncertain'] is True and '停止后重启' not in report['cycles']
    if not config.get('connect_fail'):
        assert counters['tf'] == min(config.get('tf_failures', 0) + 1, 3)
    return {'name': name, 'passed': True, 'calls': counters}

results = [scenario('正常创建、启停、重启'),
           scenario('公开和原始模式均读取失败仍实际构造', mode_fail=True),
           scenario('TF首次失败后返回', tf_failures=1),
           scenario('TF三次均失败仍执行构造与启停', tf_failures=3),
           scenario('实际构造失败不启动', construct_fail=True),
           scenario('第一次start失败仍finally尝试stop且不重启', start_fail_at=1),
           scenario('第一次stop失败不重启', stop_fail_at=1),
           scenario('重启start失败仍尝试stop', start_fail_at=2),
           scenario('观察被中断仍stop且不重启', interrupt_observation=True),
           scenario('用户不启动时不调用控制', skip=True),
           scenario('连接失败仍能生成结束汇总', connect_fail=True)]

base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for field in ['protected', 'evidence']:
    for name, expected in base[field].items():
        assert sha(ROOT / name) == expected, '保护文件被修改：' + name
record = V / '足球测试_第3轮_操作与记录.md'
old = (TASK / 'before' / record.relative_to(ROOT)).read_text(encoding='utf-8-sig')
new = record.read_text(encoding='utf-8-sig')
section = lambda s: s[s.index('## 2. 本轮记录'):s.index('## 3. 管理器功能登记')]
assert section(old) == section(new), '用户填写区有改动'

import re
link_count = 0
for p in [ROOT / x for x in base['shared']] + [V / '足球测试_第4轮_操作与记录.md', NBPATH]:
    text = p.read_text(encoding='utf-8-sig') if p.suffix == '.md' else '\n'.join(c.source for c in nb.cells if c.cell_type == 'markdown')
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith('http') or not re.search(r'足球测试_第[34]轮_', target):
            continue
        assert (p.parent / target).exists(), (p, target)
        link_count += 1

# 生成器与交付内容一致；在临时副本运行，绝不覆盖现场文件。
source = (TASK / '生成第4轮.py').read_text(encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='soccer-round4-generator-') as tmp:
    temp_v = Path(tmp)
    source = source.replace("V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'", 'V = Path(' + repr(tmp) + ')')
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, str(TASK / '生成第4轮.py'), 'exec'), {'__file__': str(TASK / '生成第4轮.py')})
    generated = nbformat.read(temp_v / NBPATH.name, as_version=4)
    assert [c.source for c in generated.cells] == [c.source for c in nb.cells]
    assert (temp_v / '足球测试_第4轮_操作与记录.md').read_text(encoding='utf-8') == (V / '足球测试_第4轮_操作与记录.md').read_text(encoding='utf-8')

out = {'nbformat_ast': True, 'cells': len(nb.cells), 'code_cells': len(codes),
       'stub_scenarios': results, 'protected_unchanged': len(base['protected']),
       'evidence_unchanged': len(base['evidence']), 'user_record_preserved': True,
       'links_checked': link_count, 'generator_matches_delivery': True, 'hardware_executed': False}
(TASK / '离线核查结果.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=2))
