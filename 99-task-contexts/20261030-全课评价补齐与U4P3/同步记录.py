from pathlib import Path
import json,re,subprocess
R=Path(__file__).resolve().parents[2];P=R/'05-internal-materials/vocational-planning/03_X课程项目';T=Path(__file__).resolve().parent
REL='05-internal-materials/vocational-planning/03_X课程项目/实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md'
TITLE='全课评价补齐与U4后三课P3（2026-10-30）'
SUMMARY='32课已核对，补齐15课独立学习评价，统一19课检查点并分开思考题；U4-L1、U5-L1～L3的教学设计、大纲和PPTX已联动，新增评价页后为28/28/29/29页。U4-L2～L4三份45分钟P3教师稿已完成，L3/L4待④；L2第16、19格仍待定向真机补验，③未登记，本稿先供审阅。原代码与执行信息保留，未运行机器人，P6仍待全课程结束统一导出。'

audit=json.loads((T/'离线核查结果.json').read_text(encoding='utf-8'))
report='''# 全课学习评价补齐与U4后三课P3覆盖记录

> 2026-10-30。依据用户本轮授权直接修订；真机确认、材料编写和用户确认分别登记。

本轮核对32份主Notebook，15课缺独立学习评价：U4四课、U5前三课、U7/U8八课。已各补3题判断、填空、选择，共45题，保留作答空位与教师答案引用块。U7/U8原有项目评分、成果核对和开放问题保留，个人测验补充检查概念及工程判断。

19课统一为`- [__]`检查点，U4-L3/L4拆开检查点与思考题，U7/U8补独立可勾选检查点并明确原开放问题的用途。U5-L4现有评价另补教师参考答案。其余17课原有题目未重写；部分既有课程采用作品或解释题，保留与本课目标对应的有效评价，不为统一题型删去实践评价。

## 1. 逐课核对

| 课程 | 原评价情况 | 本轮处理 | 当前格数/代码格 |
| --- | --- | --- | --- |
'''
for row in audit['audit']:
 action='新增三题；检查点格式统一' if row['new_evaluation'] else '已有评价；统一检查点，保留原题' if row['changed'] else '已有评价和可勾选检查点，保留'
 if row['lesson']=='U5-L4':action='已有评价；补教师答案并统一检查点、思考题标示'
 report+=f"| {row['lesson']} | {'缺独立学习评价' if row['new_evaluation'] else '已有'} | {action} | {row['cells_after']}/{row['code_cells']} |\n"
