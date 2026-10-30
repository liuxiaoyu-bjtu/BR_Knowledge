from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第2轮_深度与坐标接口.ipynb'
cells = []
def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))
def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# 足球测试第2轮：SDK深度与坐标接口

按[操作与记录表](足球测试_第2轮_操作与记录.md)逐格运行。目标是检查SDK能提供的数据，不做性能验收。

机器人保持静止，不需要足球、卷尺或重复采样。本文件不导入`x_lab`，不创建踢球管理器，不发运动或模式指令。一个接口失败时记录报错，继续完成其余读取；连接本身失败则直接保存已有记录。''')
md('''## STEP 01　连接与本轮文件夹

下面沿用第1轮备注，有变化再改。只运行连接格一次。SDK版本、模式自动读取；不切换模式。第一次连接失败时，保存输出并运行STEP 05即可。''')
code('''TESTER = "xy"
ROBOT_ID = "060100"
FIRMWARE = "1.8.1"
CAMERA_ID = ""  # 默认相机；先不修改

import sys
import json
import math
import inspect
import importlib.metadata
from datetime import datetime
from pathlib import Path
import numpy as np
from IPython.display import display

if "robot" in globals():
    raise RuntimeError("已有robot连接，不重复运行；后续格使用原连接")
OUTPUT = Path.cwd() / "足球测试结果" / datetime.now().strftime("第2轮_%Y%m%d_%H%M%S_%f")
OUTPUT.mkdir(parents=True, exist_ok=False)
report = {"test": "足球第2轮_SDK数据能力_v1", "created_at": datetime.now().isoformat(),
          "tester": TESTER, "robot_id": ROBOT_ID, "firmware_note": FIRMWARE,
          "python": sys.version, "camera_id_requested": CAMERA_ID, "capabilities": {}}

def json_safe(value):
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value

