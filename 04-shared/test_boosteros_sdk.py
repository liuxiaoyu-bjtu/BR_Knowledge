#!/usr/bin/env python3
"""
BoosterOS SDK 环境检测脚本
============================
功能：
  1. 检测 boosteros 包是否安装及其版本
  2. 连接虚拟仿真机器人，验证连通性
  3. 列出视觉检测模块中所有可用检测模型
  4.（附加）尝试获取一帧 RGB 图像验证视觉管线

使用方式：
  python test_boosteros_sdk.py

前置条件：
  - pip install boosteros          (基础包：连接、控制)
  - pip install "boosteros[brain]" (可选包：Detection 视觉检测)
  - Booster Studio 虚拟仿真环境已启动（或真机已通电联网）

注意：
  SDK 规定同一台机器人应只创建并复用一个 BoosterRobot 实例，
  本脚本全程只创建一次连接并在各测试间传递复用。
"""

import sys
import importlib
import traceback
from typing import Optional, Any


# ============================================================
# 工具函数
# ============================================================

def print_section(title: str) -> None:
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")


def print_ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def print_fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def print_info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def print_warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


# ============================================================
# 测试 1：检测 boosteros 包安装情况
# ============================================================

def test_package_installed() -> dict:
    """检测 boosteros 包是否安装、版本号及子模块可用性"""
    print_section("测试 1：boosteros 包安装检测")

    result = {
        "boosteros_installed": False,
        "version": None,
        "brain_available": False,
        "robots_available": False,
        "types_available": False,
    }

    # 1.1 检测基础包
    try:
        boosteros = importlib.import_module("boosteros")
        result["boosteros_installed"] = True
        version = getattr(boosteros, "__version__", "未知（未设置 __version__）")
        result["version"] = version
        print_ok(f"boosteros 已安装，版本: {version}")
    except ImportError:
        print_fail("boosteros 包未安装")
        print_info("请执行: pip install boosteros")
        return result

    # 1.2 检测 robots 子模块
    try:
        importlib.import_module("boosteros.robots.booster")
        result["robots_available"] = True
        print_ok("boosteros.robots.booster 子模块可用")
    except ImportError:
        print_warn("boosteros.robots.booster 子模块不可用")
        print_info("可能仅安装了部分组件，请重新安装: pip install --force-reinstall boosteros")

    # 1.3 检测 brain 子模块（含 Detection + Speech）
    try:
        importlib.import_module("boosteros.brain")
        result["brain_available"] = True
        print_ok("boosteros.brain 子模块可用（含 Speech + Detection）")
    except ImportError:
        print_warn("boosteros.brain 子模块不可用")
        print_info('如需视觉检测/语音能力，请执行: pip install "boosteros[brain]"')

    # 1.4 检测 types 子模块
    try:
        importlib.import_module("boosteros.types")
        result["types_available"] = True
        print_ok("boosteros.types 子模块可用（数据类型定义）")
    except ImportError:
        print_warn("boosteros.types 子模块不可用")

    return result


# ============================================================
# 测试 2：连接虚拟仿真机器人（返回 robot 实例供后续复用）
# ============================================================

