from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
import runpy
import shutil
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
T = Path(__file__).resolve().parent
base = json.loads((T/'基线.json').read_text(encoding='utf-8'))
result = {'robot_executed': False, 'notebooks': [], 'cases': []}


def check(condition, name):
    assert condition, name
    result['cases'].append(name)


try:
    import nbformat
except ImportError:
    nbformat = None

for i in range(25,33):
    unit, lesson = (7,i-24) if i<29 else (8,i-28)
    f = next((P/'notebooks').glob(f'U{unit}-L{lesson}_*.ipynb'))
    nb = json.loads(f.read_text(encoding='utf-8'))
    ids = [c['id'] for c in nb['cells']]
    assert len(set(ids)) == len(ids)
    all_text = '\n'.join(''.join(c['source']) for c in nb['cells'])
    assert not re.search(r'\[sss\]|<sss>', all_text, re.I)
    if nbformat:
        nbformat.validate(nb)
    headings = re.findall(r'^### (\d+)\.(\d+)\s+', all_text, re.M)
    for parent in {x for x,y in headings}:
        assert len([y for x,y in headings if x==parent]) >= 2, (f.name, '孤立子标题',parent)
    before = json.loads((T/'before'/f.relative_to(ROOT)).read_text(encoding='utf-8'))
    old = {c['id']: c for c in before['cells']}
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            ast.parse(''.join(c['source']))
        if c['id'] in old:
            assert c['metadata'] == old[c['id']]['metadata']
            if c['cell_type']=='code':
                assert c['outputs'] == old[c['id']]['outputs']
                assert c['execution_count'] == old[c['id']]['execution_count']
    with tempfile.TemporaryDirectory(prefix='u7u8-generator-') as temp:
        temp = Path(temp)
        (temp/'notebooks').mkdir()
        gen = temp/f'_gen_L{i}.py'
        shutil.copy2(P/gen.name, gen)
        runpy.run_path(str(gen))
        generated = json.loads((temp/'notebooks'/f.name).read_text(encoding='utf-8'))
        assert generated == nb
    result['notebooks'].append({'name':f.name,'cells':len(nb['cells']),
                                'code':sum(c['cell_type']=='code' for c in nb['cells']),
                                'generator_equal': True})

for rel, digest in base['protected'].items():
    assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() == digest, rel
check(True, 'U1～U6全部主Notebook字节未变')
check(True, '八课语法、ID、标签、子标题和生成器镜像核查通过')

for f in list((P/'notebooks/x_lab').glob('*.py'))+[P/'notebooks/u8_team_template.py']:
    ast.parse(f.read_text(encoding='utf-8'))
sys.path.insert(0, str(P/'notebooks'))
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('checked_team', P/'notebooks/u8_team_template.py')
team = importlib.util.module_from_spec(spec)
spec.loader.exec_module(team)  # 文件导入不执行SDK调用。
from x_lab.flows import new_session, cleanup


def config(theme='导览'):
    team.THEME = theme
    team.STEPS = ['观察','介绍','再观察','致意' if theme=='导览' else '试踢']
    team.INTRODUCTION = '离线测试文本'
    team.GREET_ID = 'validated-action'
    team.KICK_SECONDS, team.KICK_DIRECTION, team.KICK_POWER = 6.0,0.0,1.0


def session():
    return new_session(object(), object())


config()
check(team.validate()==[], '完整导览配置通过静态检查')
team.STEPS.append('致意')
check(bool(team.validate()), '重复或不匹配基础步骤被拒绝')
config('踢球')
team.KICK_DIRECTION = float('nan')
check(bool(team.validate()), '非有限踢球参数被拒绝')

config()
s = session()
with patch.object(team,'observe',side_effect=['完成','完成']) as obs, \
     patch.object(team,'introduce',return_value='完成') as intro, \
     patch.object(team,'act',return_value='完成') as act:
    log=team.run_project(s,{'导览':object()},None)
    check([r['step'] for r in log]==team.STEPS and all(r['result']=='完成' for r in log),
          '正常路径依次执行观察、介绍、新观测、行为')
    check(obs.call_count==2 and intro.call_count==act.call_count==1,
          '主流程实际调用可由本组修改的介绍和行为函数')

for phase in ['首次观察','介绍','再观察']:
    config()
    sequence = ['未检出','完成'] if phase=='首次观察' else ['完成','未检出' if phase=='再观察' else '完成']
    with patch.object(team,'observe',side_effect=sequence), \
         patch.object(team,'introduce',return_value='播放未成功' if phase=='介绍' else '完成'), \
         patch.object(team,'act') as act:
        log=team.run_project(session(),{'导览':object()},None)
        check(not act.called and log[-1]['result']=='未执行', phase+'不满足时阻断行为并标记未执行')

config()
with patch.object(team,'observe',return_value='完成'), \
     patch.object(team,'introduce',side_effect=RuntimeError('替身异常')), \
     patch.object(team,'act') as act:
    log=team.run_project(session(),{'导览':object()},None)
    check('替身异常' in log[1]['result'] and not act.called and log[2]['result']=='未执行',
          '介绍异常保留部分日志且不进入后续行为')

config('踢球')
with patch.object(team,'observe',return_value='完成'), \
     patch.object(team,'introduce',return_value='完成'), \
     patch.object(team,'kick_window',return_value=('达到观察上限', [{'x':1,'y':0}])):
    s=session();log=team.run_project(s,{'踢球':object()},{'verified':True})
    check(log[-1]['result']=='达到观察上限' and len(s['last_kick_positions'])==1,
          '试踢保留停止原因与坐标记录，不伪造进球成功')

config('踢球')
s=session();s['last_observation']={'found':True}
check(team.observe(s,{'踢球':object()},None)=='标定未核对' and s['last_observation'] is None,
      '本次没有标定记录时清除上轮观测展示，拒用旧值')

class ActiveTask:
    status = 'RUNNING'
    def done(self): return False
    def cancel(self): pass
    def wait(self,timeout): return self.status

config()
s=session();old_task=ActiveTask();s['motion_task']=old_task
with patch.object(team,'observe') as obs:
    log=team.run_project(s,{'导览':object()},None)
    check(not obs.called and log[0]['step']=='资源检查', '旧任务未结束时主流程拒绝启动')
pending=cleanup(s)
check(s['motion_task'] is old_task and bool(pending), '取消后仍未结束时保留原句柄及待处理项')

# 验证Notebook日志绑定运行时版本，拒绝启动不会覆盖上一轮证据。
nb = json.loads(next((P/'notebooks').glob('U8-L2*.ipynb')).read_text(encoding='utf-8'))
run_cell = next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and 'run_evidence =' in ''.join(c['source']))
env = {'run_evidence': {'version':'old-version','log':['baseline']},
       'robot': object()}
exec(compile(run_cell,'u8-gate','exec'),env)  # APPROVED=False短路，不接触任何SDK。
check(env['run_evidence']['version']=='old-version', '未获本次批准时保留既有运行日志与版本')

result['nbformat_validation'] = nbformat is not None
result['totals'] = {key:sum(x[key] for x in result['notebooks']) for key in ['cells','code']}
(T/'离线核查结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
