"""离线核对课程材料及必要收尾分支；替身结果不能当作真机验证。"""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import runpy
import subprocess
import sys
import types
from unittest.mock import patch

from revise import ROOT, TASK, BASE, PROJ, NB, read, write, src

checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


paths = [next(NB.glob(f'U5-L{i}_*.ipynb')) for i in range(1, 4)]
duplicate = NB/'U5-L2/U5-L2_语音合成.ipynb'
books = [json.loads(read(p)) for p in paths]
for p in paths+[duplicate]:
    b = json.loads(read(p))
    old = json.loads(read(TASK/'before'/p.relative_to(ROOT)))
    without_source = lambda n: {**n, 'cells': [{k:v for k,v in c.items() if k!='source'} for c in n['cells']]}
    check(p.name+('（发放副本）' if p==duplicate else '')+'：输出/执行次数/id/metadata等非源字段保留', without_source(b)==without_source(old))
    for i,c in enumerate(b['cells'], 1):
        if c['cell_type']=='code':
            ast.parse(src(c), filename=f'{p.name}:cell{i}')
    check(p.name+'：代码格语法', True)
    if importlib.util.find_spec('nbformat'):
        import nbformat
        nbformat.validate(nbformat.reads(json.dumps(b),as_version=4))
        check(p.name+'：nbformat结构', True)
for i, (p,b) in enumerate(zip(paths, books),17):
    gen = PROJ/f'_gen_L{i}.py'
    ast.parse(read(gen))
    generated = runpy.run_path(str(gen),run_name='verify_generator')['cells']
    check(gen.name+'：逐格类型与源内容一致', [(c['cell_type'],src(c)) for c in b['cells']]==[(c['cell_type'],src(c)) for c in generated])
d = json.loads(read(duplicate))
check('L2主稿与发放副本：逐格源内容一致', [src(c) for c in books[1]['cells']]==[src(c) for c in d['cells']])
font = NB/'U5-L2/fonts/wqy-microhei.ttc'
check('L2字体可定位', font.is_file())
check('三声道PCM换算', (16000*1*2,16000*3*2,round(3200/(16000*3*2),6),20*3200/96000,60*3200/96000)==(32000,96000,0.033333,2/3,2.0))
for i,b in enumerate(books,1):
    steps = [int(m) for c in b['cells'] if c['cell_type']=='markdown' and '**STEP' in src(c) for m in __import__('re').findall(r'\*\*STEP (\d+)',src(c))]
    check(f'L{i}：STEP连续且不重复', steps==list(range(1,len(steps)+1)))


class Stream:
    """只实现播放流公开方法；没有TaskHandle的status/error/done。"""
    def __init__(self, final='SUCCEEDED', cancel_final='CANCELLED', interrupt=False):
        self.final, self.cancel_final, self.interrupt = final,cancel_final,interrupt
        self.closed = False
        self.events = []
        self.cancelled = False
    def write(self, chunk):
        self.events.append(('write',len(chunk.data)))
        if self.interrupt:
            raise KeyboardInterrupt()
    def close(self):
        self.events.append(('close',))
        self.closed = True
    def wait(self, timeout=None):
        self.events.append(('wait',timeout))
        return self.cancel_final if self.cancelled else self.final if self.closed else 'RUNNING'
    def cancel(self):
        self.events.append(('cancel',))
        self.cancelled = True
        return True


class Manager:
    def __init__(self, stream=None):
        self.stream = stream or Stream()
        self.created = 0
    def play_stream(self, **kwargs):
        self.created += 1
        return self.stream
    def record_stream(self, **kwargs):
        while not kwargs['stop_event'].is_set():
            yield types.SimpleNamespace(data=bytes(kwargs['chunk_bytes']))


class Task:
    def __init__(self, mode='recognize', cancel_final='CANCELLED', status='RUNNING'):
        self.mode,self.cancel_final,self.status = mode,cancel_final,status
        self.error = RuntimeError('模拟任务错误') if status=='FAILED' else None
        self.waits=[]
        self.cancels=0
    def done(self):
        return self.status in ('SUCCEEDED','FAILED','CANCELLED')
    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self.mode=='chat' and timeout is None and not self.done():
            raise KeyboardInterrupt()
        return self.status
    def cancel(self):
        self.cancels+=1
        self.status=self.cancel_final
        return True
    def result(self):
        return types.SimpleNamespace(duration=types.SimpleNamespace(seconds=2.5))


