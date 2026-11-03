"""本轮复核的导航增量与隔离提交；保留其他任务的工作区和暂存内容。"""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划'
PLAN = '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md'
TITLE = '足球策略与SDK封装复核（2026-11-03）'
SHARED = ['AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
          '05-internal-materials/vocational-planning/README.md',
          '01-booster-kb/07-tech-platform/_index.md',
          '01-booster-kb/07-tech-platform/booster-sdk.md']


def git(*args, data=None, env=None):
    result = subprocess.run(['git', *args], cwd=ROOT, input=data, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).decode('utf-8', 'replace'))
    return result.stdout


def update(name, raw):
    newline = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('utf-8').replace('\r\n', '\n')
    if name.endswith('/booster-sdk.md'):
        marker = '**持续供数案例（2026-11-03用户补充）**'
        if marker not in text:
            section = text.index('### 2.9 自动踢球管理器')
            end = text.index('\n---', section)
            start = text.find('**示例**：', section, end)
            if start < 0:
                start = end  # HEAD/暂存稿可能比工作区简短，仍只追加本轮说明。
            replacement = (
                marker + '：`update_ball()`需要在管理器活动期间持续输入当前身体米制球位；'
                '单帧调用后立即`stop()`不足以演示完整踢球。开发者给出的仿真代码采用约30Hz、'
                '0.99至0的100帧预设输入，见[策划案第17.4节](../../' + PLAN + ')。'
                '该代码本次未执行，不含视觉定位；真机应使用实际球位。\n\n'
                '用户转述开发者要求“持续更新直到0”，并确认0的特殊协议含义尚未说明；'
                '不据此补发假零值，也不以零值推断踢球完成。30Hz是示例频率，最低更新要求尚待确认。'
                '开发者另提醒踢后可能后退几步，场地与结束观察需覆盖这段动作。\n'
            )
            text = text[:start] + replacement + text[end:]
    elif TITLE not in text:
        target = PLAN
        if name == '05-internal-materials/vocational-planning/README.md':
            target = PLAN.split('vocational-planning/', 1)[1]
        elif name == '01-booster-kb/07-tech-platform/_index.md':
            target = '../../' + PLAN
        if name == 'CHANGELOG.md':
            added = (
                '## 2026-11-03｜' + TITLE + '\n\n'
                '策划案新增第17节：新旧搜索/追球策略、JSON可选性、应用与SDK职责及局部冗余；'
                '保留用户转述的开发者30Hz连续供数仿真案例，0的特殊含义待确认。'
                'k1_soccer.py更新为v0.1.1-draft，修正有效零坐标被拒绝的问题，37项离线检查通过。'
                '约2秒检测与0.35秒年龄条件不匹配仍未解决，近脚供数、踢后退步与退出待核实。'
                'HTML、便携包、SDK案例说明及U7交接同步；未运行机器人，未改课程Notebook或新增确认。'
                '[复核内容](' + target + ')。\n\n'
            )
        else:
            added = (
                '> **' + TITLE + '**：[策划案第17节](' + target + ')补充新旧策略、'
                '教师JSON可选性及SDK分工/冗余审核，保留开发者连续供数仿真案例。'
                'v0.1.1修正合法零坐标被拒绝，37项离线检查通过；0的特殊含义、近脚持续供数及踢后退出待核实，'
                '未运行机器人或新增课程确认。\n\n'
            )
        anchor = '# 技术平台\n\n' if name.endswith('/_index.md') else text[:text.index('\n\n') + 2]
        if name.endswith('/_index.md') and text.count(anchor) != 1:
            raise RuntimeError('ambiguous_navigation_anchor:' + name)
        text = text.replace(anchor, anchor + added, 1)
    return text.replace('\n', newline).encode('utf-8')


def stage(env, name, raw):
    blob = git('hash-object', '-w', '--path', name, '--stdin', data=raw).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644', blob, name, env=env)


if '--commit' not in sys.argv:
    before = TASK / 'before/review-20261103'
    for name in SHARED:
        path = ROOT / name
        raw = path.read_bytes()
        backup = before / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(raw)
        path.write_bytes(update(name, raw))
    print('Updated six navigation/API documents; preserved existing text.')
else:
    head = git('rev-parse', 'HEAD').decode().strip()
    original_index = git('ls-files', '--stage', '-z')
    staged_shared = {name: git('show', ':' + name) for name in SHARED}
    env = dict(os.environ, GIT_INDEX_FILE=str(TASK / 'review-20261103.index'))
    git('read-tree', head, env=env)
    for name in SHARED:
        stage(env, name, update(name, git('show', head + ':' + name)))
    scopes = [OUT.relative_to(ROOT).as_posix(), TASK.relative_to(ROOT).as_posix()]
    changed = git('diff', '--name-only', '-z', head, '--', *scopes)
    changed += git('ls-files', '--others', '--exclude-standard', '-z', '--', *scopes)
    own = sorted({name for name in changed.decode('utf-8').split('\0') if name})
    for name in own:
        path = ROOT / name
        if not path.is_file():
            raise RuntimeError('unexpected_deletion:' + name)
        stage(env, name, path.read_bytes())
    if git('rev-parse', 'HEAD').decode().strip() != head or git('ls-files', '--stage', '-z') != original_index:
        raise RuntimeError('HEAD or shared index changed; rerun')
    git('diff', '--cached', '--check', env=env)
    print(git('diff', '--cached', '--stat', env=env).decode('utf-8'))
    print(git('commit', '-m', 'fix: accept measured zero ball coordinates and review OS SDK soccer design', env=env).decode('utf-8'))
    commit = git('rev-parse', 'HEAD').decode().strip()
    for name in own:
        stage(None, name, git('show', commit + ':' + name))
    for name in SHARED:
        stage(None, name, update(name, staged_shared[name]))
    (TASK / 'before/review-20261103/receipt.json').write_text(
        json.dumps({'parent': head, 'commit': commit, 'task_files': own,
                    'shared': SHARED, 'prior_staging_preserved': True}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Existing staging preserved. Commit: ' + commit)
