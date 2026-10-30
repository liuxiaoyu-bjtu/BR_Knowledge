"""只验证现有课程几何函数的数学行为与批准字段边界，不导入SDK、不连机器人。"""
from pathlib import Path
import copy
import importlib.util
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT/'05-internal-materials/vocational-planning/03_X课程项目/notebooks/x_lab/ball_position.py'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('audited_ball_geometry', TARGET)
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)

# 人工构造一个可逆平面投影，目的只在检查实现，不表示任何真实相机。
matrix = np.array([[0.15, -0.7, 1.8], [-0.8, 0.04, 0.4], [0.08, 0.2, 1.0]])
size = [640, 480]


def row(u, v):
    point = matrix @ [u/size[0], v/size[1], 1]
    return [u, v, float(point[0]/point[2]), float(point[1]/point[2])]


samples = [row(u,v) for u,v in [(80,80),(320,80),(560,80),(560,400),(320,400),(80,400)]]
checks = [row(u,v) for u,v in [(160,160),(320,240),(480,320)]]
cal = geo.build_calibration(samples, size, '人工构造投影：离线验证，无真实姿态含义')
errors = geo.verify_calibration(cal, checks, 1e-8)
assert cal['verified'] and max(errors) < 1e-8

shifted = copy.deepcopy(cal)
shifted['setup_note'] = '改为另一头部/机身姿态：仅文字改变'
same_pixel = [320,240]
original = geo.pixel_to_robot(cal, *same_pixel, size)
after_note_change = geo.pixel_to_robot(shifted, *same_pixel, size)
assert original == after_note_change and shifted['verified']

outside_rejected = False
try:
    geo.pixel_to_robot(cal, 2,2,size)
except ValueError:
    outside_rejected=True
assert outside_rejected

result = {
    'robot_executed':False,
    'mathematical_model':'固定h33=1的平面投影线性最小二乘拟合，输入u/宽、v/高',
    'synthetic_holdout_errors_m': errors,
    'synthetic_model_recovered':True,
    'out_of_region_rejected':outside_rejected,
    'setup_note_change_does_not_invalidate_verified':shifted['verified'],
    'same_pixel_still_returns_same_coordinate':original==after_note_change,
    'conclusion':'实现能复现所构造的投影；没有真实采样、误差或运动有效性证据。姿态说明和verified不能代替动态核查。'
}
(Path(__file__).parent/'几何核查结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