report+='''
## 2. 评价与目标的关系

| 新增评价的课程 | 题目检查的内容 | 操作能力另看什么 |
| --- | --- | --- |
| U4-L1 | 头与身体朝向、带符号偏差与单位、比例系数调整 | 对准记录、比例对照和结束原因 |
| U4-L2 | 里程计与间距、计划行进量及误差、阈值停止 | 行走/速度表、独立标定核对、学生阈值程序与最终卷尺间距 |
| U4-L3 | 近时暂停仍观察、两图像量分工、直线位移 | 跟进/暂停/再跟进记录、停稳位置和IMU记录 |
| U4-L4 | 新观测、连续计数、状态与现场分别记录 | 正常接待、未满足时阻断、旧任务退出与位移说明 |
| U5-L1 | ASR与理解、三声道数据量、播放队列和收尾 | 录音字段、4/64队列比较、文字回调与终态 |
| U5-L2 | 异步接口、TTS输入输出及句柄、自制音频共性 | 波形/音频、音色记录及先问后听 |
| U5-L3 | 提示词与工具、四部分设定和同题条件、会话切换 | 提示词、实际回答对照、取消及终态记录 |
| U7-L1 | 需求选择能力、位置记录来源、一次读取与多路最近值 | 能力选择表、初步方案与取数实验修改依据 |
| U7-L2 | 坐标方向/单位、静态与运动定位验证的区别 | 标定与独立测点、受控试踢、管理器退出和实际球路 |
| U7-L3 | 播放与工作线程、锁、线程与任务退出 | 播放前后编号、旧记录复查、两类资源退出 |
| U7-L4 | 播报后再观察、交接条件、session检查范围 | 可用片段的交接表与状态/现场效果 |
| U8-L1 | 可验收需求、接口和退出责任、能力取舍 | 主题需求、接口分工与正常/未完成用例 |
| U8-L2 | 配置检查范围、本组文件、模块到整合 | 模块测试、程序版本、整体日志及现场记录 |
| U8-L3 | 基线、复测条件及归因、交付说明 | 原始与修改版本、对照记录、未解决项 |
| U8-L4 | 评分依据、需求与证据、如实交付 | 实际展演、个人答辩、完整交付目录 |

三题测验补充概念检查，不能替代实际操作和作品评价。课堂未亲自运行的条目标注代表观察或待补做。

## 3. 已完成产物是否要补

U4-L1及U5-L1～L3已有P3教案及P5课件，但教案评价主要取自检查点与思考题，课件只有过程检查/讨论页。独立测验补入Notebook后，三份材料需要同步，已完成以下调整：

| 课程 | 新评价在Notebook | 新评价在PPT | 现有课件页数 | 联动情况 |
| --- | --- | --- | --- | --- |
| U4-L1 | 第45格、§六 | 第26页 | 28 | 教案、大纲、生成源、成品和页码映射同步 |
| U5-L1 | 第35格、§七 | 第27页 | 28 | 同上 |
| U5-L2 | 第34格、§六；阅读第35格、§七 | 第27页 | 29 | 同上；阅读页顺延第29页 |
| U5-L3 | 第32格、§六；阅读第33格、§七 | 第27页 | 29 | 同上；阅读页顺延第29页 |

保留原过程评价与思考参考，在末环节安排约2分钟个人测验，思考题选一问课堂交流，其余课后随记录补答。安全收尾及个人补做保留。学生页无答案，讲者备注保留教师参考；原后续投影页码已回填。

U1四课已有学习评价，包括用户手改正式课件的U1-L1，不属于缺项范围，本轮未覆盖正式版。现行P6是32课结束后的统一学生PDF导出，尚未执行；历史“P6课件”属于旧编号，本轮按实际已有P3/P5文件补齐。未来导出从现Notebook取题，移除教师答案，不需要提前重出全课PDF。

## 4. U4后三课P3全格覆盖

三份教案均有六个基本部分、目标下教学提示、45分钟连续时间轴、逐环节活动、板书及逐题评价答案。没有单列鸡肋附件章节；所需参数与前课记录就地引用。P3的投影描述写内容及Notebook依据，P5-B再回填实际页码。

| 课程/Notebook范围 | P3对应环节 | 课堂与后续安排 |
| --- | --- | --- |
| L2第1～12格，目标、问题、里程计及STEP 01～03 | 环节1 | 区分位置、行进量、间距，只算不动 |
| L2第13～19格，STEP 04～05 | 环节2 | 实际行进与卷尺核对；速度分组比较，重复不足另排实操 |
| L2第20～32格，STEP 06～07 | 环节3 | 完整可见条件、标定与独立核对；历史0.853不当本组阈值 |
| L2第33～35格，STEP 08 | 环节4 | 学生自主编程、静态分支、代表行走；个体未测另补 |
| L2第36～37格 | 环节5、§六 | 三表、五检查点、四思考及三题评价；安全收尾 |
| L3第1～3格，情境与知识 | 环节1 | 持续闭环与视觉伺服，对比L2单次走近 |
| L3第4～11格，STEP 01～04 | 环节2 | 复用标定、静态检查两图像量和无目标分支 |
| L3第12～13格，STEP 05 | 环节3 | IMU/里程计读数和单位，明确仅作记录 |
| L3第14～16格，STEP 06 | 环节4 | 有限短程跟随，暂停与再次跟进；未轮到者补做 |
| L3第17～20格，STEP 07～08 | 环节5 | 停稳终点、位移与朝向、安全收尾 |
| L3第21～23格 | 环节6、§六 | 记录、检查点、思考、三题；扩展阅读课后 |
| L4第1～3格，接待及交接 | 环节1 | 正常与未完成两条路径 |
| L4第4～13格，STEP 01～05 | 环节2 | 旧句柄、参数和动作ID、静态分支及人工模式操作 |
| L4第14～19格，STEP 06～08 | 环节3 | 有限等待、连续到位、新观测及致意检查 |
| L4第20～23格，STEP 09～10 | 环节4 | 正常接待、启动前无目标阻断、任务退出 |
| L4第24～27格，STEP 11～12 | 环节5 | 致意后终点解释、状态核查与回prepare |
| L4第28～30格 | 环节6、§六 | 接待/运动记录、前三课依据、检查/思考/测验；阅读课后 |

教师稿入口：

- [U4-L2教学设计](../教学设计/U4-L2_走近来宾_教学设计.md)
- [U4-L3教学设计](../教学设计/U4-L3_跟住来宾_教学设计.md)
- [U4-L4教学设计](../教学设计/U4-L4_接待来宾_教学设计.md)

L3/L4已补审评价专项，P3待用户确认④。L2按用户本轮指示先完成P3教师稿，但第16、19格停止路径仍待定向真机补验；用户先前要求“两格补验后再通过P2”继续生效，不登记③或④通过，不进入P4。

## 5. 核查和保留范围

本轮不执行SDK或机器人代码。32课原代码格、执行计数和输出均与本轮基线对照；新增Markdown均放在原代码之后，代码格号保留。L2第9格用户原文、第35格学生作答位置保留。19份受改Notebook的正式生成器已完整反向同步；U6-L3本轮前已有用户改动，提交时区分既有改动与本次格式增量。U6-L1在工作期间有其他任务修改，不纳入本轮提交。

离线内容、镜像、三方题目、时间轴及原课件文字保留检查426项通过；四份PPTX按原成品作基准校验全部通过，PowerPoint渲染114页，文字边界检查0项异常，逐页浏览及新增四页大图复核完成。答案在教师备注、学生页仅题干。

本轮证据：`99-task-contexts/20261030-全课评价补齐与U4P3/离线核查结果.json`、`课件结构校验.json`、`qa-render/bounds.json`及四份联系图。其他现场素材、用户确认⑥和L2定向补验继续保留待办。
'''
(R/REL).write_text(report,encoding='utf-8',newline='\n')

