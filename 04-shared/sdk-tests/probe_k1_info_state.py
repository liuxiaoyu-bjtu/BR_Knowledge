#!/usr/bin/env python3
"""采集 K1 的八项信息与状态接口；只读查询，结果逐项落盘。Python >= 3.10。"""
from __future__ import annotations

import argparse
import base64
import dataclasses
from datetime import date, datetime
from enum import Enum
import hashlib
import importlib.metadata
import inspect
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
from typing import Any
import zipfile


INTERFACES = (
    "robot_info", "get_mode", "list_gaits", "get_gait",
    "list_frames", "list_joints", "list_sensors", "list_actions",
)
_SESSION_ROBOT = None


def type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def safe_repr(value: Any) -> str:
    try:
        return repr(value)
    except Exception as exc:
        return f"<repr failed: {type(exc).__name__}: {exc}>"


def normalize(value: Any, warnings: list[str], path="$", stack=None) -> Any:
    """保留完整列表、嵌套字段和枚举名/值；无法展开的对象明确登记。"""
    if isinstance(value, Enum):
        return {"__enum__": type_name(value), "name": value.name,
                "value": normalize(value.value, warnings, path + ".value", stack)}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        warnings.append(f"{path}: 非有限浮点数已按标签保存")
        return {"__float__": repr(value)}
    if isinstance(value, (date, datetime)):
        return {"__type__": type_name(value), "iso": value.isoformat()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"__bytes_base64__": base64.b64encode(value).decode("ascii")}

    stack = set() if stack is None else stack
    if id(value) in stack:
        warnings.append(f"{path}: 循环引用，保留类型及repr")
        return {"__cycle__": type_name(value), "repr": safe_repr(value)}
    stack.add(id(value))
    try:
        def convert(item, suffix):
            return normalize(item, warnings, path + suffix, stack)

        if isinstance(value, dict):
            if all(isinstance(key, str) for key in value):
                return {key: convert(item, "." + key) for key, item in value.items()}
            return {"__mapping__": [[convert(k, ".key"), convert(v, ".value")]
                                    for k, v in value.items()]}
        if isinstance(value, tuple) and hasattr(value, "_fields"):
            return {name: convert(item, "." + name) for name, item in zip(value._fields, value)}
        if isinstance(value, (list, tuple, set, frozenset)):
            items = [convert(item, f"[{i}]") for i, item in enumerate(value)]
            if isinstance(value, (set, frozenset)):
                return {"__set__": items}
            return items
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return {field.name: convert(getattr(value, field.name), "." + field.name)
                    for field in dataclasses.fields(value)}
        # numpy 并非依赖；如果某版本返回 numpy 对象，仍可导出内容。
        if type(value).__module__.startswith("numpy"):
            return convert(value.tolist(), ".tolist")
        for method in ("model_dump", "to_dict", "dict"):
            function = getattr(value, method, None)
            if callable(function):
                try:
                    return convert(function(), "." + method)
                except Exception as exc:
                    warnings.append(f"{path}.{method}: {safe_repr(exc)}")
        fields = {}
        if hasattr(value, "__dict__"):
            fields.update(vars(value))
        for cls in type(value).__mro__:
            slots = getattr(cls, "__slots__", ())
            for name in ([slots] if isinstance(slots, str) else slots):
                if name not in ("__dict__", "__weakref__") and hasattr(value, name):
                    fields.setdefault(name, getattr(value, name))
        if fields:
            return {name: convert(item, "." + name) for name, item in fields.items()}
        warnings.append(f"{path}: {type_name(value)}未能展开字段，查看repr和本机定义")
        return {"__unexpanded_type__": type_name(value), "repr": safe_repr(value)}
    finally:
        stack.remove(id(value))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def now() -> str:
    return datetime.now().astimezone().isoformat()


def capture_definition(value: Any, label: str) -> str:
    lines = [f"\n===== {label} ====="]
    try:
        if isinstance(value, property):
            value = value.fget
        try:
            lines.append("signature: " + str(inspect.signature(value)))
        except (ValueError, TypeError):
            pass
        lines.append("doc: " + (inspect.getdoc(value) or "(无docstring)"))
        lines.append(inspect.getsource(value))
    except Exception as exc:
        lines.append("无法获取本机源码：" + safe_repr(exc))
    return "\n".join(lines) + "\n"


