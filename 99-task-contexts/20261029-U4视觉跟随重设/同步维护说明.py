from pathlib import Path
import ast
import difflib

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
tool = P / '_regen_from_nb.py'
before = tool.read_text(encoding='utf-8-sig')
backup = TASK / 'before' / tool.relative_to(ROOT)
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_bytes(tool.read_bytes())
descriptions = {
    '_gen_L15.py': 'U4-L3移动目标视觉跟随，25格/10代码；方向偏差与L2实测框高阈值决定跟进/暂停，IMU/odom记录运动；新稿待①②。',
    '_gen_L16.py': 'U4-L4视觉跟随与接待联调，31格/13代码；等待、跟随、连续到位、致意前复核和任务退出，停稳后分析位移朝向；新稿待①②。',
}
lines = before.splitlines(keepends=True)
for i, line in enumerate(lines):
    for name, description in descriptions.items():
        if line.lstrip().startswith(repr(name) + ':'):
            lines[i] = '    ' + repr(name) + ': ' + repr(description) + ',\n'
after = ''.join(lines)
assert before != after
ast.parse(after)
tool.write_text(after, encoding='utf-8')
(TASK / '维护工具说明增量.patch').write_text(''.join(difflib.unified_diff(
    before.splitlines(True), after.splitlines(True),
    fromfile=tool.relative_to(ROOT).as_posix(), tofile=tool.relative_to(ROOT).as_posix(), n=0)), encoding='utf-8')
print('本地维护工具说明已同步，仅保存本轮增量补丁。')
