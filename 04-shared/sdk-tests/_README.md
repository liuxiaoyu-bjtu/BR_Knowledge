---
title: SDK 测试脚本说明
category: sdk-tests
tags: [SDK, 测试, BoosterOS, 视觉, 环境验证]
status: completed
last_updated: "2026-08-13"
---

# SDK 测试脚本说明

本目录集中管理 BoosterOS SDK 相关的**测试与验证脚本**，供课程设计、开发验证、环境巡检复用。

> 📌 **定位**：SDK 测试脚本是技术平台能力的技术验证产物，直接服务 `01-booster-kb/07-tech-platform/booster-sdk.md` 文档中记录的 API。后续新增 SDK 测试/验证脚本统一存放于本目录。

## 📂 文件清单

| 文件 | 测试内容 | 覆盖接口 | 运行方式 |
|------|---------|----------|----------|
| `probe_detection_classes.py` | **模型类别探测**：验证指定检测模型实际输出类别（`default`=COCO 80 类，清单见 booster-sdk.md §3.3） | `Detection(model)` / `get_image()` / `detect()` / `plot()` | `python probe_detection_classes.py [模型ID]`（默认 `default`） |
| `test_boosteros_basic.py` | **快速验证（精简版，日常首选）**：连接 → 图像 → 模型列表（完整 JSON）→ 一次检测 → 结果图 | `BoosterRobot()` / `robot_info` / `get_image()` / `Detection.list_models()` / `detect()` / `plot()` | `python test_boosteros_basic.py` |
| `test_boosteros_sdk.py` | SDK 环境检测（4 项测试，含失败降级与汇总报告） | 包安装检测、机器人连接、`Detection.list_models()`、RGB 图像获取 | `python test_boosteros_sdk.py` |
| `test_vision_capabilities.ipynb` | 视觉能力全量测试（4 类 17 项） | `get_image()` / `get_camera_info()` / `subscribe_image()` / `Detection` 系列 / 视觉数据类型 / `set_head_angle()` / `get_transform()` / `SoccerKickManager` | Jupyter Notebook 逐 cell 运行 |
| `probe_depth_distance.py` | **深度图测距标定探针**（替代已删除的 `probe_distance_m.py`）：源码确认标准 `detect()` 的 `distance_m` 永远为 `None`，本脚本改为读深度图在 bbox 区域取深度中位数实现测距，并输出 `to_dict()` + 标定行 + 深度图 dtype/编码 | `BoosterRobot()` / `Detection(model)` / `get_image("depth")` / `to_numpy()` / `detect()` / `bbox` | `python probe_depth_distance.py [模型ID] [真实距离m]`（如 `python probe_depth_distance.py default 1.0`） |
| `probe_distance_source.py` | **源码探源**：定位 boosteros 包并递归搜索 `distance_m`，已确认全包仅 `types/vision_data.py` 一处定义、零赋值 | 包路径定位 + 源码递归搜索 | `python probe_distance_source.py` |

> **版本分工**：`test_boosteros_basic.py` 为无防御包装的冒烟验证，验证基本功能是否通；`test_boosteros_sdk.py` / `.ipynb` 为完整巡检与全量验收，含失败降级和汇总报告。日常开发优先跑精简版。

## 🧪 使用前提

- 安装 `boosteros`（基础包）：`python3 -m pip install boosteros`
- 视觉检测需安装 `boosteros[brain]`：`python3 -m pip install "boosteros[brain]"`
- 机器人连接测试需 Booster Studio 虚拟仿真已启动，或连接 K1/T1 真机
- Python >= 3.10，机器人固件 >= v1.7

## 📐 设计约定

1. **实例复用**：全程只创建一个 `BoosterRobot` 实例（SDK 硬性要求：重复创建可能导致指令冲突）
2. **失败降级**：每项测试独立错误处理，缺依赖时标记 `[SKIP]` 而非中断整体
3. **安全兜底**：涉及运动控制（如 `set_head_angle`）的测试含安全回退逻辑

## 🔗 关联文档

- 技术依据：[BoosterOS SDK V1.0](../../01-booster-kb/07-tech-platform/booster-sdk.md)
- 应用框架：[Booster Agent Framework](../../01-booster-kb/07-tech-platform/booster-agent-framework.md)
- 开发环境：[Booster Studio](../../01-booster-kb/07-tech-platform/booster-studio.md)

## 📝 维护规则

- 新增 SDK 测试脚本时在本清单追加一行
- 测试覆盖的接口更新时同步更新上表
- SDK 版本升级后重新跑一遍全量测试，结果记录到本目录或更新对应知识文档
