from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
V = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证'
E = V / '足球测试结果/第4轮完整_20261102_140630_773208'
R = V / '足球SDK完整测试_回读与U7课程边界.md'
raw = json.loads((E / '原始记录.json').read_text(encoding='utf-8'))
onsite = json.loads((TASK / '现场补充.json').read_text(encoding='utf-8'))
base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))

methods = ['SoccerKickManager', 'start', 'stop', 'update_command', 'update_ball']
counts = {}
for name in methods:
    calls = [r for r in raw['calls'] if r['method'] == name]
    counts[name] = {'attempted': len(calls), 'returned': sum(r.get('returned', False) for r in calls),
                    'errors': [r['error'] for r in calls if not r.get('returned')],
                    'return_values': sorted(set(r['return_type'] + ':' + r['return_repr']
                                                for r in calls if r.get('returned')))}
case = raw['cases']['连续球位与活动中指令更新']
last_pose = [r for r in raw['calls'] if r['case'] == '连续球位与活动中指令更新'
             and r['method'] == 'get_odom'][-1]['pose_2d']
measured = case['measured_pose']
distance = math.hypot(last_pose[0] - measured[0], last_pose[1] - measured[1])
fact = {'data_dir': E.relative_to(ROOT).as_posix(), 'created_at': raw['created_at'],
        'sdk': raw['sdk_version'], 'method_counts': counts,
        'case_count': len(raw['cases']), 'continuous_ball_updates': len(case['samples']),
        'active_command_changed': case['active_command_changed'],
        'continuous_odom_displacement_m': distance,
        'continuous_end_reason': case['end_reason'],
        'trial_inputs': {name: {key: row[key] for key in ['measured_ball_xy', 'direction', 'power', 'observation_limit_s']}
                         for name, row in raw['cases'].items() if 'measured_ball_xy' in row},
        'tf_requested': next(r['kwargs'] for r in raw['calls'] if r['method'] == 'get_transform'),
        'tf_returned': raw['transform'], 'physical_observation': onsite,
        'unexpected_api_error_count': 0,
        'notebook_local_outputs_saved': False,
        'conclusion': '构造和全部四方法实际可调用；用户观察到调整和前进，但完整踢球尚未证实；视觉米制球位仍未建立。'}
assert {k: (v['attempted'], v['returned']) for k, v in counts.items()} == {
    'SoccerKickManager': (1, 1), 'start': (5, 5), 'stop': (6, 6), 'update_command': (9, 7), 'update_ball': (7, 6)}
assert all(r.get('expected_ValueError') for r in raw['cases']['停用参数检查']['checks'])
assert all('ValueError' in err for x in counts.values() for err in x['errors'])
assert len(case['samples']) == 2 and case['active_command_changed'] is True
assert raw['control_uncertain'] is False
(TASK / '第4轮数据核对.json').write_text(json.dumps(fact, ensure_ascii=False, indent=2), encoding='utf-8')

def observed(key):
    return onsite.get(key) or '程序无法确认，现场补充尚未提供；不要求重做整轮测试'

stop_note = observed('stop_observation')
state_note = observed('current_robot_state')
origin_note = observed('measurement_origin')
stationary_note = observed('far_ball_stationary')
trial3 = onsite['trials']['改力度与重启']

