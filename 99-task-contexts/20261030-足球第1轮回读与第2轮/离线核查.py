from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import hashlib
import io
import json
import math
import inspect
import tempfile
import numpy as np
import nbformat
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
VERIFY = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
nb = nbformat.read(VERIFY / '足球测试_第2轮_深度与坐标接口.ipynb', as_version=4)
nbformat.validate(nb)
codes = [c.source for c in nb.cells if c.cell_type == 'code']
assert len(codes) == 5
for source in codes:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            assert name not in {'SoccerKickManager', 'start', 'stop', 'update_command', 'update_ball',
                                'set_mode', 'do_action', 'move', 'execute_trajectory', 'set_head_angle'}, name
    assert 'x_lab' not in source
assert all(c.execution_count is None and not c.outputs for c in nb.cells if c.cell_type == 'code')

class Frame:
    width = height = 4
    encoding = 'raw'
    header = SimpleNamespace(frame_id='head_color_optical_frame')
    def __init__(self, values):
        self.values = values
    def to_pil(self):
        return Image.new('RGB', (4, 4), 'white')
    def to_numpy(self):
        return self.values

class CameraInfo:
    width = height = 4
    frame_id = 'head_color_optical_frame'
    k = np.eye(3)
    def to_dict(self):
        return {'k': self.k.tolist(), 'width': self.width, 'height': self.height}

class Transform:
    source_frame = 'head_color_optical_frame'
    target_frame = 'head_pitch_link'
    header = 'raw header'
    translation = np.array([0.1, 0.2, 0.3])
    rotation = np.array([0, 0, 0, 1])
    def to_matrix(self):
        return np.eye(4)

class Robot:
    def __init__(self, depth='ok', frames=True, tf='ok', k='ok', sensors=True):
        self.depth_case = depth
        self.frames_case = frames
        self.tf_case = tf
        self.k_case = k
        self.sensors_case = sensors
    def list_sensors(self):
        if not self.sensors_case:
            raise RuntimeError('模拟传感器查询失败')
        return [SimpleNamespace(id='head', sensor_type='camera')]
    def list_frames(self):
        return ['head_color_optical_frame', 'head_pitch_link'] if self.frames_case else []
    def get_image(self, camera_id, img_type):
        if img_type == 'depth' and self.depth_case == 'error':
            raise RuntimeError('模拟未发布深度图')
        values = np.ones((4, 4), dtype=np.uint16)
        if img_type == 'depth' and self.depth_case == 'zero':
            values[:] = 0
        return Frame(values)
    def get_camera_info(self, camera_id):
        info = CameraInfo()
        if self.k_case == 'nan':
            info.k = np.full((3, 3), np.nan)
        return info
    def get_transform(self, target_frame, source_frame):
        assert target_frame == 'head_pitch_link'
        assert source_frame == 'head_color_optical_frame'
        if self.tf_case == 'error':
            raise RuntimeError('模拟暂无TF')
        return Transform()

cases = []
class SoccerKickManager:
    def start(self): pass
    def update_command(self, direction, power): pass
    def update_ball(self, x, y): pass
    def stop(self): pass

def check_case(label, robot, expected):
    with tempfile.TemporaryDirectory(prefix='soccer_round2_') as temp:
        output = Path(temp)
        report = {'created_at': 'offline', 'capabilities': {}, 'sdk_version': 'offline'}
        env = {'np': np, 'json': json, 'math': math, 'robot': robot, 'CAMERA_ID': '',
               'inspect': inspect, 'SoccerKickManager': SoccerKickManager,
               'OUTPUT': output, 'report': report, 'display': lambda value: None}
        functions = [n for n in ast.parse(codes[0]).body if isinstance(n, ast.FunctionDef)]
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<json_helpers>', 'exec'), env)
        with contextlib.redirect_stdout(io.StringIO()):
            for index in [1, 2, 3, 4]:
                exec(compile(codes[index], '<step>', 'exec'), env)
        for name, status in expected.items():
            assert report['capabilities'][name] == status, (label, report)
        saved = json.loads((output / '原始记录.json').read_text(encoding='utf-8'))
        assert saved['capabilities'] == report['capabilities']
        assert report['capabilities']['管理器方法清单'] == '已取得'
        assert not report['soccer_manager_missing_methods']
        assert (output / '能力汇总.md').read_text(encoding='utf-8').startswith('# 足球第2轮')
        cases.append({'case': label, 'capabilities': report['capabilities'], 'result': 'passed'})

check_case('全部返回', Robot(), {'深度图': '已取得', '相机内参': '已取得', '坐标变换查询': '已取得'})
check_case('深度报错仍读内参和TF', Robot(depth='error'), {'深度图': '接口报错', '相机内参': '已取得', '坐标变换查询': '已取得'})
check_case('全零深度', Robot(depth='zero'), {'深度图': '已返回但内容不足'})
check_case('空frame列表不猜TF参数', Robot(frames=False), {'坐标系列表': '已返回空列表', '坐标变换查询': '本轮未查询'})
check_case('TF报错', Robot(tf='error'), {'坐标变换查询': '接口报错'})
check_case('非有限内参可保存', Robot(k='nan'), {'相机内参': '已返回但内容不足'})
check_case('传感器列表报错仍读图', Robot(sensors=False), {'传感器列表': '接口报错', '深度图': '已取得'})

for group in ['protected', 'evidence']:
    for name, expected in baseline[group].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, (group, name)

result = {'robot_executed_by_assistant': False, 'nbformat_and_ast': 'passed', 'code_steps': len(codes),
          'offline_cases': cases, 'protected_sources_unchanged': len(baseline['protected']),
          'round1_evidence_unchanged': len(baseline['evidence'])}
(TASK / '离线核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('第2轮5格代码、7种构造分支通过；未连接SDK。')
print('学生源文件/旧Notebook保护：',len(baseline['protected']),'；第1轮原始证据保护：',len(baseline['evidence']))
