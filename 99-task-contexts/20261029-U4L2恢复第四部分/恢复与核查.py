from pathlib import Path
import hashlib
import json
import pprint
import runpy
import subprocess
import tempfile
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
path = PROJECT / 'notebooks/U4-L2_走近来宾.ipynb'
generator = PROJECT / '_gen_L14.py'
before_bytes = path.read_bytes()
before = json.loads(before_bytes)
head_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
reference = json.loads(subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT))
protected = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (PROJECT / 'notebooks').glob('*.ipynb') if p != path}
for file in [path, generator]:
    dest = TASK / 'before' / file.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file.read_bytes())

restored = [c for c in reference['cells'] if c['cell_type'] == 'markdown' and
            ''.join(c['source']).startswith(('### 4.1 检测框大小与距离', '### 4.2 已知距离上的标定'))]
assert len(restored) == 2
assert all(c['id'] not in {x['id'] for x in before['cells']} for c in restored)
assert ''.join(before['cells'][19]['source']).startswith('## 四、框大小的距离标定')
after = json.loads(json.dumps(before))
after['cells'][20:20] = restored
assert after['cells'][8] == before['cells'][8]
assert [c for c in after['cells'] if c['id'] not in {x['id'] for x in restored}] == before['cells']
assert [c for c in after['cells'] if c['cell_type'] == 'code'] == [c for c in before['cells'] if c['cell_type'] == 'code']
nbformat.validate(nbformat.from_dict(after))
path.write_text(json.dumps(after, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

description = ('U4-L2完整Notebook镜像；已恢复第四部分误删的4.1、4.2两格。'
               '第9格保留用户明确确认的原描述；36格，26 Markdown/10代码。'
               '运行会覆盖Notebook，须先核对用户手改。')
source = ('# -*- coding: utf-8 -*-\n' + repr(description) + '\nimport json\nfrom pathlib import Path\nNOTEBOOK = '
          + pprint.pformat(after, width=110, sort_dicts=False)
          + '\nif __name__ in ("__main__", "__gen__"):\n'
          + '    path = Path(__file__).parent / "notebooks" / ' + repr(path.name) + '\n'
          + '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
generator.write_text(source, encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='u4l2-restore-') as directory:
    sandbox = Path(directory)
    (sandbox / 'notebooks').mkdir()
    copied = sandbox / generator.name
    copied.write_bytes(generator.read_bytes())
    runpy.run_path(str(copied), run_name='__gen__')
    assert json.loads((sandbox / 'notebooks' / path.name).read_text(encoding='utf-8')) == after
for rel, digest in protected.items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel

result = {'reference_commit': head_commit, 'before_cells': len(before['cells']),
          'after_cells': len(after['cells']), 'restored': [
              {'cell': 21 + i, 'id': c['id'], 'title': ''.join(c['source']).splitlines()[0]}
              for i, c in enumerate(restored)],
          'cell_9_preserved_exactly': True, 'all_other_cells_preserved_exactly': True,
          'all_code_outputs_and_metadata_preserved': True, 'nbformat_valid': True,
          'generator_round_trip_identical': True, 'other_notebooks_unchanged': len(protected),
          'robot_executed': False}
(TASK / '恢复核查结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
