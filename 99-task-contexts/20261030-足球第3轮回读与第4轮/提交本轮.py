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
    assert not git('diff', '--cached', '--name-only'), '暂存区有其他任务，先保留，不混合提交'
    head = git('rev-parse', 'HEAD')
    subprocess.run(['git', 'merge-base', '--is-ancestor', base['head'], head], cwd=ROOT, check=True)
    scope = runpy.run_path(str(TASK / '回填与同步.py'))
    expected = set()
    for name in base['shared']:
        if name.endswith('/足球测试_第3轮_操作与记录.md'):
            subprocess.run(['git', 'add', '--', name], cwd=ROOT, check=True)
        else:
            old = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode('utf-8-sig')
            updated = scope['change'](name, old)
            staged = TASK / 'head-increment' / name
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(updated, encoding='utf-8', newline='')
            blob = git('hash-object', '-w', '--path=' + name, str(staged))
            subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + name], cwd=ROOT, check=True)
        expected.add(name)
    new = [C + '/实验验证/足球测试_第4轮_操作与记录.md',
           C + '/实验验证/足球测试_第4轮_管理器创建与启停.ipynb'] + list(base['evidence'])
    local = ['基线.json', '生成第4轮.py', '回填与同步.py', '联动记录.json', '离线核查.py',
             '离线核查结果.json', '第3轮数据核对.json', '完成记录.md', '提交本轮.py']
    new += [(TASK / name).relative_to(ROOT).as_posix() for name in local]
    subprocess.run(['git', 'add', '--', *new], cwd=ROOT, check=True)
    expected.update(new)
    actual = set(git('-c', 'core.quotepath=false', 'diff', '--cached', '--name-only').splitlines())
    assert actual == expected, (actual - expected, expected - actual)
    assert git('rev-parse', 'HEAD') == head, 'HEAD出现并行修改，先核查'
    manifest = {'head_at_stage': head, 'paths': sorted(expected), 'staged_tree': git('write-tree')}
    (TASK / '提交清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    print('已精确暂存', len(expected), '项，等待内容复核后本地提交。')
else:
    manifest = json.loads((TASK / '提交清单.json').read_text(encoding='utf-8'))
    assert git('rev-parse', 'HEAD') == manifest['head_at_stage']
    assert git('write-tree') == manifest['staged_tree'], '暂存区已变化，先核查'
    for field in ['protected', 'evidence']:
        for name, expected in base[field].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    subprocess.run(['git', 'commit', '-m', '回读足球第3轮并纠正测试归因，准备管理器实际启停与重启测试'], cwd=ROOT, check=True)
    assert not git('diff', '--cached', '--name-only')
    print(git('log', '-1', '--oneline'))
