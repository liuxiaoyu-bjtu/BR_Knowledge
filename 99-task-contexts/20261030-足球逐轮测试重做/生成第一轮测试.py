from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球测试_第1轮_静止检测.ipynb'
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))

def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# 足球测试第1轮：静止检测

配套[操作指导与记录表](足球测试_第1轮_操作与记录.md)。本轮先查清取图与足球检测的实际结果，再由助手安排下一轮。

按STEP 01～07逐格运行。机器人固定、保持静止，其他任务先结束。本文件不调用运动、模式切换或踢球管理器，不使用`x_lab`或标定文件。遇错停在该步，运行STEP 07保存已有结果；STEP 01基础导入前失败则直接记报错。''')
md('''## STEP 01　填写环境，确认参数

填写下面前三个备注字符串。参数先用默认值，程序会按这些值统计。环境版本及错误自动保存。成功后记住打印的结果目录，不必手抄版本信息。''')
code('''TESTER = ""       # 测试人
ROBOT_ID = ""     # 机器编号；不知道可写暂不清楚
FIRMWARE = ""     # 固件/系统版本；不知道可写暂不清楚

CONFIDENCE = 0.4
SAMPLE_COUNT = 20
MAX_ATTEMPTS = 60
MIN_BALL_FRAMES = 18
MAX_FALSE_FRAMES = 0

import sys
import json
import time
import math
import statistics
import importlib.metadata
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from IPython.display import display

OUTPUT = Path.cwd() / "足球测试结果" / datetime.now().strftime("第1轮_%Y%m%d_%H%M%S_%f")
OUTPUT.mkdir(parents=True, exist_ok=False)
report = {"test": "足球第1轮_静止检测_v2", "created_at": datetime.now().isoformat(),
          "tester": TESTER, "robot_id": ROBOT_ID, "firmware": FIRMWARE,
          "python": sys.version, "python_path": sys.executable,
          "thresholds": {"confidence": CONFIDENCE, "sample_count": SAMPLE_COUNT,
                         "max_attempts": MAX_ATTEMPTS, "min_ball_frames": MIN_BALL_FRAMES,
                         "max_false_frames": MAX_FALSE_FRAMES}, "batches": []}

def save():
    (OUTPUT / "原始记录.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")

try:
    report["sdk_version"] = importlib.metadata.version("boosteros")
except importlib.metadata.PackageNotFoundError:
    report["sdk_version"] = "没有找到安装元数据"
try:
    import boosteros
    from boosteros.robots.booster import BoosterRobot
    from boosteros.brain import Detection
    report["sdk_path"] = str(getattr(boosteros, "__file__", "未知"))
    report["imports"] = "成功"
except Exception as exc:
    report["import_error"] = repr(exc)
    save()
    print("导入失败；停止后续测试。错误已保存：", OUTPUT)
    raise
save()
print("SDK版本：", report["sdk_version"])
print("Python：", sys.executable)
print("检测筛选阈值：", CONFIDENCE)
print("每种场景目标新图数：", SAMPLE_COUNT, "；最多取图次数：", MAX_ATTEMPTS)
print("有球最低检出帧数：", MIN_BALL_FRAMES, "；无球最多误检帧数：", MAX_FALSE_FRAMES)
print("结果目录：", OUTPUT.resolve())''')
md('''## STEP 02　取图，检查画面

默认相机用空ID。只运行本格一次，后面复用同一个连接。若内核已有其他课程的`robot`，先完成旧任务的正常收尾，再换专用测试内核。

成功后查看图片：是不是当前画面？球是否完整可见？把现场情况记入配套表。此格不调整头部，也不切模式。''')
code('''CAMERA_ID = ""  # 默认相机；已知实际相机ID时才填写
if "robot" in globals():
    raise RuntimeError("已有robot连接，请勿重复运行本格；后续格复用原连接")
try:
    robot = BoosterRobot()
    report["camera_id_requested"] = CAMERA_ID
    report["robot_info"] = repr(robot.robot_info)
    report["mode"] = str(robot.get_mode())
    image = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
    image.to_pil().save(OUTPUT / "02_当前画面.png")
    report["first_image"] = {"width": image.width, "height": image.height,
                             "header": repr(image.header)}
    display(image.to_pil())
except Exception as exc:
    report["step02_error"] = repr(exc)
    save()
    raise
save()
print("模式：", report["mode"])
print("现场记录：确认显示的是当前画面，球完整可见。")''')
md('''## STEP 03　检测，查看返回内容

