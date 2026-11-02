from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
V = C + '/实验验证/'
REPORT = '足球SDK完整测试_回读与U7课程边界.md'

def link(prefix):
    return f'[第4轮回读与课程边界]({prefix}{REPORT})'

def note(text, prefix, updated):
    rows = [r for r in text.splitlines() if r.startswith(prefix)]
    assert len(rows) == 1, (prefix, len(rows))
    return text.replace(rows[0], updated, 1)

SUMMARY = ('第4轮五份原始文件已回读，助手代填记录并补入用户现场回忆。构造成功，start5/5、stop6/6、'
           'update_command有效7次、update_ball有效6次；另3项ValueError均为预期无效输入。'
           '活动中球位/指令更新和同对象重启已调用，机器人有前进/侧移/后退响应；基线明确未踢球，完整踢出尚未证实。')

def change(name, text):
    if name == 'AGENTS.md':
        text = note(text, '> **足球SDK能力审核（2026-11-02）**',
            '> **足球SDK能力审核（2026-11-02）**：' + SUMMARY + link(V)
            + '为当前结论，前3轮及本轮原始证据保留。TF已取得矩阵，字段方向待核；视觉米制球位仍未建立。'
            '建议U7-L2收缩为感知与控制接口、已知球位短时控制，移出从零标定；L3保持静态检测并发，L4/U8按已证实条件衔接。'
            '旧0.8秒处理门槛与实测约2秒不匹配须修订。停止按方法拆轮次，现场停稳/量法待补充；未改学生代码或登记课程确认。下方早期安排按历史阅读。')
    elif name == 'INDEX.md':
        text = note(text, '> 足球SDK完整能力 / SoccerKickManager全部公开方法',
            '> 足球SDK完整能力 / 第4轮回读 / 四方法实际调用 / None返回 / 运动响应未等于踢出 / U7课程边界：'
            + link(V) + f'、[已回填记录]({V}足球测试_第4轮_操作与记录.md)'
            + '（2026-11-02；构造与四方法已调用、参数异常符合预期；用户观察到调整，完整踢出及视觉米制来源未证实）。')
    elif name == 'CHANGELOG.md':
        heading = '# 更新日志'
        assert text.count(heading) == 1
        text = text.replace(heading, heading + '\n\n## 2026-11-02 · 足球完整测试回读与课程边界\n\n'
            + SUMMARY + '原表由助手依据程序事实和对话回忆补齐，不能由文件证明的停稳、量法等保留未知。\n\n'
            + link(V) + '给出U7-L2/L3/L4与U8的保留与删改建议：'
            '去除从零标定必修前置，区分像素、米制球位、接口返回和现场结果，不将两秒单次球位试验当作完整踢球验收。'
            '初始球位不同不能隔离方向/力度作用；TF取得矩阵但标签方向待核；公开walk掩盖原始soccer、'
            '旧0.8秒条件与第1轮约2秒检测不匹配均列入后续修订。未改学生Notebook、生成器或控制附件；'
            '不再默认生成下一轮测试，不登记整课阶段通过。五份原始证据留存，仅本地提交，用户自行推送。', 1)
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = note(text, '> **足球测试最新状态（2026-11-02）**',
            '> **足球测试最新状态（2026-11-02）**：' + SUMMARY + link('03_X课程项目/实验验证/')
            + '及原记录已回填，停止逐方法拆轮次；后续按证据收缩课程范围。原始数据/学生代码保留，尚未登记整课确认。')
    elif name.endswith('/X课程当前进度.md'):
        text = note(text, '> **足球前置能力测试（2026-11-02）**',
            '> **足球前置能力测试（2026-11-02）**：' + SUMMARY + link('实验验证/')
            + '给出课程删改建议；视觉米制球位未建立、TF返回标签待核，现场停稳/量法待补充。'
            '不以部分控制响应登记U7/U8整课①②，学生Notebook本轮未改。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = note(text, '> **足球测试范围（2026-11-02）**',
            '> **足球测试范围（2026-11-02）**：第4轮构造和四方法实际调用已核对，有效输入正常返回，预期无效输入报错；'
            '现场观察到运动调整，完整踢球尚未证实。' + link('实验验证/')
            + '已形成U7/U8设计删改建议；停止按方法拆轮次，优先明确球位来源和已证实的短时控制条件，不扩成性能验收。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = note(text, '> **足球SDK前置核查（2026-11-02）**',
            '> **足球SDK前置核查（2026-11-02）**：第4轮已实际调用全部四方法，接口链路可用；用户观察到调整，完整踢出和视觉米制供数未证实。'
            + link('实验验证/') + '建议L2围绕感知、已知球位与控制接口，移出从零矩阵标定；'
            'L3保持检测并发，L4/U8按有效输入和实际效果衔接。当前为修订建议，尚未改正文或登记阶段通过。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = note(text, '> **本机能力进展（2026-11-02）**',
            '> **本机能力进展（2026-11-02）**：' + link('../../实验验证/')
            + '已完成：构造和四方法可调用，机器人有运动响应，完整踢球未证实。视觉米制输入和固定映射未验证，'
            '不能将接口返回延伸为标定可用。建议拆开位置来源与控制，移除必修标定依赖及不匹配的0.8秒门槛；本轮附件代码保留。')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        text = note(text, '> **足球当前步骤（2026-11-02）**',
            '> **足球当前步骤（2026-11-02）**：' + link('')
            + '及第4轮记录已完成自动回填；构造、四方法、更新和重启均实际调用，有运动调整，完整踢球与视觉米制定位未证实。'
            '停止按方法继续分轮，优先按报告调整L2/L3/L4和U8范围；学生代码本轮未改，整课①②不自动通过。')
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        text = note(text, '> **足球能力进展（2026-11-02）**',
            '> **足球能力进展（2026-11-02）**：第4轮构造、四方法和重启可调用，用户观察到运动调整，完整踢球与视觉米制球位未证实。'
            + link('') + '已给出项目边界建议，U8只整合已证实输入条件，不默认加入自主追球/进球验收。未改学生Notebook。')
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        text = note(text, '> **当前审核口径（2026-11-02）**',
            '> **当前审核口径（2026-11-02）**：' + SUMMARY + link('')
            + '及第4轮已回填记录为当前证据。视觉米制输入尚未建立；停止按方法拆轮次，'
            '按报告收缩从零标定/自动追球目标。下文早期执行安排与候选模型讨论保留历史含义。')
        start = text.index('## 6. 当前完整测试与结束条件')
        end = text.index('## 7. 对后续课程的影响', start)
        text = text[:start] + '''## 6. 完整测试已回读，转入课程边界修订

''' + link('') + '''、[第4轮已回填记录](足球测试_第4轮_操作与记录.md)为当前结论。构造与四方法均实际调用，5次start、6次stop正常返回；有效指令7次、有效球位6次返回，另外三项无效输入ValueError符合预期。活动中更新和同对象复用已有运行证据，用户报告前进、侧移和后退，基线明确没有踢球动作。

这足以结束逐方法探查，不能将“有效输入正常返回”写成“完整踢球已完成”。远球因0.15米行进边界提前结束，近球各仅一次球位和约两秒观察，且三项初始球位不同；完整持续供数、实际踢出、方向/力度效果不能由这些调用单独推出。

建议学生主线保留检测、坐标输入与控制，移出从零矩阵标定，L4/U8仅接入已证实条件。TF本轮取得矩阵，但请求/返回字段方向需核对；深度到足球米制位置仍没有完整依据。旧0.8秒取图处理门槛与第1轮约2秒检测记录不匹配，要随实验设计修改，而非简单当作管理器故障。

本次不生成新的测试轮次；现场停稳、量法等由用户记忆补录，未知就保留。只有以后确实要求完成实际踢出，才针对持续供数和完整行为的具体缺口单独决定，不能继续无目的遍历方法。

''' + text[end:]
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    rows = []
    for name, expected in base['shared'].items():
        p = ROOT / name
        old = p.read_bytes()
        assert hashlib.sha256(old).hexdigest() == expected, '出现并行修改：' + name
        p.write_text(change(name, old.decode('utf-8-sig')), encoding='utf-8', newline='')
        rows.append({'path': name, 'before': expected, 'after': hashlib.sha256(p.read_bytes()).hexdigest()})
    (TASK / '联动记录.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print('当前证据、课程边界与进度备注已同步。')
