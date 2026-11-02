from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
RESULT = '04-shared/sdk-tests/K1信息状态测试结果/K1信息状态_20261102_154403_101875'
DOCUMENT = '01-booster-kb/07-tech-platform/booster-sdk-k1-info-state.md'
SUMMARY = ('K1八项信息状态接口已回读：七项返回，robot_info在GetRobotInfo时报code=100，'
           '本次设备身份和固件未取得；公开模式walk、配置步态default，支持步态default/soccer。'
           '完整收录28个坐标系、22个关节、2个传感器、10个动作及字段；'
           '清单不等于动作执行或任意TF变换通过，不新增课程确认。')


def replace_note(text, prefix, updated):
    rows = [row for row in text.splitlines() if row.startswith(prefix)]
    assert len(rows) == 1, (prefix, len(rows))
    return text.replace(rows[0], updated, 1)


def change(name, text):
    if name == 'AGENTS.md':
        return replace_note(text, '> **K1信息状态采集（2026-11-02）**',
            '> **K1信息状态实测（2026-11-02）**：' + SUMMARY
            + f'[K1专用补充]({DOCUMENT})、[原始结果]({RESULT}/采集汇总.md)。'
            '源码/脚本/JSON/分文件/ZIP一致性已核对；未改课程Notebook和控制附件。')
    if name == 'INDEX.md':
        return replace_note(text, '> K1信息与状态全量采集 /',
            '> K1信息与状态实测 / 28坐标系 / 22关节 / 2传感器 / 10动作 / code100 / '
            f'缓存步态：[K1专用补充]({DOCUMENT})、[原始结果]({RESULT}/采集汇总.md)'
            '（SDK1.2.2；七项返回，robot_info失败，固件本次未取得）。')
    if name == 'CHANGELOG.md':
        head = '# 更新日志'
        return text.replace(head, head + '\n\n## 2026-11-02 · K1信息状态实测补充\n\n'
            + SUMMARY + f'[专用补充]({DOCUMENT})保留全部坐标系名称、关节顺序和限位、'
            '传感器标识/类型/型号、动作标识及元信息，注明SDK版本和本次固件缺失。'
            'robot_info失败原因未推断；历史设备信息不填作本轮返回。原始13个文件留存，'
            '分接口与总JSON、脚本哈希和ZIP内容核对一致。同步八份入口/说明；'
            '未重跑机器人、未修改课程或采集器，未生成下一轮测试。', 1)
    if name == 'README.md':
        head = '# 加速进化 K-12 课程设计师知识库'
        return text.replace(head, head + f'\n\n> **K1专用信息补充（2026-11-02）**：新增[八项接口实测说明]({DOCUMENT})。'
            'SDK1.2.2本次取得28个坐标系、22个关节、2个传感器和10个动作；'
            'robot_info报code=100，设备身份与固件本次未取得。保留完整原始记录及使用限制。', 1)
    if name == '04-shared/sdk-tests/_README.md':
        head = '# SDK 测试脚本说明'
        text = text.replace(head, head + f'\n\n> **K1实测结果（2026-11-02）**：{SUMMARY}'
            + f'[专用补充](../../{DOCUMENT})、[原始记录](K1信息状态测试结果/K1信息状态_20261102_154403_101875/原始记录.json)。', 1)
        row = next(row for row in text.splitlines() if row.startswith('| [probe_k1_info_state.py]'))
        return text.replace(row, row.replace('真机待运行', '2026-11-02已采集，7返回/1报错'), 1)
    if name == '04-shared/sdk-tests/K1信息与状态接口_采集说明.md':
        head = '# K1 信息与状态接口：运行与记录'
        text = text.replace(head, head + '\n\n> **已有实测（2026-11-02）**：'
            f'[K1专用补充](../../{DOCUMENT})与[原始汇总](K1信息状态测试结果/K1信息状态_20261102_154403_101875/采集汇总.md)'
            '已整理。八项均执行，七项返回；robot_info报code=100，保留为失败。下文用于后续复采，当前无需重填记录表。', 1)
        text = text.replace('脚本已编写，真机记录需在机器人环境中运行后生成。', '每次在机器人环境中运行后自动生成独立记录。', 1)
        return text.replace('本次结果将补充到 SDK 的 K1 专用说明；在实际记录反馈前，不填写“已在 K1 验证通过”。',
            '2026-11-02的记录已整理成上述K1专用说明。后续复采仍按当次返回登记，单项错误不能填成通过，历史固件不能替代当次查询。', 1)
    if name == '01-booster-kb/07-tech-platform/_index.md':
        new_row = '| [booster-sdk-k1-info-state.md](booster-sdk-k1-info-state.md) | K1八项信息状态接口实测：全部名称/字段；7项返回、robot_info报code=100，SDK1.2.2，2026-11-02 |\n'
        row_start = text.index('| [booster-agent-framework.md]')
        text = text[:row_start] + new_row + text[row_start:]
        start = text.index('## K1实机信息采集')
        end = text.index('## 使用指南', start)
        return (text[:start] + '## K1实机信息采集\n\n[八项接口K1专用补充](booster-sdk-k1-info-state.md)：'
                + SUMMARY + '\n\n' + text[end:])
    if name == '01-booster-kb/07-tech-platform/booster-sdk.md':
        return replace_note(text, '> **K1实际清单采集**',
            '> **K1实测补充（2026-11-02）**：[本台K1的八项接口记录](booster-sdk-k1-info-state.md)'
            '已收录SDK1.2.2下28个坐标系、22个关节、2个传感器、10个动作及模式/步态返回。'
            'robot_info报code=100，本次固件未取得；清单与官方通用说明分别保存，未将元信息查询写成动作或TF执行验证。')
    raise ValueError(name)


