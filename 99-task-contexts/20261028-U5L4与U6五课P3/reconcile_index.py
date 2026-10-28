from pathlib import Path
import difflib
import importlib.util
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('p3_updates', TASK / 'update_records.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
patch = []
for base in (TASK / 'head').rglob('*'):
    if not base.is_file():
        continue
    rel = base.relative_to(TASK / 'head').as_posix()
    old_head = base.read_text(encoding='utf-8')
    expected = module.update(rel, old_head)
    if expected == old_head:
        continue
    staged = subprocess.check_output(['git', 'show', ':' + rel], cwd=ROOT).decode('utf-8')
    if staged == expected:
        continue
    patch.extend(difflib.unified_diff(staged.splitlines(keepends=True), expected.splitlines(keepends=True),
                                     fromfile='a/' + rel, tofile='b/' + rel))
if patch:
    path = TASK / '暂存补充.patch'
    path.write_bytes(''.join(patch).encode('utf-8'))
    subprocess.run(['git','apply','--cached','--check',str(path)], cwd=ROOT, check=True)
    subprocess.run(['git','apply','--cached',str(path)], cwd=ROOT, check=True)
print('共享记录暂存内容已与本轮目标一致；未暂存其他历史差异')