class Robot:
    def __init__(self, stream=None, play_status='SUCCEEDED'):
        self.audio_manager=Manager(stream)
        self.play_status=play_status
    def play_sound(self,*args,**kwargs):
        return Task(mode='play',status=self.play_status)


class Speech:
    instances=[]
    def __init__(self, robot, cancel_final='CANCELLED'):
        self.robot=robot
        self.cancel_final=cancel_final
        self.tasks=[]
        self.syntheses=0
        Speech.instances.append(self)
    def recognize_stream(self, on_result):
        t=Task(cancel_final=self.cancel_final)
        self.tasks.append(t)
        on_result('模拟文字')
        return t
    def chat(self, **kwargs):
        t=Task(mode='chat',cancel_final=self.cancel_final)
        self.tasks.append(t)
        return t
    def synthesize(self,*args,**kwargs):
        self.syntheses+=1
        return Task(status='SUCCEEDED')


def run(source, env):
    env.setdefault('time', fake_time)
    output=io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source,'<Notebook单元格>','exec'),env)
    return output.getvalue()


# 所有时间等待都由替身立即返回，不占用机器人或真实音频设备。
fake_time=types.ModuleType('time')
fake_time.sleep=lambda seconds: None
counter=[0]
def clock():
    counter[0]+=1
    return counter[0]/1000
fake_time.perf_counter=clock
brain=types.ModuleType('boosteros.brain')
brain.Speech=Speech
boosteros=types.ModuleType('boosteros')
boosteros.brain=brain
chunks=[types.SimpleNamespace(data=bytes(3200)) for _ in range(60)]

with patch.dict(sys.modules,{'time':fake_time,'boosteros':boosteros,'boosteros.brain':brain}):
    for final in ('SUCCEEDED','FAILED','CANCELLED','RUNNING'):
        stream=Stream(final=final)
        robot=Robot(stream=stream)
        env={'robot':robot,'chunks':chunks}
        out=run(src(books[0]['cells'][24]),env)
        check(f'L1播放流 {final}：close在有限wait之前', stream.events.index(('close',)) < stream.events.index(('wait',10.0)))
        check(f'L1播放流 {final}：不误报成功', ('播放完成，状态：' in out)==(final=='SUCCEEDED'))
        if final=='RUNNING':
            old=env['stream']
            run(src(books[0]['cells'][24]),env)
            check('L1播放流超时：保留句柄且不重复创建', env['stream'] is old and robot.audio_manager.created==1)
    stream=Stream(interrupt=True)
    env={'robot':Robot(stream=stream),'chunks':chunks}
    try:
        run(src(books[0]['cells'][24]),env)
    except KeyboardInterrupt:
        pass
    check('L1写入被中断：仍close且句柄保留', stream.closed and env['stream'] is stream)
    for cell, count in ((19,20),(23,60)):
        env={'robot':Robot()}
        run(src(books[0]['cells'][cell-1]),env)
        check(f'L1第{cell}格：实际字节换算', env['total_bytes']==3200*count and env['audio_seconds']==count*3200/96000)
    for status in ('SUCCEEDED','FAILED','CANCELLED'):
        env={'robot':Robot(play_status=status),'save_path':'模拟.wav'}
        out=run(src(books[0]['cells'][14]),env)
        check(f'L1整段播放 {status}：成功才报告完成', ('播放完成' in out)==(status=='SUCCEEDED'))
    env={'robot':Robot()}
    run(src(books[0]['cells'][30]),env)
    task=env['task']
    check('L1识别：取消后等待并确认终态',task.cancels==1 and task.waits==[5.0] and task.done())
    speech=env['speech']
    speech.cancel_final='CANCELLING'
    run(src(books[0]['cells'][32]),env)
    task=env['task']
    count=len(speech.tasks)
    run(src(books[0]['cells'][32]),env)
    check('L1识别取消未结束：不重开、不覆盖',env['task'] is task and len(speech.tasks)==count)
    env={'robot':Robot(),'task':Task(status='CANCELLING')}
    old=env['task']
    run(src(books[1]['cells'][31]),env)
    check('L2提问前旧任务未结束：不合成、不重开',env['task'] is old and env['speech'].syntheses==0)
    env={'robot':Robot()}
    run(src(books[1]['cells'][31]),env)
    check('L2提问与识别：有限播放成功后识别且取消等待',env['playback_status']=='SUCCEEDED' and env['speech'].syntheses==1 and env['task'].done() and env['task'].waits==[5.0])
    env={'robot':Robot(play_status='FAILED')}
    run(src(books[1]['cells'][31]),env)
    check('L2提问播放失败：不启动识别',not env['speech'].tasks)
    for cell in (11,15,26,28,30):
        speech=Speech(Robot())
        env={'speech':speech,'ChatConfig':lambda **k:k,'QUESTION':'固定问句'}
        run(src(books[2]['cells'][cell-1]),env)
        task=env['task']
        check(f'L3第{cell}格：保留无限wait，中断后取消并等待',task.waits==[None,5.0] and task.cancels==1 and task.done())
        speech.cancel_final='CANCELLING'
        run(src(books[2]['cells'][cell-1]),env)
        old=env['task']
        count=len(speech.tasks)
        run(src(books[2]['cells'][cell-1]),env)
        check(f'L3第{cell}格：取消未结束时不能覆盖会话',env['task'] is old and len(speech.tasks)==count)
    speech=Speech(Robot(),cancel_final='CANCELLING')
    env={'speech':speech}
    run(src(books[2]['cells'][23]),env)
    old=env['task']
    last=env['last_text']
    run(src(books[2]['cells'][23]),env)
    check('L3识别未结束：不清空旧回调变量、不重开',env['task'] is old and len(speech.tasks)==1 and env['last_text']==last)
    env.update({'ChatConfig':lambda **k:k,'QUESTION':'固定问句'})
    run(src(books[2]['cells'][25]),env)
    check('L3识别未结束：不能覆盖句柄启动chat',env['task'] is old and len(speech.tasks)==1)