report = f'''# 足球SDK完整测试回读与U7课程边界

审读日期：2026-11-02。依据为用户提交的`第4轮完整_20261102_140630_773208`五份原始文件，以及本轮对话补充的现场回忆。机器人为K1 060100，SDK 1.2.2，固件完整返回为1.8.1.2-release-02884-2026-10-15。原始JSON和本机源码保持原样。

## 1. 当前结论

**管理器构造和全部四个公开方法均已实际调用，当前没有非预期SDK调用异常。机器人有行走、侧移或后退等响应，尚未证实完整踢球。** 基线中用户明确观察到机器人尚未接近到球前，没有踢球动作。其余两项只报告了调整表现，没有足够证据写成已踢出。

这些结果可以结束按方法逐项探查，回到课程边界修订。课程可讲足球识别、米制坐标输入、方向/力度参数、控制启停与重复运行。现有证据不支持把“自动视觉定位、连续追球、完成踢球或进球”同时设成学生必达成果。

手量球位下的运动响应不能证明视觉定位已解决；单次球位、两秒观察未完成踢球，也不能证明SDK不能踢球。当前应准确描述已经验证的输入与行为，避免由课程标题先承诺完整自动踢球。

## 2. 程序已经确认的事实

| 项目 | 实际记录 | 能据此确认什么 |
| --- | --- | --- |
| 构造 | 1次调用、1次返回管理器对象 | 对象可创建；第3轮构造前模式读取报错不代表构造不可用 |
| start | 5次调用、5次返回None | 启动路径实际执行，包括同对象stop后的再次调用 |
| stop | 6次调用、6次返回None | 关闭调用实际返回；物理停稳另以现场观察判断 |
| update_command | 9次调用、7次返回None、2次ValueError | 有效参数可调用；力度0、11被范围检查拒绝 |
| update_ball | 7次调用、6次返回None、1次ValueError | 有效米制输入可调用；非数值x被拒绝 |
| 连续更新 | 活动中2次球位输入返回后，direction由0改为0.2、power由1改为2，也返回None | 已覆盖活动中的更新路径；没有证明无限时跟球或任意更新频率都可用 |
| 远球提前结束 | odom平面位移约{distance:.3f}米，触及本次0.15米边界后stop | 里程计记录到机身运动，程序按行进限制结束；此值不是卷尺验证的真实位移 |
| 三次近球场景 | 各发送1次当前机身球位，分别start、设置指令、等待约2秒、stop | 已覆盖新球位和新指令的重新设置；没有球已踢出的自动判定 |
| 返回语义 | 四方法成功时都是None | None表示方法返回，不能赋予任务句柄、完成或进球语义 |
| 模式 | 开始原始模式kWalking；stop后公开模式仍为walk、原始模式为kSoccer | 公开模式有别名，stop不等于退出足球模式；仅get_mode()==walk不足以区分普通行走和足球状态 |
| TF | 本轮取得有限4×4矩阵 | 第3轮时间错误没有阻止本次读取；不再判定TF接口整体不可用 |

三项ValueError来自主动提交的无效输入，均符合本次预期。不能将9→7和7→6的计数当作两项接口存在随机故障。

## 3. 现场回忆与解释

| 场景 | 输入 | 用户描述 | 本次可作出的判断 |
| --- | --- | --- | --- |
| 基线 | 球位(1.2,-0.3)米，direction=0，power=1 | {onsite['trials']['基线试踢']} | 有前进与向球侧调整，用户明确未观察到踢球；初始距离与两秒窗口不保证已到可踢位置 |
| 改方向 | 球位(0.5,-0.3)米，direction=0.25，power=1 | {onsite['trials']['改方向与重启']} | 有右跨调整；球仍在右侧，向右调整不等于踢球方向参数失效。球前位置、初始朝向均未与基线保持一致 |
| 改力度 | 球位(0.4,0)米，direction=0，power=2 | {trial3} | 有后退响应。原文“几乎左右移动”保留，不自行补字；仅凭后退不能判断力度是否生效，也未明确球是否踢动 |

三项初始球位不同，不能归因“方向一改就右跨”或“力度一改就后退”；底层可能先调整到适合踢球的位置，但本次没有底层状态或完成事件证据，不能把这一解释写成已经验证的机制。当前不追加参数性能比较测试，也不设置精确方向/力度控制的学习目标。

本次辅助代码对近球只发一次球位，等待两秒后停止；远球只更新两次就因行进限制提前停止。它验证了接口和部分控制响应，未验证完整持续供数下的终端踢球行为。这是本次试验范围，应在结论中保留，不能用“全部方法返回”代替“整条应用成功”。

停止后的现场表现：{stop_note}

当前机器人状态：{state_note}

量法与原点：{origin_note}

远球是否始终静止：{stationary_note}

## 4. 球位和TF的当前边界

前3轮确认检测返回Ball框，但该批distance_m为空；深度和相机内参可读。现有公开管理器类不自动识别或测量球，update_ball需要外部提供当前机身米制x/y。源码中的odom与8米虚拟目标用来维护踢球方向参考，不能当作真实球或球门定位。

本次TF请求为source=head_color_optical_frame、target=trunk，返回对象字段却写source=trunk、target=head_color_optical_frame。RosAdapter实际执行`lookup_transform(target, source, ROSTime())`，按ROS惯例对应将source点表达在target下；其文档文字与返回标签存在需要核对的差异。本轮只登记矩阵读取成功，不根据标签直接正用或求逆给出球位。

深度单位、无效值、RGB/深度配准和足球上取值位置、控制原点仍不足以形成已验证的视觉米制球位。当前不采用dtype猜单位，也不要求学生从零写单应矩阵、凸包与动态补偿。已有ball_position.py继续作为未选定候选，不能因SDK控制已返回就给它补上验证结论。

## 5. 对课程的具体修订建议

以下是基于现有证据的设计建议，尚未改学生Notebook或登记确认。现场补充只影响实际效果的叙述，不改变“接口可调用、视觉米制输入未建立”的证据结论。

| 位置 | 保留 | 建议删改 |
| --- | --- | --- |
| U7-L2 | Ball识别、图像坐标与机身米制坐标、四方法、None语义、参数检查、短时控制与退出 | 标题与目标改为足球感知与踢球控制接口；移出课内4点拟合、3点误差核对和从零标定。实验先比较检测数据和实测坐标，再由教师提供本次有效球位；学生记录调整与调用，不承诺完成踢出 |
| U7-L3 | 播报期间检测更新、线程/锁/退出，记录是否检出与像素变化 | 检测和播报保持静态，不把像素记录改称米制球位；不将本次教师测试的odom换算扩展成线程课必修 |
| U7-L4 | 观察→播报→重新确认→行为→退出，SDK返回与现场表现分开 | 足球分支在播报后重新确认场地和当前球位来源；只有已验证条件满足才进入有限控制。删除“只要检测到框并有verified就可连续视觉试踢”的暗示；有球框不能自动替代当前米制球位 |
| U8足球分支 | 需求、接口、角色分工、整合、彩排与答辩证据 | 需求限于已验证条件下的感知、播报、人工确认输入与有限控制展示。自动找球、追球或进球不能作默认验收项；需要完整踢球展示时，另有经过验证的能力实现后才纳入 |
| x_lab附件 | 简单选球、播报、资源与退出管理 | 定位来源与控制分开；撤除标定文件作为必修控制入口。测试里的静止球odom辅助不直接移进学生主线；在课程重构时再改实现 |

### 现有耗时条件必须随设计修正

U7-L2代码及x_lab/flows.py把取图与检测处理超过0.8秒作为退出条件；第1轮该设备检测中位用时约2.2～2.4秒。依这批数据，旧条件可能在下发球位之前就阻止控制。这是课程条件与设备记录不匹配，不能误判成管理器不可调用。

当前不把“0.8秒改大”当作已经解决运动数据时效。课程收缩为静态检测分析与有效球位控制后，应分别写出处理耗时、记录存放时长和实际供数条件；未验证视觉控制数据链前，不用一个任意阈值将它包装成运动条件。

### 如何结束本次审核

方法清单已覆盖，无需再补一轮只为证明方法存在。现有证据足以提出上述课程收缩方案；现场效果由本轮回忆补录，记不清的部分保留未知。接下来按方案修订课程，而不是把测量精度、检出率或参数效果比较继续扩为前置验收。

若以后明确要求课程必须完成实际踢出，需要补的是“有效球位如何持续供给、完整控制如何达到实际踢出”的具体应用条件，不是重新遍历四方法。本次不自动生成新测试Notebook。

## 6. 文件与记录

- [第4轮操作与已回填记录](足球测试_第4轮_操作与记录.md)
- [程序自动汇总](足球测试结果/第4轮完整_20261102_140630_773208/能力汇总.md)
- [原始调用JSON](足球测试结果/第4轮完整_20261102_140630_773208/原始记录.json)
- [本机管理器实现](足球测试结果/第4轮完整_20261102_140630_773208/SoccerKickManager_本机实现.txt)

知识库中的第4轮Notebook仍为未保存输出、BALL_X/Y未填写的模板。实际测量值和调用次序以提交的JSON为准，不反向伪造Notebook执行输出。用户未填原表并不影响自动记录中的证据；助手已将可确认项与对话回忆回填。
'''
assert not R.exists(), '已有审读报告，先检查后定向补充，不能整份覆盖'
R.write_text(report, encoding='utf-8')