本格重新取一张图，输出标框图和每条检测的类别、评分、距离与公开字段。这里直接读`distance_m`，因为SDK的`to_dict()`不含这个扩展字段。

先看框是否圈中真球，再记下足球类名。没有框或框错目标时，停止后续采样，先保存记录；不要先降低阈值。即使距离为`None`，也照实记录。''')
code('''def result_record(item):
    # 字段原文供下一轮审读；不会把未知字段当成控制坐标。
    fields = {}
    for name in dir(item):
        if name.startswith("_"):
            continue
        try:
            value = getattr(item, name)
            if not callable(value):
                fields[name] = repr(value)
        except Exception as exc:
            fields[name] = "读取失败：" + repr(exc)
    distance = getattr(item, "distance_m", None)
    try:
        distance = float(distance)
        if not math.isfinite(distance) or distance <= 0:
            distance = None
    except (TypeError, ValueError, OverflowError):
        distance = None
    return {"class_name": str(item.class_name), "confidence": repr(item.confidence),
            "positive_distance_m": distance, "public_fields": fields}

def save_picture(image, detections, filename):
    picture = image.to_pil().copy()
    draw = ImageDraw.Draw(picture)
    for item in detections:
        box = item.bbox
        draw.rectangle([box.x, box.y, box.x + box.width, box.y + box.height], outline="red", width=2)
        draw.text((box.x, max(0, box.y - 12)), str(item.class_name), fill="red")
    picture.save(OUTPUT / filename)
    return picture

try:
    detector = Detection(model="soccer")
    image = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
    results = detector.detect(image.to_numpy(), confidence=CONFIDENCE)
    report["single_results"] = [result_record(item) for item in results]
    report["single_image_header"] = repr(image.header)
    display(save_picture(image, results, "03_单帧检测.png"))
    print("本帧检测结果数量：", len(report["single_results"]))
    for number, item in enumerate(report["single_results"], 1):
        print("第", number, "条：类别", item["class_name"], "；评分", item["confidence"])
        print("distance_m原值：", item["public_fields"].get("distance_m", "没有这个字段"))
        print("公开字段（供记录和后续审读）：")
        for name, value in item["public_fields"].items():
            print("  ", name, "=", value)
except Exception as exc:
    report["step03_error"] = repr(exc)
    save()
    raise
save()
print("请核对：框是否圈中真球？实际足球类名是什么？")''')
md('''## STEP 04　填足球类名，准备采样

将`BALL_LABEL`填成上一格实际显示的足球类名；官方例子为`Ball`，本机不同时按本机填写。下面函数负责“取新图→检测→保存→计数”，原样运行即可，本格还不采样。

每种场景会先丢弃一个起始帧，再只计源时间戳递增的新图。重复帧会记录、跳过；源戳无效、倒退或接口异常就停止本批。成功检测完成才算一个样本。20张没有采满时，程序标“采样不足”，不拿缺少的结果作0。''')
code('''BALL_LABEL = "Ball"  # 按STEP 03实际类名填写，注意大小写
if BALL_LABEL not in [item["class_name"] for item in report.get("single_results", [])]:
    raise RuntimeError("类名不在STEP 03结果中；请核对，若单帧没有检出球，先交已有记录")
report["ball_label"] = BALL_LABEL