def render_report(report: dict) -> str:
    lines = ["# K1 信息与状态接口采集记录", "",
             f"开始时间：{report['started_at']}",
             f"测试人：{report['tester'] or '未填写'}",
             f"现场备注：{report['note'] or '未填写'}",
             f"SDK：{report['environment']['boosteros_version']}",
             f"连接：{report['connection']['status']}；来源：{report['connection']['source']}", "",
             "## 调用情况", "",
             "| 接口 | 调用结果 | 条目数 | 读取次数 | 导出提示数 |",
             "| --- | --- | --- | --- | --- |"]
    for name in INTERFACES:
        row = report["interfaces"].get(name)
        if row is None:
            lines.append(f"| {name} | 未执行 | — | 0 | — |")
            continue
        chosen = row["attempts"][row["selected_attempt"]]
        lines.append(f"| {name} | {chosen['status']} | {chosen.get('item_count', '—')} | "
                     f"{len(row['attempts'])} | {len(chosen.get('export_warnings', []))} |")
    lines += ["", "接口返回成功、空列表、报错和未执行分别登记。返回清单仅代表这台机器人、"
              "本次SDK/固件和当前配置；不是跨版本全集。", "",
              "`list_frames()`是本次可见的TF名称，不证明任意两帧可互相变换；"
              "`get_mode()`保存公开返回值，不推断底层原始模式；"
              "`get_gait()`的本机实现也已保存，不能直接当作当前实际运动的测量值。", "",
              "## 完整返回内容", ""]
    for name in INTERFACES:
        row = report["interfaces"].get(name)
        if row is None:
            continue
        chosen = row["attempts"][row["selected_attempt"]]
        lines += [f"### {name}", "", f"返回类型：{chosen.get('return_type', '未返回')}", ""]
        if chosen["status"] == "returned":
            lines += ["```json", json.dumps(chosen["value"], ensure_ascii=False, indent=2), "```", ""]
            for warning in chosen.get("export_warnings", []):
                lines.append("- 导出提示：" + warning)
        else:
            lines += ["```text", chosen.get("traceback", chosen.get("error", "")), "```", ""]
    lines += ["", "## 保存说明", "",
              "原始记录.json保存每次调用、完整结构化结果、类型、repr、异常及环境；"
              "分接口目录保存各项记录；SDK接口定义.txt保存本机接口与返回类型的定义。",
              "本次没有切换模式/步态，也没有执行动作；清单中的动作是否能执行未在本脚本中测试。",
              "结果由操作者在真机运行后生成；脚本作者的离线核查不能替代真机记录。", ""]
    return "\n".join(lines)


