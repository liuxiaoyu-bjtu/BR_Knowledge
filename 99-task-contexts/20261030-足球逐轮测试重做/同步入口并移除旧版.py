from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = '05-internal-materials/vocational-planning/03_X课程项目'
GUIDE = '足球测试_第1轮_操作与记录.md'
CODE = '足球测试_第1轮_静止检测.ipynb'
OLD_GUIDE = '足球SDK能力与定位方案_分级测试计划.md'
OLD_CODE = '足球SDK能力探查_只读.ipynb'

def links(prefix):
    return f'[第1轮操作与记录]({prefix}{GUIDE})、[配套测试Notebook]({prefix}{CODE})'

def replace_links(text):
    text = text.replace(OLD_GUIDE, GUIDE).replace(OLD_CODE, CODE)
    for old, new in [('[分级测试与记录表]', '[第1轮操作与记录]'),
                     ('[分级测试计划]', '[第1轮操作与记录]'),
                     ('[教师只读探查]', '[第1轮测试Notebook]'),
                     ('[教师只读探查Notebook]', '[第1轮测试Notebook]')]:
        text = text.replace(old, new)
    return text

def add_under_heading(text, heading, paragraph):
    assert text.count(heading) == 1, heading
    assert paragraph not in text, '本轮内容已经存在，避免重复运行'
    return text.replace(heading, heading + '\n\n' + paragraph, 1)