def add_notice(s,notice):
 lines=s.splitlines(keepends=True);lines[1:1]=['\n'+notice+'\n\n'];return ''.join(lines)

def stage_shared(rel,transform):
 f=R/rel;s=f.read_text(encoding='utf-8-sig');new=transform(s)
 assert f.read_text(encoding='utf-8-sig')==s,f
 f.write_text(new,encoding='utf-8',newline='\n')
 head=subprocess.check_output(['git','show','HEAD:'+rel]).decode('utf-8-sig');inc=transform(head)
 target=T/'head-increment'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(inc,encoding='utf-8',newline='\n')

def transform_progress(s):
 s=add_notice(s,'> **'+TITLE+'**：'+SUMMARY+' [覆盖及核查](实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md)。下方较早记录保留历史含义。')
 rows=[]
 for line in s.splitlines():
  if line.startswith('| P2审定通过，可进入P3 |'):line='| P3教师稿已完成，待④ | 2 | U4-L3、L4；评价专项补审完成 |'
  if line.startswith('| P2获批修订，待定向补验 |'):line='| P3教师稿已编，P2待定向补验 | 1 | U4-L2；第16、19格补验后再登记③，④未通过 |'
  if line.startswith('| [U4-L2 '):line='| [U4-L2 走近来宾](notebooks/U4-L2_走近来宾.ipynb) | P3教师稿已编；P2停止路径待补验 | ①及原稿②保留，③未登记，④未通过 | 补验第16、19格正常与中断停止；再审[P3教师稿](教学设计/U4-L2_走近来宾_教学设计.md) | 37格/10代码；新增评价，原参数、判断、第9格和学生作答保留 |'
  if line.startswith('| [U4-L3 '):line='| [U4-L3 跟住来宾](notebooks/U4-L3_跟住来宾.ipynb) | P3教师稿完成，待④ | ①②③保留，评价专项补审完成 | 审阅[教学设计](教学设计/U4-L3_跟住来宾_教学设计.md)，通过④后进入P4 | 23格/8代码；原代码和执行信息保留，新增评价并分开检查/思考 |'
  if line.startswith('| [U4-L4 '):line='| [U4-L4 接待来宾](notebooks/U4-L4_接待来宾.ipynb) | P3教师稿完成，待④ | ①②③保留，评价专项补审完成 | 审阅[教学设计](教学设计/U4-L4_接待来宾_教学设计.md)，通过④后进入P4 | 30格/12代码；连续到位与新观测保留，新增评价并分开检查/思考 |'
  rows.append(line)
 return '\n'.join(rows)+'\n'

def transform_plan(s):
 s=add_notice(s,'> **'+TITLE+'**：'+SUMMARY+' [具体覆盖](实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md)。')
 lines=[]
 for line in s.splitlines():
  if line.startswith('| **U4** | **L2** |'):line='| **U4** | **L2** | **走近来宾（距离估计与核对）** | 37格/10代码；独立学习评价补齐，P3教师稿已编；第16/19格停止路径待补验，③未登记，④未通过 | `U4-L2_走近来宾` |'
  if line.startswith('| **U4** | **L3** |'):line='| **U4** | **L3** | **跟住来宾（闭环与视觉伺服）** | 23格/8代码；检查/思考分开，评价专项补审；①②③保留，P3教师稿完成待④ | `U4-L3_跟住来宾` |'
  if line.startswith('| **U4** | **L4** |'):line='| **U4** | **L4** | **接待来宾（视觉跟随与流程联调）** | 30格/12代码；接待交接与运动记录保留，评价补齐；①②③保留，P3教师稿完成待④ | `U4-L4_接待来宾` |'
  lines.append(line)
 return '\n'.join(lines)+'\n'

