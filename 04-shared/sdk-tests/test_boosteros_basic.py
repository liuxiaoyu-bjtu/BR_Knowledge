#!/usr/bin/env python3
"""BoosterOS SDK 快速验证脚本（精简版）

顺序执行 5 步，任何一步失败直接抛异常终止——不做 try/except 防御包装，只验证功能通不通。
运行前提:
  pip install "boosteros[brain]"
  Booster Studio 虚拟仿真已启动（或真机已通电联网）
"""
import json

from boosteros.brain import Detection
from boosteros.robots.booster import BoosterRobot

# 1. 连接机器人
robot = BoosterRobot()
print("[1] 连接成功:", robot.robot_info.model, "SN:", robot.robot_info.serial_number)

# 2. 获取一帧 RGB 图像
img = robot.get_image(img_type="rgb")
print("[2] 图像获取成功:", img.width, "x", img.height)

# 3. 列出全部检测模型（完整 JSON，重点看 dict 里有无 classes/categories/labels/description 字段）
models = Detection.list_models()
print("[3] 检测模型 (%d 个):" % len(models))
for model in models:
    print("   ", json.dumps(model, ensure_ascii=False))

# 4. 用默认模型跑一次目标检测
detector = Detection(model="default")
results = detector.detect(img)
print("[4] 检测结果:", [(r.class_name, round(r.confidence, 2)) for r in results])

# 5. 绘制检测框并保存
detector.plot(img, results).save("detect_result.jpg")
print("[5] 结果图已保存: detect_result.jpg")
