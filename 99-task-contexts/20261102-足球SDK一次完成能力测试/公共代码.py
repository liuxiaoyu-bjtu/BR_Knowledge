TESTER = "xy"
ROBOT_ID = "060100"

import sys
import json
import time
import math
import traceback
import importlib.metadata
from datetime import datetime
from pathlib import Path
import numpy as np

if "report" in globals() or "robot" in globals():
    raise RuntimeError("已有本次连接或记录，保留原目录；继续后续步骤")
OUTPUT = Path.cwd() / "足球测试结果" / datetime.now().strftime("第4轮完整_%Y%m%d_%H%M%S_%f")
OUTPUT.mkdir(parents=True, exist_ok=False)
report = {"test": "足球SDK完整能力验证_v2", "created_at": datetime.now().isoformat(),
          "tester": TESTER, "robot_id": ROBOT_ID, "calls": [], "cases": {},
          "control_uncertain": False, "active_tests_available": False}

def save():
    (OUTPUT / "原始记录.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")

def call(method, function, *args, **kwargs):
    row = {"method": method, "case": report.get("current_case", "准备"),
           "args": list(args), "kwargs": kwargs, "attempted_at": datetime.now().isoformat()}
    report["calls"].append(row)
    save()
    try:
        value = function(*args, **kwargs)
    except (Exception, KeyboardInterrupt) as exc:
        row.update(returned=False, error=repr(exc), traceback=traceback.format_exc())
        save()
        print(method, "报错：", repr(exc))
        raise
    row.update(returned=True, return_type=type(value).__name__, return_repr=repr(value))
    save()
    if method != "get_odom":
        print(method, "返回：", repr(value))
    return value

def modes(label):
    row = {"label": label}
    for name, function in [("public", lambda: robot.get_mode()),
                           ("raw", lambda: robot.loco_client.GetMode().mode)]:
        try:
            row[name] = str(function())
        except Exception as exc:
            row[name + "_error"] = repr(exc)
    report.setdefault("modes", []).append(row)
    save()
    print(label, row)

def pose():
    state = call("get_odom", robot.get_odom)
    values = [float(v) for v in state.pose_2d]
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError("odom.pose_2d不是有限的[x,y,yaw]")
    report["calls"][-1]["pose_2d"] = values
    save()
    return values

def ball_at_current_frame(ball_xy, measured_pose, current_pose):
    # 仅用于本次教师测试：球保持静止时，利用odom补偿机身平移/转向。
    x, y = ball_xy
    x0, y0, a0 = measured_pose
    x1, y1, a1 = current_pose
    world_x = x0 + math.cos(a0) * x - math.sin(a0) * y
    world_y = y0 + math.sin(a0) * x + math.cos(a0) * y
    dx, dy = world_x - x1, world_y - y1
    return [math.cos(a1) * dx + math.sin(a1) * dy,
            -math.sin(a1) * dx + math.cos(a1) * dy]

def stop_control(case):
    try:
        call("stop", soccer.stop)
    except (Exception, KeyboardInterrupt):
        case["stop_returned"] = False
        report["control_uncertain"] = True
        report["active_tests_available"] = False
        print("stop未返回，请按既有人工控制流程接管；后续运动步骤全部跳过。")
    else:
        case["stop_returned"] = True
        report["control_uncertain"] = False
    save()

def can_run(label):
    if label in report["cases"]:
        print("本项已有记录，不重复运行：", label)
        return False
    if not report.get("manager_created"):
        print("构造未成功，运动部分不可执行；仍可完成末尾汇总。")
        return False
    if report["control_uncertain"]:
        print("控制停止情况待处理，本项跳过；请人工恢复并保存。")
        return False
    return True

def checked_ball(x, y):
    if x is None or y is None:
        print("请填写本次卷尺实测BALL_X、BALL_Y，禁止沿用上一位置的数值。")
        return None
    values = [float(x), float(y)]
    if not all(math.isfinite(v) for v in values) or values[0] <= 0:
        print("球应在前方，x为正且x、y均须为有限米制数。")
        return None
    return values

