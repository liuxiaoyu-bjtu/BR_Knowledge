"""核对本轮文稿映射与输入指纹；不运行 Notebook 或机器人代码。"""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
LESSONS = [
    ('U4-L1_转向来宾', 27),
    ('U5-L1_语音识别', 27),
    ('U5-L2_语音合成', 28),
    ('U5-L3_LLM对话', 28),
]


def section(text, prefix):
    return next(s for s in re.split(r'(?=^## )', text, flags=re.M)
                if s.startswith(prefix))


def rows(text):
    return [[c.strip() for c in line.strip().strip('|').split('|')]
            for line in text.splitlines() if line.startswith('|')]


def numbers(spec):
    result = set()
    for part in spec.split('、'):
        ends = [int(n) for n in re.split('[～–—-]', part)]
        if len(ends) == 1:
            result.add(ends[0])
        else:
            assert len(ends) == 2 and ends[0] <= ends[1], spec
            result.update(range(ends[0], ends[1] + 1))
    return result


def main():
    baseline = json.loads((TASK / '输入与本轮基线.json').read_text(encoding='utf-8'))
    inputs = []
    for item in baseline['inputs']:
        path = ROOT / item['path']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == item['sha256'], f'输入发生变化：{path}'
        inputs.append({'path': item['path'], 'sha256': digest, 'unchanged': True})

    coverage_path = PROJ / 'PPT内容设计/U4-L1_U5-L1-L3_P4覆盖检查记录.md'
    coverage = coverage_path.read_text(encoding='utf-8')
    coverage_sections = re.split(r'(?=^### U[45]-L[123])', coverage, flags=re.M)
    lesson_results = []
    documents = [coverage_path, TASK / '00-任务上下文.md', TASK / '02-产出清单与状态日志.md']
    for name, expected_pages in LESSONS:
        design_path = PROJ / '教学设计' / f'{name}_教学设计.md'
        outline_path = PROJ / 'PPT内容设计' / f'{name}_PPT内容大纲.md'
        design = design_path.read_text(encoding='utf-8')
        outline = outline_path.read_text(encoding='utf-8')
        documents.extend([design_path, outline_path])
        notebook = json.loads((PROJ / 'notebooks' / f'{name}.ipynb').read_text(encoding='utf-8'))
        cell_count = len(notebook['cells'])
        codes = {i for i, c in enumerate(notebook['cells'], 1) if c['cell_type'] == 'code'}

        page_rows = [r for r in rows(section(outline, '## 二')) if r[0].isdigit()]
        assert [int(r[0]) for r in page_rows] == list(range(1, expected_pages + 1)), name
        assert all(len(r) == 6 and all(r[1:]) for r in page_rows), f'页面字段不完整：{name}'

        mapped_codes = set()
        for row in rows(section(outline, '## 四')):
            if re.fullmatch(r'[\d、～]+', row[0]):
                assert numbers(row[0]) <= set(range(1, expected_pages + 1)), row
                match = re.match(r'\d+(?:[、～]\d+)*', row[1])
                if match:
                    mapped_codes.update(numbers(match.group()))
        assert mapped_codes == codes, f'代码格映射不符：{name}，{mapped_codes ^ codes}'

        lesson_coverage = next(s for s in coverage_sections if s.startswith('### ' + name[:5]))
        mapped_cells = set()
        for row in rows(lesson_coverage):
            if re.fullmatch(r'[\d～]+', row[0]):
                cell_set = numbers(row[0])
                assert not mapped_cells & cell_set, f'覆盖格号重复：{name}'
                mapped_cells.update(cell_set)
                assert numbers(row[2]) <= set(range(1, expected_pages + 1)), row
        assert mapped_cells == set(range(1, cell_count + 1)), f'格号覆盖不完整：{name}'

        design_times = []
        for row in rows(section(design, '## 三')):
            match = re.fullmatch(r'(\d+)[–～—-](\d+)\s*min', row[0])
            if match:
                design_times.append(tuple(map(int, match.groups())))
        outline_times, taught_pages, after_pages = [], set(), set()
        for row in rows(section(outline, '## 五')):
            match = re.fullmatch(r'(\d+)～(\d+)分钟', row[0])
            if match:
                outline_times.append(tuple(map(int, match.groups())))
                pages = numbers(row[1])
                assert not pages & taught_pages, f'课堂页重复：{name}'
                taught_pages.update(pages)
            elif row[0] == '课后':
                after_pages.update(numbers(row[1]))
        assert design_times == outline_times and design_times, f'时间轴不一致：{name}'
        assert design_times[0][0] == 0 and design_times[-1][1] == 45, name
        assert all(a < b for a, b in design_times), name
        assert all(a[1] == b[0] for a, b in zip(design_times, design_times[1:])), name
        assert not taught_pages & after_pages, name
        assert taught_pages | after_pages == set(range(1, expected_pages + 1)), name
        lesson_results.append({
            'lesson': name, 'pages': expected_pages, 'cells_mapped': cell_count,
            'code_cells_mapped': sorted(codes), 'minutes': 45,
            'time_segments': design_times, 'after_class_pages': sorted(after_pages),
        })

    link_count = 0
    for path in documents:
        for raw in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            target = unquote(raw.strip('<>').split('#')[0])
            if not target or re.match(r'^[a-zA-Z]+://', target):
                continue
            destination = (path.parent / target).resolve()
            if destination != TASK / '验证结果.json':
                assert destination.exists(), f'本地链接不存在：{path.name} → {target}'
            link_count += 1
    result = {
        'date': '2026-10-23', 'passed': True,
        'scope': '静态文稿、映射和文件指纹；不代表PPTX版面或真机验证',
        'inputs': inputs, 'lessons': lesson_results,
        'totals': {'pages': sum(x['pages'] for x in lesson_results),
                   'cells': sum(x['cells_mapped'] for x in lesson_results),
                   'code_cells': sum(len(x['code_cells_mapped']) for x in lesson_results),
                   'documents_link_checked': len(documents), 'local_links': link_count},
    }
    (TASK / '验证结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert (TASK / '验证结果.json').is_file()
    print(json.dumps({'passed': True, **result['totals'], 'unchanged_inputs': len(inputs)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
