"""隔离提交本任务；共享导航仅提交本次增量，不吞并既有暂存内容。"""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划'
spec = importlib.util.spec_from_file_location('navigation', TASK / 'update_navigation.py')
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)
shared = ['AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
          '05-internal-materials/vocational-planning/README.md',
          '01-booster-kb/07-tech-platform/_index.md']


def git(*args, data=None, env=None):
    result = subprocess.run(['git', *args], cwd=ROOT, input=data, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).decode('utf-8', 'replace'))
    return result.stdout


def insert(raw, name):
    text = raw.decode('utf-8-sig')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    normalized = text.replace('\r\n', '\n')
    return nav.update(name, normalized).replace('\n', newline).encode('utf-8')


def stage_blob(index_env, name, raw):
    blob = git('hash-object', '-w', '--path', name, '--stdin', data=raw).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644', blob, name, env=index_env)


head = git('rev-parse', 'HEAD').decode().strip()
branch = git('branch', '--show-current').decode().strip()
alt = dict(os.environ, GIT_INDEX_FILE=str(TASK / 'commit.index'))
git('read-tree', head, env=alt)
original_index = git('ls-files', '--stage', '-z')
original_shared = {name: git('show', ':' + name) for name in shared}
for name in shared:
    stage_blob(alt, name, insert(git('show', head + ':' + name), name))

new_files = []
for base in [OUT, TASK]:
    for file in base.rglob('*'):
        if not file.is_file():
            continue
        relative = file.relative_to(TASK) if base == TASK else file.relative_to(OUT)
        if any(part in {'before', '__pycache__'} for part in relative.parts):
            continue
        if (file.name == 'index.before' or file.name.endswith(('.index', '.index.lock', '_审查.png'))
                or file.name in {'提交记录.json', '提交预览.json'}):
            continue
        name = file.relative_to(ROOT).as_posix()
        new_files.append(name)
        stage_blob(alt, name, file.read_bytes())

names = git('diff', '--cached', '--name-only', env=alt).decode('utf-8').splitlines()
preview = {'head': head, 'branch': branch, 'files': names,
           'stat':git('diff', '--cached', '--stat', env=alt).decode('utf-8')}
(TASK / '提交预览.json').write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding='utf-8')
if '--commit' not in sys.argv:
    print(preview['stat'])
    print('dry-run only')
    raise SystemExit(0)
if git('rev-parse', 'HEAD').decode().strip() != head or git('ls-files', '--stage', '-z') != original_index:
    raise RuntimeError('HEAD or real index changed during preparation; rerun')
git('diff', '--cached', '--check', env=alt)
commit_output = git('commit', '-m', 'docs: plan K1 soccer workflow on OS SDK with single-file draft', env=alt).decode('utf-8')
commit = git('rev-parse', 'HEAD').decode().strip()
# 将本次新增文件纳入真实索引；共享文件在原暂存版本上加入同一导航增量。
for name in new_files:
    stage_blob(None, name, git('show', commit + ':' + name))
for name in shared:
    stage_blob(None, name, insert(original_shared[name], name))
record = {'commit':commit, 'parent':head, 'branch':branch, 'files':len(names),
          'shared_navigation':shared, 'existing_staging_preserved':True,
          'commit_output':commit_output, 'push':'pending'}
(TASK / '提交记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(commit_output)
print('real index reconciled; pre-existing staged content preserved')
