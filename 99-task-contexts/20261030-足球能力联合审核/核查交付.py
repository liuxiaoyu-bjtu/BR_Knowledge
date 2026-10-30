from pathlib import Path
import ast
import hashlib
import json
import re
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
VERIFY = COURSE / '实验验证'
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8-sig'))

parallel_changes = json.loads((TASK / '并行改动观察.json').read_text(encoding='utf-8'))
protected_changes = []
unchanged_count = 0
for name, expected in baseline['protected'].items():
    actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if actual != expected:
        if parallel_changes.get(name) != actual:
            protected_changes.append(name)
    else:
        unchanged_count += 1
assert not protected_changes, protected_changes

notebook_path = VERIFY / '足球SDK能力探查_只读.ipynb'
nb = nbformat.read(notebook_path, as_version=4)
nbformat.validate(nb)
forbidden = {'start', 'stop', 'update_ball', 'update_command', 'move', 'walk',
             'set_mode', 'switch_mode', 'do_action', 'execute_trajectory', 'set_head_angle'}
code_count = 0
for cell in nb.cells:
    if cell.cell_type != 'code':
        continue
    code_count += 1
    assert cell.execution_count is None and not cell.outputs
    tree = ast.parse(cell.source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden, node.func.attr
            if isinstance(node.func, ast.Name):
                assert node.func.id != 'SoccerKickManager', '不能构造管理器'
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            assert 'x_lab' not in ast.unparse(node)

documents = [VERIFY / '足球方案联合审核_SDK能力与教学边界.md',
             VERIFY / '足球SDK能力与定位方案_分级测试计划.md']
checked_links = 0
for path in documents:
    text = path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (path, target)
        checked_links += 1
for cell in nb.cells:
    if cell.cell_type == 'markdown':
        for target in re.findall(r'\]\(([^)]+)\)', cell.source):
            assert (notebook_path.parent / target).exists(), target
            checked_links += 1

plan = documents[1].read_text(encoding='utf-8')
rows = [line for line in plan.splitlines() if re.match(r'^\| [ABCD]\d{2}(?=\D|$)', line)]
ids = [re.match(r'^\| ([ABCD]\d{2})', line).group(1) for line in rows]
assert len(ids) == len(set(ids)) == 30, ids
assert all('未执行' in row.rsplit('|', 2)[1] for row in rows)

source_files = json.loads((TASK / 'sdk-evidence/来源清单.json').read_text(encoding='utf-8'))
assert len(source_files) == 12 and all(row['valid'] for row in source_files)
sources = []
for row in source_files:
    evidence = TASK / 'sdk-evidence' / Path(row['file']).with_suffix('.txt')
    assert evidence.exists()
    sources.append({'file': evidence.relative_to(TASK).as_posix(),
                    'url': row['canonical'],
                    'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()})
(TASK / 'sdk-evidence/正文来源与哈希.json').write_text(
    json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')

result = {'robot_executed': False, 'protected_source_files_unchanged': unchanged_count,
          'parallel_changes_preserved_and_excluded': list(parallel_changes),
          'notebook_cells': len(nb.cells), 'notebook_code_cells': code_count,
          'ast_and_nbformat': 'passed', 'motion_calls_or_manager_construction': 'none',
          'local_links_checked': checked_links, 'test_cases': len(ids),
          'all_machine_test_cases': '未执行', 'valid_official_pages': len(sources)}
(TASK / '交付核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