def change(name, text):
    text = replace_links(text)
    if name == 'AGENTS.md':
        text = add_under_heading(text, '# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览',
            '> **足球测试改为逐轮推进（2026-10-30）**：按用户反馈，当前只执行静止检测第1轮，七步操作与代码对应，'
            '自动统计有球/无球各20张新图、18/20与0/20数量标准，现场情况由用户填写。'
            + links(COURSE + '/实验验证/') + '。读取本轮结果后再生成下一轮，不预设像素米制定位路线或误差阈值。'
            '旧分级计划及旧探查Notebook已删除，有效技术审核和SDK依据保留；未运行机器人，未新增课程确认。')
    elif name == 'INDEX.md':
        text = add_under_heading(text, '# 全局关键词索引',
            '> 足球逐轮测试 / 静止检测 / 有球无球 / 自动统计与现场记录：'
            + links(COURSE + '/实验验证/') + '（2026-10-30；先做第1轮，助手读记录后再安排下一轮；已替代旧分级计划和探查Notebook）。')
    elif name == 'CHANGELOG.md':
        text = add_under_heading(text, '# 更新日志',
            '## 2026-10-30 · 足球测试改为逐轮操作与记录\n\n'
            '按用户反馈撤下30项分级计划和旧探查Notebook，改为当前只做第1轮静止检测。七步操作、现场记录、'
            '自动结果与阈值代码对应；默认有球/无球各20张新图、至少18帧/0帧返回足球类检测。'
            '重复帧不累计，采样不足或异常保留记录。距离字段仅调查，尚不设米制误差或运动验收值。\n\n'
            + links(COURSE + '/实验验证/') + '。先前用户填写的日期和K1实体机器信息已迁入新记录表。'
            'SDK技术审核及证据保留，旧文件可由Git历史追溯；当前入口已更新。未改学生课件源文件、未运行机器人，'
            '等待用户完成记录后由助手安排下一轮。仅本地提交，推送由用户完成。')
    elif name == '05-internal-materials/vocational-planning/README.md':
        text = add_under_heading(text, '# vocational-planning 目录说明',
            '> **足球测试当前入口（2026-10-30）**：' + links('03_X课程项目/实验验证/')
            + '。当前只做静止检测第1轮，用户填现场情况、程序自动记录数据，助手读完再安排下一轮。旧30项分级计划与旧探查Notebook已删除。')
    elif name.endswith('/X课程当前进度.md'):
        text = add_under_heading(text, '# X课程当前进度',
            '> **足球验证方式更新（2026-10-30）**：' + links('实验验证/')
            + '已替代旧分级计划和旧探查Notebook。当前仅第1轮静止检测待执行，结果回读后再定下一轮；不代表U7/U8确认①②通过。')
    elif name.endswith('/X课程大纲-v5.md'):
        text = add_under_heading(text, '# X 课程大纲（v5.0）',
            '> **足球能力验证（2026-10-30）**：先按' + links('实验验证/')
            + '取得第1轮静止检测结果，再由助手逐轮安排；定位路线、标定课内负担待证据明确后再定。旧分级计划已撤下。')
    elif name.endswith('/X课程开发计划-v4.md'):
        text = add_under_heading(text, '# X 课程开发计划（v4）',
            '> **足球测试执行顺序（2026-10-30）**：当前只发出' + links('实验验证/')
            + '，用户完成并记录后由助手回读、补测或生成下一轮代码；深度、坐标定位和运动部分不与第1轮同时展开。旧分级计划已撤下。')
    elif name.endswith('/notebooks/x_lab/README.md'):
        text = add_under_heading(text, '# U7/U8配套文件',
            '> **测试入口更新（2026-10-30）**：先完成' + links('../../实验验证/')
            + '，由助手回读后再安排定位验证；当前测试不使用`x_lab`。下文标定函数仍是候选实现，不作为第1轮任务。')
        text = text.replace('请先按[第1轮操作与记录]', '请先完成[第1轮操作与记录]')
    elif name.endswith('/实验验证/U7_逐课真机测试指导.md'):
        old = next(line for line in text.splitlines() if line.startswith('> **足球测试前置（2026-10-30）**'))
        new = ('> **足球测试前置（2026-10-30，逐轮版）**：当前只做' + links('')
               + '，用户填记录后由助手审读并安排下一轮。下方L2标定/试踢、L4足球等暂不作为本轮操作任务。'
               '旧分级计划与旧探查Notebook已删除；L1、L3及导览内容另按本指导执行。')
        text = text.replace(old, new, 1)
    elif name.endswith('/实验验证/U8_逐课实施与真机测试指导.md'):
        old = next(line for line in text.splitlines() if line.startswith('> **足球依赖审核（2026-10-30）**'))
        new = ('> **足球依赖审核（2026-10-30，逐轮版）**：当前先做' + links('')
               + '，等待助手读记录后再安排定位与踢球测试。下文固定映射及足球整合是后续候选内容，本轮不执行。'
               '旧分级计划已删除，导览主题不受本轮测试安排影响。')
        text = text.replace(old, new, 1)
    elif name.endswith('/实验验证/足球方案联合审核_SDK能力与教学边界.md'):
        first = '# 足球方案联合审核：SDK能力与教学边界'
        text = add_under_heading(text, first,
            '> **执行方式已更新**：本报告保留技术依据。实际测试只按' + links('')
            + '开展当前一轮，助手读完记录再发下一轮；旧30项分级计划和旧探查Notebook已删除。')
        start = text.index('## 6. 现有测试文件够不够严格')
        end = text.index('## 7. 对后续课程的影响', start)
        text = text[:start] + ('## 6. 现在怎样逐步测试\n\n'
            '原测试指导列出了标定、误差、丢球和退出等方向，但一次展开30项任务和多种路线，不便现场按步骤完成。'
            '按用户反馈，改为每次只交付当前一轮的操作、记录表及配套代码。\n\n'
            '第1轮只做静止足球检测：版本与取图、单帧字段、有球和无球各20张新图。'
            '代码按表中默认18/20、0/20数量标准自动统计；这些是调查用初步标准，不是运动性能承诺。'
            '用户记录画面与标框是否符合实际，把结果目录填回表格，助手据此安排距离字段、深度或检测问题的下一轮。'
            '本轮不要求用户填写尚无依据的米制误差阈值。\n\n'
            + links('') + '。旧分级计划和旧探查Notebook已移除，SDK证据及本报告保留。\n\n') + text[end:]
    else:
        raise ValueError(name)
    return text

if __name__ == '__main__':
    baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    changes = []
    for name in baseline['shared']:
        path = ROOT / name
        before = path.read_bytes()
        text = before.decode('utf-8-sig')
        updated = change(name, text)
        assert path.read_bytes() == before, '出现并行改动：' + name
        path.write_text(updated, encoding='utf-8', newline='')
        changes.append({'path': name, 'before_sha256': hashlib.sha256(before).hexdigest(),
                        'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    # 用户明确要求清理旧版；先前填写的两项信息已迁移，并保存了本地备份。
    for name in baseline['old']:
        path = ROOT / name
        assert path.resolve().is_relative_to((ROOT / COURSE / '实验验证').resolve())
        assert path.is_file()
        path.unlink()
    (TASK / '联动记录.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
    print('已更新11个入口/说明；删除两份旧测试文件；保留SDK技术审核。')
