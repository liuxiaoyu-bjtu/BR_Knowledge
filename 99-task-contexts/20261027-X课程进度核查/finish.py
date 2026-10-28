"""核查进度数据和链接，暂存本轮文件与共享增量；不推送。"""
from pathlib import Path
from collections import Counter
import ast
import hashlib
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = '05-internal-materials/vocational-planning/03_X课程项目'
REPORT = PROJ + '/X课程当前进度.md'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    data = json.loads((TASK / '核查数据.json').read_text(encoding='utf-8'))
    rows = data['rows']
    expected = {f'U{unit}-L{lesson}' for unit in range(1, 9) for lesson in range(1, 5)}
    assert len(rows) == 32 and {r['course'] for r in rows} == expected
    assert dict(Counter(r['category'] for r in rows)) == data['phase_counts']
    assert sum(data['phase_counts'].values()) == 32
    assert [r['course'] for r in rows if r['notebook'] is None] == [f'U8-L{i}' for i in range(1, 5)]
    for folder, count in [('notebooks', 28), ('教学设计', 16), ('PPT内容设计', 16), ('PPT', 16), ('PPT/正式版', 1)]:
        assert data['inventory'][folder]['course_count'] == count
        for path in data['inventory'][folder]['files']:
            assert (ROOT / path).is_file()
    checked_links = 0
    for source in [ROOT / REPORT, TASK / '02-产出清单与状态日志.md']:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                assert (source.parent / target).resolve().exists(), target
                checked_links += 1
    for source, before_hash in data['source_sha256_before_status_update'].items():
        if source not in data['shared']:
            assert hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == before_hash, source
    rule = ROOT / '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
    u1 = next(line for line in rule.read_text(encoding='utf-8').splitlines() if line.startswith('| `03_X课程项目/notebooks/U1-L1_'))
    assert '⑥通过' in u1.split('|')[3] and '操作图示》尚未制作' in u1
    for name in ['audit.py', 'finish.py']:
        ast.parse((TASK / name).read_text(encoding='utf-8'))
    git('apply', '--reverse', '--check', str(TASK / '工作区状态增量.patch'))
    assert not git('diff', '--cached', '--name-only').strip(), '暂存区已有改动，先核对'
    git('apply', '--cached', '--check', str(TASK / '提交状态增量.patch'))
    result = {'courses': len(rows), 'phase_counts': data['phase_counts'], 'links_checked': checked_links,
              'source_records_unchanged_except_status_entries': True, 'formal_ppt_path_exists': True,
              'u1_l1_status_written': True, 'new_confirmation_inferred': False,
              'course_body_changed': False, 'ppt_content_read': False,
              'robot_commands_executed': False, 'push': False}
    (TASK / '校验结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    git('apply', '--cached', str(TASK / '提交状态增量.patch'))
    files = [REPORT]
    for child in TASK.rglob('*'):
        if child.is_file() and not {'before', '__pycache__'}.intersection(child.relative_to(TASK).parts):
            files.append(child.relative_to(ROOT).as_posix())
    git('add', '--', *files)
    git('diff', '--cached', '--check', '--', '.', ':(exclude)*.patch')
    print(json.dumps(result, ensure_ascii=False))
    print(git('diff', '--cached', '--stat').decode('utf-8'))


if __name__ == '__main__':
    main()
