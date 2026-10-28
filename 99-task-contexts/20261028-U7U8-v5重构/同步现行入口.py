"""更新v5现行导航与状态，并生成只含本轮增量的HEAD版本供本地提交。"""
from pathlib import Path
import json
import hashlib
import subprocess
import difflib

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
C = '05-internal-materials/vocational-planning/03_X课程项目/'
RULE = '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
shared = ['AGENTS.md','INDEX.md','CHANGELOG.md','README.md','05-internal-materials/vocational-planning/README.md',
          C+'X课程开发计划-v4.md',C+'X课程当前进度.md',RULE,C+'notebooks/_外挂附件清单.md',
          C+'U8-P1开发准备.md',C+'实验验证/U7-L4与U8_内容边界排查.md',C+'实验验证/U7_修订与分格核查记录.md',
          C+'_diffcheck_u2.py',C+'_regen_from_nb.py']
base = json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
for rel in shared:
    if rel not in base['files']:
        raw=(ROOT/rel).read_bytes();p=TASK/'before'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        base['files'][rel]=hashlib.sha256(raw).hexdigest()
(TASK/'基线.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

names=['多传感器订阅','足球定位与自动踢球','多线程协作','多模态流程衔接',
       '选题与任务拆解','分主题开发模板','联调模板','展示评分表']
titles=['多传感器订阅','足球定位与自动踢球','多线程协作','多模态流程衔接',
        '选题与任务拆解','核心模块开发','真机彩排与联调','成果展演与答辩']
counts=[(15,6),(17,7),(15,6),(13,5),(5,0),(17,7),(13,5),(6,0)]
filenames=[f'U{7+i//4}-L{i%4+1}_{name}.ipynb' for i,name in enumerate(names)]
summary='按用户授权完成v5大纲与U7/U8八课P1，101格/36代码格；现有主Notebook增至32课。U7加入订阅工程策略、足球坐标与自动踢球、并发及局部流程衔接；U8导览/踢球二选一，重点为需求、接口、分工、集成、彩排复测与答辩。①②待审/验证，未进入P2。'


def once(text,old,new):
    if text.count(old)!=1:raise ValueError((text.count(old),old[:120]))
    return text.replace(old,new,1)


def beneath(text,block):
    title=next(s for s in text.splitlines() if s.startswith('# '))
    return once(text,title+'\n\n',title+'\n\n'+block+'\n\n')


def row_replace(text,prefix,new):
    rows=[s for s in text.splitlines() if s.startswith(prefix)]
    if len(rows)!=1:raise ValueError(('row',prefix,len(rows)))
    return once(text,rows[0],new)


def transform(rel,text):
    if rel=='AGENTS.md':
        text=beneath(text,'> **U7/U8 v5（2026-10-28）**：'+summary+'最新大纲：`'+C+'X课程大纲-v5.md`；审阅入口：`'+C+'实验验证/U7_U8_v5重构与验证清单.md`。下列U7修订与U8准备为本版之前的历史记录。')
        text=text.replace('最新大纲：`X课程大纲-v4.md`','最新大纲：`X课程大纲-v5.md`')
        text=text.replace('28课主Notebook，U8四课尚未产出','32课主Notebook，U7/U8八课v5 P1待①②')
        text=text.replace('7课P1待审/验证','11课P1待审/验证')
        text=text.replace('U1–U7 共 28 课时','U1–U8 共 32 课时（U7/U8为v5新P1，待①②）')
        return text
    if rel=='INDEX.md':
        text=beneath(text,'> X课程v5 / 多传感器融合与多模态 / 自动踢球 / 机器人坐标 / U8导览踢球二选一：[v5大纲]('+C+'X课程大纲-v5.md)、[八课P1与验证清单]('+C+'实验验证/U7_U8_v5重构与验证清单.md)（101格/36代码格；32课主Notebook；①②待完成）。旧U7与U8准备记录保留历史含义。')
        text=text.replace('X课程大纲-v4.md`（最新版；历史版 v3 同目录）','X课程大纲-v5.md`（最新版；历史版v3/v4同目录）')
        return row_replace(text,'| X 课程（具身智能机器人实践） |','| X 课程（具身智能机器人实践） | `'+C+'X课程大纲-v5.md` |')
    if rel=='CHANGELOG.md':
        return beneath(text,'## 2026-10-28 · v5大纲与U7/U8八课P1重构\n\n'
            '- 按用户授权先生成v5大纲，再重写U7四课并完成U8四课，合计101格/36代码格，均待①②；主Notebook现覆盖32课。U1～U6与v4原稿未改。\n'
            '- U7-L1改为多路状态观察窗，补融合与多模态定义、实时数值及队列比较；L2加入足球检测、机器人坐标、独立标定核对及自动踢球；L3保留一个检测线程与播报，L4改局部交接片段。\n'
            '- U8明确导览/踢球二选一，完整提供需求、接口分工、模块开发、跨课文件、彩排复测及展演答辩任务；移入适合项目的步骤列表与日志。\n'
            '- 提供标定、有限任务与控制收尾附件、本组模板和八份生成器；26项离线替身测试通过，不作为真机结果。球坐标近似映射的动态适用性仍待验证，无实测数据默认不运动。\n'
            '- 归档旧U7及生成器，更新主大纲导航、进度、计划、开发规则和维护工具。本地提交，推送由用户进行。')
    if rel=='README.md':
        return beneath(text,'> **X课程v5（2026-10-28）**：'+summary+'[新大纲]('+C+'X课程大纲-v5.md)、[八课P1与验证清单]('+C+'实验验证/U7_U8_v5重构与验证清单.md)。下条U7记录为本版之前的修订。')
    if rel=='05-internal-materials/vocational-planning/README.md':
        text=beneath(text,'> **U7/U8 v5（2026-10-28）**：'+summary+'[v5大纲](03_X课程项目/X课程大纲-v5.md)、[重构与逐课验证](03_X课程项目/实验验证/U7_U8_v5重构与验证清单.md)。以下U7/U8旧记录按历史范围阅读。')
        text=text.replace('28课已有主Notebook，21课已有教学设计，21课已有PPT大纲、16课已有PPTX；U8尚未产出','32课已有主Notebook，21课已有教学设计，21课已有PPT大纲、16课已有PPTX；U7/U8新P1待①②')
        text=text.replace('`X课程大纲-v4.md`（**现行**）','`X课程大纲-v4.md`（历史） / `X课程大纲-v5.md`（**现行**）')
        return text
    if rel==C+'X课程开发计划-v4.md':
        text=text.replace('> **U8开发准备（2026-10-28）**','> **U8开发准备历史记录（2026-10-28）**')
        text=beneath(text,'> **v5大纲实施（2026-10-28）**：'+summary+'本开发计划仍用v4文件名；当前课程内容依据[X课程大纲-v5](X课程大纲-v5.md)，[重构与验证清单](实验验证/U7_U8_v5重构与验证清单.md)记录新稿与归档范围。')
        text=text.replace('> **对应大纲**：X课程大纲-v4.md','> **对应大纲**：X课程大纲-v5.md（v4保留历史）')
        text=text.replace('7课P1待审/验证、4课尚未产出','11课P1待审/验证、0课未产出')
        text=text.replace('32 个 notebook，对齐 v4 大纲','32 个 notebook，对齐 v5 大纲')
        for i,title in enumerate(titles):
            unit=7+i//4;lesson=i%4+1
            if unit==7:
                desc=['多路回调/数值快照/时间戳/有限队列/融合与多模态概念',
                      'soccer检测、像素与机器人坐标、近似标定与独立核对、SoccerKickManager四接口',
                      '一个检测线程＋主线程；Lock/Event、播报期间更新、join/is_alive及SDK任务退出',
                      '导览/足球局部片段；播报后新观测、返回原因、句柄与管理器分别收尾'][i]
            else:desc=['完整委托、二选一、需求验收、模块接口与分工','本组Python模板、模块测试与整合、版本与跨课文件','基线与复测、问题依据、版本与证据保存','完整展演、两个实际概念答辩、评分与个人说明'][i-4]
            text=row_replace(text,f'| U{unit} | L{lesson} |',f'| U{unit} | L{lesson} | {title} | {desc}（v5 P1完成，待①②） | `{filenames[i][:-6]}` |')
        text=row_replace(text,'| U7     |','| U7 | 多模态行为协同 | 4 | 4 notebook（v5新P1，待①②） | 4（规划） | 4（规划） | 4（规划） |')
        text=row_replace(text,'| U8     |','| U8 | 综合应用开发与展演 | 4 | 4 notebook（v5 P1，L1/L4为完整活动材料） | 4（规划） | 4（规划） | 4（规划） |')
        text=row_replace(text,'| U8 剧场主题 |','| U8应用主题 | 二选一（v5） | A导览 / B踢球；不再保留自由主题为默认第三选项 |')
        return text
    if rel==C+'X课程当前进度.md':
        text=beneath(text,'> **v5最新状态（2026-10-28）**：U7/U8八课P1学生稿已完成，待①②；[v5大纲](X课程大纲-v5.md)、[重构与验证清单](实验验证/U7_U8_v5重构与验证清单.md)。32课已有主Notebook，本轮未进入P2。此前U8“准备完成、学生稿未产出”是历史状态。')
        text=row_replace(text,'| P1修订或待审/验证 |','| P1新稿/修订，待审或真机验证 | 11 | U4-L2～L4、U7/U8八课；新八课待①② |')
        text=row_replace(text,'| P1开发准备已完成，学生稿尚未产出 |','| 未找到P1产物 | 0 | 32课主Notebook已齐 |')
        for i,title in enumerate(titles):
            unit=7+i//4;lesson=i%4+1;prefix=f'| [U{unit}-L{lesson}' if unit==7 else f'| U{unit}-L{lesson} '
            cells,python=counts[i]
            text=row_replace(text,prefix,f'| [U{unit}-L{lesson} {title}](notebooks/{filenames[i]}) | v5 P1完成，待设计审阅与真机验证 | ①待审；②待完成；未进入P2 | 按[验证清单](实验验证/U7_U8_v5重构与验证清单.md)逐格审阅/验证 | {cells}格/{python}代码格；新稿不继承旧代码验证 |')
        text=row_replace(text,'| 当前主Notebook |','| 当前主Notebook | 32 | U1～U8各四课；另保留U3-L1“ 1”副本，旧U7已归档 |')
        text=row_replace(text,'| U8学生Notebook／教师稿／课件 |','| U8学生Notebook／教师稿／课件 | 4／0／0 | 四课P1已产出，待①②；未进入教师设计与课件阶段 |')
        text=row_replace(text,'8. **U8开发准备与学生稿分开**','8. **U8已由准备进入P1产出**：v5四课完整学生材料已写入；导览/踢球二选一，①②待完成，P2未开始。旧准备报告不作为现行完成结论。')
        text=row_replace(text,'4. 审阅U7本轮修订','4. 审阅v5大纲及U7/U8新P1，完成①与逐格真机②；优先核对足球标定、动态条件及管理器控制。旧U7验证不覆盖新稿。')
        return text
    if rel==RULE:
        text=beneath(text,'> **U7/U8 v5 P1（2026-10-28）**：'+summary+'详见[重构与验证清单](../03_X课程项目/实验验证/U7_U8_v5重构与验证清单.md)。下条U7修订为v4历史记录。')
        for i,title in enumerate(titles[:4]):
            prefix=f'| `03_X课程项目/notebooks/U7-L{i+1}_'
            cells,python=counts[i]
            if any(s.startswith(prefix) for s in text.splitlines()):
                text=row_replace(text,prefix,f'| `03_X课程项目/notebooks/{filenames[i]}` | U7·L{i+1} | 🟡 **v5 P1完成，待①②** | {cells}格/{python}代码格；生成器`_gen_L{25+i}.py`；具体任务与验证见v5重构清单，不沿用旧U7状态 |')
        # HEAD与工作区的旧进度表不完全相同，独立记录八课现行状态。
        rows=[]
        for i in range(8):
            cells,python=counts[i]
            rows.append(f'| U{7+i//4}-L{i%4+1} | {titles[i]} | {cells}格/{python}代码格 | `_gen_L{25+i}.py` | P1完成，待①② |')
        text+='\n\n### v5八课当前状态（2026-10-28）\n\n| 课程 | 课题 | 学材规模 | 生成器 | 阶段 |\n| --- | --- | --- | --- | --- |\n'+'\n'.join(rows)+'\n'
        text+='\n\n### v5多模态与项目学材（2026-10-28）\n\n- 先定义多传感器融合、多路联合观察及多模态，按实际实验结果使用名称；不因同时打印几路数据而宣称完成定位融合。\n- 新概念与练习相邻；订阅状态窗显示实际值、源时刻及本地接收后时长，不把后者当端到端延迟。L1使用SDK回调，线程在L3正式引入。\n- 坐标单位、来源与适用条件必须明确；近似标定有独立核对和动态适用性验证，缺失时不启动自动踢球。\n- 收尾并入最后操作说明；完整项目组织留给U8。活动课无代码也需完整任务、示例、记录、检查与评价。\n- 变更记录：U7/U8按v5重写101格/36代码格，①②待完成；U1～U6未改，旧U7归档。\n'
        return text
    if rel==C+'notebooks/_外挂附件清单.md':
        return text+'\n\n## U7/U8 v5附件（2026-10-28）\n\n| 附件 | 使用位置 | 发放关系/条件 | 状态 |\n| --- | --- | --- | --- |\n| `x_lab/ball_position.py`与`__init__.py` | U7-L2标定与独立核对；后续足球复用 | x_lab与Notebook同目录，依赖NumPy；ball_calibration.json由本机实验生成 | P1附件，待真机核对；不附虚构标定 |\n| `x_lab/flows.py`及`x_lab/README.md` | U7-L3/L4、U8-L2/L3局部功能和收尾 | 保留整个x_lab目录；实际SDK与视觉依赖需可用 | P1参考，离线替身测试通过，非真机结论 |\n| `u8_team_template.py` | U8-L2首次复制为u8_team.py；L3沿用本组文件 | 模板与Notebook同目录；已有本组文件不覆盖，任务退出后再重载 | 起始配置待小组填写，未冒充完整成品 |\n'
    if rel in [C+'U8-P1开发准备.md',C+'实验验证/U7-L4与U8_内容边界排查.md',C+'实验验证/U7_修订与分格核查记录.md']:
        report='实验验证/U7_U8_v5重构与验证清单.md' if rel==C+'U8-P1开发准备.md' else 'U7_U8_v5重构与验证清单.md'
        text=beneath(text,'> **历史记录说明（2026-10-28）**：本文描述v4阶段，已由用户本轮授权的v5重构接续；新U7/U8八课P1已产出，待①②。现行内容与验证要求见[重构清单]('+report+')。旧稿链接指向归档，不作为当前Notebook版本。')
        for name in ['U7-L1_多传感器订阅.ipynb','U7-L2_视觉-运动-语音桥接.ipynb','U7-L3_多线程协作.ipynb','U7-L4_小剧场预演.ipynb']:
            text=text.replace('../notebooks/'+name,'../../../../99-task-contexts/20261028-U7U8-v5重构/archive/U7-v4/'+name)
        return text
    if rel in [C+'_diffcheck_u2.py',C+'_regen_from_nb.py']:
        lines=text.splitlines(keepends=True)
        for j,line in enumerate(lines):
            if line.lstrip().startswith(('("_gen_L26.py",','("_gen_L28.py",',"('_gen_L26.py',","('_gen_L28.py',")):
                lines[j]=line.replace('U7-L2_视觉-运动-语音桥接.ipynb',filenames[1]).replace('U7-L4_小剧场预演.ipynb',filenames[3])
        text=''.join(lines)
        if rel.endswith('_diffcheck_u2.py'):
            anchor=next(line for line in text.splitlines() if line.lstrip().startswith('("_gen_L28.py",'))
            extra='\n'.join(f'    ("_gen_L{25+i}.py", "{filenames[i]}"),' for i in range(4,8))
            return once(text,anchor,anchor+'\n    # v5：U8四课完整P1。\n'+extra)
        anchor=next(line for line in text.splitlines() if line.lstrip().startswith("('_gen_L28.py',"))
        extra='\n'.join(f'    ("_gen_L{25+i}.py", os.path.join(HERE, "notebooks", "{filenames[i]}")),' for i in range(4,8))
        text=once(text,anchor,anchor+'\n    # v5：U8四课完整P1。\n'+extra)
        branch='''    # v5八课保留完整Notebook元数据、cell id与用户执行记录。
    if os.path.basename(gen_path) in [f"_gen_L{i}.py" for i in range(25, 33)]:
        import pprint
        payload = pprint.pformat(nb, width=110, sort_dicts=False)
        source = ('# -*- coding: utf-8 -*-\\n'
                  '\"\"\"v5 P1镜像；重跑前核对Notebook手改。\"\"\"\\n'
                  'import json\\nfrom pathlib import Path\\nNOTEBOOK = ' + payload + '\\n'
                  'if __name__ in ("__main__", "__gen__"):\\n'
                  '    path = Path(__file__).parent / "notebooks" / ' + repr(nbname) + '\\n'
                  '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\\\n", encoding="utf-8")\\n')
        open(gen_path, "w", encoding="utf-8", newline="\\n").write(source)
        return

'''
        text=once(text,'    parts = [HEADER_TMPL.format',branch+'    parts = [HEADER_TMPL.format')
        return once(text,'if __name__ == "__main__":',
                    'for number in range(25, 33):\n    DOC.setdefault(f"_gen_L{number}.py", "v5 P1 Notebook完整镜像")\n\nif __name__ == "__main__":')
    raise ValueError(rel)


pending=[]
local_only=[]
for rel in shared:
    data=(ROOT/rel).read_bytes()
    if hashlib.sha256(data).hexdigest()!=base['files'][rel]:raise RuntimeError('共享文件在基线后变动：'+rel)
    current=data.decode('utf-8').replace('\r\n','\n')
    found=subprocess.run(['git','show','HEAD:'+rel],cwd=ROOT,capture_output=True)
    if found.returncode:
        if rel not in [C+'_diffcheck_u2.py',C+'_regen_from_nb.py']:
            raise RuntimeError('HEAD中缺少共享文档：'+rel)
        local_only.append(rel)
        head=None
    else:
        head=found.stdout.decode('utf-8').replace('\r\n','\n')
    pending.append((rel,data,transform(rel,current),transform(rel,head) if head is not None else None))
tool_patch=[]
for rel,data,work,new_head in pending:
    newline='\r\n' if b'\r\n' in data else '\n'
    (ROOT/rel).write_bytes(work.replace('\n',newline).encode('utf-8'))
    if new_head is not None:
        p=TASK/'head-increment'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new_head,encoding='utf-8',newline='\n')
    else:
        old=data.decode('utf-8').replace('\r\n','\n')
        tool_patch.extend(difflib.unified_diff(old.splitlines(keepends=True),work.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel,n=0))
(TASK/'维护工具本轮增量.patch').write_text(''.join(tool_patch),encoding='utf-8',newline='\n')
(TASK/'共享文档清单.json').write_text(json.dumps([s for s in shared if s not in local_only],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(TASK/'本地维护工具.json').write_text(json.dumps(local_only,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('已精确同步',len(shared),'份导航、进度、历史入口与维护工具；HEAD增量已留待提交。')
