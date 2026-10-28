"""U8本组程序起始文件。先复制为u8_team.py，再按本组需求修改。

没有导入时的机器人调用；运行入口run_project需要Notebook明确授权。
局部函数来自x_lab，流程列表与参数由学生填写。不是最终提交成品。
"""
import time
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
    if not STEPS or any(step not in allowed for step in STEPS):
        problems.append('流程未填写或包含不适用于本主题的步骤')
    # 这只是起始片段约定；本组增减功能后须同步改检查和验收表。
    for step in allowed:
        if step not in STEPS:
            problems.append('起始流程缺少：' + step)
    if all(s in STEPS for s in allowed):
        indices = [STEPS.index(s) for s in allowed]
        if indices != sorted(indices):
            problems.append('起始交接顺序应为观察、介绍、再观察、行为')
    if not INTRODUCTION.strip():
        problems.append('介绍或试踢说明未填写')
    if THEME == '导览' and not GREET_ID:
        problems.append('未填写已验证动作ID')
    if THEME == '踢球' and not (0 < KICK_SECONDS <= 20 and 1 <= KICK_POWER <= 10):
        problems.append('试踢时段或力度超出课堂范围')
    return problems


def observe(session, detectors, calibration):
    robot = session['robot']
    if THEME == '导览':
        record = observe_guest(robot, detectors['导览'])
    else:
        if calibration is None or not calibration.get('verified', False):
            return '标定未核对'
        record = observe_ball(robot, detectors['踢球'], calibration)
    if not record['found']:
        return record.get('reason', '未检出目标')
    if time.monotonic()-record['received'] > 0.8:
        return '本次取图与处理过慢'
    if session.get('last_source') == record['source_stamp']:
        return '尚未取得新的源图像'
    session['last_source'] = record['source_stamp']
    return '完成'


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
    performed = 0
    for step in STEPS:
        started = time.monotonic()
        try:
            if step in ['观察', '再观察']:
                result = observe(session, detectors, calibration)
            elif step == '介绍':
                result = say(session, INTRODUCTION)
            elif step == '致意':
                result = greet(session, GREET_ID)
            else:
                result, positions = kick_window(session, detectors['踢球'], calibration,
                                               seconds=KICK_SECONDS, direction=KICK_DIRECTION,
                                               power=KICK_POWER)
                log.append({'step':'球坐标条数','result':str(len(positions)),'seconds':0.0})
        except Exception as exc:
            result = '本步异常：' + str(exc)
        log.append({'step':step,'result':result,'seconds':time.monotonic()-started})
        performed += 1
        if result != '完成':
            break
    for step in STEPS[performed:]:
        log.append({'step':step, 'result':'未执行', 'seconds':None})
    return log
