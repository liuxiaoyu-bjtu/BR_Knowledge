from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球SDK能力探查_只读.ipynb'
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))

def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# 足球SDK能力探查（教师用，只读）

对应[分级测试计划](足球SDK能力与定位方案_分级测试计划.md)的A01～A04、A06及A08原始数据采集。用于实际教学Python环境，按顺序逐格执行。它记录SDK能力，不计算球的米制位置，不生成标定文件，也不证明定位或踢球已经可用。

本文件不导入`x_lab`，不创建踢球管理器，不调用运动、模式切换或启停方法。连接前，由现场人员确认机器人已按既定流程固定，旧程序和任务已退出。连接、取图和推理仍可能发生等待或异常；保留完整报错，再核对版本，不改用未经核实的旧接口。

每轮填写机器编号、系统版本、球型、地面、姿态、已知测量位置和测试人，另存于计划的结果表。此文件只生成原始探查证据，验收门槛在计划中填写。''')
code('''import sys
import json
import time
import dataclasses
import importlib.metadata
import importlib.util
from datetime import datetime
from pathlib import Path
import numpy as np

report = {"purpose": "read_only_sdk_probe", "robot_motion_requested": False}
report["python"] = sys.version
report["python_executable"] = sys.executable
try:
    report["boosteros_version"] = importlib.metadata.version("boosteros")
except importlib.metadata.PackageNotFoundError:
    report["boosteros_version"] = "没有找到安装元数据"
spec = importlib.util.find_spec("boosteros")
report["boosteros_path"] = None if spec is None else spec.origin
print(json.dumps(report, ensure_ascii=False, indent=2))

