from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
V = C + '/实验验证/'
G3 = '足球测试_第3轮_操作与记录.md'
N3 = '足球测试_第3轮_机身变换与管理器创建.ipynb'

def links(prefix):
    return f'[第3轮操作与记录]({prefix}{G3})、[第3轮代码]({prefix}{N3})'

def replace_note(text, prefix, updated):
    found = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(found) == 1, (prefix, len(found))
    return text.replace(found[0], updated, 1)

def change(name, text):
    summary = ('SDK 1.2.2第2轮已回读：RGB/深度均544×448、共享head_color_optical_frame，内参可读；'
               '坐标系列表含trunk，原示例head_pitch_link不在列表，TF尚未查询。'
               '管理器创建及四方法签名齐全，尚未实际运行。')
    if name == 'AGENTS.md':
        text = replace_note(text, '> **足球SDK能力审核（2026-10-30）**',
            '> **足球SDK能力审核（2026-10-30）**：' + summary + '当前执行' + links(V)
            + '：用本机名查询相机到trunk，读取本机实现并实际创建管理器。'
            'start/update_command/update_ball/stop及重启全部保留后续实测。只核实课程所需能力，不补多框/遮挡等性能测试；'
            '深度单位、配准及管理器原点尚未明确，未决定采用课程自编标定，未新增课程阶段确认。下方早期测试安排为历史状态。')
    elif name == 'INDEX.md':
        text = replace_note(text, '> 足球SDK能力 / SDK 1.2.2 / distance_m为空',
            '> 足球SDK能力 / 深度mono16 / 相机内参 / trunk坐标变换 / 管理器创建：'
            f'[第2轮回读]({V}足球测试_第2轮_操作与记录.md)、' + links(V)
            + '（2026-10-30；深度和内参可读，TF改用本机名；管理器四方法仍待实际测试）。')
    elif name == 'CHANGELOG.md':
        heading = '# 更新日志'
        assert text.count(heading) == 1
        note = ('## 2026-10-30 · 足球第2轮回读与第3轮接口测试\n\n' + summary
                + '深度原数组含0和65535，单位与无效值定义未确认；同尺寸、同frame只作数据特征，不当作配准证明。'
                '第2轮现场记录和四份结果留存，助手区已回填。\n\n' + links(V)
                + '已生成：单次TF查询、本机实现读取、实际创建管理器，保持不启动控制。'
                '全部足球管理器功能继续逐轮实测，不设检出率/动态精度/响应时限等性能验收；'
                '未改学生Notebook或附件控制代码，助手未运行机器人。仅本地提交，推送由用户进行。')
        text = text.replace(heading, heading + '\n\n' + note, 1)
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = replace_note(text, '> **足球测试最新状态（2026-10-30）**',
            '> **足球测试最新状态（2026-10-30）**：' + summary + links('03_X课程项目/实验验证/')
            + '待执行，仅验证能力，不扩为性能验收；四个控制方法及重启仍需后续实测。')
    elif name.endswith('/X课程当前进度.md'):
        text = replace_note(text, '> **足球前置能力测试（2026-10-30）**',
            '> **足球前置能力测试（2026-10-30）**：' + summary + links('实验验证/')
            + '待用户执行。前两轮只登记接口与数据能力，不登记U7/U8整课①②通过。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = replace_note(text, '> **足球测试范围（2026-10-30）**',
            '> **足球测试范围（2026-10-30）**：第2轮深度与内参可读，TF改用本机head_color_optical_frame→trunk。'
            + links('实验验证/') + '包含实际管理器创建及实现读取，之后安排start、update_command方向/力度、'
            'update_ball持续米制更新、stop及重启全部功能。按能力分轮，不追加性能验收。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = replace_note(text, '> **足球SDK前置核查（2026-10-30）**',
            '> **足球SDK前置核查（2026-10-30）**：第1轮二维检测可用、distance_m为空；第2轮深度/内参可读，TF尚未调用。'
            + links('实验验证/') + '继续核实机身变换和管理器创建。能否用SDK组合数据替代课程自编映射仍待数据定义和接口实测；不提前增加学生标定任务。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = replace_note(text, '> **本机能力进展（2026-10-30）**',
            '> **本机能力进展（2026-10-30）**：SDK 1.2.2已取得二维检测、深度图与内参，尚无直接米制足球位置。'
            + links('../../实验验证/') + '将查询本机trunk变换并实际创建管理器；四个控制方法仍待后续运行。'
            '附件固定映射未被选定，本轮不修改附件或执行标定。')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        text = replace_note(text, '> **足球当前步骤（2026-10-30）**',
            '> **足球当前步骤（2026-10-30）**：第2轮深度/内参读取完成，当前执行' + links('')
            + '，查询本机trunk变换、读取实现并创建管理器；启停/方向力度/球位更新/重启仍列后续。'
            '当前仅核实SDK课程能力，下方性能/标定讨论不作为本轮任务。')
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        text = replace_note(text, '> **足球能力进展（2026-10-30）**',
            '> **足球能力进展（2026-10-30）**：第2轮取得深度和内参；当前' + links('')
            + '待执行，用本机名查变换、读取实现并创建管理器。四个控制方法仍未实测，定位路线未定，暂不重写项目分支。')
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        text = replace_note(text, '> **当前审核口径（2026-10-30）**',
            '> **当前审核口径（2026-10-30）**：核实SDK能否支撑课程，不做检出率、误差或动态性能验收。'
            '第2轮已取得544×448的RGB/深度与相机内参，TF因示例名不匹配尚未查询；'
            + links('') + '为当前任务，含trunk变换与管理器实际创建。深度单位、配准与控制原点待核实，'
            '不由同frame、正数深度推定。管理器四个方法及重启仍需逐轮运行。下文旧候选方案的性能讨论只作技术说明。')
    elif name.endswith('/实验验证/足球测试_第2轮_操作与记录.md'):
        heading = '# 足球测试第2轮：SDK深度与坐标接口'
        text = text.replace(heading, heading + '\n\n> **本轮已审读**：深度和内参可读取，TF需使用本机名称。当前进入'
                            + links('') + '；第2轮记录和原数据保留。', 1)
        start = text.index('## 5. 助手审读区')
        text = text[:start] + '''## 5. 助手审读结论（2026-10-30）

| 项目 | 结论 |
| --- | --- |
| 已读取的数据 | `足球测试结果/第2轮_20261030_181000_379153/`：能力汇总、原始JSON、RGB.png和depth.npy |
| 环境 | K1 060100，SDK 1.2.2、Python 3.10.12，模式prepare；RobotInfo完整固件为1.8.1.2-release-02884-2026-10-15 |
| RGB/深度 | 均544×448，frame均为head_color_optical_frame；RGB编码bgr8，深度mono16/uint16；原数组确实存在 |
| 深度原值 | 含0，也含65535；有限正数不等于已知有效距离。本轮只确认数据可读，不判断测距精度 |
| 内参 | K可读取，fx=fy≈207.455，cx≈280.240，cy≈214.984；d为0，p有值，r全0。原值留存，不单凭这些字段确认配准或校正算法 |
| TF未查询原因 | 上轮要求head_pitch_link，本机实际有aahead_pitch_link和trunk。未发生TF调用失败；不能判SDK缺TF |
| 管理器清单 | 构造、start、stop、update_ball(x,y)、update_command(direction,power)均可读取签名，无额外公开项。仅签名存在，尚未实际创建/调用 |
| 是否还需自编像素—米换算 | 暂不下结论。SDK已有深度和内参，值得继续核实组合能力；单位/无效值、RGB深度对应、相机到管理器参考系仍未明确 |
| 下一步 | [第3轮操作与记录](足球测试_第3轮_操作与记录.md)、[第3轮代码](足球测试_第3轮_机身变换与管理器创建.ipynb)：一次trunk变换、保存本机实现、实际创建管理器 |

### 对课程的当前判断

SDK已能提供图像、二维检测、深度和相机参数，不能继续以“只有二维框”为由认定必须自行标定。另一方面，这些数据还没有形成已核实的管理器米制球位，当前不把深度原值直接当x，也不把trunk自动等同于控制原点。

第3轮仅读取接口和创建对象；start、方向/力度设置、持续球位更新、stop与停止后重启全部保留后续实测。按用户要求，只核实课程所需功能，不因多框/遮挡或精度性能追加测试。本轮未登记U7/U8整课确认通过。
'''
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    records = []
    for name in base['shared']:
        p = ROOT / name
        before = p.read_bytes()
        updated = change(name, before.decode('utf-8-sig'))
        assert p.read_bytes() == before, '出现并行修改：' + name
        p.write_text(updated, encoding='utf-8', newline='')
        records.append({'path': name, 'before_sha256': hashlib.sha256(before).hexdigest(),
                        'after_sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    (TASK / '联动记录.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print('已回填第2轮助手结论，更新当前第3轮入口；保留用户记录。')
