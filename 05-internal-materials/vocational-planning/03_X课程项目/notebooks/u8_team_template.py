"""U8本组程序起始文件。先复制为u8_team.py，再按本组需求修改。

没有导入时的机器人调用；运行入口run_project需要Notebook明确授权。
局部调用来自课程附件x_lab；观察、介绍、行为和主流程在本文件中展开。
先填配置，再按需求修改函数，保存、加载并逐模块验证。
"""
import time
import math
from x_lab.flows import observe_guest, observe_ball, say, greet, kick_window, idle

VERSION = 'draft-1'
THEME = '导览'  # 二选一：“导览”或“踢球”
STEPS = []      # 按本组接口约定填写；下方validate提供检查
INTRODUCTION = ''  # 填本组已经核对事实的介绍或试踢说明
GREET_ID = ''
KICK_SECONDS = 6.0
KICK_DIRECTION = 0.0  # 相对当前机器人朝向，rad；正值朝左
KICK_POWER = 1.0


def validate():
    problems = []
    if THEME not in ['导览', '踢球']:
        problems.append('主题必须为导览或踢球')
    allowed = ['观察', '介绍', '再观察', '致意'] if THEME == '导览' else ['观察', '介绍', '再观察', '试踢']
    # 基础主流程在run_project中逐步写出；改变结构时同步修改此检查和接口表。
    if STEPS != allowed:
        problems.append('基础流程应填写：' + str(allowed))
    if not INTRODUCTION.strip():
        problems.append('介绍或试踢说明未填写')
    if THEME == '导览' and not GREET_ID:
        problems.append('未填写已验证动作ID')
    if THEME == '踢球':
        values = [KICK_SECONDS, KICK_DIRECTION, KICK_POWER]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            problems.append('试踢参数必须为有限数值')
        elif not (0 < KICK_SECONDS <= 20 and 1 <= KICK_POWER <= 10):
            problems.append('试踢时段或力度超出课堂范围')
    return problems


def observe(session, detectors, calibration):
    """本组观察模块：仅取得数据，返回原因，不发运动指令。"""
    session['last_observation'] = None  # 本次未取得记录时，不把上一轮当作本次输出。
    robot = session['robot']
    if THEME == '导览':
        record = observe_guest(robot, detectors['导览'])
    else:
        if calibration is None or not calibration.get('verified', False):
            return '标定未核对'
        record = observe_ball(robot, detectors['踢球'], calibration)
    session['last_observation'] = record
    if not record['found']:
        return record.get('reason', '未检出目标')
    if time.monotonic()-record['received'] > 0.8:
        return '本次取图与处理过慢'
    if session.get('last_source') == record['source_stamp']:
        return '尚未取得新的源图像'
    session['last_source'] = record['source_stamp']
    return '完成'


def introduce(session):
    """本组介绍模块：在这里按需求修改有限文本播报，保留任务退出检查。"""
    return say(session, INTRODUCTION)


def act(session, detectors, calibration):
    """本组行为模块：只运行所选主题，控制调用和参数在这里核对。"""
    if THEME == '导览':
        return greet(session, GREET_ID)
    reason, positions = kick_window(session, detectors['踢球'], calibration,
                                   seconds=KICK_SECONDS, direction=KICK_DIRECTION,
                                   power=KICK_POWER)
    session['last_kick_positions'] = positions
    return reason  # 这是停止原因，球是否进目标区由现场另记。


def record_result(log, session, step, result, started):
    """保存本步结果和现有句柄状态，不控制机器人。"""
    row = {'step': step, 'result': result, 'seconds': time.monotonic()-started}
    for key in ['audio_task', 'motion_task']:
        task = session[key]
        row[key + '_status'] = None if task is None else str(task.status)
    row['kick_active'] = session['kick_active']
    log.append(row)


def run_project(session, detectors, calibration, log=None):
    """返回每步记录；踢球只记录尝试原因，不生成“进球成功”结论。"""
    if log is None:
        log = []
    problems = validate()
    if problems:
        log.append({'step':'配置检查','result':'；'.join(problems),'seconds':0.0})
        return log
    if not idle(session):
        log.append({'step':'资源检查','result':'旧任务未结束','seconds':0.0})
        return log
    # 四次普通函数调用按顺序写出，前一步完成才进入下一步。
    # 若改成交互等待或多轮，须同步写明上限、退出条件和测试用例。
    executed_steps = 0
    step = '观察'
    started = time.monotonic()
    try:
        result = observe(session, detectors, calibration)
        record_result(log, session, step, result, started)
        executed_steps += 1

        if result == '完成':
            step = '介绍'
            started = time.monotonic()
            result = introduce(session)
            record_result(log, session, step, result, started)
            executed_steps += 1

        if result == '完成':
            step = '再观察'
            started = time.monotonic()
            result = observe(session, detectors, calibration)
            record_result(log, session, step, result, started)
            executed_steps += 1

        if result == '完成':
            step = STEPS[3]
            started = time.monotonic()
            result = act(session, detectors, calibration)
            record_result(log, session, step, result, started)
            executed_steps += 1
    except Exception as exc:
        record_result(log, session, step, '本步异常：' + str(exc), started)
        executed_steps += 1

    # 未运行部分也记下来，便于对照需求；实际资源收尾由Notebook的finally执行。
    for step in STEPS[executed_steps:]:
        log.append({'step':step, 'result':'未执行', 'seconds':None})
    return log
