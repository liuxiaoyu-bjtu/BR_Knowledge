"""球位置的课堂近似标定。算法放在附件中，学生重点核查坐标与误差。

输入样本：[检测框下缘中点u, v, 卷尺实测前向x米, 左向y米]。
同一球、相机分辨率和固定头部/站姿下拟合平面投影近似。
不是SDK定位接口，不补偿头部与机身运动；独立核对后才可授权运动。
"""
import math
import numpy as np


def _hull(points):
    points = sorted(set(tuple(p) for p in points))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _inside(point, polygon):
    for i, a in enumerate(polygon):
        b = polygon[(i+1) % len(polygon)]
        cross = (b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
        if cross < -1e-7:
            return False
    return True


def build_calibration(samples, image_size, setup_note):
    """至少四个不共线样本；返回尚未经独立验证的JSON可保存字典。"""
    data = np.asarray(samples, dtype=float)
    if data.ndim != 2 or data.shape[1] != 4 or len(data) < 4:
        raise ValueError('需至少四行[u, v, x米, y米]实测样本')
    if not np.isfinite(data).all() or np.any(data[:, 2] <= 0):
        raise ValueError('样本须为有限数值，球位于机器人前方')
    width, height = image_size
    if width <= 0 or height <= 0 or not setup_note.strip():
        raise ValueError('需填写分辨率与头部/站姿记录')
    if np.any(data[:, :2] < 0) or np.any(data[:, 0] > width) or np.any(data[:, 1] > height):
        raise ValueError('像素坐标超出图像')
    uv_hull, xy_hull = _hull(data[:, :2]), _hull(data[:, 2:])
    if len(uv_hull) < 3 or len(xy_hull) < 3:
        raise ValueError('标定点不能在同一条直线上')
    # 图像坐标先按宽高归一，减少数值尺度差异。
    a, b = [], []
    for u, v, x, y in data:
        u, v = u/width, v/height
        a += [[u,v,1,0,0,0,-x*u,-x*v], [0,0,0,u,v,1,-y*u,-y*v]]
        b += [x,y]
    solution, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
    if rank < 8:
        raise ValueError('点位分布不足以建立映射，请重新布点')
    matrix = np.append(solution, 1).reshape(3, 3)
    return {'matrix': matrix.tolist(), 'image_size': [int(width), int(height)],
            'pixel_hull': uv_hull, 'xy_hull': xy_hull,
            'setup_note': setup_note, 'samples': data.tolist(),
            'verified': False, 'check_points': [], 'tolerance_m': None}


def pixel_to_robot(calibration, u, v, image_size):
    """只在标定区域内估计，不允许无条件外推；独立核对时也可调用。"""
    if list(image_size) != list(calibration['image_size']):
        raise ValueError('分辨率与标定不一致，需重新标定')
    if not all(math.isfinite(float(q)) for q in [u, v]):
        raise ValueError('像素坐标不是有限数值')
    if not _inside((u, v), calibration['pixel_hull']):
        raise ValueError('球线索超出标定区域')
    width, height = image_size
    p = np.asarray(calibration['matrix']) @ [u/width, v/height, 1]
    if not np.isfinite(p).all() or abs(p[2]) < 1e-8:
        raise ValueError('当前位置的投影估计不可用')
    x, y = float(p[0]/p[2]), float(p[1]/p[2])
    if x <= 0 or not _inside((x, y), calibration['xy_hull']):
        raise ValueError('估计位置超出已核对的地面区域')
    return x, y


def verify_calibration(calibration, check_points, tolerance_m):
    """至少三处未参与拟合的点；任一误差超限则禁止运动。"""
    calibration['verified'] = False
    calibration['check_points'] = []
    calibration['tolerance_m'] = None
    if len(check_points) < 3 or not math.isfinite(tolerance_m) or tolerance_m <= 0:
        raise ValueError('至少三处独立核对点，并填写教师确定的正数容许误差')
    positions = [(row[2], row[3]) for row in check_points]
    if len(set(positions)) < 3:
        raise ValueError('至少选择三个不同的实测位置，不能重复同一个核对点')
    errors = []
    for u, v, measured_x, measured_y in check_points:
        if not all(math.isfinite(float(q)) for q in [u,v,measured_x,measured_y]):
            raise ValueError('核对点包含无效数值')
        for sample in calibration['samples']:
            if math.hypot(measured_x-sample[2], measured_y-sample[3]) < 1e-6:
                raise ValueError('独立核对点不能重复拟合点')
        x, y = pixel_to_robot(calibration, u, v, calibration['image_size'])
        errors.append(math.hypot(x-measured_x, y-measured_y))
    calibration['check_points'] = [list(row) for row in check_points]
    calibration['tolerance_m'] = float(tolerance_m)
    calibration['verified'] = max(errors) <= tolerance_m
    return errors


def select_ball(results, class_name='Ball'):
    best = None
    for result in results:
        if result.class_name == class_name:
            if best is None or result.confidence > best.confidence:
                best = result
    return best


def ball_pixel(ball):
    # 框下缘中点是近似线索，球的轮廓下缘不等同于精确地面接触点。
    return float(ball.bbox.center_x), float(ball.bbox.center_y + ball.bbox.height/2)
