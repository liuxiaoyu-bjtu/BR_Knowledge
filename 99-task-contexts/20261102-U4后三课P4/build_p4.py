from pathlib import Path
import json, re, hashlib
from p4_content import LESSONS

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
OUT = PROJECT / 'PPT内容设计'


def text(cell):
    return ''.join(cell['source']).strip()


def pipe(s):
    return str(s).replace('|', '／').replace('\n', ' ')


def label(cell):
    s = text(cell)
    if cell['cell_type'] == 'code':
        return '代码：' + next((x for x in s.splitlines() if x.strip() and not x.startswith('#')), '学生自主作答')[:75]
    h = re.findall(r'(?m)^#{1,4}\s+(.+)$', s)
    step = re.findall(r'(?m)^\*\*STEP[^\n]+', s)
    return '；'.join(h + step)[:140] or s.splitlines()[0][:100]


def sections(source):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'(?m)^###\s+([^\n]+)\n([\s\S]*?)(?=^###\s+|\Z)', source)}


def source_parts(notebook, d):
    record = text(notebook['cells'][d['record_cell'] - 1])
    sec = sections(record)
    checkpoints = next(v for k, v in sec.items() if '检查点' in k)
    thinking = next(v for k, v in sec.items() if '思考题' in k)
    # 记录表只提取原表头与行，不把思考题参考写进学生页面。
    tables = re.findall(r'(?m)^\|[^\n]+\n(?:^\|[^\n]*\n?)+', record)
    evaluation, answers = text(notebook['cells'][d['evaluation_cell'] - 1]).split('> 参考答案', 1)
    evaluation = re.sub(r'^##[^\n]+\n\s*', '', evaluation)
    return checkpoints, thinking, tables, evaluation.strip(), '> 参考答案' + answers


