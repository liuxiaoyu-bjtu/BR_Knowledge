from pathlib import Path
import ast
import hashlib
import json
import pprint

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
BASE = json.loads((TASK / '基线.json').read_text(encoding='utf-8'))


def protect_loop(source):
    tree = ast.parse(source)
    loop = next(node for node in tree.body if isinstance(node, ast.For))
    index = tree.body.index(loop)
    stop = tree.body[index + 1]
    assert isinstance(stop, ast.Expr)
    assert ast.unparse(stop.value) == 'robot.set_velocity(0, 0, 0)'
    lines = source.splitlines(keepends=True)
    before = ''.join(lines[:loop.lineno - 1])
    loop_text = ''.join(lines[loop.lineno - 1:loop.end_lineno])
    assert loop_text.count('        break') == 1
    loop_text = loop_text.replace('        break', '        stop_reason = "里程计读数已接近计划行进量"\n        break')
    tail = ''.join(lines[stop.end_lineno:])
    tail = tail.replace('已停止。里程计估计行进量', '已发送停止指令。循环末次里程计估计行进量')
    tail = tail.replace('已停下。里程计估计行进量', '已发送停止指令。循环末次里程计估计行进量')
    return (before + 'stop_reason = "执行中断或异常，未完成本次行进"\n'
            + 'try:\n' + ''.join('    ' + line if line.strip() else line for line in loop_text.splitlines(keepends=True))
            + '    if remain > 0.02:\n'
            + '        stop_reason = "达到轮数上限，尚未确认计划行进量"\n'
            + 'finally:\n'
            + '    robot.set_velocity(0, 0, 0)\n\n'
            + 'print("本轮结束原因：", stop_reason)\n' + tail)


rel = P / 'notebooks/U4-L2_走近来宾.ipynb'
path = ROOT / rel
before = path.read_bytes()
assert hashlib.sha256(before).hexdigest() == BASE['files'][rel.as_posix()]
nb = json.loads(before)
for number in (16, 19):
    nb['cells'][number - 1]['source'] = protect_loop(''.join(nb['cells'][number - 1]['source'])).splitlines(keepends=True)
for number in (15, 18):
    text = ''.join(nb['cells'][number - 1]['source']).rstrip()
    text += '\n\n程序用`try/finally`保留停止指令：正常退出或发生可处理的异常、中断时，都会尝试发送零速度。输出分别记录读数接近计划值或达到轮数上限；异常、中断时保留报错。发送了停止指令后，还需现场确认停稳；断网或强制结束内核时按已学按钮流程处理。\n'
    nb['cells'][number - 1]['source'] = text.splitlines(keepends=True)
assert path.read_bytes() == before
path.write_bytes((json.dumps(nb, ensure_ascii=False, indent=1) + '\n').encode('utf-8'))

gen = ROOT / P / '_gen_L14.py'
old_gen = gen.read_bytes()
text = ('# -*- coding: utf-8 -*-\n'
        '"""U4-L2学生Notebook完整镜像；P2停止路径修订，两格定向真机补验待确认。"""\n'
        'import json\nfrom pathlib import Path\nNOTEBOOK = '
        + pprint.pformat(nb, width=110, sort_dicts=False) + '\n'
        'if __name__ in ("__main__", "__gen__"):\n'
        '    path = Path(__file__).parent / "notebooks" / ' + repr(rel.name) + '\n'
        '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
assert gen.read_bytes() == old_gen
gen.write_bytes(text.encode('utf-8'))

with (TASK / '用户确认.md').open('a', encoding='utf-8', newline='\n') as record:
    record.write('\n用户对两格停止路径最小修订的明确答复：\n\n> 同意最小修订，两格补验后再通过P2\n\n据此修订L2第16、19格及紧邻说明；L2的③等待这两格真机补验，不能仅凭离线分支测试通过。\n')

print('L2第16、19格已加最小try/finally和结束原因；第15、18格说明同步，其他单元格保留。')