def build_document(raw):
    def value(name):
        row = raw['interfaces'][name]
        return row['attempts'][row['selected_attempt']]['value']
    relative = '../../' + RESULT + '/'
    lines = ['---', 'title: BoosterOS SDK：K1信息与状态接口实测补充',
             'module: 07-tech-platform', 'status: partial-verification',
             'updated: "2026-11-02"', 'sdk_version: "1.2.2"', '---', '',
             '# BoosterOS SDK：K1 信息与状态接口实测补充', '',
             '本文补充本台K1实际返回的名称、字段和状态，供代码选参、课程编写及SDK查阅使用。'
             '范围为八项信息与状态接口；未测试动作执行、模式/步态切换或任意两帧之间的坐标变换。', '',
             '## 1. 来源与适用条件', '',
             '| 项目 | 本次记录 |', '| --- | --- |',
             f"| 采集时间 | {raw['started_at']} 至 {raw['finished_at']} |",
             f"| 测试人 | {raw['tester']} |",
             '| 机型 | 用户说明为K1；本次robot_info失败，未从本轮返回重新核实型号、序列号 |',
             f"| BoosterOS SDK | {raw['environment']['boosteros_version']} |",
             '| Python / 平台 | Python 3.10.12；Linux 5.15.148-rt-tegra，aarch64 |',
             '| 固件 | 本次未取得；不将历史记录中的固件版本填作本轮返回 |',
             '| 现场备注 | 未填写 |',
             '| 连接 | 新建BoosterRobot，连接成功 |',
             '| 完整性 | 总JSON与8份分接口JSON一致；运行脚本哈希与记录一致；ZIP内12份文件与目录内容一致 |', '',
             f'[原始JSON]({relative}原始记录.json)、[原始汇总]({relative}采集汇总.md)、'
             f'[本机接口与类型定义]({relative}SDK接口定义.txt)、[运行说明](../../04-shared/sdk-tests/K1信息与状态接口_采集说明.md)。'
             '原始13个文件保持原样；本页为回读整理。后续更换机器人、SDK或配置时，重新查询对应清单。', '',
             '## 2. 八项结果', '',
             '| 接口 | 实际结果 | 本次结论 |', '| --- | --- | --- |',
             '| robot_info（属性） | RuntimeError: API call failed, code = 100 | 本次未取得身份/固件等元信息；保留错误 |',
             f"| get_mode() | `{value('get_mode')}` | 公开模式名称，本次未读取底层原始模式 |",
             f"| list_gaits() | `{value('list_gaits')}` | 本版本在当前模型下列出的步态，未执行切换 |",
             f"| get_gait() | `{value('get_gait')}` | SDK缓存的配置值，非实际步态测量 |",
             f"| list_frames() | {len(value('list_frames'))}项 | 本次可见的坐标系名称，完整列于下文 |",
             f"| list_joints() | {len(value('list_joints'))}项 | 关节静态元信息与本机返回顺序 |",
             f"| list_sensors() | {len(value('list_sensors'))}项 | 本接口返回的IMU与相机元信息 |",
             f"| list_actions() | {len(value('list_actions'))}项 | 内置动作元信息；执行与取消未测 |", '',
             '八项各调用一次；七项返回，robot_info报错。返回项没有字段导出提示。'
             '`completed=true`表示采集流程已走完，不表示八项均成功。', '',
             '### robot_info 的错误', '',
             '堆栈定位到 `BoosterRobot.robot_info → self.loco_client.GetRobotInfo()`，随后抛出code=100。'
             '本机定义表明该属性会构造RobotInfo，但本次没有取得该对象。'
             '当前材料没有给出code=100的含义，不能据此判断为不支持、超时、初始化未完成或设备故障。', '',
             '此前[足球完整测试回读](../../05-internal-materials/vocational-planning/03_X课程项目/实验验证/足球SDK完整测试_回读与U7课程边界.md)'
             '曾取得K1身份/固件信息，可作独立历史记录查阅；它不能替代本轮失败的返回。'
             '本次已有的七项结果可继续用于整理，不要求重跑整套。若需要补齐身份，只需在现有连接中单独重读robot_info并保存新结果及时间。', '',
             '## 3. 模式与步态怎样使用', '',
             '`get_mode()`本次返回walk。本机实现先取得原始模式再转换为公开名称，因此公开名称不能独立证明底层处于普通行走。'
             '此前足球测试出现过公开walk、原始kSoccer的情况；本轮没有采集原始模式，不将该历史状态写成本轮状态。', '',
             '`list_gaits()`返回default和soccer。`get_gait()`本机实现只有`return self._gait`，读取SDK对象的配置缓存。'
             '因此本次default不能证明机器人没有进入足球相关控制，也不能将它当作运动状态传感器。'
             '本轮没有调用set_gait验证两项切换。', '',
             '## 4. 坐标系：完整28项', '',
             '下面逐行保留本次返回名称和顺序。带aa前缀的名称没有删改；代码必须使用真实字符串，'
             '不能将aahead_pitch_link替换为文档示例中的head_pitch_link。', '', '```text',
             *value('list_frames'), '```', '',
             '按名称可辨认头部/相机、躯干和左右肢体相关条目，但名称本身不提供轴向、原点、父子关系或变换矩阵。'
             '`head_realsense_rgb_link`、`head_booster_stereo_rgb_link`同时出现，不能证明两种实体相机都已安装；硬件元信息见list_sensors。', '',
             '本次没有直接出现名为球位、足球场、world或odom的坐标系。这只能描述本次可见列表；'
             '不否定get_odom接口，也不证明所有潜在坐标系都不存在。'
             '这些名称可用于选择get_transform的查询参数，但任意两项是否连通、变换方向和时间是否有效仍取决于实际变换查询。', '',
             '## 5. 关节：完整22项及字段', '',
             '保留下表顺序，序号为本次列表的位置。位置限位按通用SDK文档以rad表示；显示保留六位小数，完整精度见原始JSON。'
             'max_torque、max_velocity为接口原值，本机保存的JointInfo定义未标注这两列单位，本文不增加单位结论。'
             '这些是静态元信息，不是本次测得的关节角度、实际最大力矩或安全教学动作范围。所有关节extra均为{}。', '',
             '| 序号 | name | limits.min（rad） | limits.max（rad） | max_torque原值 | max_velocity原值 |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    for i, joint in enumerate(value('list_joints'), 1):
        lines.append(f"| {i} | `{joint['name']}` | {joint['limits']['min']:.6f} | {joint['limits']['max']:.6f} | {joint['max_torque']:g} | {joint['max_velocity']:g} |")
    lines += ['', '前10项为头部2项及左右臂各4项，其后为左右腿各6项。'
              '左右关节的限位不一定相同，表中保留原值；不能为形式对称改写符号或范围。'
              '需要按顺序组织关节数据时，用实际list_joints返回顺序，不能改成按名称排序。', '',
              '## 6. 传感器：完整2项', '',
              '| id | sensor_type | model | extra |', '| --- | --- | --- | --- |']
    for sensor in value('list_sensors'):
        lines.append(f"| `{sensor['id']}` | `{sensor['sensor_type']}` | `{sensor['model']}` | `{json.dumps(sensor['extra'])}` |")
    lines += ['', '本机SensorInfo的sensor_type定义为camera或imu，list_sensors实现通过IMU与相机RPC获取元信息。'
              '因此这里只能作为该接口覆盖的清单，不能写成K1只有两种传感器、没有麦克风、里程计或其他硬件。', '',
              '相机标识head可以用于SDK相机接口的camera_id选参；imu_main_1是本次IMU元信息标识，'
              '不能不查方法签名就把它传给无传感器ID参数的读取函数。'
              'CAMERA_Model_BOOSTER_MIPI是返回的型号字符串，不能单凭此字符串确定深度单位、配准方式或所有物理规格。', '',
              '## 7. 内置动作：完整10项', '',
              '| id | type | duration原值（秒） | interruptible |', '| --- | --- | ---: | --- |']
    for action in value('list_actions'):
        lines.append(f"| `{action['id']}` | `{action['type']}` | {action['duration']:.1f} | `{str(action['interruptible']).lower()}` |")
    lines += ['', '十项均标为upper_body、duration=-1、interruptible=true。'
              '本机ActionInfo注释说明：type用于展示/分类，不直接决定运行逻辑；duration=-1表示预期时长不确定；'
              'interruptible是语义标记，实际可中断性还取决于实现。'
              '不能据此给动作安排固定sleep时间，也不能将true写成本轮取消成功。', '',
              '动作id可用于do_action的资源选择；本次没有执行do_action，不给上述十项补上执行成功、模式条件或终态结论。'
              '自录轨迹和动作工坊导出资源不属于本次内置动作列表；列表没有它们不代表其它调用入口不可用。', '',
              '## 8. 对足球定位与课程的影响', '',
              '本次补齐了相机标识、坐标系名称和关节/动作选项，可减少使用文档示例字符串造成的选参错误。'
              '例如相机元信息id为head，实际可见帧包含head_color_optical_frame与trunk。', '',
              '本次八项没有返回足球的位置、球场定位、深度单位或RGB/深度配准结果。'
              '因此update_ball所需的实时机身米制x/y仍未建立，不能仅凭列表中有相机帧和trunk就宣布坐标转换完成。'
              '后续定位工作可以使用这些真实名称，但仍需核实变换含义、深度语义及控制参考原点。', '',
              '现有学生Notebook、生成器、ball_position.py及足球控制附件本轮未改。'
              '本页记录信息查询事实，不代表U7/U8整课真机确认或自动踢球通过。', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    raw = json.loads((ROOT/RESULT/'原始记录.json').read_text(encoding='utf-8'))
    path = ROOT/DOCUMENT
    assert not path.exists()
    path.write_text(build_document(raw), encoding='utf-8')
    base = json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
    changed = []
    for name, digest in base['shared'].items():
        path = ROOT/name
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest, name
        updated = change(name, content.decode('utf-8-sig'))
        assert updated != content.decode('utf-8-sig'), name
        path.write_text(updated, encoding='utf-8', newline='')
        changed.append({'path': name, 'before': digest, 'after': hashlib.sha256(path.read_bytes()).hexdigest()})
    (TASK/'联动记录.json').write_text(json.dumps(changed, ensure_ascii=False, indent=2), encoding='utf-8')
    print('K1专用补充已生成，八份入口/说明已同步。')