def collect(robot=None, output_root=None, tester="", note="", frames_wait=5.0) -> Path:
    """已有robot可直接传入；本模块创建的实例会在同一内核后续调用时复用。"""
    global _SESSION_ROBOT
    if not math.isfinite(frames_wait) or not 0 <= frames_wait <= 30:
        raise ValueError("frames_wait须在0～30秒之间")
    root = Path(output_root) if output_root is not None else Path.cwd() / "K1信息状态测试结果"
    output = root.resolve() / datetime.now().strftime("K1信息状态_%Y%m%d_%H%M%S_%f")
    output.mkdir(parents=True, exist_ok=False)
    (output / "分接口").mkdir()
    try:
        version = importlib.metadata.version("boosteros")
    except importlib.metadata.PackageNotFoundError:
        version = "未读取到包版本"
    source = "传入的已有robot" if robot is not None else "本模块缓存" if _SESSION_ROBOT is not None else "新建BoosterRobot"
    report = {"schema_version": 1, "started_at": now(), "tester": tester, "note": note,
              "requested_model": "K1", "hardware_execution": "由现场操作者运行，按robot_info核对机型",
              "environment": {"boosteros_version": version, "python": sys.version,
                              "executable": sys.executable, "platform": platform.platform()},
              "connection": {"status": "pending", "source": source},
              "interfaces": {}, "completed": False}
    definitions = []
    seen_types = set()

    def save():
        write_json(output / "原始记录.json", report)
        (output / "采集汇总.md").write_text(render_report(report), encoding="utf-8")
        (output / "SDK接口定义.txt").write_text("".join(definitions), encoding="utf-8")

    script_path = Path(__file__).resolve()
    script_data = script_path.read_bytes()
    report["script_sha256"] = hashlib.sha256(script_data).hexdigest()
    (output / "测试脚本.py").write_bytes(script_data)
    save()
    print("结果目录：", output)
    try:
        if robot is None:
            robot = _SESSION_ROBOT
        if robot is None:
            from boosteros.robots.booster import BoosterRobot
            robot = BoosterRobot()
            _SESSION_ROBOT = robot
        report["connection"].update(status="connected", robot_type=type_name(robot))
        save()
        for name in INTERFACES:
            try:
                member = inspect.getattr_static(type(robot), name)
                definitions.append(capture_definition(member, name))
            except Exception as exc:
                definitions.append(f"\n===== {name} =====\n无法读取定义：{safe_repr(exc)}\n")
            row = {"attempts": [], "selected_attempt": 0}
            report["interfaces"][name] = row
            deadline = time.monotonic() + frames_wait
            while True:
                attempt = {"started_at": now(), "status": "started"}
                row["attempts"].append(attempt)
                row["selected_attempt"] = len(row["attempts"]) - 1
                save()
                started = time.monotonic()
                try:
                    value = getattr(robot, name) if name == "robot_info" else getattr(robot, name)()
                    attempt.update(status="returned", returned_at=now(),
                                   elapsed_s=time.monotonic() - started,
                                   return_type=type_name(value), return_repr=safe_repr(value))
                    if isinstance(value, (list, tuple, dict, set, frozenset)):
                        attempt["item_count"] = len(value)
                    warnings = []
                    try:
                        attempt["value"] = normalize(value, warnings)
                    except Exception as exc:
                        warnings.append("字段导出异常：" + traceback.format_exc())
                        attempt["value"] = {"__export_error__": safe_repr(exc)}
                    attempt["export_warnings"] = warnings
                    # 仅读取返回对象的类型定义，不遍历属性调用其它SDK接口。
                    items = value if isinstance(value, (list, tuple)) else [value]
                    for item in items:
                        cls = type(item)
                        if cls.__module__.startswith("boosteros") and cls not in seen_types:
                            seen_types.add(cls)
                            definitions.append(capture_definition(cls, "返回类型 " + type_name(item)))
                except KeyboardInterrupt:
                    attempt.update(status="interrupted", returned_at=now(),
                                   elapsed_s=time.monotonic() - started,
                                   traceback=traceback.format_exc())
                    write_json(output / "分接口" / (name + ".json"), row)
                    raise
                except Exception as exc:
                    attempt.update(status="error", returned_at=now(),
                                   elapsed_s=time.monotonic() - started,
                                   error=safe_repr(exc), traceback=traceback.format_exc())
                write_json(output / "分接口" / (name + ".json"), row)
                save()
                retry_empty_frames = (name == "list_frames" and attempt["status"] == "returned"
                                      and attempt.get("item_count") == 0 and time.monotonic() < deadline)
                if not retry_empty_frames:
                    break
                time.sleep(min(0.5, max(0, deadline - time.monotonic())))
            selected = row["attempts"][row["selected_attempt"]]
            suffix = f"，{selected['item_count']}项" if "item_count" in selected else ""
            print(f"{name}: {selected['status']}{suffix}")
        report["completed"] = True
    except KeyboardInterrupt:
        report["interrupted"] = True
        print("采集中断，保留已经取得的结果。")
    except Exception as exc:
        report["fatal_error"] = safe_repr(exc)
        report["fatal_traceback"] = traceback.format_exc()
        if report["connection"]["status"] == "pending":
            report["connection"]["status"] = "error"
        print("采集未完成：", safe_repr(exc))
    finally:
        report["finished_at"] = now()
        save()
        bundle = output / (output.name + ".zip")
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(output.rglob("*")):
                if path.is_file() and path != bundle:
                    archive.write(path, path.relative_to(output))
        print("请反馈这个压缩包：", bundle)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tester", default="", help="测试人，可留空")
    parser.add_argument("--note", default="", help="现场配置或状态备注，可留空")
    parser.add_argument("--output", type=Path, default=None, help="结果根目录")
    parser.add_argument("--frames-wait", type=float, default=5.0, help="空坐标系列表的重读窗口，默认5秒")
    args = parser.parse_args()
    output = collect(output_root=args.output, tester=args.tester,
                     note=args.note, frames_wait=args.frames_wait)
    report = json.loads((output / "原始记录.json").read_text(encoding="utf-8"))
    if not report["completed"]:
        return 2
    has_error = any(row["attempts"][row["selected_attempt"]]["status"] != "returned"
                    for row in report["interfaces"].values())
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
