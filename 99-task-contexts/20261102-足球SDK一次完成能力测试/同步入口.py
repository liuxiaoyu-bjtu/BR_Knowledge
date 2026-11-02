from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
V = C + '/实验验证/'
OLD = '足球测试_第4轮_管理器创建与启停.ipynb'
NEW = '足球测试_第4轮_完整能力验证.ipynb'

def links(prefix):
    return f'[完整操作与记录]({prefix}足球测试_第4轮_操作与记录.md)、[完整测试Notebook]({prefix}{NEW})'

def note(text, prefix, updated):
    rows = [r for r in text.splitlines() if r.startswith(prefix)]
    assert len(rows) == 1, (prefix, len(rows))
    return text.replace(rows[0], updated, 1)

SUMMARY = ('按用户要求，将尚未执行的第4轮合并为一次现场完整能力验证，逐步操作后统一回传；'
           '覆盖实际构造、全部四个公开方法、方向/力度更新、活动中持续球位、真实试踢及停止后同对象复用。')

def change(name, text):
    text = text.replace(OLD, NEW)
    if name == 'AGENTS.md':
        text = note(text, '> **足球SDK能力审核（2026-10-30）**',
            '> **足球SDK能力审核（2026-11-02）**：' + SUMMARY + links(V)
            + '为唯一当前操作入口。卷尺手量球位隔离控制能力，静止球odom换算仅作教师测试工具；'
            'TF失败不挡住控制测试。旧启停版已替换，前3轮原始证据保留。结果用于U7-L2/L3/L4与U8足球边界决策，'
            '视觉米制来源未核实时不把自编标定设为学生必修前置；不默认再拆轮次、不设性能验收，未执行机器人或登记课程确认。下方早期安排为历史记录。')
    elif name == 'INDEX.md':
        text = note(text, '> 足球SDK能力 / TF时间外推',
            '> 足球SDK完整能力 / SoccerKickManager全部公开方法 / 方向力度 / 持续球位 / 试踢与重启 / U7课程边界：'
            + links(V) + '（2026-11-02；一次现场逐步完成、统一回传后决策课程；手量输入隔离控制能力，视觉定位不作前置阻塞）。')
    elif name == 'CHANGELOG.md':
        heading = '# 更新日志'
        assert text.count(heading) == 1
        text = text.replace(heading, heading + '\n\n## 2026-11-02 · 足球SDK测试合并，直接服务课程决策\n\n'
            + SUMMARY + '此前将“逐步操作”拆成多次回传，未能及时收敛课程边界；现改为9步一次现场完成，'
            '不再逐方法等待助手回读。\n\n' + links(V)
            + '已替换旧启停版，保留前3轮证据。代码保存参数、真实返回、完整堆栈和执行覆盖；'
            '卷尺手量球位与有限静止球odom更新用于隔离SDK控制，真实试踢仅下发一次当前球位，'
            '球移动后不按静止假设续发。TF失败不阻断管理器测试，故障和跳过项照实记录。'
            '新增结果到U7-L2/L3/L4和U8的课程决策表，不以None返回认定踢球成功，'
            '不把未核实的视觉映射带入必修主线。未运行机器人或改学生教材。仅本地提交，推送由用户执行。', 1)
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = note(text, '> **足球测试最新状态（2026-10-30）**',
            '> **足球测试最新状态（2026-11-02）**：' + SUMMARY + links('03_X课程项目/实验验证/')
            + '待用户一次完成；不再逐项等待助手回读。结果直接用于课程边界与实验设计，前3轮证据保留，旧启停版已替换。')
    elif name.endswith('/X课程当前进度.md'):
        text = note(text, '> **足球前置能力测试（2026-10-30）**',
            '> **足球前置能力测试（2026-11-02）**：' + SUMMARY + links('实验验证/')
            + '待执行。手量球位隔离SDK控制，未核实的视觉定位不阻断本次方法测试；回读后确定课程删改，未新增整课①②。下方早期状态按历史阅读。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = note(text, '> **足球测试范围（2026-10-30）**',
            '> **足球测试范围（2026-11-02）**：' + SUMMARY + links('实验验证/')
            + '一次执行后统一回读，形成U7/U8足球教学边界及实验删改。不默认继续拆轮次；'
            'TF/视觉球位来源单列结论，不阻断手量输入的控制能力验证，不扩为性能验收。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = note(text, '> **足球SDK前置核查（2026-10-30）**',
            '> **足球SDK前置核查（2026-11-02）**：' + links('实验验证/')
            + '已合并为一次现场完整能力测试，覆盖全部四方法及课程所需控制流程。'
            '以手量球位隔离控制能力；视觉米制来源未证实时，课程应收缩为定点输入与短时控制，'
            '不把自编矩阵标定设为必修前置。待实际记录后确定U7/U8删改，当前未登记阶段通过。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = note(text, '> **本机能力进展（2026-10-30）**',
            '> **本机能力进展（2026-11-02）**：当前使用' + links('../../实验验证/')
            + '，在一次现场操作覆盖构造、四方法、更新、试踢和复用。测试手量球位及静止球odom辅助用于隔离控制能力，'
            '不属于学生定位实现。固定映射仍为候选；记录回读后再决定附件删改与课程范围。下方早期入口按历史阅读。')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        text = note(text, '> **足球当前步骤（2026-10-30）**',
            '> **足球当前步骤（2026-11-02）**：使用' + links('')
            + '一次覆盖全部公开方法及更新、试踢、复用；中间无需回传等候。TF和视觉定位不挡住手量输入的控制试验。'
            '统一回读后确定L2/L3/L4与U8足球内容边界，不再默认多轮探查。下方旧标定/性能安排不作为本次任务。')
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        text = note(text, '> **足球能力进展（2026-10-30）**',
            '> **足球能力进展（2026-11-02）**：当前' + links('')
            + '一次执行、统一回读后给出U7/U8足球边界与实验删改。覆盖四方法及实际试踢、停止后复用；'
            '手量米制输入不代表视觉定位已解决，未验证能力不放入U8必做项目。')
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        text = note(text, '> **当前审核口径（2026-10-30）**',
            '> **当前审核口径（2026-11-02）**：使用' + links('')
            + '一次现场覆盖构造、全部四方法、指令/球位更新、真实试踢及同对象复用，统一回读后决策课程。'
            '卷尺手量输入隔离控制能力；TF或视觉米制来源未明确不挡住方法测试，也不据此先增加学生标定。'
            '故障/跳过项直接纳入课程收缩结论，不默认继续逐轮探查。下方旧执行方式与性能讨论为历史。')
        start = text.index('## 6. 现在怎样逐步测试')
        end = text.index('## 7. 对后续课程的影响', start)
        text = text[:start] + '''## 6. 当前完整测试与结束条件

前3轮已取得二维检测、深度/内参及管理器完整源码；第3轮TF有时间外推，管理器被构造前模式读取挡住。此前按小项逐轮回传拖慢了课程决策，现按用户要求将尚未执行的第4轮合并。

''' + links('') + '''在一次现场操作中覆盖实际构造、四个公开方法、有效与无效输入、活动中指令/球位更新、真实试踢和带新指令的停止后复用。前3轮证据沿用，不重复做性能采样。

米制球位由卷尺提供，用于隔离SDK控制能力。远处静止球试验只在有限接近范围内按odom补偿机身运动；近球试踢只下发一次当前球位，不把被踢动后的球继续当作静止点。该测试工具不等于已解决视觉定位，也不放进学生必修算法。

完成后应形成U7-L2/L3/L4及U8足球分支的保留、删改与待核事项。若视觉米制来源仍不足，缩小必修实验为定点输入与短时控制，移除从零标定与自主追球的完成要求；不因希望维持原稿设计而无限补测。若构造/启停失败，明确当前环境不具备学生试踢条件。仅在具体故障确实阻碍边界判断时提出定向补测。

''' + text[end:]
    elif name.endswith('/实验验证/足球测试_第3轮_操作与记录.md'):
        # 原始用户填写与助手审读结论只更新链接，保留当时判断。
        pass
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    rows = []
    for name, before_hash in base['shared'].items():
        p = ROOT / name
        before = p.read_bytes()
        assert hashlib.sha256(before).hexdigest() == before_hash, '出现并行修改：' + name
        updated = change(name, before.decode('utf-8-sig'))
        p.write_text(updated, encoding='utf-8', newline='')
        rows.append({'path': name, 'before': before_hash, 'after': hashlib.sha256(p.read_bytes()).hexdigest()})
    (TASK / '联动记录.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print('当前入口、技术审核和课程决策口径已同步。')
