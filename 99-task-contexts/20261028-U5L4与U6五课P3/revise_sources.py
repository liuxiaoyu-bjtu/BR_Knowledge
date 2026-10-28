from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
COURSE = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'

def load(lesson):
    paths = list((COURSE / 'notebooks').glob(lesson + '_*.ipynb'))
    assert len(paths) == 1
    path = paths[0]
    return path, json.loads(path.read_text(encoding='utf-8'))

def source(nb, number):
    return ''.join(nb['cells'][number - 1]['source'])

def change(nb, number, old, new):
    text = source(nb, number)
    assert text.count(old) == 1, (number, old)
    nb['cells'][number - 1]['source'] = text.replace(old, new).splitlines(keepends=True)

changes = []
path, nb = load('U6-L4')
change(nb, 1,
       '前一步成功后才进入下一步；未完成时停止启动后续动作并保留记录。',
       '结合动作实际表现与取消终态判断结果；未确认结束时不重复启动。')
change(nb, 4,
       '程序需要等待前一步进入终态，并检查状态是`SUCCEEDED`，再发起下一步。失败、取消或等待超时，都不能记作完成。',
       '本课当前实验版本先给动作一段运行时间，再调用`cancel()`请求释放任务；随后有限等待，返回`CANCELLED`才进入下一步。这个状态表示任务已取消，动作是否按设计完成还要结合现场观察。第一次等待达到上限，不会自动停止动作。')
change(nb, 4,
       '等待成功只解决了执行顺序，没有自动生成两个动作之间的过渡轨迹。',
       '确认任务结束只解决了任务衔接条件，没有自动生成两个动作之间的过渡轨迹。')
change(nb, 8, 'robot = BoosterRobot()\n',
       'robot = BoosterRobot()\nactive_motion = None\nplan_ready = False\nrun_log = []\n')
change(nb, 11,
       '`for step in prepared_steps`依次取出准备好的动作。`step[0]`、`step[1]`、`step[2]`分别是素材类型、文件名或ID、执行所需数据。',
       '`for source, resource, data in prepared_steps`依次取出准备好的动作，并把每项中的素材类型、文件名或ID、执行所需数据分别交给这三个变量。')
change(nb, 11,
       '`wait(timeout=45.0)`每步最多等待45秒，教师应根据所选动作时长调整。返回`SUCCEEDED`才继续下一步；其他状态都停止后续启动。超时不会自动停止机器人，此时保留句柄，由教师检查仍在运行的任务。',
       '轨迹先等待其记录时长加1秒，内置动作先等待5秒；教师须按已验证素材核对这些等待参数，不能把它们当作所有动作的完成时间。接着调用`cancel()`请求结束任务，再用`wait(timeout=5.0)`等待取消结果。当前代码取得`CANCELLED`才继续下一步，其他状态均停止后续启动。`CANCELLED`不能证明动作已经完整播放，现场还要记录动作表现。超时不会自动停止机器人，未确认结束时保留句柄，由教师检查。')
change(nb, 12, 'active_motion = None\nrun_log = []', 'run_log = []')
change(nb, 12, 'print("本步未成功完成，不启动后续动作")',
       'print("本步未取得预期的取消终态，不启动后续动作")')
change(nb, 13,
       '任务状态全部为成功时，仍需观察节奏、首尾姿态和动作间过渡是否符合设计。',
       '即使各步都取得`CANCELLED`，仍需逐项观察动作是否完整、节奏与首尾姿态是否符合设计。任务被取消与动作效果合意应分别记录。')
change(nb, 18,
       '且每步成功后才继续。',
       '且按本课版本在确认取消终态后继续，并分别记录动作表现。')
change(nb, 18,
       '记录能否区分任务成功、动作衔接效果与未执行步骤。',
       '记录能否区分任务结束方式、动作完整性与衔接效果、未执行步骤。')
change(nb, 18,
       '指出脚本中保存当前句柄、等待任务和判断成功的代码位置，解释各自作用。',
       '指出脚本中保存当前句柄、等待任务和判断是否继续的代码位置，解释各自作用。')
change(nb, 18,
       '`active_motion`、`wait()`、`done()`及`SUCCEEDED`判断',
       '`active_motion`保存句柄，两次`wait()`分别等待运行与取消结果，`cancel()`提交取消请求，当前版本以`CANCELLED`决定是否继续；`done()`用于重跑前核对，动作完整性另据现场观察')
path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
changes.append({'lesson': 'U6-L4', 'cells': [1, 4, 8, 11, 12, 13, 18],
                'reason': '用户确认等待后取消的真机用法；同步表述与评价，并把句柄初始化移至首次连接格'})

path, nb = load('U6-L2')
change(nb, 10, 'print("已保存到 my_action.btraj")', 'print("已保存到 my_action_v1.btraj")')
change(nb, 15, '待站立稳定后，；再由人工扶着', '待站立稳定后，再由人工扶着')
path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
changes.append({'lesson': 'U6-L2', 'cells': [10, 15], 'reason': '保存提示与实际路径一致；删去收尾说明中的多余标点，不改调用逻辑'})

for lesson, number in [('U5-L4', 20), ('U6-L1', 21), ('U6-L2', 22), ('U6-L3', 23), ('U6-L4', 24)]:
    path, nb = load(lesson)
    generator = COURSE / f'_gen_L{number}.py'
    content = '# -*- coding: utf-8 -*-\n'
    content += repr(f'{lesson} Notebook反向同步镜像。2026-10-28以用户当前稿为准。P2通过，P3教学设计待确认④；禁止运行旧生成器覆盖Notebook。') + '\n'
    content += 'import json, os\n'
    content += 'OUT = os.path.join(os.path.dirname(__file__), "notebooks", ' + repr(path.name) + ')\n'
    content += 'cells = []\n'
    for cell in nb['cells']:
        content += 'cells.append(' + repr(cell) + ')\n'
    shell = {key: value for key, value in nb.items() if key != 'cells'}
    content += 'notebook = ' + repr(shell) + '\n'
    content += 'notebook["cells"] = cells\n'
    content += 'if __name__ == "__main__":\n'
    content += '    with open(OUT, "w", encoding="utf-8") as output:\n'
    content += '        json.dump(notebook, output, ensure_ascii=False, indent=1)\n'
    content += '        output.write("\\n")\n'
    ast.parse(content)
    generator.write_text(content, encoding='utf-8')

(TASK / '源文件调整.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
print('已同步两课的小范围修订及五课生成器；未运行任何生成器或机器人代码')