def baseline():
    label = "无球位启停"
    if not can_run(label):
        return
    if input("确认机器人可进入足球模式，输入“启停”：").strip() != "启停":
        print("本项未启动。")
        return
    row = {"start_returned": False, "stop_returned": False}
    report["cases"][label] = row
    report["current_case"] = label
    try:
        report["control_uncertain"] = True
        call("start", soccer.start)
        row["start_returned"] = True
        time.sleep(1.0)
    except (Exception, KeyboardInterrupt) as exc:
        row["error"] = repr(exc)
    finally:
        stop_control(row)
    report["active_tests_available"] = bool(row["start_returned"] and row["stop_returned"] and not row.get("error"))
    modes("无球位启停后")
    save()

def motion_case(label, x, y, direction=0.0, power=1.0, continuous=False, observe_s=2.0):
    if not can_run(label):
        return
    if not report["active_tests_available"]:
        print("无球位启停尚未正常完成，跳过本项；故障已足以判定当前实验条件不足。")
        return
    xy = checked_ball(x, y)
    if xy is None:
        return
    if continuous and (xy[0] < 1.2 or abs(xy[1]) > 0.3):
        print("连续更新试验请把静止球放在前方至少1.2米、侧向0.3米以内，再实测填写。")
        return
    if not (math.isfinite(observe_s) and 0 < observe_s <= 4.0):
        print("本次观察窗口须在0至4秒内。")
        return
    if input("已重新摆球并实测，现场可试验，输入“执行”：").strip() != "执行":
        print("本项未启动。")
        return
    row = {"measured_ball_xy": xy, "direction": direction, "power": power,
           "continuous": continuous, "samples": [], "start_returned": False,
           "stop_returned": False, "observation_limit_s": observe_s}
    report["cases"][label] = row
    report["current_case"] = label
    save()
    # 测量时机器人和球保持不动，先取位姿，再启动；启动后补偿发生的机身位移。
    try:
        initial_pose = pose()
        row["measured_pose"] = initial_pose
    except (Exception, KeyboardInterrupt) as exc:
        row["error"] = "启动前里程计读取失败：" + repr(exc)
        save()
        return
    try:
        report["control_uncertain"] = True
        call("start", soccer.start)
        row["start_returned"] = True
        call("update_command", soccer.update_command, direction=direction, power=power)
        started = time.monotonic()
        changed = False
        while time.monotonic() - started < observe_s:
            current = pose()
            bx, by = ball_at_current_frame(xy, initial_pose, current)
            displacement = math.hypot(current[0] - initial_pose[0], current[1] - initial_pose[1])
            if continuous and (bx < 0.8 or displacement >= 0.15):
                row["end_reason"] = "达到本次接近试验的行进边界，提前停止"
                break
            call("update_ball", soccer.update_ball, x=bx, y=by)
            row["samples"].append({"odom": current, "ball_xy": [bx, by]})
            save()
            if not continuous:
                # 真实试踢只下发一次当前球位。球被踢动后不再用静止球假设续发。
                time.sleep(observe_s)
                row["end_reason"] = "单次球位输入观察结束；实际是否踢出另记"
                break
            if not changed and len(row["samples"]) >= 2:
                # 活动中实际修改方向和力度；源码允许根据旧球位/odom立即重新发布。
                call("update_command", soccer.update_command, direction=0.20, power=2.0)
                row["active_command_changed"] = True
                changed = True
            time.sleep(0.1)
        row.setdefault("end_reason", "连续更新观察窗口结束")
    except KeyboardInterrupt:
        row["observation_interrupted"] = True
        row["end_reason"] = "人工中断本次观察，finally尝试stop；现场原因另记"
        if not row["start_returned"] or not row["samples"]:
            report["active_tests_available"] = False
    except Exception as exc:
        row["error"] = repr(exc)
        report["active_tests_available"] = False
    finally:
        stop_control(row)
    modes(label + "停止后")
    save()
    print(label, "已记录；球位调用次数：", len(row["samples"]), "；请记录实际表现。")

try:
    report["sdk_version"] = importlib.metadata.version("boosteros")
    from boosteros.robots.booster import BoosterRobot, SoccerKickManager
    robot = call("BoosterRobot", BoosterRobot, enable_tf_listener=True)
except Exception as exc:
    report["connection_error"] = repr(exc)
    save()
    raise
try:
    report["robot_info"] = repr(robot.robot_info)
except Exception as exc:
    report["robot_info_error"] = repr(exc)
modes("连接后")
print("结果目录：", OUTPUT.resolve())
