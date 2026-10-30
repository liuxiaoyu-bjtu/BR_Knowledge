from pathlib import Path
import ast
import contextlib
import hashlib
import io
import json
import re
import runpy
import shutil
import tempfile
from types import SimpleNamespace
import nbformat

ROOT = Path(__file__).resolve().parents[2]
T = Path(__file__).resolve().parent
P = ROOT/'05-internal-materials/vocational-planning/03_X课程项目'
f = next((P/'notebooks').glob('U7-L1*.ipynb'))
nb = json.loads(f.read_text(encoding='utf-8'))
base = json.loads((T/'基线.json').read_text(encoding='utf-8'))
before = json.loads((T/'before'/f.relative_to(ROOT)).read_text(encoding='utf-8'))
cases = []


def check(ok, name):
    assert ok, name
    cases.append(name)


nbformat.validate(nb)
check(len(nb['cells'])==21 and sum(c['cell_type']=='code' for c in nb['cells'])==8,
      '21格/8代码格，nbformat合法')
check(len({c['id'] for c in nb['cells']})==len(nb['cells']), '单元格ID唯一')
new_by_id={c['id']:c for c in nb['cells']}
for c in before['cells']:
    if c['cell_type']=='code':
        check(new_by_id[c['id']]==c, '原代码及执行信息保留：'+c['id'])
for c in nb['cells']:
    if c['cell_type']=='code':
        ast.parse(''.join(c['source']))
text='\n'.join(''.join(c['source']) for c in nb['cells'])
check(not re.search(r'\[sss\]|<sss>',text,re.I), '主稿无未处理标签')
headings=re.findall(r'^### (\d+)\.(\d+)\s',text,re.M)
check(all(sum(x==parent for x,y in headings)>=2 for parent in {x for x,y in headings}),
      '子标题无孤立编号')
check(text.index('**活动A')<text.index('### 1.2')<text.index('**活动B')<text.index('STEP 01A'),
      '学生先选择，再看参考并画方案，之后测试')
for rel,digest in base['protected'].items():
    check(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest, '未改其他课：'+Path(rel).name)
with tempfile.TemporaryDirectory(prefix='u7l1-generator-') as temp:
    temp=Path(temp);(temp/'notebooks').mkdir()
    shutil.copy2(P/'_gen_L25.py',temp/'_gen_L25.py')
    runpy.run_path(str(temp/'_gen_L25.py'))
    check(json.loads((temp/'notebooks'/f.name).read_text(encoding='utf-8'))==nb,
          '生成器沙箱重建与主Notebook完全一致')


class RobotDouble:
    def __init__(self):
        self.gets=0;self.callback=None;self.exits=0
    def get_imu(self):
        self.gets+=1
        return SimpleNamespace(timestamp=100+self.gets, angular_velocity=[0,0,self.gets/100])
    def subscribe_imu(self,callback,queue_size,overflow):
        assert queue_size==1 and overflow=='drop_oldest'
        owner=self
        class Subscription:
            def __enter__(self): owner.callback=callback;return self
            def __exit__(self,*args):owner.callback=None;owner.exits+=1
        return Subscription()


class ClockDouble:
    def __init__(self,robot):self.robot=robot;self.sleeps=0;self.fail=False
    def sleep(self,seconds):
        self.sleeps+=1
        if self.fail:raise RuntimeError('替身等待中断')
        if self.robot.callback:
            stamp=200+self.sleeps
            self.robot.callback(SimpleNamespace(timestamp=stamp,angular_velocity=[0,0,0.1]))


code_a=''.join(nb['cells'][6]['source'])
code_b=''.join(nb['cells'][8]['source'])
robot=RobotDouble();clock=ClockDouble(robot);env={'robot':robot,'time':clock}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(code_a,'STEP01A','exec'),env)
check(robot.gets==2 and env['once_stamp']==101 and env['again_imu'].timestamp==102,
      '一次读取格保留旧标量，并在等待后明确重新读取')
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(code_b,'STEP01B','exec'),env)
check(robot.gets==2 and env['comparison']['IMU']['count']==3,
      '订阅格由回调更新，不循环调用get_imu')
check(robot.callback is None and robot.exits==1, '订阅正常退出，保留最后记录')
clock.fail=True
try:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code_b,'STEP01B-interrupt','exec'),env)
except RuntimeError:
    pass
else:
    raise AssertionError('替身应触发中断')
check(robot.callback is None and robot.exits==2, 'Python异常离开with时执行订阅退出')

result={'robot_executed':False,'cells':21,'code':8,'checks':cases,'status':'passed'}
(T/'离线核查结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('离线核查通过：',len(cases),'项；未加载机器人SDK。')
