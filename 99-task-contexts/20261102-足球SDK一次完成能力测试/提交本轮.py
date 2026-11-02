from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
assert sys.argv[1:] in [['stage'], ['commit']]
if sys.argv[1] == 'stage':
    assert not git('diff', '--cached', '--name-only'), '其他任务已有暂存，先保留'
    head = git('rev-parse', 'HEAD')
    scope = runpy.run_path(str(TASK / '同步入口.py'))
    expected = set()
    for name in base['shared']:
        old = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode('utf-8-sig')
        updated = scope['change'](name, old)
        p = TASK / 'head-increment' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(updated, encoding='utf-8', newline='')
        blob = git('hash-object', '-w', '--path=' + name, str(p))
        subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + name], cwd=ROOT, check=True)
        expected.add(name)
    new = base['replace'] + [C + '/实验验证/足球测试_第4轮_完整能力验证.ipynb']
    local = ['基线.json', '公共代码.py', '生成完整测试.py', '同步入口.py', '联动记录.json',
             '离线核查.py', '离线核查结果.json', '完成记录.md', '提交本轮.py']
    new += [(TASK / n).relative_to(ROOT).as_posix() for n in local]
    subprocess.run(['git', 'add', '--', *new], cwd=ROOT, check=True)
    expected.update(new)
    actual = set(git('-c', 'core.quotePath=false', 'diff', '--cached', '--name-only').splitlines())
    assert actual == expected, (actual - expected, expected - actual)
    assert git('rev-parse', 'HEAD') == head
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    (TASK / '提交清单.json').write_text(json.dumps({'head': head, 'paths': sorted(expected), 'tree': git('write-tree')}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('精确暂存', len(expected), '项。')
else:
    manifest = json.loads((TASK / '提交清单.json').read_text(encoding='utf-8'))
    assert git('rev-parse', 'HEAD') == manifest['head'] and git('write-tree') == manifest['tree']
    for name, expected in base['protected'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    subprocess.run(['git', 'commit', '-m', '合并足球SDK完整能力测试，以一次现场记录决策U7课程边界'], cwd=ROOT, check=True)
    assert not git('diff', '--cached', '--name-only')
    print(git('log', '-1', '--oneline'))