def collect(scene):
    batch = {"scene": scene, "records": [], "samples": [], "errors": [],
             "duplicate_frames": 0, "backward_stamps": 0}
    report["batches"].append(batch)
    batch_id = len(report["batches"])
    save()
    try:
        first = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
        last_stamp = float(first.header.timestamp)
        if not math.isfinite(last_stamp) or last_stamp <= 0:
            raise ValueError("源时间戳缺失或无效")
        batch["discarded_initial_header"] = repr(first.header)
        for attempt in range(MAX_ATTEMPTS):
            row = {"attempt": attempt + 1, "local_start": time.time()}
            batch["records"].append(row)
            image = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
            stamp = float(image.header.timestamp)
            row["source_stamp"] = stamp if math.isfinite(stamp) else repr(stamp)
            row["frame_id"] = str(image.header.frame_id)
            if not math.isfinite(stamp) or stamp <= 0:
                raise ValueError("源时间戳无效；本批停止")
            if stamp < last_stamp:
                batch["backward_stamps"] += 1
                raise ValueError("源时间戳倒退；本批停止")
            if stamp == last_stamp:
                batch["duplicate_frames"] += 1
                row["skip"] = "重复源帧"
                save()
                time.sleep(0.1)
                continue
            last_stamp = stamp
            started = time.monotonic()
            detections = detector.detect(image.to_numpy(), confidence=CONFIDENCE)
            row["detection_seconds"] = time.monotonic() - started
            row["results"] = [result_record(item) for item in detections]
            balls = [item for item in row["results"] if item["class_name"] == BALL_LABEL]
            row["ball_count"] = len(balls)
            row["has_positive_distance"] = any(item["positive_distance_m"] is not None for item in balls)
            filename = f"{batch_id:02d}_{scene}_{len(batch['samples']) + 1:02d}.png"
            save_picture(image, detections, filename)
            row["picture"] = filename
            row["local_end"] = time.time()
            batch["samples"].append(row.copy())
            save()
            print("有效样本", len(batch["samples"]), "/", SAMPLE_COUNT, "球类框数", len(balls))
            if len(batch["samples"]) >= SAMPLE_COUNT:
                break
            time.sleep(0.1)
    except Exception as exc:
        batch["errors"].append(repr(exc))
        print("本批停止：", repr(exc))
    samples = batch["samples"]
    found = sum(row["ball_count"] > 0 for row in samples)
    distance_count = sum(row["has_positive_distance"] for row in samples)
    if batch["errors"]:
        conclusion = "需复核：本批有异常，保留已有样本"
    elif len(samples) < SAMPLE_COUNT:
        conclusion = "采样不足：不判通过"
    elif scene == "with_ball":
        conclusion = "达到本轮数量标准，仍需人工看框" if found >= MIN_BALL_FRAMES else "未达到本轮有球数量标准"
    else:
        conclusion = "达到本轮无球标准" if found <= MAX_FALSE_FRAMES else "未达到本轮无球标准：存在球类框"
    times = [row["detection_seconds"] for row in samples]
    timing = None if not times else {"min": min(times), "median": statistics.median(times), "max": max(times)}
    batch["summary"] = {"sample_count": len(samples), "ball_frames": found,
                        "distance_frames": distance_count, "duplicate_frames": batch["duplicate_frames"],
                        "multi_ball_frames": sum(row["ball_count"] > 1 for row in samples),
                        "backward_stamps": batch["backward_stamps"],
                        "detection_seconds": timing, "conclusion": conclusion}
    save()
    print("本批结束：新图", len(samples), "张；其中返回球类框", found, "张")
    print("距离字段为有限正数：", distance_count, "张；重复旧帧跳过", batch["duplicate_frames"], "次")
    if timing is not None:
        print(f"检测调用耗时：最小{timing['min']:.3f}秒，中位{timing['median']:.3f}秒，最大{timing['max']:.3f}秒")
    print("结论：", conclusion)
    return batch

save()
print("足球类名：", BALL_LABEL, "；准备完成，下一格才开始有球采样。")''')
md('''## STEP 05　有球场景

保持一只球完整可见，机器人和球都不动，运行下一格。程序目标是20张新的、成功完成检测的图像，至少18张返回足球类框。数量达标后，仍需打开结果目录中的标框图片，确认框对应真球。

运行结束后，填写指导表中STEP 05的现场情况。异常或采样不足也保存，不反复重跑来只留最好的一次。''')
code('''with_ball_batch = collect("with_ball")''')
md('''## STEP 06　无球场景

在机器人固定、静止的条件下，把画面内全部足球移走。先运行下一格中的取图，程序会显示当前画面，随后要求输入“无球”；确认画面无足球再输入。若仍有球或画面不是当前场景，直接回车取消，把情况记入指导表。

采20张新图，默认0张返回足球类框；若有误检，图像和框都会保存。此格不会启动机器人运动。''')
code('''try:
    empty_image = robot.get_image(camera_id=CAMERA_ID, img_type="rgb")
    display(empty_image.to_pil())
    if input("确认当前画面无足球，输入“无球”开始采样；其他输入取消：").strip() == "无球":
        without_ball_batch = collect("without_ball")
    else:
        report["without_ball_note"] = "操作员未确认无球，本步未采样"
        print("本步未采样，请记录原因。")
except Exception as exc:
    report["step06_error"] = repr(exc)
    raise
finally:
    save()''')
md('''## STEP 07　保存汇总，本轮结束

前面中途出错也可以运行本格，汇总会保留“未执行”。它不要求先完成后续步骤。复制打印的结果目录到[操作与记录表](足球测试_第1轮_操作与记录.md)，填写现场观察并保存Notebook输出。

