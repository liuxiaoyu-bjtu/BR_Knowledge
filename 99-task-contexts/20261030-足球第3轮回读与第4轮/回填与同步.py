from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
V = C + '/实验验证/'
G4 = '足球测试_第4轮_操作与记录.md'
N4 = '足球测试_第4轮_管理器创建与启停.ipynb'

def links(prefix):
    return f'[第4轮操作与记录]({prefix}{G4})、[第4轮代码]({prefix}{N4})'

def replace_note(text, prefix, updated):
    found = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(found) == 1, (prefix, len(found))
    return text.replace(found[0], updated, 1)

SUMMARY = ('第3轮TF实际报ExtrapolationException，查询时间早于缓存首帧约16.47毫秒，未取得矩阵；'
           '管理器构造前的get_mode报错，SoccerKickManager(robot)尚未执行，原“创建失败”需按阶段校正。')

ASSISTANT = '''## 4. 助手审读结论（2026-10-30）

| 项目 | 结论 |
| --- | --- |
| 数据目录 | `足球测试结果/第3轮_20261030_183245_679424/`，原始JSON、自动汇总和三份本机实现，共5份；原文件保留 |
| 环境 | K1 060100，SDK 1.2.2、Python 3.10.12；本轮连接时公开模式为walk；完整固件仍为1.8.1.2-release-02884-2026-10-15 |
| TF请求 | `head_color_optical_frame → trunk`，两个名称均在实际列表；请求已执行 |
| TF实际结果 | JSON记录ExtrapolationException：请求时间1793356373.951769，缓存最早1793356373.968237，早约16.47毫秒；没有transform或matrix字段，尚未取得矩阵。人工表中“矩阵”保留原填，当前按原始报错判定 |
| “创建失败”的实际发生位置 | STEP 04先执行`report["mode_before_create"] = str(robot.get_mode())`。JSON没有mode_before_create，也没有manager_type；错误为Failed to get robot mode。赋值右侧报错，后面的构造函数未执行 |
| 对测试代码的纠正 | 上轮把创建前读取模式与构造放在同一try块，错误被统一记作“创建失败”。这是测试程序归因不准确，当前应登记“前置模式读取失败，构造未执行”，不能推断SDK构造不可用 |
| 已读实现 | 足球管理器完整类、BoosterRobot.get_image与get_transform。后两者继续转给ros_adapter；没有给出深度单位和配准证明 |
| 下一轮 | [第4轮操作与记录](足球测试_第4轮_操作与记录.md)、[第4轮代码](足球测试_第4轮_管理器创建与启停.ipynb)：构造独立记录，成功后实际start/stop，再用同一对象重启；TF最多三次复查，保存完整堆栈 |

### 本机源码带来的结论

1. `SoccerKickManager(robot)`初始化发布通道和内部参考；这个类的构造体不调用start，也不负责识别或测量球。它还调用`robot._get_model()`，该内部调用是否可用要以实际构造和堆栈判断。
2. `start()`进入原始soccer模式并启用VisualKick；`stop()`关闭VisualKick、清空当前球位及虚拟目标，但没有切回prepare或walk的代码。因此，公开模式名、原始模式和现场姿态应分开记录。
3. `update_command(direction, power)`读取里程计，把所给方向转换为odom中的虚拟固定目标点，内部假设目标距离8米。这是管理器的方向参考，不是测出的真实球门位置。
4. `update_ball(x, y)`仍要接收当前机器人坐标系中的米制球位，读取里程计保存该次参考；启用控制且目标参考齐全时发布Kick消息。更新方向时会把保存的旧球位按里程计变到当前机身参考；本类没有自动从图像得到球位。
5. `update_command`方向相对调用时机器人朝向，单位rad、向左为正，力度范围1～10。持续重复调用相同相对方向会按当时朝向重新建立目标，不应无理由在每帧里刷新方向。后续测试分别检查方向、力度与球位更新。

这些是本机SDK 1.2.2的实现证据，不能替代实际运行。当前尚未实际创建管理器，也未调用start、stop、update_command或update_ball。第4轮先补构造与启停；方向/力度更新、持续球位更新、实际踢球和带指令重启仍全部保留。

### 对课程的影响

“管理器内部已有坐标转换”仅涵盖里程计参考与踢球目标方向，不表示已经提供足球世界位置查询。外部球位来源仍待核实；深度单位、配准、相机到控制原点的对应未明确，暂不要求学生开展像素—米标定。本轮不改学生Notebook、生成器或x_lab控制代码，不登记整课确认。
'''

