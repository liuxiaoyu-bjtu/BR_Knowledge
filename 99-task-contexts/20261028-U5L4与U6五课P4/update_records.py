from pathlib import Path
import difflib,json,re
ROOT=Path(__file__).resolve().parents[2]
TASK=Path(__file__).resolve().parent
BASE='05-internal-materials/vocational-planning/'
CP=BASE+'03_X课程项目/'
LINK=CP+'PPT内容设计/U5-L4_U6_P4覆盖检查记录.md'
NEWS='用户已确认U5-L4及U6四课确认④通过；五份P4逐页内容大纲完成，页数依次28/28/25/27/26，共134页，待确认⑤。保留U6-L4经实测确认的等待后取消流程，取消终态与现场动作效果分别判断。'
KEYS=['U5-L4','U6-L1','U6-L2','U6-L3','U6-L4']
SHARED=json.loads((TASK/'输入指纹.json').read_text(encoding='utf-8'))

def update(rel,text):
    if rel=='AGENTS.md':
        text=re.sub(r'> \*\*五课P3（2026-10-28）\*\*：[^\n]*\n> 入口：[^\n]*',f'> **五课P4（2026-10-28）**：{NEWS}\n> 入口：`{LINK}`。',text,count=1)
        text=text.replace('U5-L4与U6四课P3待确认④','U5-L4与U6四课P4大纲完成待确认⑤')
        text=text.replace('四份P3教学设计已产出，待确认④。','四份教学设计确认④通过，P4大纲完成、待确认⑤。')
        text=text.replace('登记③并按授权完成P3教学设计，待确认④','登记③并完成P3教学设计；用户现已通过④，P4大纲完成待⑤')
        text=text.replace('Notebook原字节保留，生成器反向同步。入口：`实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md`','Notebook原字节保留，生成器反向同步。P4入口：`PPT内容设计/U5-L4_U6_P4覆盖检查记录.md`')
    elif rel=='INDEX.md':
        text=text.replace('last_updated: "2026-10-26"','last_updated: "2026-10-28"',1)
        text=text.replace('四课P2通过，P3待④','四课P2及④通过，P4大纲完成待⑤')
        entry=f'> U5-L4与U6五课P4 / 逐页大纲 / 全格与评价覆盖：[P4审阅入口]({LINK})（④已通过；28/28/25/27/26页，待⑤；含全部96格、20代码格及逐题映射）。\n\n'
        text=text.replace('# 全局关键词索引\n\n','# 全局关键词索引\n\n'+entry,1)
    elif rel=='CHANGELOG.md':
        note='''## 2026-10-28 · U5-L4与U6四课确认④及P4大纲

- 按用户确认登记五课④通过；完成28/28/25/27/26页PPT内容大纲，共134页，待确认⑤。U5-L4一页课后阅读，其余页面按五课各45分钟安排。
- 覆盖96格Notebook、20格代码、15项目标、18项检查、14道思考/解释题、16项评价；逐页落实三层标题、代码来源、图示对象关系与真实素材、记录及课内外安排，学生题目不带参考答案。
- 保留会话有限等待与终态区别、L2两版录制回放、L3训练超时使用样例与条件部署、L4等待后取消及两类实际混编；导出附件与真实素材仍列准备项。
- 五份Notebook、五个生成器及教学设计正文保留，未运行机器人或制作PPTX；大纲覆盖由16课增至21课，PPTX仍16课。同步逐课状态、计划、规则及导航，本地提交由用户推送。

'''
        text=text.replace('# 更新日志\n\n','# 更新日志\n\n'+note,1)
    elif rel==BASE+'README.md':
        text=re.sub(r'> \*\*五课P3（2026-10-28）\*\*：[^\n]*',f'> **五课P4（2026-10-28）**：{NEWS}',text,count=1)
        text=text.replace('[五份教学设计与覆盖检查](03_X课程项目/实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md)','[五份P4大纲与覆盖检查](03_X课程项目/PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)')
        text=text.replace('16课已有PPT大纲/课件产物','21课已有PPT大纲、16课已有PPTX')
    elif rel==CP+'X课程开发计划-v4.md':
        text=re.sub(r'> \*\*五课P3（2026-10-28）\*\*：[^\n]*',f'> **五课P4（2026-10-28）**：{NEWS}',text,count=1)
        text=text.replace('[教师稿与覆盖检查](实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md)。本轮五课教学设计完成，等待确认④；未生成P4内容大纲。','[五份逐页大纲及覆盖检查](PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)。五课P4完成待⑤，P5尚未启动。')
        text=text.replace('5课P3待④','5课P4待⑤')
        text=text.replace('五课P3教学设计已产出，先由用户确认④；通过后再按授权进入P4。','五课教学设计确认④已通过，P4逐页大纲已产出，待确认⑤后进入P5。')
        text=text.replace('P3教学设计待④','P3确认④通过；P4大纲完成待⑤')
    elif rel==BASE+'02_共创规则与上下文/notebook开发规则.md':
        text=re.sub(r'> \*\*五课阶段更新（2026-10-28）\*\*：[^\n]*',f'> **五课阶段更新（2026-10-28）**：{NEWS}',text,count=1)
        # 顶部入口改为当前阶段；历史变更记录保留。
        lines=text.splitlines(keepends=True)
        for i,line in enumerate(lines):
            if i<15 and 'U5-L4_U6_P3教学设计覆盖检查记录' in line:
                lines[i]=line.replace('实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md','PPT内容设计/U5-L4_U6_P4覆盖检查记录.md').replace('教师稿与覆盖检查','P4大纲与覆盖检查').replace('P3教师稿、全部格映射及确认④检查项','P4大纲、全部格映射及确认⑤审阅入口')
            if line.startswith('| `03_X课程项目/notebooks/') and any('/notebooks/'+k+'_' in line for k in KEYS):
                parts=line.split(' | ',3);assert len(parts)==4
                parts[2]='🟢 **确认④通过；P4大纲完成，待确认⑤（2026-10-28）**'
                parts[3]=parts[3].replace('P3教师稿待④','P3教师稿④已通过').replace('45分钟教师稿待④','45分钟教师稿④已通过')
                lines[i]=' | '.join(parts)
        text=''.join(lines)
        note='- 2026-10-28 **五课④通过与P4交付**：用户通过U5-L4和U6四课确认④，五份P4大纲完成，28/28/25/27/26页；96格/20代码格、15目标、18检查、14思考/解释和16评价逐项定位。原Notebook、生成器与教学设计正文不改，待⑤后P5，实际投影页码留P5-B。详见[覆盖检查](../03_X课程项目/PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)。\n\n'
        text=text.replace('## 7. 变更记录\n','## 7. 变更记录\n\n'+note,1)
        text=text.replace('（确认①通过；P2复核中，整课②依据待齐）','（P2及确认④通过；P4大纲完成待⑤）')
        text=text.replace('当前稿①通过，整课真机依据待齐','当前稿P2及④通过，P4大纲待⑤')
    elif rel==CP+'X课程当前进度.md':
        text=text.replace('P2通过，P3教师稿完成、待确认④','P2及确认④通过，P4逐页大纲完成、待确认⑤')
        text=text.replace('P3教学设计已产出，确认④待审','P4内容大纲已产出，确认⑤待审')
        text=text.replace('用户已确认P2通过 |','用户已确认P2和④通过 |')
        lines=text.splitlines(keepends=True)
        for i,line in enumerate(lines):
            if line.startswith('| [') and any('[%s '%k in line for k in KEYS):
                parts=line.split(' | ');assert len(parts)==5
                key=next(k for k in KEYS if '['+k+' ' in line)
                parts[1]='P4逐页内容大纲已完成，待确认⑤'
                parts[2]=parts[2]+'；用户已确认④通过'
                title={'U5-L4':'语音会话管理','U6-L1':'动作的来源','U6-L2':'动作录制与回放','U6-L3':'视频动作训练','U6-L4':'动作编排'}[key]
                parts[3]=f'审阅[P4大纲](PPT内容设计/{key}_{title}_PPT内容大纲.md)并确认⑤'
                lines[i]=' | '.join(parts)
        text=''.join(lines)
        text=text.replace('本轮五课待④','本轮五课④通过')
        text=text.replace('| PPT内容大纲 | 16 | 同上；覆盖检查文档不计为课程大纲 |','| PPT内容大纲 | 21 | 原16课加U5-L4、U6四课；覆盖检查文档不计为课程大纲 |')
        text=text.replace('| PPT文件 | 16 | 同上；','| PPT文件 | 16 | 本轮五课未制作PPTX；')
        text=text.replace('五课教师稿已完成、待④','五课教师稿已通过④，P4大纲完成待⑤')
        text=text.replace('审阅U5-L4与U6四课P3教学设计，确认④后再进入P4','审阅U5-L4与U6四课P4大纲，确认⑤后进入P5')
        text=text.replace('## 8. 五课P3最新依据（2026-10-28）','## 8. 五课P4最新依据（2026-10-28）')
        text=text.replace('2026-10-28：用户确认U5-L4 P2复核通过，U6四课P1/P2评审及确认①②通过；五课P3教学设计已产出，待用户确认④。U6-L4按用户真机结论保留等待后取消，以现场动作表现和取消终态共同判断；不把CANCELLED解释为动作完整完成。',NEWS)
        text=text.replace('详见[五课覆盖检查](实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md)及五份教师稿。P3尚待确认④，未登记P4/P5完成。','详见[五课P4覆盖检查](PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)及其中五份大纲。已登记④通过、P4产出，⑤待审；未开始P5。')
    elif rel==CP+'实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md':
        text=text.replace('日期：2026-10-28。',f'> **当前状态**：用户已确认五课④通过；[五课P4大纲及覆盖检查](../PPT内容设计/U5-L4_U6_P4覆盖检查记录.md)已完成，待确认⑤。以下保留P3设计依据与实施准备事项。\n\n日期：2026-10-28。',1)
        text=text.replace('**待用户确认④，未进入P4**','**确认④已由用户通过，P4大纲已完成、待确认⑤**')
        text=text.replace('## 五、确认④重点与实施准备','## 五、确认④审阅记录与后续实施准备')
        text=text.replace('以上为本轮教学设计审阅项目，不重开用户已通过的①②或P2，不登记④已通过。','以上为P3送审时的核对与准备项目。用户现已通过④，P4已完成；附件、样例、资源接入及实际投影定位仍按后续实施条件准备，不登记其已完成。')
    return text

patch=[];changed=[]
for rel in SHARED:
    if '/notebooks/' in rel or '/教学设计/' in rel or '/_gen_' in rel:continue
    original=(TASK/'before'/rel).read_bytes();current=(ROOT/rel).read_bytes()
    assert original==current,'基线后发生外部修改，暂停：'+rel
    old=original.decode('utf-8');new=update(rel,old.replace('\r\n','\n'))
    assert new!=old.replace('\r\n','\n'),rel
    if b'\r\n' in original:new=new.replace('\n','\r\n')
    (ROOT/rel).write_bytes(new.encode('utf-8'));changed.append(rel)
    head=TASK/'head'/rel
    if head.exists():
        before=head.read_text(encoding='utf-8');after=update(rel,before)
        patch+=difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel)
(TASK/'提交状态增量.patch').write_bytes(''.join(patch).encode('utf-8'))
(TASK/'状态更新范围.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),encoding='utf-8')
print('更新',len(changed),'份状态与导航；独立暂存增量已生成，未混入工作区既有差异')