结果在另一台机器时，把整个文件夹复制回知识库`实验验证/足球测试结果/`。然后告诉助手“第一轮已记录”。本轮到这里结束，下一轮由助手读完记录后再生成。''')
code('''save()
lines = ["# 足球第1轮自动统计", "", "生成时间：" + report["created_at"],
         "", "Python：" + report["python_path"], "", "SDK：" + report.get("sdk_version", "未知"),
         "", "SDK路径：" + report.get("sdk_path", "未取得"), "",
         f"本轮参数：筛选阈值{CONFIDENCE}；每景{SAMPLE_COUNT}张新图；最多取图{MAX_ATTEMPTS}次；",
         f"有球至少{MIN_BALL_FRAMES}张返回球类框，无球最多{MAX_FALSE_FRAMES}张返回球类框。", "",
         "## 步骤状态", ""]
lines += ["| 步骤 | 自动记录 |", "| --- | --- |",
          "| 环境导入 | " + report.get("imports", "未完成") + " |",
          "| 取到第一张图 | " + ("已取得" if "first_image" in report else "未完成") + " |",
          "| 单帧检测 | " + (str(len(report["single_results"])) + "条结果" if "single_results" in report else "未完成") + " |",
          "| 采用的足球类名 | " + report.get("ball_label", "未填写/未确认") + " |", ""]
for key in ["import_error", "step02_error", "step03_error", "step06_error", "without_ball_note"]:
    if key in report:
        lines.append("- " + key + "：`" + str(report[key]).replace("`", "'") + "`")
lines += ["", "## 单帧返回字段", ""]
for number, item in enumerate(report.get("single_results", []), 1):
    lines += ["- 第" + str(number) + "条：类别`" + item["class_name"] + "`，评分`" + item["confidence"]
              + "`，distance_m原值`" + item["public_fields"].get("distance_m", "没有这个字段") + "`。"]
lines += ["", "其余公开字段供助手读取原始记录.json；现场只需判断是否框中真球。", ""]
for scene, title in [("with_ball", "有球"), ("without_ball", "无球")]:
    batches = [batch for batch in report["batches"] if batch["scene"] == scene]
    lines += ["## " + title + "场景", ""]
    if not batches:
        lines += ["未执行。", ""]
    for number, batch in enumerate(batches, 1):
        summary = batch.get("summary")
        lines += ["第" + str(number) + "批：", ""]
        if summary is None:
            lines += ["中断，已有记录保存在原始记录.json中。", ""]
        else:
            lines += ["| 检查项 | 实际结果 |", "| --- | --- |",
                      "| 完成检测的新图 | " + str(summary["sample_count"]) + "张 |",
                      "| 返回足球类框 | " + str(summary["ball_frames"]) + "张 |",
                      "| 距离为有限正数 | " + str(summary["distance_frames"]) + "张 |",
                      "| 跳过重复旧图 | " + str(summary["duplicate_frames"]) + "次 |",
                      "| 同图多个足球类框 | " + str(summary["multi_ball_frames"]) + "张 |",
                      "| 源时间戳倒退 | " + str(summary["backward_stamps"]) + "次 |",
                      "| 本轮检查结论 | " + summary["conclusion"] + " |", ""]
            timing = summary["detection_seconds"]
            if timing is not None:
                lines += [f"检测调用耗时：最小{timing['min']:.3f}秒，中位{timing['median']:.3f}秒，最大{timing['max']:.3f}秒。", ""]
        if batch["errors"]:
            lines += ["异常：" + repr(batch["errors"]), ""]
lines += ["数量统计仅供本轮检查；正确框选需要人工看图。距离字段有值也不代表位置正确。",
          "", "下一轮：等待助手读取操作记录及本目录后安排。"]
(OUTPUT / "自动统计.md").write_text("\\n".join(lines), encoding="utf-8")
print("请在记录表填写这个结果目录：", OUTPUT.resolve())
print("已保存：自动统计.md、原始记录.json及本轮已有图片。")
print("第一轮结束；填写现场记录后交助手审读。")''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'}, 'purpose': 'soccer_round1_static_detection_v2',
    'robot_executed': False})
nbf.validate(nb)
if OUT.exists():
    old = nbf.read(OUT, as_version=4)
    assert old.metadata.get('purpose') == 'soccer_round1_static_detection_v2'
    assert all(c.get('execution_count') is None and not c.get('outputs')
               for c in old.cells if c.cell_type == 'code'), '已有现场输出，不覆盖'
OUT.write_text(nbf.writes(nb), encoding='utf-8')
print(OUT)
print({'cells': len(cells), 'code_cells': sum(c.cell_type == 'code' for c in cells)})