guide_path = ROOT / base['guide']
guide = guide_path.read_text(encoding='utf-8-sig')
baseline = (TASK / 'before' / base['guide']).read_text(encoding='utf-8-sig')
assert guide == baseline, '测试表出现新的用户修改，先保留'
guide = guide.replace('# 足球SDK完整能力验证：一次现场测试与课程决策',
    '# 足球SDK完整能力验证：一次现场测试与课程决策\n\n> **本轮已回读（2026-11-02）**：构造与全部四方法实际调用完成；三项ValueError为预期参数检查。自动事实与用户现场回忆已由助手填入第4、6部分。接口返回和运动响应已经确认，完整踢球尚未证实。[详细课程边界](足球SDK完整测试_回读与U7课程边界.md)。无需重新填写整表。', 1)
start = guide.index('## 4. 现场记录（请填写）')
end = guide.index('## 5. 结果怎样决定U7内容', start)
record = f'''## 4. 已回填记录（程序事实与现场补充分列）

| 项目 | 记录与依据 |
| --- | --- |
| 日期/测试人/观察者 | 2026-11-02 14:06～14:16，TESTER=xy（JSON）；观察者姓名未记录 |
| 机器人、SDK、模式 | K1 060100、SDK 1.2.2；连接时公开walk、原始kWalking；固件1.8.1.2-release-02884-2026-10-15 |
| 卷尺测量原点及量法 | {origin_note} |
| 02构造/里程计/TF | 构造返回管理器对象；odom可读；TF取得有限4×4矩阵，但返回source/target标签与请求顺序相反，几何方向不直接照标签套用 |
| 03启停 | start、stop均返回None；现场启停表现另以用户补充为准 |
| 04参数与ValueError | 有效输入正常返回；力度0/11、非数值x分别报预期ValueError，共3项；finally中的stop返回None |
| 05持续更新 | 实测输入(1.3,-0.3)米，update_ball正常2次后活动中改direction=0.2/power=2，正常返回；odom位移约{distance:.3f}米触发0.15米边界后stop返回 |
| 05球是否静止及现场表现 | {stationary_note} |
| 06基线试踢 | 输入(1.2,-0.3)米、direction=0/power=1，仅1次球位；用户：{onsite['trials']['基线试踢']} |
| 07改方向与重启 | 输入(0.5,-0.3)米、direction=0.25/power=1；start、指令、球位和stop均返回；用户：{onsite['trials']['改方向与重启']} |
| 08改力度与重启 | 输入(0.4,0)米、direction=0/power=2；各调用正常；用户原文：{trial3} |
| stop返回与实际停稳 | 自动记录6次stop均返回None；{stop_note} |
| 哪些步骤执行或跳过 | JSON中7类场景均有记录，构造和全部4方法已实际调用；远球因预设行进边界提前结束，非异常跳过 |
| 参数/代码情况 | 本地Notebook未保存执行输出且仍为None参数模板；JSON留存4组实际球位和2秒窗口。未取得现场Notebook，不能断言全部代码未改 |
| 最终恢复与当前状态 | {state_note} |
| 结果目录 | 足球测试结果/第4轮完整_20261102_140630_773208/（五份文件） |

以上程序项由助手读取原始文件填写，现场描述来自本轮对话。原始JSON、自动汇总和源码未改；不把未提供的现场信息填成“正常”。

'''
guide = guide[:start] + record + guide[end:]
start = guide.index('## 6. 助手回读与课程决策（待记录后填写）')
guide = guide[:start] + '''## 6. 助手回读与课程决策

| 项目 | 结论 |
| --- | --- |
| 构造与四方法 | 全部实际调用；有效输入返回，三个无效输入按预期ValueError，不属于SDK意外失败 |
| 活动中指令/球位更新 | 已有2次球位与1次活动中方向/力度变更；正常返回、odom记到运动，完整持续跟球未验证 |
| 试踢与重启 | 同对象启停复用可调用；用户观察到前进、侧移、后退；基线明确没有踢球，完整踢出未证实 |
| 参数效果 | 初始球位分别(1.2,-0.3)、(0.5,-0.3)、(0.4,0)，无法将动作差异单独归因方向或力度，不设精确效果学习成果 |
| 视觉球位 | 二维检测可用；深度/内参/TF数据可读，仍没有经过核实的完整视觉米制球位供数 |
| U7-L2 | 建议转为足球感知与控制接口、已知球位的有限控制；移出从零矩阵标定，不把踢出设为已验证目标 |
| U7-L3/L4与U8 | L3保持检测与播报并发；L4/U8只整合已证实条件，区分球框、有效米制输入、返回与实际结果 |
| 其他须修正 | 旧0.8秒处理门槛与第1轮约2秒检测不匹配；公开walk与原始soccer需区分；TF返回标签不能直接推坐标转换方向 |
| 后续 | [详细审核与课程删改建议](足球SDK完整测试_回读与U7课程边界.md)。停止按方法拆轮次，不自动生成新测试；当前未改学生Notebook或登记整课通过 |
'''
guide_path.write_text(guide, encoding='utf-8')
print('已回填自动记录和现场回忆，生成课程边界报告；原始证据和Notebook保持原样。')
