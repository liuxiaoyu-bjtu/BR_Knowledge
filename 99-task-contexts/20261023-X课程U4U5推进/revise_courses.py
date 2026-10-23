"""本轮课程源稿同步与离线验证；不连接机器人，不自动推送。"""
from pathlib import Path
import ast
import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import uuid

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BASE = ROOT / '05-internal-materials/vocational-planning'
PROJ = BASE / '03_X课程项目'
NB = PROJ / 'notebooks'

def text(p):
    return p.read_text(encoding='utf-8')

def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8', newline='\n')

def source(c):
    s = c['source']
    return s if isinstance(s, str) else ''.join(s)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def selected_notebooks():
    return [next(NB.glob(f'U5-L{i}_*.ipynb')) for i in range(1,5)]

def generator(p, cells):
    # 学生源稿是主稿；生成器不携带真机输出，不执行它覆盖现稿。
    body = [f'"""{p.stem}：按 2026-10-23 学生 Notebook 反向同步。',
            'Notebook 为主稿；重建将清空输出，不用于覆盖用户真机记录。"""',
            'import json', 'from pathlib import Path',
            f'OUT = Path(__file__).resolve().parent / "notebooks" / {p.name!r}',
            'def md(s):', '    return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}',
            'def code(s):', '    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(keepends=True)}',
            'cells = []']
    for c in cells:
        fun = 'md' if c['cell_type'] == 'markdown' else 'code'
        body.append(f'cells.append({fun}({source(c)!r}))')
    body += ['if __name__ == "__main__":',
             '    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}',
             f'    OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + {chr(10)!r}, encoding="utf-8")',
             '    print(OUT)', '']
    return '\n'.join(body)

def build():
    protected = [next(NB.glob('U4-L1_*.ipynb'))] + selected_notebooks()[:3]
    protected += [p for p in (NB/'U5-L2').rglob('*') if p.is_file()]
    baseline = TASK / 'protected_files_sha256.json'
    if not baseline.exists():
        write(baseline, json.dumps({p.relative_to(ROOT).as_posix():digest(p) for p in protected}, ensure_ascii=False, indent=2))
    p = selected_notebooks()[3]
    old = json.loads(text(p))
    backup = TASK/'U5-L4_重构前.ipynb'
    if not backup.exists():
        backup.write_bytes(p.read_bytes())
    parts = re.split(r'^@@ (markdown|code)\s*\n', text(TASK/'U5-L4_cells.md'), flags=re.M)
    assert not parts[0].strip()
    cells = []
    for k in range(1, len(parts), 2):
        kind, s = parts[k], parts[k+1].strip()+'\n'
        c = {'cell_type':kind, 'id':uuid.uuid4().hex[:8], 'metadata':{}, 'source':s.splitlines(keepends=True)}
        if kind == 'code':
            ast.parse(s)
            c.update(execution_count=None, outputs=[])
        cells.append(c)
    old['cells'] = cells
    old['nbformat'], old['nbformat_minor'] = 4, 5
    write(p, json.dumps(old, ensure_ascii=False, indent=1)+'\n')
    for i, p in enumerate(selected_notebooks(), 17):
        notebook=json.loads(text(p))
        write(PROJ/f'_gen_L{i}.py', generator(p, notebook['cells']))
    print('BUILT U5-L4:', len(cells), 'cells,', sum(c['cell_type']=='code' for c in cells), 'code')
    print('SYNCED _gen_L17..20；保护 U4-L1、U5-L1..3 及 L2 发放目录原文件。')

def short():
    for rel, start, end in [
        ('AGENTS.md',116,130), ('INDEX.md',210,222),
        ('05-internal-materials/vocational-planning/README.md',37,49),
        ('05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md',1,21),
        ('05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md',245,253),
        ('05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',201,220),
        ('CHANGELOG.md',1,15)]:
        print('\nFILE',rel)
        for i, line in enumerate(text(ROOT/rel).splitlines(),1):
            if start <= i <= end:
                print(f'{i}: {line}')
    for i in (17,18,19,20):
        p=PROJ/f'_gen_L{i}.py'
        tree=ast.parse(text(p))
        appends=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='append']
        print(p.name, len(appends),'cell append statements')

