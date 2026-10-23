"""离线核验课程源稿与会话管理分支；替身不代表SDK或真机实测。"""
import ast
import contextlib
import hashlib
import io
import json
import re
import runpy
from pathlib import Path
from revise import ROOT, TASK, PROJ, NB, SHARED

checks = []
def check(name, condition):
    assert condition, name
    checks.append(name)

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']
check('27格，18 Markdown与9代码', len(cells)==27 and sum(c['cell_type']=='code' for c in cells)==9)
check('单元格id有效且不重复', len({c['id'] for c in cells})==27 and all(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',c['id']) for c in cells))
try:
    import nbformat
except ImportError:
    raise RuntimeError('需要nbformat进行Notebook格式核验；未跳过此检查。')
nbformat.validate(nbformat.from_dict(nb))
checks.append('nbformat结构验证通过')
code_cells = [(i+1, ''.join(c['source'])) for i,c in enumerate(cells) if c['cell_type']=='code']
for i, s in code_cells:
    ast.parse(s)
    check(f'第{i}格不伪造输出或执行次数', not cells[i-1]['outputs'] and cells[i-1]['execution_count'] is None)
checks.append('9个代码格语法通过')
genpath = PROJ/'_gen_L20.py'
ast.parse(genpath.read_text(encoding='utf-8'))
generated = runpy.run_path(str(genpath), run_name='verify_only')['cells']
check('生成器27格类型、id、源内容逐格一致', all(a['cell_type']==b['cell_type'] and a['id']==b['id'] and a['source']==b['source'] for a,b in zip(cells,generated)) and len(generated)==27)
alltext = '\n'.join(''.join(c['source']) for c in cells)
for term in ('recognize()', 'sleep(10)', '没有公开', '一轮回答已经说完', 'Thread(', 'Lock('):
    check(f'学生材料无停用内容：{term}', term not in alltext)
check('不使用result领取聊天结果', not any('.result(' in s for _,s in code_cells))
for i, s in code_cells:
    tree = ast.parse(s)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            check(f'第{i}格不向SDK只读status赋值', not any(isinstance(t,ast.Attribute) and t.attr=='status' for t in node.targets))
check('STEP01至09齐全', re.findall(r'\*\*STEP (\d+)', alltext)==[f'{i:02}' for i in range(1,10)])
hashes = json.loads((TASK/'前三课基线指纹.json').read_text(encoding='utf-8'))
for name, h in hashes.items():
    check('前三课未改：'+Path(name).name, hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h)

class FakeTask:
    def __init__(self, trace_id='old', status='RUNNING', accept=True, wait_final='CANCELLED'):
        self.trace_id, self._status = trace_id, status
        self.accept, self.wait_final = accept, wait_final
        self.error = '模拟服务错误' if status=='FAILED' else None
        self.cancel_calls, self.wait_calls = 0, []
        self.callbacks = []
    @property
    def status(self):
        return self._status
    def done(self):
        return self._status in ('SUCCEEDED','FAILED','CANCELLED')
    def set_status(self, s):
        self._status = s
        for callback in self.callbacks:
            callback(self)
    def cancel(self):
        self.cancel_calls += 1
        if self.accept:
            self.set_status('CANCELLING')
        return self.accept
    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        if self._status=='CANCELLING' and self.wait_final:
            self.set_status(self.wait_final)
        return self._status
    def add_status_change_callback(self, callback):
        self.callbacks.append(callback)
        callback(self)

class FakeSpeech:
    def __init__(self):
        self.created = []
    def chat(self, **kwargs):
        task = FakeTask(trace_id=f'new-{len(self.created)+1}')
        self.created.append(task)
        return task

speech = FakeSpeech()
ns = dict(speech=speech, ChatConfig=lambda **kw:kw, PROMPT='测试提示词')
exec(''.join(cells[18]['source']), ns)
manage = ns['manage_chat']
output = io.StringIO()
with contextlib.redirect_stdout(output):
    task,state = manage('开始',None,'待机')
    check('首次开始创建并保存句柄', task is speech.created[0] and state=='会话已发起')
    same,state = manage('开始',task,state)
    check('重复开始保留旧任务且不创建第二个', same is task and len(speech.created)==1)
    task,state = manage('停止',task,state)
    check('正常取消确认终态后回待机', task.done() and state=='待机' and task.cancel_calls==1)
    new,state = manage('开始',task,state)
    check('终态后可重新创建任务', new is not task and len(speech.created)==2)
    new,state = manage('停止',new,state)
    check('重开会话也能完成最终停止', new.done() and state=='待机')

    delayed = FakeTask(wait_final=None)
    old,state = manage('停止',delayed,'会话已发起')
    check('停止等待超时保留句柄和停止请求状态', old is delayed and not old.done() and state=='停止请求已发出')
    count = len(speech.created)
    old,state = manage('开始',old,state)
    check('取消中阻止重开', old is delayed and len(speech.created)==count)
    old,state = manage('停止',old,state)
    check('重复停止只继续等待原任务', delayed.cancel_calls==1 and len(delayed.wait_calls)==2)
    delayed.set_status('CANCELLED')
    old,state = manage('查看',old,state)
    check('后台结束后下次操作更新待机', old is delayed and state=='待机')

    reject = FakeTask(accept=False)
    old,state = manage('停止',reject,'会话已发起')
    check('取消拒绝保持原会话且检查等待', old is reject and state=='会话已发起' and reject.wait_calls==[5.0])
    old,state = manage('开始',old,state)
    check('取消拒绝后仍拦截重复开始', old is reject and len(speech.created)==count)

    for status in ('PENDING','RUNNING','CANCELLING'):
        active = FakeTask(status=status,wait_final=None)
        old,state = manage('开始',active,'待机')
        check(f'{status}不当成已结束并放行', old is active and len(speech.created)==count)
    for status in ('SUCCEEDED','CANCELLED','FAILED'):
        old = FakeTask(status=status)
        same,state = manage('查看',old,'会话已发起')
        check(f'{status}可刷新为待机', same is old and state=='待机')

    before = len(speech.created)
    failed = FakeTask(status='FAILED')
    current,state = manage('开始',failed,'会话已发起')
    check('旧任务失败先报告错误再允许手动重开', current is not failed and len(speech.created)==before+1 and '旧任务错误信息' in output.getvalue())
    active = FakeTask()
    old,state = manage('未知操作',active,'会话已发起')
    check('未知操作不改变任务', old is active and state=='会话已发起' and active.cancel_calls==0)
    old,state = manage('停止',None,'待机')
    check('没有任务时停止不调用SDK', old is None and state=='待机')

    active = FakeTask(wait_final=None)
    obs = {'chat_task':active}
    exec(''.join(cells[11]['source']),obs)
    check('有限观察等待不取消任务', active.status=='RUNNING' and active.cancel_calls==0 and active.wait_calls==[2.0])
    exec(''.join(cells[13]['source']),obs)
    check('回调只登记一次且参数与契约相符', len(active.callbacks)==1 and '状态回调：' in output.getvalue())
    active.set_status('FAILED')
    check('替身驱动状态回调可读取新状态', 'old FAILED' in output.getvalue())

    rejected = FakeTask(accept=False)
    stopns = {'chat_task':rejected}
    exec(''.join(cells[15]['source']),stopns)
    check('独立停止格取消拒绝仍保留句柄', stopns['chat_task'] is rejected and not rejected.done())

# 仅验证教师给出的条件；学生格中的False是待补练习，不当成成品条件。
for task,state,expected in ((None,'待机',True), (FakeTask(),'会话已发起',False),
                            (FakeTask(status='CANCELLING'),'停止请求已发出',False),
                            (FakeTask(status='CANCELLED'),'待机',True)):
    check('教师启动条件真值表'+state, (state=='待机' and (task is None or task.done()))==expected)

doc = PROJ/'实验验证/U5-L4_教学审阅与真机验证建议.md'
for path in [doc, PROJ/'实验验证/U5-L4_真机问题复评与重构建议.md']:
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if not link.startswith(('https://','http://','#')):
            check('文档本地链接存在：'+link, (path.parent/link.split('#')[0]).exists())

# 确认共享文件增量是当前工作区的反向可恢复补丁。
import subprocess
subprocess.run(['git','apply','--reverse','--check',str(TASK/'共享文档本轮增量.patch')],cwd=ROOT,check=True,capture_output=True)
checks.append('共享文档增量可反向校验；未实际应用或覆盖共享文件')
result = dict(status='passed', total=len(checks), checks=checks,
              scope='离线语法、源稿一致性与替身控制分支；非SDK实现或真机测试')
(TASK/'验证结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(checks)}项离线检查通过；未连接机器人。')
