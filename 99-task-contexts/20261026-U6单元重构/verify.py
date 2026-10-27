"""只做静态及Fake SDK分支核验，不导入boosteros、不连接机器人。"""
from pathlib import Path
from types import SimpleNamespace
from contextlib import redirect_stdout
import ast
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
CHECKS = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source, env, expected=None):
    with redirect_stdout(io.StringIO()):
        try:
            exec(compile(source, '<notebook cell>', 'exec'), env)
        except BaseException as exc:
            if expected and isinstance(exc, expected):
                return exc
            raise
    assert expected is None, f'应抛出{expected}'


class FakeTrajectory:
    saved = {}
    next_id = 0

    def __init__(self):
        type(self).next_id += 1
        self.id = 'test-' + str(self.next_id)
        self.points = [1, 2, 3]
        self.joint_names = ['test_joint']
        self.duration = SimpleNamespace(seconds=2.0)

    def save(self, path):
        Path(path).write_text('模拟测试轨迹，非机器人资源', encoding='utf-8')
        self.saved[str(Path(path).resolve())] = copy.deepcopy(self)

    @classmethod
    def load(cls, path):
        return copy.deepcopy(cls.saved[str(Path(path).resolve())])


class FakeTask:
    def __init__(self, status='SUCCEEDED', events=None):
        self.status = status
        self.error = None if status == 'SUCCEEDED' else '模拟结果'
        self.events = events if events is not None else []

    def wait(self, timeout):
        self.events.append(('wait', self.status))
        return self.status

    def done(self):
        return self.status in {'SUCCEEDED', 'FAILED', 'CANCELLED'}


class FakeGuiding:
    def __init__(self):
        self.is_recording = False
        self.events = []

    def __enter__(self):
        self.events.append('enter')
        return self

    def __exit__(self, *args):
        self.events.append('exit')

    def start_recording(self):
        self.is_recording = True
        self.events.append('start')

    def stop_recording(self):
        self.is_recording = False
        self.events.append('stop')
        return FakeTrajectory()

    def get_recording_duration(self):
        return 2.1


class FakeRobot:
    def __init__(self, statuses=None, busy=False):
        self.statuses = iter(statuses or ['SUCCEEDED'] * 8)
        self.busy = busy
        self.events = []
        self.hand_guiding_manager = FakeGuiding()

    def get_mode(self):
        return 'walk'

    def get_active_tasks(self, predicate):
        return [SimpleNamespace(group='motion')] if self.busy else []

    def execute_trajectory(self, data):
        self.events.append(('start', 'trajectory'))
        return FakeTask(next(self.statuses), self.events)

    def do_action(self, data):
        self.events.append(('start', data))
        return FakeTask(next(self.statuses), self.events)


def base_env(robot=None):
    return {'Path': Path, 'TrajectoryData': FakeTrajectory, 'time': time,
            'robot': robot or FakeRobot(), 'input': lambda _: '试演',
            'action_by_id': {'hand_wave': object(), 'bow': object()}}


def with_steps(source, steps):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'steps' for t in n.targets))
    node.value = ast.parse(repr(steps), mode='eval').body
    return ast.unparse(ast.fix_missing_locations(tree))