def transform_rules(s):
 s=add_notice(s,'> **'+TITLE+'**：'+SUMMARY+' [专项覆盖](../03_X课程项目/实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md)。')
 mark='## 4. cell 结构规则'
 block='''### P2评价专项必查（2026-10-30补充）

- 每课逐项核对观察记录、可勾选检查点、思考题及独立学习评价。检查点用`- [__]`，与思考题分开；过程记录和项目评分不能替代个人概念检查。
- 学习评价题目必须能回到已讲内容与课程目标，提供作答位置和教师答案；保留有效项目评价，不强行删除实践题。新补课按§4的2～3题要求编写。
- P2报告列明评价与目标、操作证据的对应关系。已产出P3/P4/P5的课，变更评价后同步教案、逐页大纲、课件学生题干和教师备注，更新投影页码及生成器。
- P6从当前Notebook导出，移除教师参考答案，保留题目和作答位置；确认记录不因文稿补项自动升级。

'''
 assert mark in s;s=s.replace(mark,block+mark,1)
 lines=[]
 for line in s.splitlines():
  if line.startswith('| `03_X课程项目/notebooks/U4-L2_'):line='| `03_X课程项目/notebooks/U4-L2_走近来宾.ipynb` | U4·L2 | 🟡 **P3教师稿已编；P2停止路径待补验，③未登记** | 37格/10代码；新增评价、统一检查点。第16/19格补验后再通过P2；④未通过。原代码、第9格和学生作答保留。 |'
  if line.startswith('| `03_X课程项目/notebooks/U4-L3_'):line='| `03_X课程项目/notebooks/U4-L3_跟住来宾.ipynb` | U4·L3 | 🟢 **①②③保留；P3教师稿完成，待④** | 23格/8代码；检查点与思考分开、评价补齐并补审，原代码及输出保留。 |'
  if line.startswith('| `03_X课程项目/notebooks/U4-L4_'):line='| `03_X课程项目/notebooks/U4-L4_接待来宾.ipynb` | U4·L4 | 🟢 **①②③保留；P3教师稿完成，待④** | 30格/12代码；新增可勾选检查点和独立评价，原交接逻辑与执行信息保留。 |'
  lines.append(line)
 return '\n'.join(lines)+'\n'

shared=['AGENTS.md','INDEX.md','README.md','CHANGELOG.md','05-internal-materials/vocational-planning/README.md',P.relative_to(R).as_posix()+'/X课程当前进度.md',P.relative_to(R).as_posix()+'/X课程开发计划-v4.md',P.parent.relative_to(R).as_posix()+'/02_共创规则与上下文/notebook开发规则.md']
for rel in shared:
 if rel.endswith('X课程当前进度.md'):fn=transform_progress
 elif rel.endswith('X课程开发计划-v4.md'):fn=transform_plan
 elif rel.endswith('notebook开发规则.md'):fn=transform_rules
 elif rel=='CHANGELOG.md':fn=lambda s:add_notice(s,'## 2026-10-30｜全课评价补齐、既有课件联动与U4后三课P3\n\n'+SUMMARY+'\n\n详见[覆盖与核查]('+REL+')。本轮本地提交，推送由用户手动进行。')
 else:
  link=REL if '/' not in rel else '03_X课程项目/实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md'
  fn=lambda s,link=link:add_notice(s,'> **'+TITLE+'**：'+SUMMARY+' 现有24课教学设计、21课PPTX。[逐课补项及P3覆盖]('+link+')。')
 stage_shared(rel,fn)

# 专项文件本轮仅追加有日期的新依据，较早核查保留历史范围。
append_files=[P/'实验验证/U4-L2-L3-L4_P2复核与定稿记录.md',P/'PPT内容设计/U4-L1_U5-L1-L3_P4覆盖检查记录.md',P/'PPT/U4L1_U5L1-L3_Codex源文件/U4-L1_U5-L1-L3_P5交付检查记录.md',P/'PPT/U4L1_U5L1-L3_Codex源文件/README.md']
for f in append_files:
 s=f.read_text(encoding='utf-8-sig');s+='\n\n## 2026-10-30评价补齐与P3更新\n\n'+SUMMARY+'\n\n新评价页：U4-L1第26页，U5-L1/L2/L3第27页；课件为28/28/29/29页。结构校验通过，114页PowerPoint渲染及文字边界检查通过（0项）；原页面文字、代码摘录及三方题干对照通过。学习评价不替代操作记录，学生答案仅教师备注。\n\n[完整覆盖记录]('+('../../../实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md' if f.parent.name=='U4L1_U5L1-L3_Codex源文件' else '../实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md' if f.parent.name=='PPT内容设计' else '全课学习评价补齐与U4后三课P3覆盖记录.md')+')。旧记录中的格数与页数按原日期阅读。\n'
 f.write_text(s,encoding='utf-8',newline='\n')
(T/'共享文件清单.json').write_text(json.dumps(shared,ensure_ascii=False,indent=2),encoding='utf-8')
print('专项报告、进度、规则及导航已同步')