# 从附件抽出播放函数，真实执行其判断；声音算法和绘图函数另以AST比较。
helper=NB/'U5-L2/sound_lab.py'
tree=ast.parse(read(helper))
old_tree=ast.parse(read(TASK/'before'/helper.relative_to(ROOT)))
for name in ('synthesize_tone','plot_waves'):
    get=lambda t: next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
    check(f'L2附件 {name}：算法未改',ast.dump(get(tree),include_attributes=False)==ast.dump(get(old_tree),include_attributes=False))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='play_sound')
class Audio:
    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)
    def with_data(self,data):
        return Audio(**{**self.__dict__,'data':data})
for final in ('SUCCEEDED','FAILED','CANCELLED','RUNNING'):
    stream=Stream(final=final,cancel_final='CANCELLING')
    robot=Robot(stream=stream)
    env={'AudioData':Audio,'Header':lambda:None,'_playback_stream':None}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<sound_lab.play_sound>','exec'),env)
    error=None
    try:
        env['play_sound'](robot,bytes(9600))
    except RuntimeError as e:
        error=str(e)
    check(f'L2附件 {final}：正常完成才返回', (error is None)==(final=='SUCCEEDED'))
    check(f'L2附件 {final}：close在wait前',stream.events.index(('close',))<stream.events.index(('wait',10.0)))
    if final=='RUNNING':
        check('L2附件超时：请求取消并保留句柄',('cancel',) in stream.events and env['_playback_stream'] is stream)
        try:
            env['play_sound'](robot,bytes(9600))
        except RuntimeError:
            pass
        check('L2附件取消未结束：不重复创建流',robot.audio_manager.created==1)


# 与上轮保存值比较本轮无须修改的课程、字体和历史音频。
protected=json.loads(read(ROOT/'99-task-contexts/20261023-X课程U4U5推进/protected_files_sha256.json'))
for rel, expected in protected.items():
    if 'U4-L1_' in rel or rel.endswith(('.ttc', '.wav')):
        check(rel+'：本轮未改', hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected)
l4=next(NB.glob('U5-L4_*.ipynb'))
l4_saved=subprocess.run(['git','show','99f3f1c:'+l4.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,check=True).stdout
check('U5-L4：与上一轮提交相同，本轮未改',json.loads(l4.read_bytes())==json.loads(l4_saved))
font_hash=hashlib.sha256(font.read_bytes()).hexdigest()
write(TASK/'验证结果.json',json.dumps({'checks':checks,'passed':len(checks),'font_sha256':font_hash,'scope':'离线语法、保存信息、一致性和任务分支；不代替真机补验'},ensure_ascii=False,indent=2)+'\n')
print(f'离线检查 {len(checks)} 项通过；未连接机器人。')
print('主稿格数：'+', '.join(f'L{i}={len(b["cells"])}' for i,b in enumerate(books,1)))
print('字体SHA-256：'+font_hash)