def simulations(codes):
    old_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='u6-notebook-check-') as temp:
        os.chdir(temp)
        try:
            FakeTrajectory().save('my_action_v1.btraj')
            precheck, perform = codes['L4'][1:3]
            env = base_env()
            run(precheck, env)
            run(perform, env)
            assert env['robot'].events == [('start', 'hand_wave'), ('wait', 'SUCCEEDED'), ('start', 'trajectory'), ('wait', 'SUCCEEDED'), ('start', 'bow'), ('wait', 'SUCCEEDED')]
            assert len(env['run_log']) == 3
            CHECKS.append('L4两类素材按start/wait顺序执行，共三步成功')
            for status in ['FAILED', 'CANCELLED', 'RUNNING']:
                env = base_env(FakeRobot(['SUCCEEDED', status]))
                run(precheck, env)
                run(perform, env)
                assert len(env['run_log']) == 2
                assert sum(x[0] == 'start' for x in env['robot'].events) == 2
                CHECKS.append('L4第二步' + status + '时不启动第三步')
            bad_plans = [
                [('action', 'hand_wave'), ('trajectory', 'my_action_v1.btraj'), ('workshop', 'sample')],
                [('action', 'hand_wave'), ('trajectory', 'missing.btraj'), ('action', 'bow')],
                [('action', 'unknown'), ('trajectory', 'my_action_v1.btraj'), ('action', 'bow')],
                [('action', 'hand_wave')] * 3,
            ]
            for plan in bad_plans:
                env = base_env()
                run(precheck, env)  # 模拟先有一份已通过的旧计划
                run(with_steps(precheck, plan), env, (ValueError, FileNotFoundError))
                assert env['plan_ready'] is False
                run(perform, env, RuntimeError)
                assert not env['robot'].events
            CHECKS.append('L4未知类型/缺文件/未知ID/缺素材类别均不执行部分清单')
            for kind in ['changed', 'active', 'busy']:
                env = base_env()
                run(precheck, env)
                if kind == 'changed':
                    env['steps'][0] = ('action', 'bow')
                elif kind == 'active':
                    env['active_motion'] = FakeTask('RUNNING')
                else:
                    env['robot'].busy = True
                run(perform, env, RuntimeError)
                assert not env['robot'].events
            CHECKS.append('L4清单改动/旧句柄未结束/已有运动任务时拒绝启动')

            record, verify, replay = codes['L2'][1:]
            env = base_env()
            answers = iter(['record_v1.btraj', ''])
            env['input'] = lambda _: next(answers)
            env.update(same_data=True, verified_path=Path('old.btraj').resolve())
            run(record, env)
            assert env['same_data'] is False and env['verified_path'] is None
            assert env['robot'].hand_guiding_manager.events == ['enter', 'start', 'stop', 'exit']
            run(replay, env, RuntimeError)
            assert not env['robot'].events
            run(verify, env)
            env['input'] = lambda _: '回放'
            run(replay, env)
            assert env['robot'].events == [('start', 'trajectory'), ('wait', 'SUCCEEDED')]
            CHECKS.append('L2退出示教后才允许回放；重录失效旧核对，完成读回后可启动')
            env['traj'].id = 'changed'
            run(verify, env, RuntimeError)
            env['robot'].events.clear()
            run(replay, env, RuntimeError)
            assert not env['robot'].events
            CHECKS.append('L2读回不一致时拒绝回放')
            env = base_env()
            answers = iter(['interrupted.btraj'])
            def interrupted_input(_):
                try:
                    return next(answers)
                except StopIteration:
                    raise KeyboardInterrupt()
            env['input'] = interrupted_input
            run(record, env, KeyboardInterrupt)
            assert env['robot'].hand_guiding_manager.events == ['enter', 'start', 'stop', 'exit']
            assert not Path('interrupted.btraj').exists() and not env['robot'].events
            CHECKS.append('L2录制期间中断仍停止录制并退出上下文，不保存或自动回放')
        finally:
            os.chdir(old_cwd)


def main():
    manifest = json.loads((TASK / '重构清单.json').read_text(encoding='utf-8'))
    assert digest(PROJ / 'notebooks/U6-L1_动作的来源.ipynb') == manifest['l1_preserved_sha256']
    codes, lessons = {}, []
    for item in manifest['lessons']:
        path = ROOT / item['path']
        doc = json.loads(path.read_text(encoding='utf-8'))
        assert digest(path) == item['after_sha256']
        assert len({c['id'] for c in doc['cells']}) == len(doc['cells'])
        code_cells = [c for c in doc['cells'] if c['cell_type'] == 'code']
        for c in code_cells:
            ast.parse(''.join(c['source']))
            assert c['execution_count'] is None and c['outputs'] == []
        codes[item['lesson']] = [''.join(c['source']) for c in code_cells]
        tree = ast.parse((ROOT / item['generator']).read_text(encoding='utf-8'))
        mirrored = [ast.literal_eval(n.value.args[0]) for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'cells' and n.value.func.attr == 'append']
        assert mirrored == doc['cells']
        combined = ''.join(''.join(c['source']) for c in doc['cells'])
        assert 'execute_whole_body_control(' not in combined
        assert 'robot.set_mode(' not in combined
        assert '参考答案（教师留存，PDF学生版删除）' in combined
        lessons.append({'lesson': item['lesson'], 'cells': len(doc['cells']), 'code_cells': len(code_cells), 'generator_matches': True, 'sha256': digest(path)})
    simulations(codes)
    report = PROJ / '实验验证/U6_单元重构与动作编排核验.md'
    count = 0
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        assert (report.parent / target).resolve().exists(), target
        count += 1
    for name in ['rebuild.py', 'records.py', 'verify.py', 'research.py', 'stage.py']:
        ast.parse((TASK / name).read_text(encoding='utf-8'))
    for name, args in [('工作区联动增量.patch', ['--reverse', '--check']), ('联动暂存增量.patch', ['--cached', '--check'])]:
        proc = subprocess.run(['git', 'apply', *args, str(TASK / name)], cwd=ROOT, capture_output=True)
        if proc.returncode and '--cached' in args:
            proc = subprocess.run(['git', 'apply', '--cached', '--reverse', '--check', str(TASK / name)], cwd=ROOT, capture_output=True)
        assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')
    try:
        import nbformat
    except ImportError:
        schema = 'nbformat未安装；JSON、必需字段及ID唯一性已检查'
    else:
        for item in manifest['lessons']:
            nbformat.validate(nbformat.read(ROOT / item['path'], as_version=4))
        schema = 'nbformat.validate通过'
    result = {'date': '2026-10-26', 'lessons': lessons, 'l1_preserved': True,
              'syntax': 'passed', 'notebook_schema': schema, 'simulation_checks': CHECKS,
              'report_links_checked': count, 'patch_checks': 'passed',
              'robot_commands_executed': False, 'platform_training_started': False,
              'confirmations_passed': [], 'git_push': False}
    (TASK / '校验结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
