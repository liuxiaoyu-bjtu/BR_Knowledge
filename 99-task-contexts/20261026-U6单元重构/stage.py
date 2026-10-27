"""只暂存本轮产物及共享文件增量；不提交其他工作、不推送。"""
from pathlib import Path
import difflib
import json
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ = '05-internal-materials/vocational-planning/03_X课程项目'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    assert not git('diff', '--cached', '--name-only').strip(), '暂存区已有内容，先核对'
    git('apply', '--cached', '--check', str(TASK / '联动暂存增量.patch'))
    git('apply', '--cached', str(TASK / '联动暂存增量.patch'))
    rule = '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
    source = (ROOT / rule).read_text(encoding='utf-8')
    note = next(line for line in source.splitlines() if line.startswith('> **U6本轮重构'))
    base = git('show', 'HEAD:' + rule).decode('utf-8').replace('\r\n', '\n')
    heading = next(line for line in base.splitlines() if line.startswith('# ')) + '\n'
    target = base.replace(heading, heading + '\n' + note + '\n', 1)
    patch = ''.join(difflib.unified_diff(base.splitlines(keepends=True), target.splitlines(keepends=True), fromfile='a/' + rule, tofile='b/' + rule))
    path = TASK / '规则暂存补充.patch'
    path.write_text(patch, encoding='utf-8', newline='\n')
    git('apply', '--cached', '--check', str(path))
    git('apply', '--cached', str(path))
    manifest = json.loads((TASK / '重构清单.json').read_text(encoding='utf-8'))
    paths = []
    for item in manifest['lessons']:
        paths.extend([item['path'], item['generator']])
    paths.append(PROJ + '/实验验证/U6_单元重构与动作编排核验.md')
    for child in TASK.rglob('*'):
        if child.is_file() and not {'before', '__pycache__'}.intersection(child.relative_to(TASK).parts):
            paths.append(child.relative_to(ROOT).as_posix())
    git('add', '--', *paths)
    # 补丁的空白上下文行由diff语法要求保留；其适用性由verify.py检查。
    git('diff', '--cached', '--check', '--', '.', ':(exclude)*.patch')
    print(git('diff', '--cached', '--stat').decode('utf-8'))


if __name__ == '__main__':
    main()
