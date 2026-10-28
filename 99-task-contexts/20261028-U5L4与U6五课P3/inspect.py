from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
SHARED = [
    'AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
    '05-internal-materials/vocational-planning/README.md',
    '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
    '05-internal-materials/vocational-planning/03_X课程项目/X课程当前进度.md',
    '05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md',
    '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_P2复核与定稿记录.md',
    '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U6_单元重构与动作编排核验.md',
]
LESSONS = ['U5-L4', 'U6-L1', 'U6-L2', 'U6-L3', 'U6-L4']

def notebook(lesson):
    matches = list((COURSE / 'notebooks').glob(lesson + '_*.ipynb'))
    assert len(matches) == 1, matches
    return matches[0]

if sys.argv[1] == 'snapshot':
    assert not (TASK / '输入指纹.json').exists(), '已有基线，禁止覆盖'
    paths = [ROOT / p for p in SHARED] + [notebook(k) for k in LESSONS]
    paths += [COURSE / f'_gen_L{k}.py' for k in (20, 21, 22, 23, 24)]
    manifest = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        target = TASK / 'before' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        manifest[rel] = hashlib.sha256(raw).hexdigest()
        old = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=ROOT, capture_output=True)
        if old.returncode == 0:
            target = TASK / 'head' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(old.stdout)
    (TASK / '输入指纹.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    status = subprocess.check_output(['git', 'status', '--porcelain', '-z'], cwd=ROOT)
    (TASK / 'before' / 'git-status.z').write_bytes(status)
    print('已保存', len(manifest), '份输入指纹及工作区/HEAD基线')
elif sys.argv[1] in ('nb', 'nbslice'):
    lessons = sys.argv[2:] if sys.argv[1] == 'nb' else [sys.argv[2]]
    for lesson in lessons:
        path = notebook(lesson)
        nb = json.loads(path.read_text(encoding='utf-8'))
        print('\nFILE', path.relative_to(ROOT).as_posix())
        for i, cell in enumerate(nb['cells'], 1):
            if sys.argv[1] == 'nbslice' and not int(sys.argv[3]) <= i <= int(sys.argv[4]):
                continue
            print(f'\n--- 第{i}格 {cell["cell_type"]} ---')
            print(''.join(cell['source']))
elif sys.argv[1] == 'section':
    path = ROOT / sys.argv[2]
    lines = path.read_text(encoding='utf-8').splitlines()
    start, stop = int(sys.argv[3]), int(sys.argv[4])
    for i in range(start - 1, min(stop, len(lines))):
        print(f'{i+1}: {lines[i]}')