def test_virtual_robot_connection(pkg_info: dict) -> tuple[dict, Optional[Any]]:
    """
    尝试连接虚拟仿真机器人。
    返回 (result_dict, robot_instance)。
    如果连接失败，robot_instance 为 None。
    """
    print_section("测试 2：虚拟仿真机器人连接检测")

    result = {
        "connected": False,
        "robot_info": None,
        "mode": None,
        "joints_count": None,
        "error": None,
    }

    if not pkg_info["boosteros_installed"] or not pkg_info["robots_available"]:
        print_fail("boosteros 或 robots 子模块不可用，跳过连接测试")
        return result, None

    try:
        from boosteros.robots.booster import BoosterRobot
    except ImportError as e:
        print_fail(f"无法导入 BoosterRobot: {e}")
        result["error"] = str(e)
        return result, None

    print_info("正在连接虚拟仿真机器人（超时 10 秒）...")
    print_info("请确保 Booster Studio 虚拟仿真环境已启动")

    try:
        robot = BoosterRobot(timeout=10.0)
        result["connected"] = True
        print_ok("机器人连接成功！")

        # 获取机器人元信息
        info = robot.robot_info
        result["robot_info"] = {
            "manufacturer": info.manufacturer,
            "model": info.model,
            "serial_number": info.serial_number,
            "firmware_version": info.firmware_version,
        }
        print_ok(f"制造商: {info.manufacturer}")
        print_ok(f"型号:   {info.model}")
        print_ok(f"序列号: {info.serial_number}")
        print_ok(f"固件版本: {info.firmware_version}")

        # 获取当前模式
        mode = robot.get_mode()
        result["mode"] = mode
        print_ok(f"当前模式: {mode}")

        # 获取关节数量
        joints = robot.list_joints()
        result["joints_count"] = len(joints)
        print_ok(f"关节数量: {len(joints)}")

        # 列出前 5 个关节名称
        joint_names = [j.name for j in joints[:5]]
        print_info(f"前 5 个关节: {joint_names}")

        return result, robot

    except Exception as e:
        print_fail(f"连接失败: {e}")
        result["error"] = str(e)
        print_info("可能原因：")
        print_info("  1. Booster Studio 虚拟仿真环境未启动")
        print_info("  2. 网络配置不正确（domain_id / DDS 配置）")
        print_info("  3. 机器人固件版本低于 v1.7")
        traceback.print_exc()
        return result, None


# ============================================================
# 测试 3：列出视觉检测可用模型
# ============================================================

def test_detection_models(pkg_info: dict) -> dict:
    """列出 Detection 模块中所有可用的检测模型"""
    print_section("测试 3：视觉检测可用模型列表")

    result = {
        "brain_available": False,
        "models": [],
        "error": None,
    }

    if not pkg_info["boosteros_installed"]:
        print_fail("boosteros 包未安装，跳过检测模型测试")
        return result

    if not pkg_info["brain_available"]:
        print_fail("boosteros.brain 子模块不可用，跳过检测模型测试")
        print_info('请执行: pip install "boosteros[brain]"')
        return result

    try:
        from boosteros.brain import Detection
        result["brain_available"] = True
        print_ok("成功导入 boosteros.brain.Detection")
    except ImportError as e:
        print_fail(f"导入 Detection 失败: {e}")
        result["error"] = str(e)
        return result

    print_info("正在获取可用检测模型列表...")
    try:
        models = Detection.list_models()
        result["models"] = models
        print_ok(f"共找到 {len(models)} 个可用检测模型:")
        print()

        for i, model in enumerate(models, 1):
            # list_models 返回 list[dict]，但做防御性解析
            if isinstance(model, dict):
                model_name = model.get("name", "未知")
                model_id = model.get("id", "未知")
                model_backend = model.get("backend", "未知")
                model_classes = model.get("classes", [])
                model_description = model.get("description", "")

                print(f"  [{i}] 模型名称: {model_name}")
                print(f"      模型 ID:   {model_id}")
                print(f"      推理后端:   {model_backend}")
                if model_classes:
                    print(f"      检测类别:   {model_classes}")
                if model_description:
                    print(f"      描述:       {model_description}")
                print()
            else:
                # 如果返回的不是 dict，直接打印原始值
                print(f"  [{i}] {model}")
                print()

    except Exception as e:
        print_fail(f"获取检测模型列表失败: {e}")
        result["error"] = str(e)
        print_info("可能原因：")
        print_info("  1. boosteros[brain] 依赖未完整安装")
        print_info("  2. 模型文件缺失或路径配置错误")
        traceback.print_exc()

    return result


