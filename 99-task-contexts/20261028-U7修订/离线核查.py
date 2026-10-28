"""离线检查U7的Notebook结构、分格依赖与关键分支，不连接机器人。"""
from pathlib import Path
from types import SimpleNamespace as NS
from contextlib import redirect_stdout
import ast, io, json, threading
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
TASK=Path(__file__).parent
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
def read(lesson):
    f=next((P/'notebooks').glob(f'U7-L{lesson}_*.ipynb'))
    return f,json.loads(f.read_text(encoding='utf-8'))
def definitions(lesson):
    env={'time':FakeTime(),'threading':threading,'threads':[],'asr_task':None,'motion_task':None}
    for c in read(lesson)[1]['cells']:
        if c['cell_type']!='code':continue
        tree=ast.parse(''.join(c['source']))
        for node in tree.body:
            # 仅定义函数和普通参数赋值；不导入SDK，不执行连接、线程启动与试演格。
            if isinstance(node,ast.FunctionDef):exec(compile(ast.Module(body=[node],type_ignores=[]),'<nb-def>','exec'),env)
            elif isinstance(node,ast.Assign):
                try:value=ast.literal_eval(node.value)
                except (ValueError,TypeError):continue
                for target in node.targets:
                    if isinstance(target,ast.Name):env[target.id]=value
    return env
class FakeTime:
    def __init__(self):self.now=0
    def monotonic(self):return self.now
    def sleep(self,s):self.now+=s
class Task:
    def __init__(self,status='SUCCEEDED',done=True):self.status=status;self.ended=done;self.error='stub';self.cancelled=False
    def wait(self,timeout=None):return self.status
    def done(self):return self.ended
    def cancel(self):self.cancelled=True;return True
class Robot:
    def __init__(self):self.moves=[];self.x=0;self.task=Task();self.protected=False
    def set_velocity(self,*v):self.moves.append(v)
    def reset_odom(self):self.x=0
    def get_odom(self):return NS(pose_2d=(self.x,0,0))
    def get_fall_down_state(self):return NS(has_fallen=self.protected,is_falling=False)
    def get_image(self,**kwargs):return IMAGE
    def do_action(self,i):return self.task
IMAGE=NS(width=544,to_numpy=lambda:object())
def result(label,score,x=272):return NS(class_name=label,confidence=score,bbox=NS(center_x=x))
BOTTLE=result('bottle',.8)
PERSON=result('person',.9)
class Detector:
    def __init__(self,results):self.results=results
    def detect(self,*args,**kwargs):return self.results

for lesson in range(1,5):
    f,n=read(lesson);check(f'L{lesson} JSON和cell id',len({c['id'] for c in n['cells']})==len(n['cells']))
    for i,c in enumerate(n['cells'],1):
        s=''.join(c['source'])
        check(f'L{lesson}格{i}逐行source',c['source']==s.splitlines(keepends=True))
        if c['cell_type']=='code':
            ast.parse(s);check(f'L{lesson}格{i}执行记录为空',c['execution_count'] is None and c['outputs']==[])
    check(f'L{lesson}移除空泛量词',not any(w in ''.join(''.join(c['source']) for c in n['cells']) for w in ['件事','三样东西','顺序不能反过来']))

