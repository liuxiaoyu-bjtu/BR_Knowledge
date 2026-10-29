from pathlib import Path
import ast
import hashlib
import json
import re
import runpy
import tempfile
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
results = {'notebooks': [], 'protected': [], 'links': [], 'robot_executed': False}
external_path = TASK / '外部改动核对.json'
external = json.loads(external_path.read_text(encoding='utf-8')) if external_path.exists() else {}
results['external_changes_preserved'] = []
regen = runpy.run_path(str(PROJECT / '_regen_from_nb.py'), run_name='maintenance_check')

for number, prefix in [(15, 'U4-L3'), (16, 'U4-L4'), (25, 'U7-L1'), (26, 'U7-L2'), (27, 'U7-L3'), (28, 'U7-L4')]:
    path = next((PROJECT / 'notebooks').glob(prefix + '_*.ipynb'))
    raw = path.read_bytes()
    notebook = json.loads(raw)
    before = json.loads((TASK / 'before' / path.relative_to(ROOT)).read_text(encoding='utf-8-sig'))
    nbformat.validate(nbformat.reads(raw.decode('utf-8-sig'), as_version=4))
    assert len(notebook['cells']) == len(before['cells'])
    ids = [c['id'] for c in notebook['cells']]
    assert len(set(ids)) == len(ids)
    for i, (old, new) in enumerate(zip(before['cells'], notebook['cells']), 1):
        assert {k: v for k, v in old.items() if k not in ('source', 'id')} == {k: v for k, v in new.items() if k not in ('source', 'id')}, (prefix, i)
        assert new['id'] == old.get('id', f'{prefix.lower()}-cell-{i:02}')
        if new['cell_type'] == 'code':
            assert {k: v for k, v in old.items() if k != 'id'} == {k: v for k, v in new.items() if k != 'id'}, (prefix, i, 'code_changed')
            ast.parse(''.join(new['source']))
        assert not re.search(r'<\s*sss\s*>', ''.join(new['source']), re.I), (prefix, i)
    gen = PROJECT / f'_gen_L{number}.py'
    ast.parse(gen.read_text(encoding='utf-8-sig'))
    with tempfile.TemporaryDirectory(prefix='u4u7-check-') as tmp:
        sandbox = Path(tmp)
        (sandbox / 'notebooks').mkdir()
        copied = sandbox / gen.name
        copied.write_bytes(gen.read_bytes())
        runpy.run_path(str(copied), run_name='__gen__')
        output = sandbox / 'notebooks' / path.name
        assert json.loads(output.read_text(encoding='utf-8')) == notebook, (prefix, 'forward')
        regen['build'](str(copied), str(output), '本轮完整镜像核查')
        runpy.run_path(str(copied), run_name='__gen__')
        assert json.loads(output.read_text(encoding='utf-8')) == notebook, (prefix, 'reverse')
    assert raw == path.read_bytes(), (prefix, 'source_overwritten')
    results['notebooks'].append({'file': path.name, 'cells': len(notebook['cells']),
        'code_cells': sum(c['cell_type'] == 'code' for c in notebook['cells']),
        'code_outputs_metadata_preserved': True, 'nbformat': True,
        'forward_and_reverse_generator': True, 'sss_remaining': 0})

for rel, digest in baseline['protected'].items():
    actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    if actual != digest:
        assert rel in external and actual == external[rel]['observed_sha256'], ('protected_changed', rel)
        results['external_changes_preserved'].append(rel)
    else:
        results['protected'].append(rel)

docs = [PROJECT / '实验验证/U4-L3-L4_承接新版L2的同步审查.md', PROJECT / '实验验证/U7_逐课真机测试指导.md']
for doc in docs:
    text = doc.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]*\]\(([^\n)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        target = target.split('#')[0]
        resolved = doc.parent / target
        assert resolved.exists(), (doc.name, target)
        results['links'].append({'file': doc.name, 'target': target})

changes = json.loads((TASK / '逐格修改记录.json').read_text(encoding='utf-8'))
results['markdown_replacements'] = len(changes)
results['added_cell_ids'] = len(json.loads((TASK / '新增cellID.json').read_text(encoding='utf-8')))
results['changed_cells'] = sorted(set((c['file'], c['cell']) for c in changes))
(TASK / '离线核查结果.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('通过：六课格式、代码语法、代码/输出/元数据保留、正反向生成器、标记清零、报告链接；', len(results['protected']), '份其他Notebook字节未变，', len(results['external_changes_preserved']), '份外部新改动已保留。未运行SDK或机器人。')
