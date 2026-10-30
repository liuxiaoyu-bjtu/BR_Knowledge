from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
T=Path(__file__).resolve().parent
P='05-internal-materials/vocational-planning/03_X课程项目/'
REPORT='U7-L1_能力选择与初步方案修订.md'
SUMMARY='L1先分解接待需求，选择感知单元与基本能力、说明理由，再画初步方案并实验检查取数安排；新增一次读取/订阅对比，跨路换算和慢队列降为选做。21格/8代码，原六格代码与执行信息保留，生成器同步；P1修订待①②，未运行机器人。'


def prepend(text,note):
    first,rest=text.split('\n',1)
    return first+'\n\n'+note+'\n'+rest


def transform(rel,text):
    text=text.replace('\r\n','\n')
    if rel=='AGENTS.md':
        return prepend(text,f'> **U7-L1能力主线（2026-10-30）**：{SUMMARY}当前U7四课66格/26代码，八课109格/39代码，其他课Notebook不变。入口：`{P}实验验证/{REPORT}`。下方103格/37代码为此前统计。')
    if rel=='CHANGELOG.md':
        return prepend(text,f'## 2026-10-30 — U7-L1从能力选择进入技术方案\n\n{SUMMARY}\n\n同步单元分工、计划进度与测试格号，其他31课主Notebook与附件不变。[修订依据]({P}实验验证/{REPORT})。当前八课109格/39代码；仅本地Git提交，推送由用户操作。\n')
    if rel=='INDEX.md':
        return prepend(text,f'> U7-L1能力选择 / 需求到技术方案 / 感知选型 / 一次读取与轮询订阅：[本轮修订]({P}实验验证/{REPORT})（2026-10-30，21格/8代码；U7四课66格/26代码，八课109格/39代码；P1待①②）。')
    if rel=='05-internal-materials/vocational-planning/README.md':
        return prepend(text,f'> **U7-L1能力主线（2026-10-30）**：{SUMMARY}[修订依据](03_X课程项目/实验验证/{REPORT})。当前八课109格/39代码。')
    if rel.endswith('notebook开发规则.md'):
        text=text.replace('| U7-L1 | 多传感器订阅 | 15格/6代码格 |','| U7-L1 | 多传感器订阅 | 21格/8代码格 |')
        return text.rstrip()+f'''\n\n## 从问题选择能力，再安排接口（2026-10-30）

按用户对U7能力链的说明：先根据真实问题选择机器人感知单元与基本能力，再综合组织方案，随后逐步实现。L1重点为前两步，取数代码用于验证方案中的一部分。

- 先拆任务的信息与行为，再选择能力并说明用途和限制；不能先规定多路配置，再把会调用接口当作会选型。
- 学生先作判断，参考随后提供；追问不选什么、需求缩减后去掉什么，不以接口数量评价质量。
- 方案写信息怎样支持判断、何时更新、缺失如何处理，实验后回修并给依据。
- 一次读取、轮询、订阅分别解释；需要多次读数不等于只能订阅。高级时序与队列可选做，不挤占能力活动。
- L1不代替U8完整需求验收、模块分工与整合；静止原始数据不证明检测与行为已实现。

L1现21格/8代码，八课109格/39代码，P1待①②。[依据](../03_X课程项目/实验验证/{REPORT})。\n'''
    note=f'> **U7-L1能力主线（2026-10-30）**：{SUMMARY}[设计依据](实验验证/{REPORT})。当前八课109格/39代码，其他31课Notebook与附件不变。'
    if rel.endswith('X课程大纲-v5.md'):
        start=text.index('### U7：');end=text.index('### U8：',start)
        section=text[start:end].replace('先解决“读到了什么、还能不能用”，再解决','先从问题选择感知与基本能力，画初步方案、检验取数安排，再解决')
        lines=[]
        for line in section.splitlines(keepends=True):
            if line.startswith('| 1 | 多传感器订阅 |'):
                line='| 1 | 多传感器订阅 | 从接待问题分解信息与行为，选择感知单元和基本能力并说明理由；画初步方案，安排更新和交接；定义融合、多路观察与多模态 | 先填选择表和技术路线；get_imu一次读取/轮询概念与subscribe_imu实测比较；三路取数检查方案，缺失和时间有据记录；跨路换算和慢队列选做 | 需求到能力选择、初步方案；E09时序基础，联合观察不等于融合定位 | 能力选择表、初步方案及实验后修订、取数对照与待验项 |\n'
            lines.append(line)
        section=''.join(lines).replace('**课时分工**：L1保持静止，无需自行创建线程；','**课时分工**：L1重点为从问题选择能力、组织初步方案，再静止验证取数；订阅为候选方式，时序/队列深化按条件选做，无需自行创建线程；')
        section=section.replace('**单元产出**：三路数据与队列实验、','**单元产出**：能力选择与初步方案、读取/订阅和三路取数记录（队列拓展选做）、')
        text=text[:start]+section+text[end:]
    elif rel.endswith('X课程开发计划-v4.md'):
        text=text.replace('多路回调/数值快照/时间戳/有限队列/融合与多模态概念（v5 P1完成，待①②）','问题分解与能力选择、初步方案、一次读取/订阅对比和三路取数验证；时序换算/慢队列选做（21格/8代码，P1修订待①②）')
    elif rel.endswith('X课程当前进度.md'):
        lines=[]
        for line in text.splitlines(keepends=True):
            if line.startswith('| [U7-L1 '):
                line=line.replace('v5 P1完成，待设计审阅与真机验证','P1能力主线修订，待审阅与真机验证').replace('15格/6代码格；新稿不继承旧代码验证','21格/8代码格；先审选择与方案，再验取数；无新增真机确认')
            lines.append(line)
        text=''.join(lines)
    elif rel.endswith('U7_逐课真机测试指导.md'):
        start=text.index('## 2. L1：');end=text.index('## 3. L2：',start)
        text=text[:start]+(T/'L1测试段.md').read_text(encoding='utf-8')+'\n'+text[end:]
        text=text.replace('共 60 格、24 格代码','共 66 格、26 格代码')
        text=text.replace('本指导对应2026-10-29学材补全后的四份 v5 Notebook','本指导对应2026-10-30更新后的四份 v5 Notebook')
        text=text.replace('| 三路数值与时间含义、队列、退出订阅 |','| 能力选择与初步方案、读取/订阅对比、多路取数与回修；队列选做 |')
        text=text.replace('1. L1 的真实字段与时间条件是否支持现有说明；队列和中断后退出是否符合预期。','1. L1能否先作能力选择与方案，再用取数结果修订；字段、时间和退出是否符合说明，队列可记选做。')
        note=f'> **L1主线更新（2026-10-30）**：L1现21格/8代码，先审能力选择与初步方案，再验取数；新增STEP 01A/01B，原格号顺延，第二部分已更新。[依据]({REPORT})。其余三课代码格号不变，未新增真机结论。下方10月29日说明的旧统计与格号保留历史含义，当前以本段与第二部分为准。'
    elif rel.endswith('U7_U8_v5重构与验证清单.md'):
        text=text.replace('| 短回调、最近记录、时间含义、有限队列；定义融合与多模态 | 使用SDK回调，不要求自行创建线程；不宣称实现融合定位 | 同一观察时刻的三路数值、时间核实和队列比较 |','| 接待问题分解、能力选择、初步方案；读取/订阅与多路取数验证 | 先选择再决定调用，时序/队列深化选做，不要求线程或实现融合定位 | 选择依据、方案及实验后修订、取数对照 |')
        note=f'> **L1主线接续（2026-10-30）**：{SUMMARY}[依据]({REPORT})。现U7四课66格/26代码、八课109格/39代码，下文旧目标和统计按历史范围阅读。'
    return prepend(text,note)


shared=json.loads((T/'共享文档清单.json').read_text(encoding='utf-8'))
updates=[]
for rel in shared:
    current=(ROOT/rel).read_bytes()
    updates.append((rel,current,transform(rel,current.decode('utf-8'))))
    if '--apply' in sys.argv:
        head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT).decode('utf-8')
        dest=T/'head-increment'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(transform(rel,head),encoding='utf-8')
    print(rel,'仅补本轮说明及L1相关字段')
if '--apply' not in sys.argv:
    print('只读预检，未改共享文档。')
else:
    for rel,current,result in updates:
        assert (ROOT/rel).read_bytes()==current,'出现新编辑，停止：'+rel
    for rel,current,result in updates:
        assert (ROOT/rel).read_bytes()==current,'写入前出现新编辑，停止：'+rel
        (ROOT/rel).write_text(result,encoding='utf-8')
    print('已在当前工作区上同步10份入口，保留其他编辑，确认状态未变。')
