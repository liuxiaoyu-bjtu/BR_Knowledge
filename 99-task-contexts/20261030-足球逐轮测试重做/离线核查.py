from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import hashlib
import io
import json
import math
import statistics
import tempfile
import nbformat
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
VERIFY = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
path = VERIFY / '足球测试_第1轮_静止检测.ipynb'
nb = nbformat.read(path, as_version=4)
nbformat.validate(nb)
codes = [cell.source for cell in nb.cells if cell.cell_type == 'code']
for source in codes:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            assert name not in {'SoccerKickManager', 'start', 'stop', 'update_ball', 'update_command',
                                'move', 'set_mode', 'do_action', 'set_head_angle', 'execute_trajectory'}, name
    assert 'x_lab' not in source
assert len(codes) == 7
assert all(cell.execution_count is None and not cell.outputs for cell in nb.cells if cell.cell_type == 'code')

guide = (VERIFY / '足球测试_第1轮_操作与记录.md').read_text(encoding='utf-8')
for token in ['CONFIDENCE = 0.4', 'SAMPLE_COUNT = 20', 'MAX_ATTEMPTS = 60',
              'MIN_BALL_FRAMES = 18', 'MAX_FALSE_FRAMES = 0']:
    assert token in codes[0] and token in guide, token
for i in range(1, 8):
    assert f'STEP {i:02d}' in guide
    assert any(f'STEP {i:02d}' in cell.source for cell in nb.cells if cell.cell_type == 'markdown')

class Clock:
    def __init__(self):
        self.now = 1000.0
    def time(self):
        self.now += 0.01
        return self.now
    monotonic = time
    def sleep(self, seconds):
        self.now += seconds

class Frame:
    width = height = 32
    def __init__(self, stamp, found, distance):
        self.header = SimpleNamespace(timestamp=stamp, frame_id='camera')
        self.found = found
        self.distance = distance
    def to_numpy(self):
        return self
    def to_pil(self):
        return Image.new('RGB', (32, 32), 'white')

class Robot:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.last = None
    def get_image(self, **kwargs):
        self.last = next(self.frames, self.last)
        return self.last

class Detector:
    def detect(self, frame, confidence):
        assert confidence == 0.4
        if frame.found == 'error':
            raise RuntimeError('模拟推理异常')
        if not frame.found:
            return []
        return [SimpleNamespace(class_name='Ball', confidence=0.8,
                                bbox=SimpleNamespace(x=5, y=5, width=10, height=10),
                                distance_m=frame.distance)]

cases = []
def run_case(name, scene, found, expected_text, distance=1.2, stamps=None):
    if stamps is None:
        stamps = list(range(100, 101 + len(found)))
    frames = [Frame(stamps[0], False, None)]
    frames += [Frame(stamp, value, distance) for stamp, value in zip(stamps[1:], found)]
    with tempfile.TemporaryDirectory(prefix='soccer_round1_') as temp:
        output = Path(temp)
        report = {'created_at': 'offline', 'python_path': 'offline', 'thresholds': {}, 'batches': [],
                  'single_results': [{'class_name': 'Ball', 'confidence': '0.8',
                                      'public_fields': {'distance_m': 'None'}}]}
        env = {'OUTPUT': output, 'report': report, 'CAMERA_ID': '', 'CONFIDENCE': 0.4,
               'SAMPLE_COUNT': 20, 'MAX_ATTEMPTS': 60, 'MIN_BALL_FRAMES': 18,
               'MAX_FALSE_FRAMES': 0, 'robot': Robot(frames), 'detector': Detector(),
               'time': Clock(), 'math': math, 'statistics': statistics, 'json': json,
               'ImageDraw': ImageDraw}
        def save():
            (output / '原始记录.json').write_text(
                json.dumps(report, ensure_ascii=False, default=str, allow_nan=False), encoding='utf-8')
        env['save'] = save
        functions = [node for node in ast.parse(codes[2]).body if isinstance(node, ast.FunctionDef)]
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<helper>', 'exec'), env)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(codes[3], '<STEP04>', 'exec'), env)
            batch = env['collect'](scene)
            exec(compile(codes[6], '<STEP07>', 'exec'), env)
        summary = batch['summary']
        assert expected_text in summary['conclusion'], (name, summary)
        assert (output / '自动统计.md').read_text(encoding='utf-8').startswith('# 足球第1轮自动统计\n')
        saved = json.loads((output / '原始记录.json').read_text(encoding='utf-8'))
        assert saved['batches'][0]['summary'] == summary
        if distance is None:
            assert summary['distance_frames'] == 0
        cases.append({'case': name, 'summary': summary, 'result': 'passed'})

run_case('有球18帧达标', 'with_ball', [True] * 18 + [False] * 2, '达到本轮数量标准')
run_case('有球17帧不达标', 'with_ball', [True] * 17 + [False] * 3, '未达到')
run_case('无球0误检', 'without_ball', [False] * 20, '达到本轮无球标准')
run_case('无球1次误检', 'without_ball', [True] + [False] * 19, '未达到')
run_case('距离空值如实记录', 'with_ball', [True] * 20, '达到本轮数量标准', distance=None)
run_case('旧图不补足样本', 'with_ball', [True], '采样不足', stamps=[100, 100])
run_case('源戳倒退停止', 'with_ball', [True, True], '需复核', stamps=[100, 101, 99])
run_case('接口异常保留前两帧', 'with_ball', [True, True, 'error'], '需复核')
assert cases[-1]['summary']['sample_count'] == 2

unchanged = []
concurrent = []
for name, expected in baseline['protected'].items():
    actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if actual == expected:
        unchanged.append(name)
    else:
        concurrent.append({'path': name, 'sha256': actual})

result = {'robot_executed': False, 'nbformat_and_ast': 'passed', 'code_steps': len(codes),
          'thresholds_match_guide': True, 'offline_branch_cases': cases,
          'protected_sources_unchanged': len(unchanged), 'concurrent_changes_not_touched': concurrent}
(TASK / '离线核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'offline_branch_cases'}, ensure_ascii=False, indent=2))
print('构造数据核查：', len(cases), '个分支通过；未导入SDK或连接机器人。')
