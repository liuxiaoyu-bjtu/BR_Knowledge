from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

assert not git('diff', '--cached', '--name-only'), '其他任务正在暂存；不混合提交'
head = git('rev-parse', 'HEAD')
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8-sig'))
subprocess.run(['git', 'merge-base', '--is-ancestor', baseline['head'], head], cwd=ROOT, check=True)

# 读取本轮明确的插入规则；不执行其后面的工作区同步操作。
definitions = (TASK / '同步审核入口.py').read_text(encoding='utf-8').split("baseline = json.loads", 1)[0]
scope = {'__file__': str(TASK / '同步审核入口.py')}
exec(compile(definitions, str(TASK / '同步审核入口.py'), 'exec'), scope)
expected = set()
for name, (anchor, paragraph) in scope['rules'].items():
    head_text = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode('utf-8-sig')
    if paragraph in head_text:
        continue
    assert head_text.count(anchor) == 1, name
    updated = head_text.replace(anchor, anchor + '\n\n' + paragraph, 1)
    staged_file = TASK / 'head-increment' / name
    staged_file.parent.mkdir(parents=True, exist_ok=True)
    staged_file.write_text(updated, encoding='utf-8', newline='')
    blob = git('hash-object', '-w', '--path=' + name, str(staged_file))
    subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + name],
                   cwd=ROOT, check=True)
    expected.add(name)

course = '05-internal-materials/vocational-planning/03_X课程项目/实验验证/'
newfiles = [course + '足球方案联合审核_SDK能力与教学边界.md',
            course + '足球SDK能力与定位方案_分级测试计划.md',
            course + '足球SDK能力探查_只读.ipynb']
local = ['00-审核任务记录.md', '基线.json', '并行改动观察.json', '核查几何假设.py', '几何核查结果.json',
         '生成只读探查.py', '同步审核入口.py', '入口更新与暂存来源.json', '核查交付.py', '交付核查结果.json',
         '提交审核记录.py', 'sdk-evidence/README.md', 'sdk-evidence/来源清单.json', 'sdk-evidence/正文来源与哈希.json']
newfiles += [(TASK / name).relative_to(ROOT).as_posix() for name in local]
sources = json.loads((TASK / 'sdk-evidence/正文来源与哈希.json').read_text(encoding='utf-8'))
newfiles += [(TASK / source['file']).relative_to(ROOT).as_posix() for source in sources]
subprocess.run(['git', 'add', '--', *newfiles], cwd=ROOT, check=True)
expected.update(newfiles)
actual = set(git('-c', 'core.quotepath=false', 'diff', '--cached', '--name-only').splitlines())
assert actual == expected, (actual - expected, expected - actual)
assert git('rev-parse', 'HEAD') == head, 'HEAD在暂存过程中发生变化，先复核'
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
print(git('diff', '--cached', '--stat'))
(TASK / '提交清单.json').write_text(json.dumps(sorted(expected), ensure_ascii=False, indent=2), encoding='utf-8')
subprocess.run(['git', 'commit', '-m', '审核足球定位方案并补充SDK能力探查与分级测试计划'], cwd=ROOT, check=True)
print('本地提交：', git('rev-parse', '--short', 'HEAD'))