def change(name, text):
    if name == 'AGENTS.md':
        text = replace_note(text, '> **足球SDK能力审核（2026-10-30）**',
            '> **足球SDK能力审核（2026-10-30）**：' + SUMMARY + '当前执行' + links(V)
            + '：独立实际构造，成功后start/stop与同对象重启，TF有限复查。'
            '本机类用odom固定虚拟踢球目标，仍需外部米制球位；方向/力度、持续球位更新及实际踢球后续逐项测试。'
            '只核实课程能力，深度单位/配准与控制原点待核，未选定自编标定，未新增阶段确认。下方早期安排保留历史含义。')
    elif name == 'INDEX.md':
        text = replace_note(text, '> 足球SDK能力 / 深度mono16',
            '> 足球SDK能力 / TF时间外推 / 创建前模式读取 / start-stop重启 / odom虚拟目标：'
            f'[第3轮回读]({V}足球测试_第3轮_操作与记录.md)、' + links(V)
            + '（2026-10-30；TF报时间错误，构造尚未执行；第4轮补构造与实际启停，方向/力度和球位更新仍待测试）。')
    elif name == 'CHANGELOG.md':
        heading = '# 更新日志'
        assert text.count(heading) == 1
        note = ('## 2026-10-30 · 足球第3轮回读与实际启停测试\n\n' + SUMMARY
                + '人工记录与五份原始文件保留，在助手区说明差异。本机源码证实管理器用odom维护虚拟目标方向，'
                '外部仍须提供当前机身米制球位；没有自动球位识别/测量。\n\n' + links(V)
                + '已生成：模式读取独立、构造实际调用、完整堆栈；成功后实际启停与同对象重启，每次finally尝试stop；'
                'TF至多三次复查。方向/力度更新、持续球位与实际试踢保留后续，不设性能验收。'
                '未改学生Notebook或控制附件，未运行机器人或推进课程Phase。本地提交，用户自行推送。')
        text = text.replace(heading, heading + '\n\n' + note, 1)
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = replace_note(text, '> **足球测试最新状态（2026-10-30）**',
            '> **足球测试最新状态（2026-10-30）**：' + SUMMARY + links('03_X课程项目/实验验证/')
            + '补实际构造、start/stop与同对象重启；方向/力度和持续球位仍待后续，按能力逐轮推进。下方此前状态为历史记录。')
    elif name.endswith('/X课程当前进度.md'):
        text = replace_note(text, '> **足球前置能力测试（2026-10-30）**',
            '> **足球前置能力测试（2026-10-30）**：' + SUMMARY + links('实验验证/')
            + '待执行，补实际构造、启停与重启；前3轮结果不代表U7/U8整课①②通过。下方早期测试状态保留历史含义。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = replace_note(text, '> **足球测试范围（2026-10-30）**',
            '> **足球测试范围（2026-10-30）**：第3轮TF有时间外推错误，管理器构造被前置模式读取挡住，尚未执行。'
            + links('实验验证/') + '将独立构造并实际启停、同对象重启。之后继续方向/力度更新、持续米制球位更新、'
            '实际踢球及带指令重启；不扩为性能验收，不据部分接口测试登记整课确认。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = replace_note(text, '> **足球SDK前置核查（2026-10-30）**',
            '> **足球SDK前置核查（2026-10-30）**：检测、深度和内参可读；第3轮TF时间外推，管理器尚未进入实际构造。'
            '本机源码只负责odom虚拟目标方向及控制，球位仍须外部提供。' + links('实验验证/')
            + '补构造与启停；定位路线继续待核，不提前给学生增加标定任务。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = replace_note(text, '> **本机能力进展（2026-10-30）**',
            '> **本机能力进展（2026-10-30）**：第3轮TF时间外推，管理器构造前模式读取失败，构造尚未执行。'
            '本机类用odom固定虚拟目标，仍需外部米制球位。' + links('../../实验验证/')
            + '补实际构造、启停与重启；方向/力度与球位更新后续测试，固定映射仍为候选。下方早期状态保留历史含义。')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        text = replace_note(text, '> **足球当前步骤（2026-10-30）**',
            '> **足球当前步骤（2026-10-30）**：第3轮已回读，TF时间外推、构造被前置模式读取挡住，尚未创建。'
            '当前执行' + links('') + '，独立构造并测试启停/重启。方向/力度、持续球位与实际踢球仍待后续；'
            '只核实课程SDK能力，下方早期性能/标定安排不作为当前任务。')
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        text = replace_note(text, '> **足球能力进展（2026-10-30）**',
            '> **足球能力进展（2026-10-30）**：第3轮TF时间外推，管理器尚未进入构造调用。当前'
            + links('') + '补实际构造、启停与同对象重启；方向/力度和球位更新仍待实际运行，球位路线未定。')
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        text = replace_note(text, '> **当前审核口径（2026-10-30）**',
            '> **当前审核口径（2026-10-30）**：' + SUMMARY + '本机实现用odom维护虚拟目标方向，外部仍须提供米制球位。'
            + links('') + '补实际构造和启停/重启；方向/力度及球位更新后续实测。'
            '只核实课程功能，深度单位、配准与控制原点待核，下文此前测试及性能讨论保留历史含义。')
    elif name.endswith('/实验验证/足球测试_第3轮_操作与记录.md'):
        heading = '# 足球测试第3轮：查询机身变换与创建管理器'
        assert text.count(heading) == 1
        text = text.replace(heading, heading + '\n\n> **本轮已审读**：TF原始记录是时间外推错误，未取得矩阵；'
            '创建前模式读取失败，构造函数尚未执行。人工表和自动原始文件保留，助手结论见第4部分。当前进入'
            + links('') + '。', 1)
        start = text.index('## 3. 管理器功能登记')
        text = text[:start] + '''## 3. 管理器功能登记

| 功能 | 当前实际证据 | 待做 |
| --- | --- | --- |
| `SoccerKickManager(robot)` | 第3轮构造前get_mode报错，构造未执行；原自动汇总“失败”为测试归因问题 | 第4轮独立实际构造 |
| `start()` | 已读完整实现，尚未调用 | 第4轮构造成功后实际启动 |
| `update_command(direction, power)` | 已读实现：odom虚拟目标，rad，力度1～10；尚未调用 | 实际方向和力度更新、相应作用 |
| `update_ball(x, y)` | 已读实现：外部当前机身米制坐标；尚未调用 | 球位来源核实后实际下发及持续更新 |
| `stop()`与重启 | 已读实现：关闭控制并清空参考，不主动切回其他模式；尚未调用 | 第4轮先测无球位的启停/重启；带指令重启后续实测 |

''' + ASSISTANT
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    rows = []
    for name, original_hash in base['shared'].items():
        p = ROOT / name
        old = p.read_bytes()
        assert hashlib.sha256(old).hexdigest() == original_hash, '出现并行编辑：' + name
        updated = change(name, old.decode('utf-8-sig'))
        p.write_text(updated, encoding='utf-8', newline='')
        rows.append({'path': name, 'before': original_hash,
                     'after': hashlib.sha256(p.read_bytes()).hexdigest()})
    (TASK / '联动记录.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print('第3轮助手结论与第4轮当前入口已回填。')