def build():
    manifest = {}
    for code, d in LESSONS.items():
        nb_path = next((PROJECT / 'notebooks').glob(code + '_*.ipynb'))
        nb = json.loads(nb_path.read_text(encoding='utf-8'))
        design = PROJECT / '教学设计' / f'{code}_{d["name"]}_教学设计.md'
        rows = d['pages']
        mapping = {i: [j for j, row in enumerate(rows, 1) if i in row[4]] for i in range(1, len(nb['cells']) + 1)}
        assert all(mapping.values()), code + '有未安排的单元格'
        cp, thinking, tables, evaluation, answers = source_parts(nb, d)
        count_code = sum(c['cell_type'] == 'code' for c in nb['cells'])
        count_cp = len(re.findall(r'(?m)^- \[__\]', cp))
        count_q = len(re.findall(r'(?m)^(?:\d+\. |- )', thinking))
        title = f'{code}_{d["name"]}_PPT内容大纲.md'
        head = [
            f'# {code} {d["name"]}｜PPT内容大纲', '',
            '> 日期：2026-11-02。用户明确确认本课P2、P3通过（③④），授权进入P4。本稿待确认⑤；尚未制作P5课件。',
            '> 格号从1计，包含Markdown。页面依据当前Notebook及已确认的45分钟教学设计；本轮不修改Notebook、执行信息或生成器，不执行机器人程序。', '',
            f'[学生Notebook](../notebooks/{nb_path.name}) · [已确认教学设计](../教学设计/{design.name}) · [三课覆盖检查](U4-L2-L3-L4_P4覆盖检查记录.md)', '',
            '## 一、课件定位与课堂安排', '', d['purpose'], '',
            f'共{len(rows)}页，覆盖{len(nb["cells"])}格、{count_code}个代码格。页面用于讲解、操作驻留、图表核对和题目回看，不按一页一段连续讲授计算时间。' + ('最后一页为课后阅读，课堂结束时只定位阅读入口。' if d['reading_cell'] else ''), '',
            '前置条件、代表演示、个人补做及安全收尾沿已确认教学设计。课堂共享代表数据时写明来源，未亲自运行的项目另排受监护实操。课件不把“程序返回”“发出零速度”和“现场停稳”混为同一结果。', '',
            '## 二、逐页设计', '',
            '| 页码 | 章节标签 | 主标题 | ——副标题 | 类型 | 内容与呈现要求 | Notebook格号 |',
            '| --- | --- | --- | --- | --- | --- | --- |',
        ]
        for page, (main, sub, kind, body, cells) in enumerate(rows, 1):
            part = next((part for a, b, part, start, end in d['times'] if start <= page <= end), '课后阅读')
            head.append('| ' + ' | '.join(map(pipe, [page, part, main, '——' + sub, kind, body, '、'.join(map(str, cells))])) + ' |')
        head += ['', '## 三、关键图示与真实素材', '', '| 页面 | 图示对象 | 必须说明的关系与边界 |', '| --- | --- | --- |']
        for pages, name, detail in d['visuals']:
            head.append(f'| {"、".join(map(str, pages))} | {name} | {pipe(detail)} |')
        head += ['', '真实材料在P5制作时对应页面补入，现有Notebook输出先核对目标、版本与拍摄条件；未取得的结果不伪造成实测。可以先用标明“示意”或“假设数据”的图解释关系，不能将其列为学生实验完成证据。', '']
        head += ['- ' + x for x in d['materials']]
        head += ['', '## 四、全部单元格与代码覆盖', '', '| 原格号 | 类型 | 内容定位 | 设计页 |', '| --- | --- | --- | --- |']
        for i, cell in enumerate(nb['cells'], 1):
            head.append(f'| {i} | {cell["cell_type"]} | {pipe(label(cell))} | {"、".join(map(str, mapping[i]))} |')
        head += ['', '代码页只放当前需要理解的关键行或分支，完整程序在Notebook中运行。长循环拆为取数、计算、指令、退出与记录图，不把整格缩成小字。', '', '| 代码格 | 设计页 | 核对重点 |', '| --- | --- | --- |']
        for i, focus in d['code_focus'].items():
            head.append(f'| {i} | {"、".join(map(str, mapping[i]))} | {pipe(focus)} |')
        head += ['', '## 五、教学时间与目标覆盖', '', '| 已确认教学时间 | 环节 | 页面 | 驻留与完成依据 |', '| --- | --- | --- | --- |']
        for a, b, part, start, end in d['times']:
            head.append(f'| {a}～{b}分钟 | {part} | {start}～{end} | 按教学设计本环节运行、观察或填写记录；页面可回看，不追加新的运动测试。 |')
        head += ['', '末环节保留约2分钟个人测验；思考题课堂选一问交流，其余结合记录课后补答。安全收尾按实际操作时机执行，不因课件页序延后。', '', '| 课程目标原文 | 对应页面 | 判断依据 |', '| --- | --- | --- |']
        goals = re.findall(r'(?m)^\d+\. (.+)$', text(nb['cells'][0]))
        assert len(goals) == 3
        for i, (goal, pages) in enumerate(zip(goals, d['goal_pages']), 1):
            head.append(f'| {i}. {pipe(goal)} | {"、".join(map(str, pages))} | 与教学设计§六及Notebook过程记录对应；概念题、代码解释与实际操作分别核对。 |')
        head += ['', '## 六、记录表与学生作答页', '', f'以下内容取自Notebook第{d["record_cell"]}格。表头在P5保持完整，可按用途拆页；课堂详细填写仍在Notebook。', '']
        for i, table in enumerate(tables, 1):
            head += [f'### 原记录表{i}', '', table.strip(), '']
        head += [f'### 检查点原文（第{"、".join(map(str, d["checkpoint_pages"]))}页）', '', cp, '', f'### 思考题原文（第{"、".join(map(str, d["thinking_pages"]))}页）', '', thinking, '', f'### 学习评价原文（第{"、".join(map(str, d["evaluation_pages"]))}页）', '', evaluation, '', '### 教师讲者备注，学生页面不显示', '', answers, '', '思考题参考沿已确认教学设计§六及相关环节提问说明；FAQ随相关页进入讲者备注。参考答案不放在学生可见页面，P6导出学生PDF时同样删除。', '', '## 七、制作与交接要求', '']
        head += ['- ' + x for x in d['boundaries']]
        head += [
            '- 16:9白底、微软雅黑，沿U1正式稿与项目视觉规范；知识蓝#2563EB、实践青绿#0EA5A4、思考橘黄#F59E0B，安全红#E5484D只标安全内容，页脚仅页码。',
            '- 章节标签、主标题、——副标题保持层级。表格与长问题分块排版，完整题干和选项不得因缩字而难以投影阅读。',
            '- 本轮P4页码是制作设计页。待确认⑤后进入P5-A制作检查，再于P5-B回填原教学设计的实际投影页码与页内区域，确认⑥由用户作出。', '',
        ]
        (OUT / title).write_text('\n'.join(head), encoding='utf-8')
        manifest[code] = {'file': title, 'pages': len(rows), 'cells': len(nb['cells']), 'code_cells': count_code, 'checkpoints': count_cp, 'thinking_questions': count_q, 'evaluation_items': 3, 'tables': len(tables), 'mapping': mapping, 'notebook_sha256': hashlib.sha256(nb_path.read_bytes()).hexdigest()}
    (TASK / '页面与覆盖清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(manifest)
    print('P4已生成：', {k: v['pages'] for k, v in manifest.items()}, '共', sum(v['pages'] for v in manifest.values()), '页')


def write_report(manifest):
    report = ['# U4-L2、L3、L4 P4覆盖检查记录', '', '> 日期：2026-11-02。用户明确确认“U4-L2、L3、L4的P2、P3均确认，可以进行P4”。据此登记三课③④通过；L2原第16、19格待办按本次P2确认收口，不编造补验过程或新增执行输出。三份P4待确认⑤，尚未进入P5。', '', '## 一、三课产物与阶段', '', '| 课程 | 逐页大纲 | 页数 | Notebook格/代码 | 检查点/思考/测验 |', '| --- | --- | --- | --- | --- |']
    for code, m in manifest.items():
        report.append(f'| {code} {LESSONS[code]["name"]} | [内容大纲]({m["file"]}) | {m["pages"]} | {m["cells"]}/{m["code_cells"]} | {m["checkpoints"]}/{m["thinking_questions"]}/3 |')
    report += ['', '合计84页，覆盖90格、30个代码格、9项目标、12项检查点、12道思考题和9道学习评价。L3第27页、L4第29页为课后阅读，其余页面按各课45分钟设计用于讲解、操作驻留、记录及回看。学生未亲自运行的项目按原教学设计另排实操，不用页数推算讲授时长。', '', '## 二、课程分工与保留条件', '', '| 课程 | 主线 | P4特别核对 |', '| --- | --- | --- |', '| L2 | 里程计行进核对、框高距离标定及学生阈值程序 | 行进量与最终间距分开；独立核对不复用标定点；0.853是历史样本，停止阈值来自本组；保留学生编程空位。 |', '| L3 | 移动目标的持续视觉跟随 | 达到阈值只暂停前进，循环继续；偏差大先转向；IMU/odom仅记录；指令持续时间还含读状态耗时。 |', '| L4 | 连续到位、新观测和致意交接 | 只有“到位”进入致意；确认后新取图；句柄状态和物理效果分开；不将U6的取消继续规则套来改写L4。 |', '', '当前K1信息采集和足球专项测试的结论不用于擅改本组三课已确认代码。robot_info等接口在P4仅按现稿说明其用途，真实输出由课件素材核对，不用固定身份信息替代现场结果。', '', '## 三、全部代码格逐项定位', '', '| 课程 | 代码格 | 页面 | 主要内容 |', '| --- | --- | --- | --- |']
    for code, d in LESSONS.items():
        m = manifest[code]
        for i, focus in d['code_focus'].items():
            report.append(f'| {code} | {i} | {"、".join(map(str, m["mapping"][i]))} | {pipe(focus)} |')
    report += ['', '全部Markdown格的知识、操作说明、记录、检查、思考、评价和阅读均在各课大纲§四逐格映射。§六完整复制现稿记录表、检查点、思考题与评价题干；教师答案单列备注，不进入学生页面。', '', '## 四、后续制作需要的材料', '', '| 课程 | 需要核对的真实素材 |', '| --- | --- |']
    for code, d in LESSONS.items():
        report.append(f'| {code} | {pipe("；".join(d["materials"]))} |')
    report += ['', '现阶段不要求为课件重做已确认实验；制作时先使用用户保存的实际资料，未取得素材标待补或改用明确标注的概念示意。图片及视频来源须可追溯；示意不能作为完成证据。', '', '## 五、确认记录与下一步', '', '- 本次三课P2、P3通过，以用户明确确认登记；助手未连接机器人、未追加真机验证结论或执行输出。', '- 三课Notebook及正式生成器逐字节保留，教学设计只更新当前状态和L2已失效的待补验说法，教学活动、时长和评价不变。', '- 三份P4待用户确认⑤。确认后再制作P5-A，并于P5-B按成品回填原教学设计；本轮不生成PPTX，不登记⑤⑥。', '- 当前全课分布：4课有P5完成记录、17课P5审查稿待⑥、3课P4待⑤、8课P1待①②。教学设计24课，PPT内容大纲24课，PPTX覆盖21课；P6仍待全课程结束统一执行。', '', '离线检查结果与输入基线位于`99-task-contexts/20261102-U4后三课P4/`。Git仅本地记录，推送由用户手动进行。', '']
    (OUT / 'U4-L2-L3-L4_P4覆盖检查记录.md').write_text('\n'.join(report), encoding='utf-8')


if __name__ == '__main__':
    build()
