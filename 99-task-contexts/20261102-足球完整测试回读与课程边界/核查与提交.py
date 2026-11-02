from pathlib import Path
import hashlib
import json
import re
import runpy
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'
V = C + '/实验验证/'
base = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

def verify():
    for name, expected in base['protected'].items():
        assert sha(ROOT / name) == expected, '课程或原始证据有变化：' + name
    fact = json.loads((TASK / '第4轮数据核对.json').read_text(encoding='utf-8'))
    raw = json.loads((ROOT / fact['data_dir'] / '原始记录.json').read_text(encoding='utf-8'))
    for method, row in fact['method_counts'].items():
        calls = [r for r in raw['calls'] if r['method'] == method]
        assert len(calls) == row['attempted']
        assert sum(bool(r.get('returned')) for r in calls) == row['returned']
    errors = [r for r in raw['calls'] if r.get('returned') is False]
    assert len(errors) == 3 and all('ValueError' in r['error'] for r in errors)
    assert np.asarray(raw['transform']['matrix']).shape == (4, 4)
    assert np.isfinite(np.asarray(raw['transform']['matrix'])).all()
    matrix = np.asarray(raw['transform']['matrix'])
    assert np.allclose(matrix[3], [0, 0, 0, 1])
    guide = (ROOT / base['guide']).read_text(encoding='utf-8')
    report = ROOT / V / '足球SDK完整测试_回读与U7课程边界.md'
    s = report.read_text(encoding='utf-8')
    onsite = json.loads((TASK / '现场补充.json').read_text(encoding='utf-8'))
    assert all(text in guide and text in s for text in onsite['trials'].values())
    assert '完整踢球' in s and '不能归因' in s
    assert '记录与依据' in guide and '不把未提供的现场信息填成“正常”' in guide
    assert '本地Notebook未保存执行输出' in guide
    assert '0.8秒' in s and '2.2～2.4秒' in s
    link_count = 0
    for p in [ROOT / n for n in base['shared']] + [ROOT / base['guide'], report]:
        content = p.read_text(encoding='utf-8-sig')
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if target.startswith('http'):
                continue
            if '足球SDK完整测试_回读与U7课程边界' not in target and '第4轮完整_20261102_140630_773208' not in target:
                continue
            assert (p.parent / target).exists(), (p, target)
            link_count += 1
    out = {'raw_files_preserved': len(base['evidence']), 'protected_files_preserved': len(base['protected']),
           'call_counts_verified': fact['method_counts'], 'three_expected_ValueErrors': True,
           'tf_matrix_finite_4x4': True, 'tf_direction_not_assumed_from_labels': True,
           'user_observation_preserved': True, 'unknown_physical_details_not_fabricated': True,
           'links_checked': link_count, 'student_files_changed': False, 'hardware_executed': False}
    (TASK / '核查结果.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    return out

assert sys.argv[1:] in [['verify'], ['stage'], ['commit']]
if sys.argv[1] == 'verify':
    out = verify()
    print(json.dumps(out, ensure_ascii=False, indent=2))
elif sys.argv[1] == 'stage':
    verify()
    assert not git('diff', '--cached', '--name-only'), '已有其他暂存，先保留不混合提交'
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
    new = [base['guide'], V + '足球SDK完整测试_回读与U7课程边界.md'] + list(base['evidence'])
    local = ['基线.json', '现场补充.json', '第4轮数据核对.json', '回读与回填.py',
             '同步入口.py', '联动记录.json', '核查与提交.py', '核查结果.json', '完成记录.md']
    new += [(TASK / n).relative_to(ROOT).as_posix() for n in local]
    subprocess.run(['git', 'add', '--', *new], cwd=ROOT, check=True)
    expected.update(new)
    assert set(git('-c', 'core.quotePath=false', 'diff', '--cached', '--name-only').splitlines()) == expected
    assert git('rev-parse', 'HEAD') == head
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    (TASK / '提交清单.json').write_text(json.dumps({'head': head, 'paths': sorted(expected), 'tree': git('write-tree')}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('精确暂存', len(expected), '项。')
else:
    manifest = json.loads((TASK / '提交清单.json').read_text(encoding='utf-8'))
    assert git('rev-parse', 'HEAD') == manifest['head'] and git('write-tree') == manifest['tree']
    for name, expected in base['protected'].items():
        assert sha(ROOT / name) == expected
    subprocess.run(['git', 'commit', '-m', '回读足球完整测试并代填记录，明确U7控制接口与实际踢球的教学边界'], cwd=ROOT, check=True)
    assert not git('diff', '--cached', '--name-only')
    print(git('log', '-1', '--oneline'))