# ============================================================
# 测试 4（附加）：获取一帧图像验证视觉管线（复用同一 robot 实例）
# ============================================================

def test_image_capture(robot: Optional[Any]) -> dict:
    """使用已连接的 robot 实例获取一帧 RGB 图像"""
    print_section("测试 4（附加）：图像采集验证")

    result = {
        "attempted": False,
        "success": False,
        "image_size": None,
        "save_path": None,
        "error": None,
    }

    if robot is None:
        print_info("机器人未连接，跳过图像采集测试")
        return result

    result["attempted"] = True
    print_info("正在获取一帧 RGB 图像（使用复用的 robot 实例）...")

    try:
        img = robot.get_image(img_type="rgb")
        result["success"] = True
        result["image_size"] = (img.width, img.height)
        print_ok(f"图像获取成功: {img.width} x {img.height}")

        # 保存图像到临时目录
        save_path = "/tmp/boosteros_test_rgb.jpg"
        img.save(save_path)
        result["save_path"] = save_path
        print_ok(f"图像已保存: {save_path}")

    except Exception as e:
        print_fail(f"图像获取失败: {e}")
        result["error"] = str(e)
        print_info("可能原因：")
        print_info("  1. 相机话题未发布（在仿真环境中检查相机节点）")
        print_info("  2. 图像数据尚未就绪（首次获取可能需要等待几秒）")
        print_info("  3. 在终端执行 ros2 topic hz /boostercamera/head/raw/rgb 检查相机话题")
        traceback.print_exc()

    return result


# ============================================================
# 汇总报告
# ============================================================

def print_summary(pkg: dict, conn: dict, det: dict, img: dict) -> None:
    print_section("汇总报告")

    checks = [
        ("boosteros 包安装", pkg["boosteros_installed"]),
        ("boosteros.robots 子模块", pkg["robots_available"]),
        ("boosteros.brain 子模块", pkg["brain_available"]),
        ("boosteros.types 子模块", pkg["types_available"]),
        ("版本号获取", pkg["version"] is not None),
        ("虚拟机器人连接", conn.get("connected", False)),
        ("机器人元信息获取", conn.get("robot_info") is not None),
        ("检测模型列表获取", len(det.get("models", [])) > 0),
        ("图像采集", img.get("success", False)),
    ]

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)

    for label, ok in checks:
        status = "[PASS]" if ok else "[SKIP]"
        print(f"  {status}  {label}")

    print(f"\n  通过: {passed}/{total}")

    print(f"\n  boosteros 版本: {pkg.get('version', '未安装')}")
    if conn.get("robot_info"):
        ri = conn["robot_info"]
        print(f"  机器人型号: {ri['manufacturer']} {ri['model']} (SN: {ri['serial_number']})")
    if det.get("models"):
        model_names = []
        for m in det["models"]:
            if isinstance(m, dict):
                model_names.append(m.get("name", str(m)))
            else:
                model_names.append(str(m))
        print(f"  可用检测模型: {model_names}")
    if img.get("image_size"):
        print(f"  图像尺寸: {img['image_size'][0]} x {img['image_size'][1]}")


# ============================================================
# 主函数
# ============================================================

def main() -> int:
    print_section("BoosterOS SDK 环境检测脚本")
    print(f"  Python 版本: {sys.version}")
    print(f"  Python 路径: {sys.executable}")

    # 测试 1：包安装
    pkg_info = test_package_installed()

    # 测试 2：虚拟机器人连接（返回 robot 实例供后续复用）
    conn_info, robot = test_virtual_robot_connection(pkg_info)

    # 测试 3：检测模型（不依赖 robot 实例，仅依赖 brain 模块）
    det_info = test_detection_models(pkg_info)

    # 测试 4：图像采集（复用同一 robot 实例，避免重复创建连接）
    img_info = test_image_capture(robot)

    # 汇总
    print_summary(pkg_info, conn_info, det_info, img_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
