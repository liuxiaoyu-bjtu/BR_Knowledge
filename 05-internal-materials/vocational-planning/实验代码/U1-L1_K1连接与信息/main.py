"""
U1-L1：认识 K1 — 首次连接与信息探索
==========================================
实验目标：连接 K1 机器人，通过 SDK 接口读取并打印
机器的身份信息、关节列表、预定义动作库和当前状态。

⚠️ 本脚本不涉及任何机器人运动——只读操作，安全无害。
"""

from boosteros.robots.booster import BoosterRobot


def print_section(title, emoji=""):
    """打印章节分隔线"""
    print(f"\n{'='*50}")
    print(f" {emoji} {title}")
    print(f"{'='*50}")


def main():
    # -------------------------------------------------
    # 步骤 1：连接机器人
    # -------------------------------------------------
    print_section("正在连接 K1 机器人...", "⏳")

    try:
        robot = BoosterRobot()
        print("机器人连接成功！")
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        print("排查建议：")
        print("  1. K1 机器人是否已开机？")
        print("  2. 电脑与 K1 是否连接同一 WiFi？")
        print("  3. 执行 'pip install boosteros' 确保 SDK 已安装")
        return

    # -------------------------------------------------
    # 步骤 2：读取机器人身份信息
    # -------------------------------------------------
    print_section("K1 机器人身份信息", "🤖")

    info = robot.robot_info
    print(f"  制造商：    {info.manufacturer}")
    print(f"  型号：      {info.model}")
    print(f"  序列号：    {info.serial_number}")
    print(f"  固件版本：  {info.firmware_version}")
    if info.extra:
        print(f"  额外信息：")
        for key, val in info.extra.items():
            print(f"    {key}: {val}")

    # -------------------------------------------------
    # 步骤 3：浏览关节清单
    #   JointInfo 结构：name / limits(min,max) / max_torque / max_velocity
    # -------------------------------------------------
    print_section("K1 关节清单", "🦾")

    joints = robot.list_joints()
    print(f"  关节总数：{len(joints)}\n")
    print(f"  {'关节名':<35} {'限位范围 (min/max rad)':<32} {'最大力矩':<12} {'最大速度'}")
    print(f"  {'-'*35} {'-'*32} {'-'*12} {'-'*12}")

    for j in joints:
        limits_str = f"{j.limits.min:6.2f} / {j.limits.max:6.2f}"
        torque_str = f"{j.max_torque:6.1f}"
        vel_str = f"{j.max_velocity:6.2f}"
        print(f"  {j.name:<35} {limits_str:<32} {torque_str:<12} {vel_str}")

    # -------------------------------------------------
    # 步骤 4：浏览预定义动作库
    #   ActionInfo 结构：id / type / duration / interruptible
    # -------------------------------------------------
    print_section("K1 预定义动作库", "🕺")

    actions = robot.list_actions()
    print(f"  预定义动作总数：{len(actions)}\n")
    print(f"  {'动作 ID':<25} {'类型':<22} {'时长(秒)':<12} {'可中断'}")
    print(f"  {'-'*25} {'-'*22} {'-'*12} {'-'*10}")

    for a in actions:
        dur_str = f"{a.duration:.1f}" if a.duration is not None else "-"
        interrupt_str = "✓" if a.interruptible else "✗"
        print(f"  {a.id:<25} {a.type:<22} {dur_str:<12} {interrupt_str}")

    # -------------------------------------------------
    # 步骤 5：查看当前状态
    # -------------------------------------------------
    print_section("当前状态总结", "📊")

    mode = robot.get_mode()
    print(f"  当前模式：    {mode}")
    print(f"  关节数量：    {len(joints)}")
    print(f"  预定义动作数：{len(actions)}")

    # 模式说明
    mode_desc = {
        "damping": "零力矩模式——关节松弛，可自由拖拽",
        "prepare": "准备模式——机器人站立并保持姿态",
        "walk": "行走模式——可下发速度控制指令",
        "custom": "自定义模式——用于高级控制场景",
    }
    print(f"  模式说明：    {mode_desc.get(mode, '未知模式')}")

    # -------------------------------------------------
    # 步骤 6（扩展探索）
    #   取消下方注释即可运行
    # -------------------------------------------------
    """
    print_section("扩展探索：关节实时角度", "🔍")
    joint_states = robot.get_joint_states()
    print(f"\n  当前关节状态（前 10 个关节）：")
    print(f"  {'关节名':<35} {'位置 (rad)'}")
    print(f"  {'-'*35} {'-'*12}")
    for name in joint_states.names[:10]:
        js = joint_states.get_joint(name)
        print(f"  {name:<35} {js.position:10.4f}")
    """

    print(f"\n{'='*50}")
    print(" 🎉 实验完成！你已经认识了 K1 的基本信息和身体结构。")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
