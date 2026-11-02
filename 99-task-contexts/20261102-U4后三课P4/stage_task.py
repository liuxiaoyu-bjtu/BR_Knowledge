"""仅暂存本轮增量，保留共享文件中其他任务的工作区改动。"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = '05-internal-materials/vocational-planning/03_X课程项目'


def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=ROOT, **kwargs)


def main():
    already_staged = set(filter(None, git('diff', '--cached', '--name-only', '-z').decode('utf-8').split('\0')))
    assert git('rev-parse', '--short', 'HEAD').decode().strip() == '8dbfd90', 'HEAD已改变，请先核查'
    baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
    modified = json.loads((TASK / '本轮修改清单.json').read_text(encoding='utf-8'))['modified']
    payloads = {}
    for rel in modified:
        head = git('show', 'HEAD:' + rel)
        assert hashlib.sha256(head).hexdigest() == baseline[rel]['head_sha256'], rel
        payloads[rel] = (TASK / 'head-increment' / rel).read_bytes()
    # 当前进度的HEAD旧表尚未反映既有五课P5，提交时保持总表与逐课行一致。
    progress_rel = PROJECT + '/X课程当前进度.md'
    progress = payloads[progress_rel].decode('utf-8').replace('\r\n', '\n')
    current = (ROOT / progress_rel).read_text(encoding='utf-8')
    section = current.split('## 1. 当前分布', 1)[1].split('## 2.', 1)[0]
    progress = re.sub(r'## 1\. 当前分布[\s\S]+?(?=## 2\.)', lambda _: '## 1. 当前分布' + section, progress, count=1)
    for code in ['U5-L4', 'U6-L1', 'U6-L2', 'U6-L3', 'U6-L4']:
        row = next(line for line in current.splitlines() if line.startswith('| [' + code + ' '))
        progress = re.sub(r'(?m)^\| \[' + code + r' [^\n]+$', lambda _: row, progress, count=1)
    ppt_row = next(line for line in current.splitlines() if line.startswith('| PPT文件 |'))
    progress = re.sub(r'(?m)^\| PPT文件 \|[^\n]+$', lambda _: ppt_row, progress, count=1)
    distribution = progress.split('## 1. 当前分布', 1)[1].split('## 2.', 1)[0]
    assert sum(map(int, re.findall(r'(?m)^\| [^|]+ \| (\d+) \|', distribution))) == 32
    payloads[progress_rel] = progress.encode('utf-8')
    filenames = [
        'U4-L2_走近来宾_PPT内容大纲.md',
        'U4-L3_跟住来宾_PPT内容大纲.md',
        'U4-L4_接待来宾_PPT内容大纲.md',
        'U4-L2-L3-L4_P4覆盖检查记录.md',
    ]
    for name in filenames:
        rel = PROJECT + '/PPT内容设计/' + name
        assert subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + rel], cwd=ROOT, capture_output=True).returncode != 0, rel
        payloads[rel] = (ROOT / rel).read_bytes()
    for name in [
        'build_p4.py', 'p4_content.py', 'sync_status.py', 'verify.py',
        'stage_task.py', '基线.json', '本轮修改清单.json',
        '页面与覆盖清单.json', '离线核查结果.json', '02-产出清单与状态日志.md',
    ]:
        path = TASK / name
        payloads[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    assert already_staged <= set(payloads), '暂存区存在本轮清单以外的改动'
    for rel, data in payloads.items():
        # hash-object不经过autocrlf过滤，文本须在写入Git对象前统一为LF。
        data = data.replace(b'\r\n', b'\n')
        blob = git('hash-object', '-w', '--stdin', input=data).decode().strip()
        git('update-index', '--add', '--cacheinfo', '100644', blob, rel)
    staged = set(git('diff', '--cached', '--name-only', '-z').decode('utf-8').strip('\0').split('\0'))
    assert staged == set(payloads), '暂存文件与清单不一致'
    git('diff', '--cached', '--check')
    print(f'已精准暂存{len(payloads)}份文件；共享文件只暂存本轮增量。')


if __name__ == '__main__':
    main()
