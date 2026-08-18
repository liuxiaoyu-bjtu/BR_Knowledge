"""
黑盒探测：确认某个检测模型能识别哪些目标类别。

用法：每次把一个已知物体放到机器人相机前，运行本脚本，
记录输出的 class_name，即可逐步确定模型的能力范围。

例如按顺序探测：人 → 杯子 → 瓶子 → 手机 → 椅子 → 球 → 书本 …
```
python probe_detection_classes.py default
```

📌 已知结论（2026-08-14 实测确认）：
- `default` 模型 = COCO 80 类通用检测（class_id 0-79），
  完整类别表见知识库 `01-booster-kb/07-tech-platform/booster-sdk.md` §3.3
- `person` 模型 = 人物检测（单一类别）
- `soccer` 模型 = RoboCup 场景检测（足球/球门/场线等）

本脚本用于验证模型在此环境下实际输出是否符合预期，
不再用于"从零摸索 default 模型的类别范围"。
"""
import sys
from boosteros import BoosterRobot
from boosteros.brain import Detection

model_id = sys.argv[1] if len(sys.argv) > 1 else "default"

robot = BoosterRobot()                          # 连接虚拟仿真机器人
detector = Detection(model=model_id)            # 加载指定检测模型

img = robot.get_image(img_type="rgb")           # 取一帧图像
results = detector.detect(img, confidence=0.3)  # 降低置信度阈值，尽量多出目标

print(f"[模型 {model_id}] 检测到 {len(results)} 个目标：")
for r in results:
    print(f"  class={r.class_name:<12} id={r.class_id}  conf={r.confidence:.2f}")

detector.plot(img, results).save("detect_result.jpg")  # 结果图，肉眼对照