run_dir = Path.cwd() / ("soccer_probe_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
run_dir.mkdir(exist_ok=False)
print("本轮文件目录：", run_dir.resolve())''')
md('''## 1. 核对当前接口（A01）

这里只导入类名，未构造管理器。若失败，先把报错与上一格版本信息交SDK支持人员核对。本文件没有自动安装、升级或旧API替代步骤。''')
code('''try:
    from boosteros.robots.booster import BoosterRobot, SoccerKickManager
    from boosteros.brain import Detection
except Exception as exc:
    report["import_error"] = {"type": type(exc).__name__, "message": str(exc)}
    (run_dir / "import_error.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    raise

report["imports"] = ["BoosterRobot", "Detection", "SoccerKickManager"]
print("类名导入成功；尚未连接机器人或创建管理器。")''')
md('''## 2. 记录工具与只读连接（A02）

下面的辅助函数只负责把对象公开数据写入JSON，并记录接口异常。大数组在JSON中仅保留形状与少量样本；图像及检测中的数值数组另存`.npy`，不把摘要当成完整原数据。

确认现场准备后，将`READ_ONLY_READY`改为`True`，只运行本格一次。同一轮后续格复用这个连接。''')
code('''def json_value(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: json_value(getattr(value, f.name))
                for f in dataclasses.fields(value) if not f.name.startswith("_")}
    if isinstance(value, np.ndarray):
        if value.size <= 256:
            return value.tolist()
        return {"shape": list(value.shape), "dtype": str(value.dtype),
                "sample": value.reshape(-1)[:16].tolist(), "summary_only": True}
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return repr(value)

def read_fields(obj, names):
    data = {"python_type": type(obj).__module__ + "." + type(obj).__name__}
    for name in names:
        try:
            data[name] = json_value(getattr(obj, name))
        except Exception as exc:
            data[name] = {"read_error": type(exc).__name__ + ": " + str(exc)}
    return data

def save_report():
    (run_dir / "report.json").write_text(
        json.dumps(json_value(report), ensure_ascii=False, indent=2), encoding="utf-8")

READ_ONLY_READY = False  # 由现场人员确认后修改
if not READ_ONLY_READY:
    raise RuntimeError("请先完成现场准备，再将READ_ONLY_READY改为True")
if "robot" in globals():
    raise RuntimeError("本内核已有robot，请复用原连接；不要重复执行连接格")
robot = BoosterRobot(enable_tf_listener=True)
report["connected_at"] = datetime.now().isoformat()
print("只读连接已建立。")''')
code('''metadata = {}
for name in ["robot_info", "get_mode", "list_sensors", "list_frames"]:
    try:
        value = getattr(robot, name)
        if name != "robot_info":
            value = value()
        metadata[name] = json_value(value)
    except Exception as exc:
        metadata[name] = {"error": type(exc).__name__ + ": " + str(exc)}
report["metadata"] = metadata
save_report()
print(json.dumps(metadata, ensure_ascii=False, indent=2))''')
md('''## 3. 图像、相机参数与原数组（A02、A06）

从`list_sensors`结果中选择实际相机ID；空字符串表示SDK默认相机，需用返回的frame等信息确认它是谁。RGB和深度分别请求，不能据此认定它们已同步或配准。记录源时间戳与本地调用起止；两者时钟未核实前，不相减来计算图龄。

此格逐次运行会追加文件。`uint16/float32`只说明存储类型，不证明单位；原数组留给SDK支持人员确认编码、单位、无效值和深度含义。''')
code('''CAMERA_ID = ""
capture_records = report.setdefault("image_captures", [])
for img_type in ["rgb", "depth"]:
    record = {"camera_id_requested": CAMERA_ID, "img_type": img_type,
              "local_start_epoch": time.time(), "local_start_monotonic": time.monotonic()}
    try:
        image = robot.get_image(camera_id=CAMERA_ID, img_type=img_type)
        record["get_return_epoch"] = time.time()
        record["image"] = read_fields(image, ["width", "height", "encoding", "header"])
        array = image.to_numpy()
        filename = f"image_{len(capture_records):03d}_{img_type}.npy"
        np.save(run_dir / filename, array, allow_pickle=False)
        record["array"] = {"file": filename, "shape": list(array.shape), "dtype": str(array.dtype)}
    except Exception as exc:
        record["error"] = type(exc).__name__ + ": " + str(exc)
    record["local_end_epoch"] = time.time()
    record["local_end_monotonic"] = time.monotonic()
    capture_records.append(record)
    save_report()
    print(json.dumps(record, ensure_ascii=False, indent=2))

try:
    info = robot.get_camera_info(camera_id=CAMERA_ID)
    report["camera_info"] = read_fields(info, ["header", "width", "height", "k", "d", "r", "p",
                                               "distortion_model", "binning_x", "binning_y", "roi"])
except Exception as exc:
    report["camera_info"] = {"error": type(exc).__name__ + ": " + str(exc)}
save_report()
print(json.dumps(report["camera_info"], ensure_ascii=False, indent=2))''')
md('''## 4. 单帧足球检测与完整字段（A03）

机器人静止，画面放一只球。此格重新取RGB。`to_dict()`按公开文档只包含基础字段，本探查直接读取`distance_m/mask/keypoints`，并保存dataclass中的公开字段或公开实例字段，同时列出公开属性名称。发现新字段后核实定义，不按名称猜单位或参考系。

JSON保留字段；数值数组另存`.npy`。若扩展对象无法序列化，保留类型/文本表示，交SDK支持人员进一步检查，不把它记为“没有数据”。''')
code('''detector = Detection(model="soccer")
single = {"camera_id_requested": CAMERA_ID, "local_start_epoch": time.time(),
          "local_start_monotonic": time.monotonic()}
rgb = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
single["get_return_epoch"] = time.time()
single["image"] = read_fields(rgb, ["width", "height", "encoding", "header"])
rgb_array = rgb.to_numpy()
np.save(run_dir / "detection_rgb.npy", rgb_array, allow_pickle=False)
results = detector.detect(rgb_array, confidence=0.4)

def detection_record(item, prefix):
    names = {"class_name", "class_id", "confidence", "bbox", "mask", "keypoints", "distance_m"}
    if dataclasses.is_dataclass(item):
        names.update(f.name for f in dataclasses.fields(item) if not f.name.startswith("_"))
    if hasattr(item, "__dict__"):
        names.update(n for n in vars(item) if not n.startswith("_"))
    data = read_fields(item, sorted(names))
    data["public_attribute_names"] = [n for n in dir(item) if not n.startswith("_")]
    for name in sorted(names):
        value = getattr(item, name, None)
        if isinstance(value, np.ndarray) and value.dtype != object:
            filename = f"{prefix}_{name}.npy"
            np.save(run_dir / filename, value, allow_pickle=False)
            data[name] = {"array_file": filename, "summary": json_value(value)}
    return data

single["detections"] = []
for index, item in enumerate(results):
    single["detections"].append(detection_record(item, f"single_{index}"))
single["local_end_epoch"] = time.time()
single["local_end_monotonic"] = time.monotonic()
report["single_detection"] = single
save_report()
print(json.dumps(single, ensure_ascii=False, indent=2))''')
md('''## 5. 有球/无球重复观察（A04）

先保持一只球不动，运行本格。然后在机器人固定、没有运动任务的条件下移走球，把`SCENE`改为`without_ball`再运行。每次最多请求60次、目标20个不同有效源戳；全部请求都有记录，重复帧不计作独立样本。若源戳缺失、为0或重复，保留问题，不用本地计时替代源戳。

软件条件仅限制两次调用之间的循环；SDK调用内部阻塞时，此格不能保证在指定秒数结束。数据可用于核查检出率与字段，米制误差还须计划A05/B中的独立测量。''')
code('''SCENE = "with_ball"  # 移走球后改为without_ball
batch_number = len(report.setdefault("batches", []))
batch = {"scene": SCENE, "records": [], "distinct_valid_source_stamps": 0}
report["batches"].append(batch)
seen = set()
for attempt in range(60):
    row = {"attempt": attempt + 1, "local_start_epoch": time.time(),
           "local_start_monotonic": time.monotonic()}
    try:
        image = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
        row["get_return_epoch"] = time.time()
        row["image"] = read_fields(image, ["width", "height", "encoding", "header"])
        header = getattr(image, "header", None)
        stamp = getattr(header, "timestamp", None)
        frame_id = getattr(header, "frame_id", None)
        key = (str(frame_id), str(stamp))
        valid_stamp = isinstance(stamp, (int, float, np.number)) and bool(np.isfinite(stamp)) and stamp > 0
        row["source_stamp"] = json_value(stamp)
        row["new_valid_source_stamp"] = valid_stamp and key not in seen
        if row["new_valid_source_stamp"]:
            seen.add(key)
            array = image.to_numpy()
            filename = f"batch_{batch_number}_{len(seen):02d}_rgb.npy"
            np.save(run_dir / filename, array, allow_pickle=False)
            row["image_array_file"] = filename
            items = detector.detect(array, confidence=0.4)
            row["detections"] = []
            for index, item in enumerate(items):
                row["detections"].append(detection_record(item, f"batch_{batch_number}_{len(seen)}_{index}"))
    except Exception as exc:
        row["error"] = type(exc).__name__ + ": " + str(exc)
    row["local_end_epoch"] = time.time()
    row["local_end_monotonic"] = time.monotonic()
    batch["records"].append(row)
    batch["distinct_valid_source_stamps"] = len(seen)
    save_report()
    print("请求", attempt + 1, "不同有效源戳", len(seen), "异常", row.get("error"))
    if "error" in row or len(seen) >= 20:
        break
    time.sleep(0.1)
print("本批场景：", SCENE, "不同有效源戳：", len(seen))''')
md('''## 6. 查询实际坐标变换（A08）

从上面`list_frames`结果选相机源坐标系和机身目标坐标系。只有确认管理器的机身参考原点后才能把它作为控制坐标；这里仅记录查询，不将检测结果转换或发送出去。未填写时跳过。

文档规定`get_transform(target_frame, source_frame)`为源到目标。把查询参数、返回字段和矩阵一起保留，现场用已知方向验证。坐标变换存在只说明参考系关系，不能证明已经定位了足球。''')
code('''SOURCE_FRAME = ""
TARGET_FRAME = ""
if not SOURCE_FRAME or not TARGET_FRAME:
    print("未填写实际frame，本格跳过；A08仍为待执行。")
else:
    query = {"source_frame_requested": SOURCE_FRAME, "target_frame_requested": TARGET_FRAME,
             "local_start_epoch": time.time()}
    try:
        transform = robot.get_transform(target_frame=TARGET_FRAME, source_frame=SOURCE_FRAME)
        query["returned"] = read_fields(transform, ["source_frame", "target_frame", "header",
                                                    "translation", "rotation", "rpy", "timestamp"])
        query["matrix"] = json_value(transform.to_matrix())
    except Exception as exc:
        query["error"] = type(exc).__name__ + ": " + str(exc)
    query["local_end_epoch"] = time.time()
    report.setdefault("transform_queries", []).append(query)
    save_report()
    print(json.dumps(query, ensure_ascii=False, indent=2))''')
md('''## 7. 保存与下一步

运行最后一格，保留本轮目录，并把结果填入计划中对应编号。目录里有原始图像/深度数值数组和JSON；通过`np.load(path, allow_pickle=False)`可以重新读取数组。源戳的单位和时钟仍需核实。拍摄条件、物理测量、接口报错截图与产品答复另附。

- `distance_m`有值：核实距离定义和参考点，再做A05，不把它直接当x。
- 出现位置字段或相关frame：核实来源、坐标系、单位、时效，再验证。
- 有深度、内参和TF：先查配准与定义，由教师验证组合方案。
- 只有二维框：先完成A09产品能力问答，再决定是否做B固定映射验证。

本文件没有启动运动任务，无需在这里补模式切换或踢球停止指令。连接释放按本机SDK既有操作流程处理，退出内核不能用来代替其他程序的任务收尾。''')
code('''save_report()
print("探查记录已保存：", (run_dir / "report.json").resolve())
print("只读探查结束；请在分级测试计划中填写结果，未进行运动验收。")''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3'},
    'purpose': 'teacher_read_only_sdk_probe',
    'robot_executed': False,
})
nbf.validate(nb)
# 该脚本只重建本轮新增的教师探查文件，不操作学生Notebook。
if OUT.exists():
    old = nbf.read(OUT, as_version=4)
    assert old.metadata.get('purpose') == 'teacher_read_only_sdk_probe'
    assert all(c.get('execution_count') is None and not c.get('outputs')
               for c in old.cells if c.cell_type == 'code'), '已有现场结果，不覆盖'
OUT.write_text(nbf.writes(nb), encoding='utf-8')
print(OUT)
print({'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
