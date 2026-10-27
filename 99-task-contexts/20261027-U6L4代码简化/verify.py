"""核验学生稿结构及Fake SDK分支；不运行机器人。"""
from pathlib import Path
from types import SimpleNamespace
from contextlib import redirect_stdout
import ast
import copy
import io
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
CHECKS = []


class FakeTask:
    def __init__(self, status, events):
        self.status = status
        self.events = events

    def wait(self, timeout):
        self.events.append(('wait', timeout))
        if self.status == 'WAIT_ERROR':
            raise RuntimeError('模拟等待错误')
        if self.status == 'INTERRUPT':
            raise KeyboardInterrupt()
        return self.status

    def done(self):
        return self.status in ['SUCCEEDED', 'FAILED', 'CANCELLED']


class FakeRobot:
    def __init__(self, statuses=None, mode='walk'):
        self.statuses = iter(statuses or ['SUCCEEDED'] * 3)
        self.mode = mode
        self.events = []

    def get_mode(self):
        return self.mode

    def start(self, source, data):
        self.events.append(('call', source))
        status = next(self.statuses)
        if status == 'BUSY':
            raise RuntimeError('Robot is busy executing another action; cannot start action task')
        return FakeTask(status, self.events)

    def do_action(self, data):
        return self.start('action', data)

    def execute_trajectory(self, data):
        return self.start('trajectory', data)


class FakeTrajectory:
    @classmethod
    def load(cls, name):
        if name == 'missing.btraj':
            raise FileNotFoundError(name)
        return SimpleNamespace(points=[] if name == 'empty.btraj' else [1, 2], duration=SimpleNamespace(seconds=2))


def run(source, env, expected=None):
    output = io.StringIO()
    with redirect_stdout(output):
        try:
            exec(compile(source, '<student cell>', 'exec'), env)
        except BaseException as exc:
            if expected and isinstance(exc, expected):
                return output.getvalue()
            raise
    assert expected is None
    return output.getvalue()


def env_for(robot=None):
    return {'robot': robot or FakeRobot(), 'active_motion': None, 'plan_ready': False,
            'run_log': [], 'action_ids': ['hand_wave', 'bow'], 'TrajectoryData': FakeTrajectory}


def main():
    manifest = json.loads((TASK / '修改清单.json').read_text(encoding='utf-8'))
    path = ROOT / manifest['notebook']
    doc = json.loads(path.read_text(encoding='utf-8'))
    before = json.loads((TASK / 'before' / manifest['notebook']).read_text(encoding='utf-8'))
    assert len(doc['cells']) == len(before['cells']) == 18
    assert {k: v for k, v in doc.items() if k != 'cells'} == {k: v for k, v in before.items() if k != 'cells'}
    changed = []
    for number, (a, b) in enumerate(zip(before['cells'], doc['cells']), 1):
        assert {k: v for k, v in a.items() if k != 'source'} == {k: v for k, v in b.items() if k != 'source'}
        if a != b:
            changed.append(number)
    assert changed == manifest['changed_cells']
    codes = [''.join(c['source']) for c in doc['cells'] if c['cell_type'] == 'code']
    assert len(codes) == 4
    handlers = []
    for source in codes:
        tree = ast.parse(source)
        assert not any(isinstance(n, (ast.Lambda, ast.Raise, ast.DictComp, ast.SetComp, ast.ListComp)) for n in ast.walk(tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in ['globals', 'enumerate']
            if isinstance(node, ast.ExceptHandler):
                handlers.append(node.type.id)
    assert handlers == ['RuntimeError']
    assert 'time.monotonic' not in ''.join(codes) and 'prepared_signature' not in ''.join(codes)
    gen = ast.parse((ROOT / manifest['generator']).read_text(encoding='utf-8'))
    mirrored = [ast.literal_eval(n.value.args[0]) for n in gen.body if isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'cells'
                and n.value.func.attr == 'append']
    assert mirrored == doc['cells']
    import nbformat
    nbformat.validate(nbformat.read(path, as_version=4))
    prep, perform, log = codes[1:]
    env = env_for()
    run(prep, env)
    run(perform, env)
    assert env['robot'].events == [('call', 'action'), ('wait', 45.0), ('call', 'trajectory'), ('wait', 45.0), ('call', 'action'), ('wait', 45.0)]
    assert env['run_log'] == [['action', 'hand_wave', 'SUCCEEDED'], ['trajectory', 'my_action_v1.btraj', 'SUCCEEDED'], ['action', 'bow', 'SUCCEEDED']]
    assert 'hand_wave' in run(log, env)
    CHECKS.append('两类素材按顺序启动并等待，三列日志与清单对应')
    for status in ['FAILED', 'CANCELLED', 'RUNNING', 'BUSY', 'WAIT_ERROR']:
        env = env_for(FakeRobot(['SUCCEEDED', status]))
        run(prep, env)
        run(perform, env)
        assert len(env['robot'].events) in [3, 4]
        assert sum(event[0] == 'call' for event in env['robot'].events) == 2
        assert len(env['run_log']) == 2
        if status in ['RUNNING', 'WAIT_ERROR']:
            previous = env['active_motion']
            events_before = list(env['robot'].events)
            run(perform, env)
            assert env['active_motion'] is previous and env['robot'].events == events_before
        CHECKS.append('第二步' + status + '后不调用第三步' + ('；未结束句柄阻止重跑' if status in ['RUNNING', 'WAIT_ERROR'] else ''))
    env = env_for(FakeRobot(['INTERRUPT']))
    run(prep, env)
    run(perform, env, KeyboardInterrupt)
    old_task = env['active_motion']
    run(perform, env)
    assert env['active_motion'] is old_task and len(env['robot'].events) == 2
    CHECKS.append('键盘中断保留句柄，下次运行先拒绝未结束任务')
    for source, expected in [
        (prep.replace('my_action_v1.btraj', 'missing.btraj'), FileNotFoundError),
        (prep.replace('my_action_v1.btraj', 'empty.btraj'), None),
        (prep.replace('"hand_wave"', '"unknown"'), None),
        (prep.replace('["trajectory",', '["workshop",'), None),
    ]:
        env = env_for()
        run(prep, env)  # 原来曾有可执行清单
        run(source, env, expected)
        assert env['plan_ready'] is False
        run(perform, env)
        assert not env['robot'].events
    CHECKS.append('缺文件、无效轨迹、未知ID、未接入类型均使素材检查失效，不执行部分或旧清单')
    env = env_for(FakeRobot(mode='prepare'))
    run(prep, env)
    run(perform, env)
    assert not env['robot'].events
    CHECKS.append('模式不符时不发起动作')
    for name, args in [('工作区增量.patch', ['--reverse', '--check']), ('提交增量.patch', ['--cached', '--check'])]:
        result = subprocess.run(['git', 'apply', *args, str(TASK / name)], cwd=ROOT, capture_output=True)
        if result.returncode and '--cached' in args:
            result = subprocess.run(['git', 'apply', '--cached', '--reverse', '--check', str(TASK / name)], cwd=ROOT, capture_output=True)
        assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    report = ROOT / manifest['report']
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
        if '://' not in target:
            assert (report.parent / target).resolve().exists(), target
    result = {'date': '2026-10-27', 'cells': 18, 'code_cells': 4, 'changed_cells': changed,
              'cell_metadata_preserved': True, 'syntax': 'passed', 'nbformat': 'passed',
              'generator_matches': True, 'exception_handlers': handlers,
              'simulation_checks': CHECKS, 'shared_patch_checks': 'passed',
              'robot_commands_executed': False, 'new_confirmations': [], 'pushed': False}
    (TASK / '校验结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
