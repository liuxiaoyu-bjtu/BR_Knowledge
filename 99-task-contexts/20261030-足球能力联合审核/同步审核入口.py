from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = '05-internal-materials/vocational-planning/03_X课程项目'
AUDIT = '足球方案联合审核_SDK能力与教学边界.md'
PLAN = '足球SDK能力与定位方案_分级测试计划.md'
PROBE = '足球SDK能力探查_只读.ipynb'
TAG = '足球定位联合审核（2026-10-30）'

def link(prefix, name, title):
    return f'[{title}]({prefix}{name})'

def note(prefix):
    return (f'> **{TAG}**：`ball_position.py`为课程自编的固定平面映射候选，静态`verified`不代表步态中定位通过。'
            '先由教师探查实际SDK球位、深度/内参/TF能力，再选择定位来源；学生不承担从零复现矩阵算法。'
            f'{link(prefix, AUDIT, "审核依据")}、{link(prefix, PLAN, "分级测试与记录表")}、'
            f'{link(prefix, PROBE, "教师只读探查")}。'
            '本轮未改学生Notebook、附件控制代码或生成器，未运行机器人，未新增阶段确认。')

rules = {
    'AGENTS.md': ('# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览', note(COURSE + '/实验验证/')),
    'INDEX.md': ('# 全局关键词索引',
        '> 足球SDK能力探查 / 球位坐标 / 像素米制映射 / 单应标定 / 定位测试验收：'
        + link(COURSE + '/实验验证/', AUDIT, '联合审核') + '、'
        + link(COURSE + '/实验验证/', PLAN, '分级测试计划') + '、'
        + link(COURSE + '/实验验证/', PROBE, '教师只读探查')
        + '（2026-10-30；先核实本机SDK能力，固定映射为候选；全部真机项目待执行）。'),
    'CHANGELOG.md': ('# 更新日志',
        '## 2026-10-30 · 足球定位方案联合审核与测试准备\n\n'
        '回读U7-L2及L3/L4、U8足球分支和`ball_position.py`，重新核查12篇官方SDK正文。'
        '明确管理器接收当前机器人米制球位，二维检测、可选距离和坐标变换各有不同职责；'
        '公开资料不足以替代本机能力确认。课程固定映射缺少动态实测证据，先列为候选。\n\n'
        + link(COURSE + '/实验验证/', AUDIT, '审核与教学范围') + '、'
        + link(COURSE + '/实验验证/', PLAN, '分级测试计划') + '及'
        + link(COURSE + '/实验验证/', PROBE, '教师只读探查Notebook')
        + '已建立。补充验收门槛、重复采样、方案选择和统一结果记录，学生不要求复现矩阵算法。'
        '仅做离线几何、格式与代码静态检查，未运行机器人，未改学生源文件或推进确认；Git本地提交，推送由用户操作。'),
    '05-internal-materials/vocational-planning/README.md': ('# vocational-planning 目录说明', note('03_X课程项目/实验验证/')),
    COURSE + '/X课程当前进度.md': ('# X课程当前进度', note('实验验证/')),
    COURSE + '/X课程大纲-v5.md': ('# X 课程大纲（v5.0）', note('实验验证/') + '\n> 足球定位的教学范围建议：理解坐标、读数、有效性与管理器调用；课内采点范围在本机能力比较后确定，当前大纲中的自编映射不视为已经选定的必修实现。'),
    COURSE + '/X课程开发计划-v4.md': ('# X 课程开发计划（v4）', note('实验验证/') + '\n> 足球运动测试顺序调整为：教师能力探查→选择并验证定位来源→核查管理器契约与控制→课程联调。U7/U8仍保留P1待审/验证状态。'),
    COURSE + '/notebooks/x_lab/README.md': ('# U7/U8配套文件',
        '> **教师审核说明（2026-10-30）**：以下描述的是当前候选实现。`ball_position.py`尚无K1足球步态定位实测依据，'
        '`verified=True`仅代表给定静态点满足所设误差，不能认定运动中可用。请先按'
        + link('../../实验验证/', PLAN, '分级测试计划') + '探查本机SDK能力，再选择定位来源。'
        '学生需理解输入输出、坐标与误差，矩阵拟合和凸包不列为从零编写要求。'
        + link('../../实验验证/', AUDIT, '完整审核依据') + '。'),
    COURSE + '/实验验证/U7_逐课真机测试指导.md': ('# U7 逐课真机测试指导',
        '> **足球测试前置（2026-10-30）**：足球运动测试先执行'
        + link('', PLAN, '分级测试计划') + '的A能力探查，再决定是否需要固定映射B。'
        '本文的标定与动态核查指当前候选实现，不代表已选定定位方案；'
        '量化验收、重复次数与结果记录按新计划执行。L3类别/像素观察、导览及L1可独立测试。'),
    COURSE + '/实验验证/U8_逐课实施与真机测试指导.md': ('# U8 逐课实施与真机测试指导',
        '> **足球依赖审核（2026-10-30）**：先按'
        + link('', PLAN, '分级测试计划') + '核实本机SDK能力并选择定位来源。'
        '下文`ball_calibration.json`要求对应当前固定映射候选；最终若改用可靠SDK球位，应统一修订依赖后再联调。'
        'U8整合已预验证能力，不承担排查基础定位算法；导览通过不代替足球测试。'),
}

baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8-sig'))
current_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert current_head == baseline['head'], 'HEAD发生变化，请重新检查提交基线'
index_paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, text=True)
assert not index_paths.strip(), '暂存区非空，先保留并审查其他任务改动'

def insert(text, anchor, paragraph):
    assert text.count(anchor) == 1, anchor
    assert paragraph not in text, '已包含本轮入口，不重复写入'
    return text.replace(anchor, anchor + '\n\n' + paragraph, 1)

records = []
for path, (anchor, paragraph) in rules.items():
    full = ROOT / path
    current_bytes = full.read_bytes()
    current_text = current_bytes.decode('utf-8-sig')
    updated_text = insert(current_text, anchor, paragraph)
    # 只在刚读到的当前文本中插入小段，不从历史备份覆盖工作区。
    assert full.read_bytes() == current_bytes, f'检测到并行改动：{path}'
    full.write_text(updated_text, encoding='utf-8', newline='')
    head_bytes = subprocess.check_output(['git', 'show', f'HEAD:{path}'], cwd=ROOT)
    head_text = head_bytes.decode('utf-8-sig')
    staged_text = insert(head_text, anchor, paragraph)
    staged_path = TASK / 'head-increment' / path
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    staged_path.write_text(staged_text, encoding='utf-8', newline='')
    records.append({'path': path,
                    'before_sha256': hashlib.sha256(current_bytes).hexdigest(),
                    'after_sha256': hashlib.sha256(full.read_bytes()).hexdigest(),
                    'same_as_task_start': hashlib.sha256(current_bytes).hexdigest() == baseline['shared'].get(path),
                    'staged_source': staged_path.relative_to(ROOT).as_posix()})

(TASK / '入口更新与暂存来源.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(records, ensure_ascii=False, indent=2))
