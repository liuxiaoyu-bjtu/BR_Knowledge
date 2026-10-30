from pathlib import Path
import json
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()

assert not git('diff', '--cached', '--name-only'), '其他任务有暂存，请保留并等待，不混合提交'
head = git('rev-parse', 'HEAD')
baseline = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))
subprocess.run(['git', 'merge-base', '--is-ancestor', baseline['head'], head], cwd=ROOT, check=True)
scope = runpy.run_path(str(TASK / '回填与同步.py'))
expected = set()
user_record = C + '/实验验证/足球测试_第1轮_操作与记录.md'
for name in baseline['shared']:
    if name == user_record:
        # 用户现场记录及本轮助手结论一并存档，不用HEAD中的空表覆盖填写内容。
        subprocess.run(['git', 'add', '--', name], cwd=ROOT, check=True)
    else:
        original = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode('utf-8-sig')
        updated = scope['change'](name, original)
        staged_path = TASK / 'head-increment' / name
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        staged_path.write_text(updated, encoding='utf-8', newline='')
        blob = git('hash-object', '-w', '--path=' + name, str(staged_path))
        subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + name], cwd=ROOT, check=True)
    expected.add(name)

new = [C + '/实验验证/足球测试_第2轮_操作与记录.md', C + '/实验验证/足球测试_第2轮_深度与坐标接口.ipynb']
new += list(baseline['evidence'])
local = ['基线.json', '逐帧候选核对.json', '生成第2轮.py', '回填与同步.py', '回填与联动记录.json',
         '离线核查.py', '离线核查结果.json', '完成记录.md', '提交本轮.py']
new += [(TASK / name).relative_to(ROOT).as_posix() for name in local]
subprocess.run(['git', 'add', '--', *new], cwd=ROOT, check=True)
expected.update(new)
actual = set(git('-c', 'core.quotepath=false', 'diff', '--cached', '--name-only').splitlines())
assert actual == expected, (actual - expected, expected - actual)
assert git('rev-parse', 'HEAD') == head, '暂存中HEAD发生变化，请复核'
subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
(TASK / '提交清单.json').write_text(json.dumps(sorted(expected), ensure_ascii=False, indent=2), encoding='utf-8')
print('本轮精确暂存：', len(expected), '项，含用户第1轮原始证据44份。')
subprocess.run(['git', 'commit', '-m', '回读足球第1轮能力结果并安排第2轮SDK数据与管理器接口核查'], cwd=ROOT, check=True)
print(git('log', '-1', '--oneline'))
