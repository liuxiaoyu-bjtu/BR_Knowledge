"""保留工作区其他任务修改；共享文件单独生成基于HEAD的本轮提交增量。"""
from pathlib import Path
import hashlib
import json
import subprocess

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[1]
C='05-internal-materials/vocational-planning/03_X课程项目/'
RULE='05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md'
REPORT='实验验证/U4-L2_重开发回读与第五部分同步.md'
base=json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
note='用户重开发稿已逐格回读，第五部分按实际行走/速度比较、框高标定核对、阈值程序重写；36格（26 Markdown/10代码）。目标、反比例解释及生成器已同步，用户代码和执行信息保留；未新增确认①②或P2通过。'

def top(text,block):
    title=next(s for s in text.splitlines() if s.startswith('# '))
    return text.replace(title+'\n\n',title+'\n\n'+block+'\n\n',1)

def row(text,prefix,new):
    lines=[s for s in text.splitlines() if s.startswith(prefix)]
    if len(lines)!=1:raise ValueError((prefix,len(lines)))
    return text.replace(lines[0],new,1)

def transform(rel,text):
    if rel=='AGENTS.md':
        return top(text,'> **U4-L2重开发稿同步（2026-10-29）**：'+note+'入口：`'+C+REPORT+'`。旧41格及“实验前移待实施”描述保留历史含义；运动异常清理、视觉无效数据处理及学生阈值代码仍须真机核对。')
    if rel=='INDEX.md':
        return top(text,'> U4-L2重开发 / 行进速度比较 / 框高反比例估距 / 视觉停止阈值：[第五部分与后续Phase依据]('+C+REPORT+')（2026-10-29；36格/10代码，生成器同步，未新增真机确认）。')
    if rel=='CHANGELOG.md':
        return top(text,'## 2026-10-29 · U4-L2重开发稿回读与记录同步\n\n'
                   '- 依据用户当前36格稿重写第五部分，按STEP04～08设置行走与速度比较、框高标定及独立核对、停止阈值采样与程序验证记录，重写检查点和思考题。\n'
                   '- 同步三项目标，修正框高公式的正反比例混淆、x分量与累计路程等直接影响学习的说明；用户10代码格、执行信息与元数据保留。\n'
                   '- 反向同步生成器和本地维护工具，更新v5大纲、计划、逐课进度、开发规则与入口；旧复评保留历史范围，L3/L4既有程序不变。\n'
                   '- 本轮只做离线核查，未登记①②或P2通过；记录运动退出、视觉前置检查及学生自主程序等待验项。本地提交，用户手动推送。')
    if rel=='05-internal-materials/vocational-planning/README.md':
        return top(text,'> **U4-L2（2026-10-29）**：'+note+'[同步与后续Phase清单](03_X课程项目/'+REPORT+')。旧41格与旧实验顺序记录按历史阅读。')
    if rel==C+'X课程大纲-v5.md':
        text=top(text,'> **U4-L2现稿同步（2026-10-29）**：'+note+'[阶段依据与待验项]('+REPORT+')。L2采用分组实验记录，不再要求同一次停靠强制取得三项距离；L3/L4既有控制流程未据此改写。')
        text=text.replace('L2 对照视觉估距、里程计推算与卷尺实测','L2 分别核对里程计行进、视觉估距与实测停止阈值')
        text=text.replace('5. 对照同一次停靠的里程计推算间距、框高估距与卷尺实测，解释读数差异及交叉核对的作用；不要求自动修正里程计偏差。',
                          '5. 引用L2行走、框高标定核对与阈值程序的有效记录，分别用卷尺检查实际位移或间距，解释差异与适用条件；跨次实验注明条件，不拼接为同一次停靠，不要求自动修正里程计。')
        text=row(text,'| **2** | 走近来宾', '| **2** | 走近来宾（距离估计与核对） | 区分计划行进量、里程计位置分量和实际间距；相近条件下比较速度；理解框高反比例近似与实测阈值的用途 | `reset_odom()`清零；STEP04按里程计行进量停止，STEP05比较vx；STEP06取图、检测和画框，STEP07独立核对框高估距，STEP08自主编写阈值停止程序 | **标定(B11)**：已知距离对应与独立核对；**传感局限(B12)**：视野、目标、姿态、起停与测量条件 | — | ② 行走/速度比较及卷尺记录；③ 框高标定、独立误差和停止阈值验证；不要求优化漂移 |')
        text=text.replace('引用 L2 的里程计推算、框高估距与卷尺实测，说明交叉核对的作用', '分别引用L2行走、视觉标定与阈值验证记录，说明测量核查的作用')
        text=text.replace('里程计接近与视觉估距记录', '里程计行走/速度比较、框高标定与阈值验证记录')
        return text
    if rel==C+'X课程开发计划-v4.md':
        text=top(text,'> **U4-L2现稿（2026-10-29）**：'+note+'后续P2～P6按[新稿映射]('+REPORT+')推进，旧STEP08/09记录要求不再沿用。')
        return row(text,'| **U4** | **L2** |','| **U4** | **L2** | **走近来宾（距离估计与核对）** | STEP04实际行走、STEP05比较vx、STEP06框高标定、STEP07独立核对、STEP08实测阈值自主程序；第五部分分组记录；36格/10代码，生成器同步，真机②仍待确认 | `U4-L2_走近来宾` |')
    if rel==C+'X课程当前进度.md':
        text=row(text,'| [U4-L2 走近来宾]', '| [U4-L2 走近来宾](notebooks/U4-L2_走近来宾.ipynb) | 用户重开发P1稿；第五部分及关联说明已同步 | 本轮未新增①②确认；②未完成，未进P2 | 按[回读与待验清单]('+REPORT+')逐格验证，再P2 | 36格/10代码；学生阈值代码仍待编写验证；循环末值、异常清理与视觉有效条件需核对 |')
        return row(text,'1. U4-L2的实验结构', '1. U4-L2已由用户前移真实行走并增加速度比较、阈值任务；第五部分与生成器已按36格稿同步。按[待验清单]('+REPORT+')确认①②，再审定P2；L3/L4的控制和旧L2引用仍需各自复核。')
    if rel==RULE:
        text=top(text,'> **U4-L2重开发稿（2026-10-29）**：'+note+'详见[后续阶段依据](../03_X课程项目/'+REPORT+')。')
        prefix='| `03_X课程项目/notebooks/U4-L2_走近来宾.ipynb`'
        new=prefix+' | U4·L2 | 🟡 **用户重开发P1稿；真机确认②未完成** | **36格（26 md/10代码）**；STEP04行走、STEP05速度比较、STEP06标定、STEP07独立核对、STEP08阈值自主程序；第五部分、目标与完整镜像`_gen_L14.py`同步。代码与执行记录保留；不得用旧41格或旧三值并列要求生成后续材料。 |'
        if any(s.startswith(prefix) for s in text.splitlines()):text=row(text,prefix,new)
        else:text+='\n\n### U4-L2当前源文件（2026-10-29）\n\n| 文件 | 课节 | 阶段 | 内容 |\n| --- | --- | --- | --- |\n'+new+'\n'
        return text
    if rel==C+'实验验证/U4-L2-L4_距离实验复评与文字校对.md':
        return top(text,'> **L2后续状态（2026-10-29）**：用户已经重开发L2，真实行走前移并增加速度比较和实测阈值自主任务；现稿36格，第五部分、目标及生成器已同步。[现行依据与待验清单](U4-L2_重开发回读与第五部分同步.md)。本报告的旧格号、STEP与“尚未实施”只描述当时版本；L3/L4的未完成项仍按各自现稿核对，未新增②。')
    raise ValueError(rel)

pending=[]
for rel in base['shared']:
    data=(ROOT/rel).read_bytes()
    assert hashlib.sha256(data).hexdigest()==base['files'][rel], '共享文件已变化：'+rel
    current=data.decode('utf-8').replace('\r\n','\n')
    head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
    pending.append((rel,data,transform(rel,current),transform(rel,head)))
for rel,data,work,head in pending:
    newline='\r\n' if b'\r\n' in data else '\n'
    (ROOT/rel).write_bytes(work.replace('\n',newline).encode('utf-8'))
    p=TASK/'head-increment'/rel;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(head,encoding='utf-8',newline='\n')
print('已同步',len(pending),'份现行入口与历史说明；其他任务改动未纳入本轮HEAD增量。')