def save():
    (OUTPUT / "原始记录.json").write_text(
        json.dumps(json_safe(report), ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")

try:
    report["sdk_version"] = importlib.metadata.version("boosteros")
    from boosteros.robots.booster import BoosterRobot, SoccerKickManager
    robot = BoosterRobot(enable_tf_listener=True)
    report["robot_info"] = repr(robot.robot_info)
    report["mode"] = str(robot.get_mode())
    report["connected"] = True
except Exception as exc:
    report["connected"] = False
    report["connect_error"] = repr(exc)
    save()
    raise
save()
print("SDK：", report["sdk_version"], "模式：", report["mode"])
print("本轮目录：", OUTPUT.resolve())''')
md('''## STEP 02　相机与坐标系列表

原样运行。代码读取传感器、坐标系列表及足球管理器公开方法和签名，不要求你判断frame名称的几何含义。这里不构造或启动管理器，类名存在也不等于功能已经实测。

空列表或报错都是本轮结果，不自行安装、升级或改接口。管理器全部功能的后续安排见操作记录表。''')
code('''frames = []
try:
    sensors = robot.list_sensors()
    sensor_rows = []
    for sensor in sensors:
        row = {}
        for name in dir(sensor):
            if name.startswith("_"):
                continue
            try:
                value = getattr(sensor, name)
                if not callable(value):
                    row[name] = repr(value)
            except Exception as exc:
                row[name] = "读取失败：" + repr(exc)
        sensor_rows.append(row)
    report["sensors"] = sensor_rows
    report["capabilities"]["传感器列表"] = "已取得" if sensors else "已返回空列表"
    for row in sensor_rows:
        print(row)
except Exception as exc:
    report["sensor_error"] = repr(exc)
    report["capabilities"]["传感器列表"] = "接口报错"
    print("传感器列表：", repr(exc))
try:
    frames = list(robot.list_frames())
    report["frames"] = frames
    report["capabilities"]["坐标系列表"] = "已取得" if frames else "已返回空列表"
    print("坐标系列表：", frames)
except Exception as exc:
    report["frame_error"] = repr(exc)
    report["capabilities"]["坐标系列表"] = "接口报错"
    print("坐标系列表：", repr(exc))
try:
    api = {}
    for name in ["__init__"] + [n for n in dir(SoccerKickManager) if not n.startswith("_")]:
        member = getattr(SoccerKickManager, name)
        if callable(member):
            try:
                api[name] = str(inspect.signature(member))
            except (TypeError, ValueError):
                api[name] = "签名不可读：" + repr(member)
        else:
            api[name] = repr(member)
    report["soccer_manager_public_api"] = api
    required = ["start", "update_command", "update_ball", "stop"]
    missing = [name for name in required if not callable(getattr(SoccerKickManager, name, None))]
    report["soccer_manager_missing_methods"] = missing
    report["capabilities"]["管理器方法清单"] = "已取得" if not missing else "已返回但四个方法不齐"
    print("足球管理器方法/签名（尚未实际调用）：")
    for name, signature in api.items():
        print(name, signature)
except Exception as exc:
    report["manager_api_error"] = repr(exc)
    report["capabilities"]["管理器方法清单"] = "读取报错"
    print("管理器方法清单：", repr(exc))
save()''')
md('''## STEP 03　读取RGB、深度和相机内参

每种数据只读一次。三段调用各自保存结果或错误；深度失败时，内参仍可继续读取。

RGB与深度是分别请求的，不据此认为已对齐或同步。深度数组的`dtype/encoding`原样记录，不按它们猜米或毫米。内参只检查矩阵是否有可读取的基本结构，不检验精度。''')
code('''rgb_frame = ""
try:
    rgb = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
    rgb.to_pil().save(OUTPUT / "RGB.png")
    rgb_frame = str(rgb.header.frame_id)
    report["rgb"] = {"width": rgb.width, "height": rgb.height,
                     "encoding": str(getattr(rgb, "encoding", "未提供")),
                     "header": repr(rgb.header), "frame_id": rgb_frame}
    report["capabilities"]["RGB图"] = "已取得"
    display(rgb.to_pil())
except Exception as exc:
    report["rgb_error"] = repr(exc)
    report["capabilities"]["RGB图"] = "接口报错"
    print("RGB：", repr(exc))
save()

try:
    depth = robot.get_image(camera_id=CAMERA_ID, img_type="depth")
    array = np.asarray(depth.to_numpy())
    np.save(OUTPUT / "depth.npy", array, allow_pickle=False)
    numeric = np.issubdtype(array.dtype, np.number)
    structure_ok = array.ndim == 2 and array.size > 0 and numeric
    positive = array[np.isfinite(array) & (array > 0)] if structure_ok else np.array([])
    report["depth"] = {"width": depth.width, "height": depth.height,
                       "encoding": str(getattr(depth, "encoding", "未提供")),
                       "header": repr(depth.header), "frame_id": str(depth.header.frame_id),
                       "shape": list(array.shape), "dtype": str(array.dtype),
                       "nonempty_2d_numeric": structure_ok, "finite_positive_count": int(positive.size),
                       "positive_min_raw": float(positive.min()) if positive.size else None,
                       "positive_max_raw": float(positive.max()) if positive.size else None,
                       "unit": "本轮未确认"}
    report["capabilities"]["深度图"] = "已取得" if structure_ok and positive.size else "已返回但内容不足"
    print("深度尺寸/类型：", list(array.shape), str(array.dtype))
    print("有限正数个数：", int(positive.size), "；原始范围：",
          report["depth"]["positive_min_raw"], "到", report["depth"]["positive_max_raw"])
except Exception as exc:
    report["depth_error"] = repr(exc)
    report["capabilities"]["深度图"] = "接口报错"
    print("深度：", repr(exc))
save()

try:
    info = robot.get_camera_info(camera_id=CAMERA_ID)
    k = np.asarray(info.k)
    basic_k = bool(k.shape == (3, 3) and np.isfinite(k).all() and k[0, 0] > 0 and k[1, 1] > 0)
    report["camera_info"] = info.to_dict()
    report["camera_info_repr"] = repr(info)
    report["camera_k_structure_ok"] = basic_k
    report["capabilities"]["相机内参"] = "已取得" if basic_k else "已返回但内容不足"
    print("内参尺寸：", info.width, info.height, "；frame：", info.frame_id)
    print("K矩阵：")
    print(k)
except Exception as exc:
    report["camera_info_error"] = repr(exc)
    report["capabilities"]["相机内参"] = "接口报错"
    print("内参：", repr(exc))
save()''')
md('''## STEP 04　查询一次坐标变换

原样运行。程序只用本机列表确实包含的坐标系：优先实际RGB源到`head_pitch_link`，其次用文档示例`head_point → head_pitch_link`。没有这些名称就保存列表，标“本轮未查询”；我读完列表后再确定下一次查询参数。

成功时保存实际请求、返回的源/目标、平移、旋转及矩阵。这一步仅确认TF查询能否工作；不把头部坐标系当作踢球机身原点，也不把TF当作球位。''')
code('''source_frame = ""
target_frame = ""
if "head_pitch_link" in frames:
    if rgb_frame in frames and rgb_frame != "head_pitch_link":
        source_frame = rgb_frame
        target_frame = "head_pitch_link"
    elif "head_point" in frames:
        source_frame = "head_point"
        target_frame = "head_pitch_link"

if not source_frame or not target_frame:
    report["capabilities"]["坐标变换查询"] = "本轮未查询"
    report["transform_note"] = "列表中没有本轮预设示例组合，等待助手读列表后确定参数"
    print(report["transform_note"])
else:
    report["transform_request"] = {"source_frame": source_frame, "target_frame": target_frame}
    try:
        transform = robot.get_transform(target_frame=target_frame, source_frame=source_frame)
        matrix = np.asarray(transform.to_matrix())
        basic_matrix = bool(matrix.shape == (4, 4) and np.isfinite(matrix).all())
        report["transform"] = {"source_frame_returned": transform.source_frame,
                               "target_frame_returned": transform.target_frame,
                               "header": repr(transform.header),
                               "translation": np.asarray(transform.translation).tolist(),
                               "rotation": np.asarray(transform.rotation).tolist(),
                               "matrix": matrix.tolist(), "matrix_structure_ok": basic_matrix}
        report["capabilities"]["坐标变换查询"] = "已取得" if basic_matrix else "已返回但内容不足"
        print("实际请求：", source_frame, "→", target_frame)
        print("返回源/目标：", transform.source_frame, "→", transform.target_frame)
        print("平移：", transform.translation)
        print("矩阵：")
        print(matrix)
    except Exception as exc:
        report["transform_error"] = repr(exc)
        report["capabilities"]["坐标变换查询"] = "接口报错"
        print("TF：", repr(exc))
save()''')
md('''## STEP 05　保存能力汇总

运行本格，结果不足或报错也保留。把目录填回[第2轮记录表](足球测试_第2轮_操作与记录.md)，保存输出，复制本轮目录回知识库。你无需解释深度单位、矩阵或决定定位路线。

本轮到这里结束。告诉助手“第2轮已记录”，助手读数据后再判断SDK能支撑的课程范围与下一步。''')
code('''save()
names = ["传感器列表", "坐标系列表", "管理器方法清单", "RGB图", "深度图", "相机内参", "坐标变换查询"]
lines = ["# 足球第2轮：SDK数据能力", "", "时间：" + report["created_at"],
         "", "SDK：" + report.get("sdk_version", "未取得"),
         "", "模式：" + report.get("mode", "未取得"), "",
         "| 检查项 | 本轮结果 |", "| --- | --- |"]
for name in names:
    status = report["capabilities"].get(name, "未执行")
    lines.append("| " + name + " | " + status + " |")
    print(name, "：", status)
lines += ["", "## 报错或未查询原因", ""]
for key, value in report.items():
    if key.endswith("_error") or key == "transform_note":
        lines += ["- " + key + "：`" + str(value).replace("`", "'") + "`"]
lines += ["", "本轮仅确认接口及返回结构，不检验精度、检出率或动态性能。",
          "", "深度单位、RGB/深度对应和机身参考原点仍由助手据结果核实；尚未生成足球x/y。"]
(OUTPUT / "能力汇总.md").write_text("\\n".join(lines), encoding="utf-8")
print("结果目录：", OUTPUT.resolve())
print("本轮结束。请填写操作记录，再告诉助手第2轮已记录。")''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'}, 'purpose': 'soccer_round2_sdk_capability_v1',
    'robot_executed': False})
nbf.validate(nb)
if OUT.exists():
    old = nbf.read(OUT, as_version=4)
    assert old.metadata.get('purpose') == 'soccer_round2_sdk_capability_v1'
    assert all(c.get('execution_count') is None and not c.get('outputs')
               for c in old.cells if c.cell_type == 'code'), '已有现场结果，不覆盖'
OUT.write_text(nbf.writes(nb), encoding='utf-8')
print({'path': str(OUT), 'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