def resync():
    for i, p in enumerate(selected_notebooks(), 17):
        write(PROJ/f'_gen_L{i}.py', generator(p, json.loads(text(p))['cells']))
    print('仅反向同步 _gen_L17..20；未写入任何 Notebook。')

def final_wording():
    p=selected_notebooks()[3]
    nb=json.loads(text(p))
    before='需要坐下收起时由人工支撑、扶坐，再进入 `damping`'
    after='需要坐下收起时，先在 `prepare` 模式站稳，由人工支撑，再进入 `damping` 并扶坐'
    found=0
    for cell in nb['cells']:
        s=source(cell)
        if before in s:
            cell['source']=s.replace(before,after).splitlines(keepends=True)
            found+=1
    assert found==1, found
    write(p,json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    intermediate=TASK/'U5-L4_cells.md'
    if before in text(intermediate):
        write(intermediate,text(intermediate).replace(before,after))
    resync()

def details():
    for p in selected_notebooks()[:3]:
        print('\nNOTEBOOK',p.name)
        for i,c in enumerate(json.loads(text(p))['cells'],1):
            s=source(c)
            if c['cell_type']=='code':
                print('CELL',i,'CODE',s[:130].replace('\n',' / '))
            else:
                print('CELL',i, s[:200].replace('\n',' / '))
    rules=BASE/'02_共创规则与上下文/notebook开发规则.md'
    for i,line in enumerate(text(rules).splitlines(),1):
        if line.startswith('## 7') or line.startswith('## 8') or ('2026-10-22' in line and not line.startswith('|')):
            print('RULE',i,line[:300])
    status=subprocess.run(['git','-c','core.quotepath=false','status','--short','--untracked-files=normal'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8').stdout
    lines=status.splitlines()
    print('STATUS total',len(lines),'staged',sum(s[:2] not in (' M','??',' D') for s in lines))
    for line in lines:
        if any(k in line for k in ('_gen_L17','_gen_L18','_gen_L19','_gen_L20','U5-L','U4-L1','AGENTS.md','INDEX.md','CHANGELOG.md','X课程开发计划-v4.md','X课程大纲-v4.md','notebook开发规则.md','vocational-planning/README.md')):
            print(line)

def update_records():
    paths = [ROOT/'AGENTS.md', ROOT/'INDEX.md', ROOT/'CHANGELOG.md', BASE/'README.md',
             BASE/'02_共创规则与上下文/notebook开发规则.md',
             PROJ/'X课程大纲-v4.md', PROJ/'X课程开发计划-v4.md',
             PROJ/'实验验证/U5-L4_真机问题复评与重构建议.md']
    snapshots=TASK/'before-record-updates'
    for p in paths:
        backup=snapshots/p.relative_to(ROOT)
        if not backup.exists():
            backup.parent.mkdir(parents=True,exist_ok=True)
            backup.write_bytes(p.read_bytes())

    def change(p, fn):
        s=text(p)
        out=fn(s)
        if s != out:
            write(p,out)
            print('UPDATED',p.relative_to(ROOT).as_posix())

    def prefix(s, beginning, replacement):
        lines=s.splitlines()
        ids=[i for i,line in enumerate(lines) if line.startswith(beginning)]
        assert len(ids)==1, (beginning, len(ids))
        lines[ids[0]]=replacement
        return '\n'.join(lines)+'\n'

    u4='U4-L1 P3教学设计已完成，待用户确认④；Notebook未改。U4-L2～L4仍待真机确认②。'
    u5='U5-L1～L3的P2复核已完成，发现问题，待用户确认修改方案，尚未定稿；保留确认②历史记录，现稿34/34/32格及L2附件未改，生成器已反向同步。'
    l4='U5-L4已按用户认可方向重构为持续会话管理，23格（15 Markdown/8代码），待新稿确认①、②；不再测单轮或ASR/LLM/TTS分段延迟，不使用U7线程与锁。'
    def agents(s):
        s=s.replace('## 6. 当前进行中的工作（2026-10-22）','## 6. 当前进行中的工作（2026-10-23）')
        return prefix(s,'  - U4-L1已于2026-10-22', '  - '+u4+u5+l4+'产物见`03_X课程项目/教学设计/U4-L1_转向来宾_教学设计.md`及`实验验证/U5-L1-L2-L3_P2复核与修改方案.md`、`实验验证/U5_语音SDK能力核验记录.md`。L3保留用户实测的`wait()`与中断收尾；任务结束与一轮回答结束分别解释。')
    change(ROOT/'AGENTS.md',agents)

    def index(s):
        s=prefix(s,'| X课程 U4-L1 P2 /', '| X课程 U4-L1 P2 / 转向对准 / 结束原因 | [复核与定稿记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L1_P2复核与定稿记录.md)（2026-10-22通过；P3已编写，确认④待审） |')
        s=prefix(s,'| X课程 U5-L4 /', '| X课程 U5-L4 / 语音计时问题 / 会话管理重构 | [真机问题复评与重构建议](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L4_真机问题复评与重构建议.md)（2026-10-23新稿已重构，23格；待新确认①②） |')
        marker='\n## 临时任务记录'
        new='\n| X课程 U4-L1 P3 / 教学设计 | [转向来宾教学设计](05-internal-materials/vocational-planning/03_X课程项目/教学设计/U4-L1_转向来宾_教学设计.md)（45分钟；确认④待审） |\n| X课程 U5 P2 / 三课复核与修改方案 | [U5-L1～L3复核方案](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5-L1-L2-L3_P2复核与修改方案.md)（已复核，有问题待修改方案确认） |\n| X课程 语音SDK / TaskHandle / 持续会话 / 有限音频识别 | [能力核验记录](05-internal-materials/vocational-planning/03_X课程项目/实验验证/U5_语音SDK能力核验记录.md)（用户指定16页及6个关联类型，2026-10-23） |\n'
        assert marker in s
        return s.replace(marker,new+marker,1)
    change(ROOT/'INDEX.md',index)

    def nav(s):
        s=prefix(s,'- **U4/U5进度（', '- **U4/U5进度（2026-10-23）**：'+u4+u5+l4)
        s=prefix(s,'- U4-L1审定入口：','- U4-L1入口：[P2复核与定稿记录](03_X课程项目/实验验证/U4-L1_P2复核与定稿记录.md)、[P3教学设计](03_X课程项目/教学设计/U4-L1_转向来宾_教学设计.md)（确认④待审）。')
        return prefix(s,'- U5-L4复评入口：','- U5入口：[前三课P2复核与修改方案](03_X课程项目/实验验证/U5-L1-L2-L3_P2复核与修改方案.md)、[语音SDK能力核验记录](03_X课程项目/实验验证/U5_语音SDK能力核验记录.md)、[L4重构依据及补验清单](03_X课程项目/实验验证/U5-L4_真机问题复评与重构建议.md)（新学生稿已替换；L2发放目录见[附件清单](03_X课程项目/notebooks/_外挂附件清单.md)）。')
    change(BASE/'README.md',nav)

    def plan(s):
        s=prefix(s,'> **U4/U5更新（','> **U4/U5更新（2026-10-23）**：'+u4+u5+l4+'详见[教学设计](教学设计/U4-L1_转向来宾_教学设计.md)、[P2修改方案](实验验证/U5-L1-L2-L3_P2复核与修改方案.md)与[SDK核验记录](实验验证/U5_语音SDK能力核验记录.md)。')
        s=prefix(s,'| U5 | L4 |','| U5 | L4 | 语音问答闭环（持续会话管理） | `Speech.chat()`→保留`TaskHandle`；`status/error/done()`查看任务；`cancel()`提交停止请求、`wait(timeout=5.0)`有限等待并确认终态；不以`running()==False`放行重开 | `U5-L4_语音问答闭环` |')
        s=s.replace('## 十三、下一步（2026-10-22）','## 十三、下一步（2026-10-23）')
        s=prefix(s,'3. U4-L1的P2已通过','3. U4-L1 P3教学设计已完成，待用户确认④；覆盖Notebook全部学习内容及评价，垂直居中自主编程列为教师安排下课后补验；P5-B再回填实际投影定位。其余三课继续完成真机确认②。')
        return prefix(s,'4. U5-L1～L3确认②已由用户报告完成','4. U5-L1～L3已完成P2复核，具体修改方案待用户确认；保留用户真机稿、执行记录和L3的wait用法。确认后修订、同步并按清单补验，再判断是否定稿。U5-L4会话管理新稿已完成，待新确认①②，不能沿用旧确认。L2发放时保留Notebook、sound_lab.py和fonts/相对位置。')
    change(PROJ/'X课程开发计划-v4.md',plan)

    def outline(s):
        s=prefix(s,'| **4** | 语音交互闭环','| **4** | 语音问答闭环 | 采音、ASR、LLM、TTS、播放的功能关系；一轮问答与持续会话；应用状态与任务状态的区别 | 保存`chat()`句柄；查看`status/error/done()`；取消并有限等待、核查终态；用字符串、条件和函数管理开始/查看/停止，阻止未结束时重开 | **状态机(B05)**：待机→会话已发起→停止请求已发出；确认终态回待机，转换依据应用操作与任务结果 | — | ④ 会话管理：连续问答、拦住重复开始、确认停止、重新开始并记录实际状态 |')
        s=prefix(s,'**单元产出**：ASR 测试记录','**单元产出**：ASR测试记录 + 波形与TTS试听记录 + 人设对照记录 + 持续会话管理脚本、状态图及操作记录')
        return prefix(s,'> **U5-L4设计复评（','> **U5更新（2026-10-23）**：用户认可持续会话管理方向，L4新Notebook已重构为23格，待设计确认①、真机确认②；原单轮/分段延迟及内部四阶段程序状态机不再沿用。接口依据见[SDK能力核验记录](实验验证/U5_语音SDK能力核验记录.md)。L1～L3保留真机确认②，P2已复核、有问题待[修改方案](实验验证/U5-L1-L2-L3_P2复核与修改方案.md)确认；定稿后再同步相应课时的大纲文字。')
    change(PROJ/'X课程大纲-v4.md',outline)

    def rules(s):
        s=prefix(s,'> **状态更新（2026-10-22，U4-L1与U5）**','> **状态更新（2026-10-23，U4-L1与U5）**：'+u4+u5+l4+'详见教学设计及实验验证目录新增记录。')
        for i in range(1,5):
            start=f'| `03_X课程项目/notebooks/U5-L{i}_'
            if i<4:
                name={1:'语音识别',2:'语音合成',3:'LLM对话'}[i]
                count={1:'34格（25 md/9 code）',2:'34格（24 md/10 code）',3:'32格（25 md/7 code）'}[i]
                extra={1:'保留三声道实测参数；声块时长、队列及任务收尾问题列入方案。',2:'保留sound_lab.py、fonts/wqy-microhei.ttc及发放目录；源内容与附件收尾问题列入方案。',3:'保留用户实测wait及KeyboardInterrupt收尾；终态核查、事实表述与编号问题列入方案。'}[i]
                row=f'| `03_X课程项目/notebooks/U5-L{i}_{name}.ipynb` | U5·L{i} | 🟡 **确认②历史通过；P2已复核、有问题待修改方案确认（2026-10-23）** | 现稿{count}，本轮未改Notebook、输出和执行次数；`_gen_L{16+i}.py`已从现稿逐格反向同步。{extra}具体格号、改法及补验范围见`实验验证/U5-L1-L2-L3_P2复核与修改方案.md`。未登记③通过，未进入P3。 |'
            else:
                row='| `03_X课程项目/notebooks/U5-L4_语音问答闭环.ipynb` | U5·L4 | 🟡 **P1重构稿完成（2026-10-23）；待新确认①②** | 23格（15 md/8 code），`_gen_L20.py`已同步。持续会话管理：开始、查看、停止；保存旧句柄，以done()判断是否可重新开始，区分取消请求与终态。三应用状态为待机、会话已发起、停止请求已发出。8个STEP，三道学习评价与两道思考题。停用单轮/分段计时及内部聆听/处理/回答的伪状态；未使用U7线程或锁。旧稿留存任务记录，不能继承旧确认。 |'
            s=prefix(s,start,row)
        # U4原行前次记录很长，更新本轮阶段而不改其历史代码结论。
        lines=s.splitlines()
        for k,line in enumerate(lines):
            if line.startswith('| `03_X课程项目/notebooks/U4-L1_'):
                lines[k]='| `03_X课程项目/notebooks/U4-L1_转向来宾.ipynb` | U4·L1 | 🟡 **P2已通过；P3教学设计完成，待确认④（2026-10-23）** | 现稿44格（30 md/14 code），本轮未改Notebook。教学设计覆盖STEP01～12、比例对照、两种转身、额外Kpx、观察记录及评价；垂直居中课后在教师安排下补验，投影定位待P5-B回填。用户确认的模式归位、瓶子索引、停止分支及两次0.5秒等待沿用。 |'
        s='\n'.join(lines)+'\n'
        entry='- 2026-10-23 **U4-L1 P3、U5语音SDK核验与P2复核**：U4-L1教学设计完成待确认④；依据16个官方接口/入口页及6个关联类型页，将U5-L4改为23格持续会话管理新稿，待新确认①②。前三课P2发现文字、声块时长、任务终态及附件收尾问题，形成具体修改方案待用户确认，暂不定稿；保留真机Notebook与L3的wait用法，反向同步生成器。新代码只做离线核验，未运行机器人。\n\n'
        s=s.replace('## 7. 变更记录\n\n','## 7. 变更记录\n\n'+entry,1)
        s=s.replace('L1～L3的现稿及确认②状态见§6。语言约定仍须结合具体知识与接口核查。','L1～L3的现稿及确认②状态见§6。2026-10-23已按官方文档重写L4，但新稿尚未真机验证，暂不作为已验证范例；L3用户实测的wait与KeyboardInterrupt收尾保留。语言约定仍须结合具体知识与接口核查。',1)
        return s
    change(BASE/'02_共创规则与上下文/notebook开发规则.md',rules)

    def history(s):
        s=prefix(s,'日期：2026-10-22。状态：','初评日期：2026-10-22；进展更新：2026-10-23。用户认可持续会话管理方向，学生Notebook和生成器已重写；新稿待设计确认①、真机确认②。本记录保留原问题依据，不代表新代码已验证。')
        s=s.replace('以下单元格按现稿从 1 开始计数。','以下单元格按2026-10-22重构前稿从1开始计数，新稿不沿用这些格号。',1)
        s=s.replace('## 8. 确认后联动范围','## 8. 已完成的重构与联动')
        s=s.replace('确认方向后，重写 `notebooks/U5-L4_语音问答闭环.ipynb` 并同步 `_gen_L20.py`；调整','已重写 `notebooks/U5-L4_语音问答闭环.ipynb`（23格，15 md/8 code）并同步 `_gen_L20.py`；已调整',1)
        s=s.replace('本次登记了失效范围与建议方案，并在计划、大纲和规则中注明原设计暂停沿用。原 L4 Notebook、生成器及大纲课程行的内容尚未重写；确认重构方向后再形成学生稿并重新验证，不能沿用原确认①作为新设计的通过记录。','2026-10-23新稿已替换原学生稿及生成器，联动大纲、计划、规则和导航；依据见[语音SDK能力核验记录](U5_语音SDK能力核验记录.md)。旧稿保存在`99-task-contexts/20261023-X课程U4U5推进/U5-L4_重构前.ipynb`供核对。新稿以done()保留未终止的旧句柄，包含取消超时后不重开、终态后重开等分支；离线替身检查只证明控制逻辑，不替代真机确认②。以上补验清单继续有效，原确认①不能作为新设计的通过记录。',1)
        return s
    change(PROJ/'实验验证/U5-L4_真机问题复评与重构建议.md',history)

    def log(s):
        entry='## 2026-10-23 · U4-L1教学设计与U5语音SDK核验、P2复核\n\n- U4-L1完成P3教学设计：45分钟安排覆盖STEP01～12、额外换算、观察记录、检查点和思考题；垂直居中自主编程在教师安排下课后补验。保留已定稿Notebook，教学设计待用户确认④；实际投影定位留待P5-B。\n- 核对用户指定16个语音/音频官方页面及6个关联类型页面，新增能力核验记录，明确chat持续会话、TaskHandle终态、有限音频识别/合成与播放流的能力和限制。保留L3用户实测wait与中断收尾。\n- U5-L4按用户认可方向重写为23格会话管理新稿（15 md/8 code）：开始、查看、取消、确认终态、再次启动；取消超时或任务未结束时保留旧句柄。停用单轮与分段延迟目标，不使用U7线程或锁；待新确认①②。\n- U5-L1～L3已执行P2复核，发现三声道声块换算、播放与任务收尾、音频时长、LLM表述和编号问题，形成逐格修改方案与补验清单，待用户确认后修订，尚未定稿。三课Notebook、执行记录及L2附件保持原稿，生成器反向同步。\n- 联动大纲、计划、开发规则、AGENTS、索引及课程导航。离线验证见本次任务执行记录；未连接机器人，新代码未做真机验证。Git仅本地记录，推送由用户手动完成。\n\n'
        return s.replace('# 更新日志\n\n','# 更新日志\n\n'+entry,1)
    change(ROOT/'CHANGELOG.md',log)

def verify():
    results=[]
    notebooks=selected_notebooks()
    protected=json.loads(text(TASK/'protected_files_sha256.json'))
    for rel,sha in protected.items():
        assert digest(ROOT/rel)==sha, ('protected file changed',rel)
    results.append(f'保护文件SHA-256一致：{len(protected)}份（U4-L1、U5前三课、L2发放目录现有文件）。')
    try:
        import nbformat
    except ImportError:
        nbformat=None
    for i,p in enumerate(notebooks,17):
        nb=json.loads(text(p))
        if nbformat is not None:
            nbformat.validate(nb)
        for c in nb['cells']:
            if c['cell_type']=='code':
                ast.parse(source(c))
        gen=PROJ/f'_gen_L{i}.py'
        # main guard隔离输出，不执行任何SDK代码，不重建Notebook。
        ns={'__name__':'offline_source_check','__file__':str(gen)}
        exec(compile(text(gen),str(gen),'exec'),ns)
        assert [(c['cell_type'],source(c)) for c in nb['cells']]==[(c['cell_type'],source(c)) for c in ns['cells']],gen
        class MemoryOutput:
            def write_text(self, payload, **kwargs):
                self.payload=payload
        memory=MemoryOutput()
        ns['OUT']=memory
        guard=ast.parse(text(gen)).body[-1]
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(ast.Module(body=guard.body, type_ignores=[]),str(gen),'exec'),ns)
        rebuilt=json.loads(memory.payload)
        assert memory.payload.endswith(chr(10))
        assert [(c['cell_type'],source(c)) for c in rebuilt['cells']]==[(c['cell_type'],source(c)) for c in nb['cells']]
        results.append(f'{p.name}：{len(nb["cells"])}格；JSON、代码AST、生成器逐格源内容及内存序列化一致。')
    root_copy=json.loads(text(notebooks[1]))
    issued=NB/'U5-L2'/notebooks[1].name
    assert issued.exists()
    issued_copy=json.loads(text(issued))
    assert [(c['cell_type'],source(c)) for c in root_copy['cells']]==[(c['cell_type'],source(c)) for c in issued_copy['cells']]
    assert (NB/'U5-L2/sound_lab.py').is_file()
    assert (NB/'U5-L2/fonts/wqy-microhei.ttc').is_file()
    ast.parse(text(NB/'U5-L2/sound_lab.py'))
    results.append('U5-L2根稿与发放副本源内容一致；sound_lab.py语法可解析，配套字体存在，保持相对目录。')
    nb4=json.loads(text(notebooks[3]))
    codes=[source(c) for c in nb4['cells'] if c['cell_type']=='code']
    assert len(codes)==8
    assert all('sleep(' not in s and 'Thread(' not in s and 'Lock(' not in s for s in codes)
    assert all(not c['outputs'] and c['execution_count'] is None for c in nb4['cells'] if c['cell_type']=='code')
    class FakeTask:
        def __init__(self,status='RUNNING',accept=True,wait_to=None):
            self.status,self.accept,self.wait_to=status,accept,wait_to
            self.error=RuntimeError('离线替身错误') if status=='FAILED' else None
            self.cancels=0
            self.waits=[]
        def done(self):
            return self.status in ('SUCCEEDED','CANCELLED','FAILED')
        def cancel(self):
            self.cancels+=1
            if self.accept:
                self.status='CANCELLING'
            return self.accept
        def wait(self,timeout=None):
            self.waits.append(timeout)
            if self.wait_to:
                self.status=self.wait_to
            return self.status
    class FakeSpeech:
        def __init__(self):
            self.created=[]
        def chat(self,**kwargs):
            t=FakeTask()
            self.created.append(t)
            return t
    fake=FakeSpeech()
    ns={'speech':fake,'PROMPT':'离线测试','ChatConfig':lambda **kw:kw}
    func_code=next(s for s in codes if s.startswith('def manage_chat('))
    exec(compile(func_code,'L4_manage_chat','exec'),ns)
    f=ns['manage_chat']
    def call(cmd,t,state):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            new,state2=f(cmd,t,state)
        return new,state2,output.getvalue()
    scenarios=[]
    def checked(label,cond):
        assert cond,label
        scenarios.append(label)
    t,st,_=call('查看',None,'待机')
    checked('无旧任务时查看不创建',t is None and st=='待机' and len(fake.created)==0)
    t,st,_=call('停止',None,'待机')
    checked('无旧任务时停止不创建',t is None and st=='待机' and len(fake.created)==0)
    t,st,_=call('开始',None,'待机')
    checked('首次启动保存句柄',t is fake.created[-1] and st=='会话已发起')
    for status in ('PENDING','RUNNING','CANCELLING'):
        t=FakeTask(status)
        n=len(fake.created)
        new,st,_=call('开始',t,'停止请求已发出' if status=='CANCELLING' else '会话已发起')
        checked(status+'未终态禁止覆盖',new is t and len(fake.created)==n)
    t=FakeTask(wait_to=None)
    new,st,_=call('停止',t,'会话已发起')
    checked('取消已提交但等待超时保留句柄',new is t and st=='停止请求已发出' and not t.done() and t.waits==[5.0])
    n=len(fake.created)
    new,st,_=call('开始',t,st)
    checked('取消后未终止不能重开',new is t and len(fake.created)==n)
    t.status='CANCELLED'
    new,st,_=call('查看',t,st)
    checked('稍后查看终态回待机',new is t and st=='待机')
    new,st,_=call('开始',t,st)
    checked('已确认终态后允许重开',new is not t and st=='会话已发起' and len(fake.created)==n+1)
    t=FakeTask(accept=False)
    new,st,_=call('停止',t,'会话已发起')
    checked('取消请求未提交保留原状态',new is t and st=='会话已发起' and t.waits==[])
    t=FakeTask(wait_to='CANCELLED')
    new,st,_=call('停止',t,'会话已发起')
    checked('取消完成回待机',new is t and st=='待机' and t.done())
    for status in ('SUCCEEDED','CANCELLED','FAILED'):
        t=FakeTask(status)
        new,st,out=call('查看',t,'会话已发起')
        checked(status+'终态可识别',new is t and st=='待机' and (status!='FAILED' or '离线替身错误' in out))
    t=FakeTask()
    n=len(fake.created)
    new,st,out=call('未知操作',t,'会话已发起')
    checked('未知操作不创建也不取消',new is t and st=='会话已发起' and len(fake.created)==n and t.cancels==0)
    # STEP02与STEP04的逐格代码也核对保护与有限等待，不执行SDK导入格。
    t=FakeTask('PENDING')
    ns2={'speech':fake,'PROMPT':'测试','ChatConfig':lambda **kw:kw,'chat_task':t,'app_state':'会话已发起'}
    n=len(fake.created)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(codes[1],ns2)
    checked('STEP02防重复',ns2['chat_task'] is t and len(fake.created)==n)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(codes[3],ns2)
    checked('STEP04保留未结束任务',ns2['chat_task'] is t and ns2['app_state']=='停止请求已发出')
    # 按练习格保存两个返回值，最终收尾格能够停掉已有会话。
    ns2.update(manage_chat=f,command='开始')
    with contextlib.redirect_stdout(io.StringIO()):
        exec(codes[5],ns2)
    checked('STEP06不丢弃句柄',ns2['chat_task'] is t)
    t.wait_to='CANCELLED'
    with contextlib.redirect_stdout(io.StringIO()):
        exec(codes[7],ns2)
    checked('STEP08最终收尾',ns2['chat_task'] is t and ns2['app_state']=='待机' and t.done())
    results.append(f'U5-L4管理逻辑：{len(scenarios)}个离线替身情境通过；不含设备/API联调结论。')
    u4path=next(NB.glob('U4-L1_*.ipynb'))
    u4=json.loads(text(u4path))
    teach=PROJ/'教学设计/U4-L1_转向来宾_教学设计.md'
    ts=text(teach)
    assert len(u4['cells'])==44 and sum(c['cell_type']=='code' for c in u4['cells'])==14
    assert len(re.findall(r'^### 环节[1-6]',ts,flags=re.M))==6
    covered_steps=set()
    for first,last in re.findall(r'STEP\s*(\d{2})(?:[–～—-](\d{2}))?',ts):
        covered_steps.update(range(int(first),int(last or first)+1))
    assert covered_steps==set(range(1,13)),covered_steps
    for word in ('垂直居中','Kpx','5.1','5.2','5.3','5.4'):
        assert word in ts,word
    assert sum((4,6,11,9,9,6))==45
    assert '教学资源与附件' not in ts
    results.append('U4-L1 P3：六环节共45分钟，STEP01～12及自主编程、额外Kpx、全部观察/检查点/思考题均有安排；未修改Notebook。')
    # 只检查本轮交付文档中的本地Markdown链接。
    link_docs=[teach]+list((PROJ/'实验验证').glob('U5*复核与修改方案.md'))+[(PROJ/'实验验证/U5_语音SDK能力核验记录.md')]
    for p in link_docs:
        for target in re.findall(r'\]\(([^)]+)\)',text(p)):
            if not target.startswith(('http:','https:','#')):
                assert (p.parent/target.split('#')[0]).exists(),(p,target)
    results.append('本轮新增教师稿、P2方案及SDK记录的本地链接可定位。')
    log='\n'.join(results)+'\n\nL4离线情境：\n'+'\n'.join('- '+s for s in scenarios)+'\n'
    write(TASK/'离线检查结果.txt',log)
    print(log)

mode = sys.argv[2] if len(sys.argv)>2 else 'short'
if mode=='build':
    build()
elif mode=='short':
    short()
elif mode=='details':
    details()
elif mode=='records':
    update_records()
elif mode=='verify':
    verify()
elif mode=='resync':
    resync()
elif mode=='final_wording':
    final_wording()
