"""U7/U8局部功能参考。导入不执行SDK调用，所有运动须由Notebook明确启动。"""
import time
from .ball_position import select_ball, ball_pixel, pixel_to_robot


def new_session(robot, speech):
    return {'robot': robot, 'speech': speech, 'audio_task': None,
            'motion_task': None, 'manager': None, 'kick_active': False}


def idle(session):
    if session['kick_active']:
        return False
    for key in ['audio_task', 'motion_task']:
        task = session[key]
        if task is not None and not task.done():
            return False
    return True


def _wait_task(task, seconds):
    status = task.wait(timeout=seconds)
    if not task.done():
        task.cancel()
        task.wait(timeout=3.0)
        return '等待上限；当前状态：' + str(task.status)
    return '完成' if status == 'SUCCEEDED' else '任务状态：' + str(status)


def say(session, text, seconds=15.0):
    if not idle(session):
        return '旧任务未结束'
    task = session['speech'].synthesize(text)
    session['audio_task'] = task
    reason = _wait_task(task, seconds)
    if reason != '完成':
        return '合成' + reason
    audio = task.result()
    task = session['robot'].play_sound(audio)
    session['audio_task'] = task
    return _wait_task(task, seconds)


def greet(session, action_id, seconds=15.0):
    if not idle(session):
        return '旧任务未结束'
    robot = session['robot']
    if robot.get_mode() != 'walk':
        return '请先按实验要求确认行走模式'
    ids = [a.id for a in robot.list_actions()]
    if action_id not in ids:
        return '动作ID未在当前清单中'
    task = robot.do_action(action_id)
    session['motion_task'] = task
    return _wait_task(task, seconds)


def observe_guest(robot, detector, class_name='person'):
    started = time.monotonic()
    image = robot.get_image(img_type='rgb')
    result = select_ball(detector.detect(image.to_numpy()), class_name)
    # selected helper只按类别选评分最高的一条，亦可用于person；不表示身份跟踪。
    return {'found': result is not None, 'received': started,
            'finished': time.monotonic(), 'source_stamp': image.header.timestamp,
            'result': result}


def observe_ball(robot, detector, calibration, class_name='Ball'):
    started = time.monotonic()
    image = robot.get_image(img_type='rgb')
    result = select_ball(detector.detect(image.to_numpy()), class_name)
    record = {'found': False, 'received': started, 'finished': time.monotonic(),
              'source_stamp': image.header.timestamp, 'reason': '未检出足球'}
    if result is not None:
        u, v = ball_pixel(result)
        try:
            x, y = pixel_to_robot(calibration, u, v, [image.width, image.height])
            record.update(found=True, x=x, y=y, u=u, v=v, reason='有可用坐标')
        except ValueError as exc:
            record['reason'] = str(exc)
    return record


def stop_kick(session):
    if session['manager'] is not None and session['kick_active']:
        session['manager'].stop()
        session['kick_active'] = False  # stop成功返回后才清除，异常则保留占用标记。


def kick_window(session, detector, calibration, seconds=6.0, direction=0.0,
                power=1.0, max_age=0.8, class_name='Ball'):
    """有限观测窗口，不返回踢球成功；过期判断是本地取图前计时，非端到端图龄。"""
    import math
    from boosteros.robots.booster import SoccerKickManager
    if not idle(session):
        return '旧任务未结束', []
    if not calibration.get('verified', False):
        return '标定未通过独立核对', []
    if not all(math.isfinite(float(v)) for v in [seconds,direction,power,max_age]):
        return '参数不是有限数值', []
    if not 0 < seconds <= 20 or not 1 <= power <= 10 or max_age <= 0:
        return '参数超出课堂范围', []
    robot = session['robot']
    if robot.get_mode() != 'walk':
        return '请先按实验要求确认行走模式', []
    first = observe_ball(robot, detector, calibration, class_name)
    if not first['found']:
        return first['reason'], []
    if time.monotonic()-first['received'] > max_age:
        return '首次取图与处理已超时', []
    state = robot.get_fall_down_state()
    if not state.is_normal:
        return '状态不满足启动条件', []
    if session['manager'] is None:
        session['manager'] = SoccerKickManager(robot)
    records = []
    reason = '达到本次观察上限，踢球效果需现场核对'
    try:
        session['kick_active'] = True  # 即使start部分失败，finally也会尝试stop。
        session['manager'].start()
        session['manager'].update_command(direction=direction, power=power)
        started = time.monotonic()
        last_source = first['source_stamp']
        while time.monotonic()-started < seconds:
            state = robot.get_fall_down_state()
            if not state.is_normal:
                reason = '状态异常'
                break
            observation = observe_ball(robot, detector, calibration, class_name)
            age = time.monotonic()-observation['received']
            if not observation['found']:
                reason = observation['reason']
                break
            if age > max_age:
                reason = '取图与检测处理超时'
                break
            if observation['source_stamp'] == last_source:
                reason = '图像源时间戳未更新，不重复下发旧球位'
                break
            last_source = observation['source_stamp']
            # 管理器启动后重新检测，不把start前旧坐标发给已移动的机器人。
            session['manager'].update_ball(observation['x'], observation['y'])
            records.append({'x':observation['x'], 'y':observation['y'], 'age':age})
            time.sleep(0.1)
    finally:
        stop_kick(session)
    return reason, records


def cleanup(session):
    """尽力收尾，每个句柄分别处理；返回待处理项，不重置未结束句柄。"""
    problems = []
    try:
        stop_kick(session)
    except Exception as exc:
        problems.append('踢球停止异常：' + str(exc))
    for name in ['audio_task','motion_task']:
        task = session[name]
        if task is not None and not task.done():
            try:
                task.cancel()
                task.wait(timeout=3.0)
            except Exception as exc:
                problems.append(name + '收尾异常：' + str(exc))
            if not task.done():
                problems.append(name + '尚未结束')
    return problems
