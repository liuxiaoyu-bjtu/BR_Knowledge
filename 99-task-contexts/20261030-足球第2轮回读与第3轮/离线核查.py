from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import hashlib
import io
import json
import math
import tempfile
import numpy as np
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
VERIFY = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
nb = nbformat.read(VERIFY / '足球测试_第3轮_机身变换与管理器创建.ipynb', as_version=4)
nbformat.validate(nb)
codes = [c.source for c in nb.cells if c.cell_type == 'code']
assert len(codes) == 5
constructors = 0
for source in codes:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            assert name not in {'start', 'stop', 'update_command', 'update_ball', 'set_mode',
                                'move', 'set_head_angle', 'execute_trajectory', 'do_action'}, name
            constructors += name == 'SoccerKickManager'
    assert 'x_lab' not in source
assert constructors == 1
assert all(c.execution_count is None and not c.outputs for c in nb.cells if c.cell_type == 'code')

class Robot:
    def __init__(self, frames=True, tf=True, mode_after=True):
        self.has_frames = frames
        self.has_tf = tf
        self.mode_after = mode_after
        self.mode_calls = 0
    def list_frames(self):
        return ['head_color_optical_frame', 'trunk'] if self.has_frames else ['head_point']
    def get_transform(self, target_frame, source_frame):
        assert target_frame == 'trunk' and source_frame == 'head_color_optical_frame'
        if not self.has_tf:
            raise RuntimeError('模拟TF失败')
        return SimpleNamespace(source_frame=source_frame, target_frame=target_frame,
                               header='raw header', translation=np.array([0, 0, 0.4]),
                               rotation=np.array([0, 0, 0, 1]), to_matrix=lambda: np.eye(4))
    def get_mode(self):
        self.mode_calls += 1
        if self.mode_calls > 1 and not self.mode_after:
            raise RuntimeError('模拟创建后模式读取失败')
        return 'prepare'
    def get_image(self):
        raise AssertionError('本轮不应取图')

class Inspector:
    def __init__(self, can_read=True):
        self.can_read = can_read
    def getdoc(self, obj):
        return 'offline documentation'
    def getfile(self, obj):
        return '/offline/sdk.py'
    def getsource(self, obj):
        if not self.can_read:
            raise OSError('模拟源码不可直接读')
        return '# offline source\n'

def manager_methods_forbid(*args, **kwargs):
    raise AssertionError('不能调用四个控制方法')

cases = []
def case(name, robot, create=True, readable=True, expected_tf='已取得', expected_create='成功'):
    with tempfile.TemporaryDirectory(prefix='soccer_round3_') as temp:
        output = Path(temp)
        report = {'created_at': 'offline', 'capabilities': {}, 'sdk_version': 'offline'}
        created = []
        def manager_ctor(robot):
            if not create:
                raise RuntimeError('模拟创建失败')
            created.append(robot)
            return SimpleNamespace(start=manager_methods_forbid, stop=manager_methods_forbid,
                                   update_command=manager_methods_forbid, update_ball=manager_methods_forbid)
        env = {'OUTPUT': output, 'report': report, 'np': np, 'math': math, 'json': json,
               'robot': robot, 'SoccerKickManager': manager_ctor, 'inspect': Inspector(readable)}
        functions = [n for n in ast.parse(codes[0]).body if isinstance(n, ast.FunctionDef)]
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<helpers>', 'exec'), env)
        with contextlib.redirect_stdout(io.StringIO()):
            for source in codes[1:]:
                exec(compile(source, '<step>', 'exec'), env)
        assert report['capabilities']['相机到trunk变换'] == expected_tf
        assert report['capabilities']['创建足球管理器'] == expected_create
        assert len(created) == int(create)
        saved = json.loads((output / '原始记录.json').read_text(encoding='utf-8'))
        assert saved['capabilities'] == report['capabilities']
        assert (output / '能力汇总.md').read_text(encoding='utf-8').startswith('# 足球第3轮')
        if not readable:
            assert all('source_error' in row for row in report['sdk_sources'])
        if not robot.mode_after and create:
            assert 'mode_after_create_error' in report
        cases.append({'case': name, 'capabilities': report['capabilities'], 'result': 'passed'})

case('TF与创建正常', Robot())
case('frame不在列表仍创建', Robot(frames=False), expected_tf='坐标系本轮未列出')
case('TF报错仍创建', Robot(tf=False), expected_tf='接口报错')
case('源码不可读仍创建', Robot(), readable=False)
case('创建失败记录错误', Robot(), create=False, expected_create='失败')
case('创建后模式读取失败不改写创建结果', Robot(mode_after=False))

for group in ['protected', 'evidence']:
    for name, expected in base[group].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, (group, name)

evidence_dir = VERIFY / '足球测试结果/第2轮_20261030_181000_379153'
raw = json.loads((evidence_dir / '原始记录.json').read_text(encoding='utf-8'))
array = np.load(evidence_dir / 'depth.npy', allow_pickle=False)
evidence_summary = {'sdk_version': raw['sdk_version'], 'frames': raw['frames'],
                    'manager_signatures': raw['soccer_manager_public_api'],
                    'depth_shape': list(array.shape), 'depth_dtype': str(array.dtype),
                    'zero_count': int((array == 0).sum()), 'value_65535_count': int((array == 65535).sum()),
                    'source_unit': raw['depth']['unit'], 'tf_state': raw['capabilities']['坐标变换查询'],
                    'scope': '接口与数据能力，不做性能验收'}
(TASK / '第2轮数据核对.json').write_text(json.dumps(evidence_summary, ensure_ascii=False, indent=2), encoding='utf-8')
result = {'assistant_robot_executed': False, 'nbformat_ast': 'passed', 'code_steps': len(codes),
          'manager_constructors_in_notebook': constructors, 'control_method_calls': 0,
          'offline_cases': cases, 'protected_sources_unchanged': len(base['protected']),
          'round2_evidence_unchanged': len(base['evidence'])}
(TASK / '离线核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('第3轮5格代码与6种构造分支通过；助手未导入SDK或连接机器人。')
print('受保护源文件', len(base['protected']), '；第2轮证据', len(base['evidence']), '均未变化。')
