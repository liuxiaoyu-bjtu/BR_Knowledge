from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
G1 = '足球测试_第1轮_操作与记录.md'
G2 = '足球测试_第2轮_操作与记录.md'
N2 = '足球测试_第2轮_深度与坐标接口.ipynb'

def links(prefix):
    return f'[第2轮操作与记录]({prefix}{G2})、[第2轮代码]({prefix}{N2})'

def add(text, heading, note):
    assert text.count(heading) == 1, heading
    assert note not in text, '本轮说明已写入，避免重复回填'
    return text.replace(heading, heading + '\n\n' + note, 1)

def change(name, text):
    common = ('第1轮已回读：K1 060100、SDK 1.2.2可取RGB并运行soccer检测，本次distance_m全为None。'
              '用户明确本任务审核SDK能否支撑课程，多框、遮挡及耗时只作备注，不补做性能测试。'
              '管理器创建及start/update_command/update_ball/stop全部列入后续逐轮实测，不能只验证方法存在。')
    if name == 'AGENTS.md':
        text = add(text, '# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览',
            '> **足球SDK能力审核（2026-10-30）**：' + common
            + '当前发出' + links(C + '/实验验证/')
            + '，每项只读一次深度、内参、坐标系列表和TF；结果回读后再判断定位来源。'
            '当前仍未取得可直接用于管理器的米制球位，未推进U7/U8课程确认。下方“第1轮待执行”等为历史状态。')
    elif name == 'INDEX.md':
        text = add(text, '# 全局关键词索引',
            '> 足球SDK能力 / SDK 1.2.2 / distance_m为空 / 深度与内参 / TF查询：'
            + f'[第1轮回读]({C}/实验验证/{G1})、' + links(C + '/实验验证/')
            + '（2026-10-30；第1轮检测能力已确认；不补做多框/遮挡性能测试；第2轮待读数）。')
    elif name == 'CHANGELOG.md':
        text = add(text, '# 更新日志',
            '## 2026-10-30 · 足球第1轮回读与SDK数据能力第2轮\n\n'
            + common + '原记录与44份原始证据保留，补写助手审读结论。第1轮有球20/20、无球0/20；'
            '这些数量保留为本次输出，不外推识别性能。\n\n'
            + links(C + '/实验验证/')
            + '已生成，五步逐格，只读一次接口及返回结构，不要求重复采样、误差阈值或像素米制标定。'
            '自动保存中文能力表、深度数组和接口错误；等待用户测试后继续判断。'
            '学生Notebook、附件控制和生成器未改，助手未连接机器人，未新增课程阶段确认；本地提交，推送由用户操作。')
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = add(text, '# vocational-planning 目录说明',
            '> **足球测试最新状态（2026-10-30）**：' + common + links('03_X课程项目/实验验证/')
            + '已发出，当前仅能力读取待执行，助手读结果后再安排下一步。')
    elif name.endswith('/X课程当前进度.md'):
        text = add(text, '# X课程当前进度',
            '> **足球前置能力测试（2026-10-30）**：' + common + links('实验验证/')
            + '待用户执行。只登记测试证据，不把该轮接口调用扩展为U7/U8整课①②通过。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = add(text, '# X 课程开发计划（v4）',
            '> **足球测试范围（2026-10-30）**：按用户最新意见，前置测试只核实SDK是否提供课程所需能力。'
            '第1轮检测接口可用，distance_m为空；不补做多框、遮挡等性能验收。'
            '当前执行' + links('实验验证/') + '，逐项单次读深度、内参和TF，等待回读后定实现路线。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = add(text, '# X 课程大纲（v5.0）',
            '> **足球SDK前置核查（2026-10-30）**：检测能力在SDK 1.2.2已确认，返回二维框、distance_m为空。'
            '当前按' + links('实验验证/')
            + '核实深度、相机参数及坐标查询是否可用；能力数据明确后再决定课程是否需要自编转换。'
            '不因本次多框、遮挡追加性能测试，也不提前增加学生标定负担。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = add(text, '# U7/U8配套文件',
            '> **本机能力进展（2026-10-30）**：第1轮soccer检测可用，本次distance_m为空。'
            + links('../../实验验证/')
            + '用于核实能否由SDK提供深度/内参/变换来支撑课程；本轮不使用或改动附件算法。'
            '用户已明确不补做多框、遮挡等性能测试，固定平面映射仍待方案选择。')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        text = add(text, '# U7 逐课真机测试指导',
            '> **足球当前步骤（2026-10-30）**：第1轮检测能力已确认，distance_m为空。'
            '用户要求先审核SDK能力，不补多框、遮挡性能测试；当前只执行'
            + links('') + '，下方标定/动态定位测试不作为这一轮的前置要求。')
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        text = add(text, '# U8 逐课实施与真机测试指导',
            '> **足球能力进展（2026-10-30）**：第1轮确认检测可调用，尚无直接米制球位返回；当前'
            + links('') + '待读数据后再定课程定位来源。多框、遮挡只留备注，不补做性能测试。导览分支按原指导。')
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        text = add(text, '# 足球方案联合审核：SDK能力与教学边界',
            '> **当前审核口径（2026-10-30）**：用户明确先核实OS SDK能否支撑课程，不做检出率、误差或动态性能验收。'
            '第1轮已确认SDK 1.2.2检测接口可用，distance_m全为None；不因多框、遮挡追加补测。'
            + links('') + '为当前任务；下文旧候选方案的动态精度讨论保留为技术条件说明，不列为本轮必测项。')
        text = text.replace('目标机器安装版本未知。有效SDK正文12篇已留本地证据；',
                            '公开文档查阅时目标版本未知；第1轮现已记录目标SDK 1.2.2、固件1.8.1（完整返回见原始记录）。有效SDK正文12篇已留本地证据；')
    elif name.endswith('/实验验证/' + G1):
        text = add(text, '# 足球测试第1轮：操作指导与记录',
            '> **已审读，当前进入第2轮**：SDK足球检测能力已确认。本轮数量和图像现象作为实测记录保留；'
            '用户明确不因多框、遮挡补做性能测试。下一步为' + links('') + '，只读接口与返回数据。')
        text = text.replace('上一版已经填写的“20261030、K1实体机器人”迁入下表。尚没有真机检测结果，日期如有变化请修改。',
                            '下表为用户实际记录，日期2026-10-30；原始数据已回读，助手结论见第5部分。')
        start = text.index('## 5. 审读后填写（由助手填写）')
        text = text[:start] + '''## 5. 助手审读结论（2026-10-30）

| 项目 | 结论 |
| --- | --- |
| 已读取的记录/数据目录 | `足球测试结果/第1轮_20261030_173437_745363/`；现场表、自动统计、原始JSON及40张采样图，另看单帧标框图 |
| 本机环境 | 机器人端Python 3.10.12、SDK 1.2.2；K1 060100，用户记固件1.8.1；完整RobotInfo保留在JSON |
| 已确认的SDK能力 | 可取RGB图、可用soccer模型返回类别、评分和二维框；图像544×448，源frame为`head_color_optical_frame` |
| 距离/位置字段 | 单帧及20张有球样本的`distance_m`均为None；本批公开字段未见可直接使用的米制x/y。仅限本次调用，不能推成所有SDK/服务都没有球位能力 |
| 是否需要补做第1轮 | 不需要。用户明确本次核实课程所需能力，多框、遮挡和耗时只作备注，不安排性能补测 |
| 当前是否已证明能够给管理器提供球位 | 尚未。已证明检测可调用，还需核实SDK能否提供深度、内参和坐标变换等数据 |
| 下一步 | [第2轮操作与记录](足球测试_第2轮_操作与记录.md)、[第2轮代码](足球测试_第2轮_深度与坐标接口.ipynb)，每项读取一次，不设性能阈值 |

### 留存的实测现象

- 有球20张均返回Ball框，9张另有画面左边缘Ball框；在本批图像中，最高分Ball均对应场地中的足球，评分约0.851～0.855。这只描述本批数据，不将选最高分扩大为普遍保证，也不改检测阈值。
- 无球批20张没有Ball框，图片近处大部分被人体/衣物遮挡。按用户意见留存，不要求同背景重拍，不据此宣称场地误检率为0。
- 有球检测调用中位数2.404秒，无球2.235秒；仅为本次耗时，不作为接口能力否决或课程动态性能结论。
- 用户记录站姿为STAND，SDK模式字段为`prepare`；两项原文均保留，不为统一称谓要求切模式。
- JSON残留一次`without_ball_note`未确认标志，但后续无球批完整保存20张；按实际批次回读，不将旧提示当作整步未执行。

本轮登记“检测接口能力已确认”，不登记U7/U8整课确认①②或课程阶段通过。
'''
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    records = []
    for name in baseline['shared']:
        p = ROOT / name
        before = p.read_bytes()
        updated = change(name, before.decode('utf-8-sig'))
        assert p.read_bytes() == before, '检测到并行修改：' + name
        p.write_text(updated, encoding='utf-8', newline='')
        records.append({'path': name, 'before_sha256': hashlib.sha256(before).hexdigest(),
                        'after_sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    (TASK / '回填与联动记录.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print('已回填第1轮助手区并同步12份记录/入口；保留用户现场记录。')