with redirect_stdout(io.StringIO()):
    e=definitions(2);r=Robot();e.update(robot=r,detector=Detector([PERSON,result('bottle',.6),BOTTLE]))
    check('L2按类别筛选且取最高评分',e['find_bottle']()[1] is BOTTLE)
    e['detector']=Detector([PERSON]);check('L2其他类别不代替瓶子',e['find_bottle']()[1] is None)
    e['detector']=Detector([]);check('L2空列表返回None',e['find_bottle']()[1] is None)
    e.update(find_bottle=lambda:(IMAGE,None),MAX_ROUNDS=2)
    out=io.StringIO()
    with redirect_stdout(out):e['run_trial']()
    check('L2未检出不误报到位','未检出bottle' in out.getvalue() and r.moves[-1]==(0,0,0))
    calls=[]
    def once():
        calls.append(1);return IMAGE,BOTTLE if len(calls)==1 else None
    e.update(find_bottle=once,say=lambda s:True)
    out=io.StringIO()
    with redirect_stdout(out):e['run_trial'](with_speech=True)
    check('L2播报后重新检测、丢失时不运动',len(calls)==2 and not any(v[0]>0 for v in r.moves))
    e.update(find_bottle=lambda:(IMAGE,BOTTLE),TARGET_X_M=0,MAX_ROUNDS=2)
    out=io.StringIO()
    with redirect_stdout(out):e['run_trial']()
    check('L2条件满足才记录完成','满足位移与对准条件' in out.getvalue())
    e['TARGET_X_M']=1.2
    out=io.StringIO()
    with redirect_stdout(out):e['run_trial']()
    check('L2轮数耗尽不误报到位','达到轮数上限' in out.getvalue() and r.moves[-1]==(0,0,0))
    r.protected=True;out=io.StringIO()
    with redirect_stdout(out):e['run_trial'](with_protection=True)
    check('L2状态保护退出','状态保护' in out.getvalue())
    r.protected=False
    def explode():raise RuntimeError('offline error')
    e['find_bottle']=explode
    try:e['run_trial']()
    except RuntimeError:pass
    check('L2检测异常仍发送零速度',r.moves[-1]==(0,0,0))
    e=definitions(3);e.update(STOP=threading.Event(),lock=threading.Lock(),shared={'command':None,'guest_error':0,'vision_time':0,'worker_error':None})
    e['on_text']('过来 停下');check('L3停止关键词优先',e['shared']['command']=='stop')
    e['STOP'].set();e['on_text']('过来');check('L3停止后回调不再写入',e['shared']['command']=='stop')
    e['STOP'].clear();e['shared']['command']='approach';e.update(robot=Robot(),RUN_SECONDS=1.0,MAX_VISION_AGE=2)
    e['motion_loop']();check('L3清空指令后模式持续',sum(v[0]>0 for v in e['robot'].moves)==2)
    check('L3主循环退出请求停止并发零速度',e['STOP'].is_set() and e['robot'].moves[-1]==(0,0,0))
    e['STOP'].clear();e['time']=FakeTime();e['shared'].update(command='approach',guest_error=None);e['robot']=Robot()
    e['motion_loop']();check('L3目标丢失只发送零速度',all(v==(0,0,0) for v in e['robot'].moves))
    e['STOP'].clear();e['time']=FakeTime();e['shared'].update(command='approach',guest_error=0,vision_time=-5);e['robot']=Robot()
    e['motion_loop']();check('L3旧检测结果停止使用',all(v==(0,0,0) for v in e['robot'].moves))
    e['STOP'].clear();e['asr_task']=None
    class Speech:
        def recognize_stream(self,**kwargs):e['STOP'].set();return Task('RUNNING',False)
    e['speech']=Speech();e['talk_loop']()
    check('L3保留未结束识别句柄',e['asr_task'] is not None and e['asr_task'].cancelled and not e['asr_task'].done())
    init_cell=next(''.join(c['source']) for c in read(3)[1]['cells'] if c['cell_type']=='code' and ''.join(c['source']).startswith('if any'))
    old_stop=e['STOP']
    try:exec(init_cell,e)
    except RuntimeError:pass
    else:raise AssertionError('未结束任务应阻止初始化')
    check('L3未结束任务阻止重绑STOP',e['STOP'] is old_stop)
    e=definitions(4);r=Robot();e.update(robot=r,GREET_ID='verified')
    for status in ['SUCCEEDED','FAILED','CANCELLED']:
        r.task=Task(status);e['motion_task']=None;actual=e['act_greet']()
        check('L4动作状态判定'+status,(actual=='完成')==(status=='SUCCEEDED'))
    r.task=Task('RUNNING',False);e['motion_task']=None
    check('L4超时取消不冒充成功',e['act_greet']()!='完成' and r.task.cancelled and e['motion_task'] is r.task)
    old=r.task;e['act_greet']();check('L4未结束句柄保留',e['motion_task'] is old)
    e['find_guest']=lambda:(IMAGE,None);check('L4未检出立即结束迎宾',e['act_approach']()=='未检出来宾' and r.moves[-1]==(0,0,0))
    e['say']=lambda s:'FAILED';check('L4播放失败不前进',e['act_forward']().startswith('播放未成功'))
    # 从实际预演格执行外层流程，验证失败阻断和日志记录。
    run_cell=next(''.join(c['source']) for c in read(4)[1]['cells'] if c['cell_type']=='code' and ''.join(c['source']).startswith('if motion_task is not None'))
    visited=[];e.update(motion_task=None,fallen=lambda:False,script=[('幕一',lambda:'未检出'),('幕二',lambda:visited.append(2))])
    exec(run_cell,e);check('L4前幕失败阻断后幕且记录原因',not visited and len(e['log'])==1 and e['log'][0][1]=='未检出')
    def error_step():raise RuntimeError('stub error')
    e['script']=[('异常幕',error_step)];exec(run_cell,e)
    check('L4异常记录所在幕并发零速度',e['log'][0][0]=='异常幕' and '异常' in e['log'][0][1] and r.moves[-1]==(0,0,0))

metrics=[]
for lesson in range(1,5):
    f,n=read(lesson);backup=TASK/'before'/f.relative_to(ROOT)
    old=json.loads(backup.read_text(encoding='utf-8')) if backup.exists() else None
    def counts(nb):
        codes=[c for c in nb['cells'] if c['cell_type']=='code']
        return {'cells':len(nb['cells']),'code_cells':len(codes),'max_code_lines':max(len(''.join(c['source']).splitlines()) for c in codes)}
    previous=json.loads((TASK/'离线核查结果.json').read_text(encoding='utf-8'))['metrics'][lesson-1]['before'] if old is None else counts(old)
    metrics.append({'lesson':f'U7-L{lesson}','before':previous,'after':counts(n)})
report={'kind':'离线结构与替身对象分支检查；不等于SDK或真机验证','checks_passed':len(checks),'checks':checks,'metrics':metrics}
(TASK/'离线核查结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks_passed':len(checks),'metrics':metrics},ensure_ascii=False,indent=2))
