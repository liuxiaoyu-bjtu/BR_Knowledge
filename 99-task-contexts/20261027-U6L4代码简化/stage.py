"""隔离其他任务改动，仅暂存本次L4简化。"""
from pathlib import Path
import json
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    assert not git('diff', '--cached', '--name-only').strip(), '暂存区已有改动，先核对'
    git('apply', '--cached', '--check', str(TASK / '提交增量.patch'))
    git('apply', '--cached', str(TASK / '提交增量.patch'))
    manifest = json.loads((TASK / '修改清单.json').read_text(encoding='utf-8'))
    files = [manifest['notebook'], manifest['generator'], manifest['report']]
    for child in TASK.rglob('*'):
        if child.is_file() and not {'before', '__pycache__'}.intersection(child.relative_to(TASK).parts):
            files.append(child.relative_to(ROOT).as_posix())
    git('add', '--', *files)
    # 补丁上下文空行保留diff格式，适用性另由verify.py核对。
    git('diff', '--cached', '--check', '--', '.', ':(exclude)*.patch')
    print(git('diff', '--cached', '--stat').decode('utf-8'))


if __name__ == '__main__':
    main()
