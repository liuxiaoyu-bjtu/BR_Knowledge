from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
T = Path(__file__).resolve().parent
P = Path('05-internal-materials/vocational-planning/03_X课程项目')
report = 'U7_U8_学材补全与附件说明.md'
u8guide = 'U8_逐课实施与真机测试指导.md'
shared = json.loads((T/'共享文档清单.json').read_text(encoding='utf-8'))
extra = (P/'实验验证/U7_U8_v5重构与验证清单.md').as_posix()
if extra not in shared:
    shared.append(extra)
    dest=T/'before'/extra
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/extra,dest)
    base=json.loads((T/'基线.json').read_text(encoding='utf-8'))
    base['files'][extra]=hashlib.sha256((ROOT/extra).read_bytes()).hexdigest()
    (T/'基线.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
    (T/'共享文档清单.json').write_text(json.dumps(shared,ensure_ascii=False,indent=2),encoding='utf-8')


def insert(text, note):
    first, rest = text.split('\n',1)
    return first+'\n\n'+note+'\n'+rest


def change(rel,text):
    text=text.replace('\r\n','\n')
    course=(rel.startswith(P.as_posix()))
    common='U7-L1/L2九处[sss]反馈已落实，L3/L4及U8四课补足概念、过渡、操作与输出解释。八课103格/37代码；本组模板展开观察、介绍、再观察、行为调用，新增行为独立测试，补齐文件保存加载、基线与复测。八份生成器同步，离线检查通过；仍为P1修订稿，①②待完成，未运行机器人。'
    if rel=='AGENTS.md':
        note=f'> **U7/U8学材补全（2026-10-29）**：{common}入口：`{P.as_posix()}/实验验证/{report}`。U7/U8附件均为课程代码，非SDK新增包；后续审阅按本版与新U8测试指导。'
    elif rel=='CHANGELOG.md':
        note=f'## 2026-10-29 — U7/U8学材补全\n\n{common}\n\n[修订依据与附件职责]({P.as_posix()}/实验验证/{report})、[U8逐课实施与真机测试]({P.as_posix()}/实验验证/{u8guide})。本轮未改U1～U6主Notebook，未新增阶段确认；Git仅本地提交，推送由用户操作。\n'
    elif rel=='INDEX.md':
        note=f'> U7九处sss反馈 / U8项目逻辑 / u8_team_template / x_lab / 文件重载与逐模块测试：[学材补全与附件说明]({P.as_posix()}/实验验证/{report})、[U8实施与真机测试]({P.as_posix()}/实验验证/{u8guide})（2026-10-29，八课103格/37代码，P1待①②）。下方101格/36代码为此前版本统计。'
    elif rel=='05-internal-materials/vocational-planning/README.md':
        note=f'> **U7/U8学材补全（2026-10-29）**：{common}[修订与附件说明](03_X课程项目/实验验证/{report})、[U8逐课实施与真机测试](03_X课程项目/实验验证/{u8guide})。'
    elif rel.endswith('notebook开发规则.md'):
        text=text.replace('| U8-L2 | 核心模块开发 | 17格/7代码格 |','| U8-L2 | 核心模块开发 | 19格/8代码格 |')
        return text.rstrip()+f'''\n\n## U7/U8学材可操作性补充（2026-10-29）

- 首次使用回调、队列、锁、停止标志、任务记录等概念时，先说明具体需求、所指对象与操作，再给代码。代词指向明确，相邻句子需交代因果或承接。
- 课程附件与SDK分开说明来源、输入输出和适用条件。封装重复计算和调用时，保留可读源文件、关键调用路径和本组修改位置，避免学生仅填参数却不知发生什么。
- 跨文件操作写清目录、打开哪个文件、修改保存、加载/重载、检查输出和重复运行条件；活动资源未退出时保留原对象。纸面活动也需示例、操作、记录与核查。
- 每项时间值写明从哪个事件计到哪个事件，单位和计时基准未证实时不跨源换算；未满足扩展比较条件时仍应有可完成的基础观察。
- 标题层级应服务实际内容，避免只有一个编号子节；收尾操作附在相应步骤，不以模式切换独占一节。

本次八课103格/37代码，U8-L2新增本组行为独立测试，其他课格数不变。{common}[依据与逐课修订](../03_X课程项目/实验验证/{report})。\n'''
    elif rel.endswith('U7_逐课真机测试指导.md'):
        text=text.replace('本指导对应本轮补齐情境后的四份 v5 Notebook', '本指导对应2026-10-29学材补全后的四份 v5 Notebook')
        text=text.replace('接收后时长','回调记录后时长').replace('接收时间仍应更新','回调记录时刻仍应更新')
        text=text.replace('只说明待核；不会计算跨路差值','先打印三路源时间戳原值，再说明跨路比较待核；不计算跨路差值')
        text=text.replace('至少保留一组完整快照','至少保留两轮完整快照')
        note=f'> **本轮说明（2026-10-29）**：九处标签已落实；源时间戳基础观察不依赖跨路换算，纸张仅用于STEP 02中心像素观察，队列实验只比较时间记录。L3/L4已补概念、交接和重试说明，四课仍60格/24代码，原STEP与代码格号不变。[改动依据]({report})。'
    elif rel.endswith('U7_U8_v5重构与验证清单.md'):
        note=f'> **学材接续（2026-10-29）**：当前八课103格/37代码，U8-L2为19格/8代码。九处反馈、L3/L4阅读问题及U8文件/模块操作已直接修订；模板新增本组介绍和行为函数，主流程明确展开，生成器同步。原文101格/36代码和旧模板离线结论保留历史含义，当前依据见[修订记录]({report})、[U8测试指导]({u8guide})；①②仍待完成。'
    else:
        note=f'> **U7/U8学材补全（2026-10-29）**：{common}[修订与附件说明](实验验证/{report})、[U8测试指导](实验验证/{u8guide})。以下101格/36代码为此前版本统计。'
        if rel.endswith('X课程当前进度.md'):
            lines=[]
            for line in text.splitlines(keepends=True):
                if line.startswith('| [U8-L2 '):
                    line=line.replace('17格/7代码格','19格/8代码格')
                if line.startswith('| [U8-L'):
                    line=line.replace('[验证清单](实验验证/U7_U8_v5重构与验证清单.md)','[实施与真机指导](实验验证/'+u8guide+')')
                lines.append(line)
            text=''.join(lines)
        elif rel.endswith('X课程大纲-v5.md'):
            text=text.replace('定时打印数值、源时间戳、接收后经过时长','定时打印数值、源时间戳、回调记录后经过时长')
            text=text.replace('比较播报前后检测记录、接收后年龄与停止','比较播报前后检测记录、取图处理耗时及处理后存放时长与停止')
            text=text.replace('阅读功能片段，按本组约定修改模块；分别测试，再接为最小可运行流程；明确跨课文件与版本','阅读并修改本组observe/introduce/act函数；先观察、介绍、行为独立测试，再整体运行；明确文件保存/加载、版本和证据')
        elif rel.endswith('X课程开发计划-v4.md'):
            text=text.replace('本组Python模板、模块测试与整合、版本与跨课文件（v5 P1完成，待①②）','本组Python文件与observe/introduce/act函数、独立测试和整合、保存重载与跨课版本（v5 P1修订，待①②）')
    return insert(text,note)


updates=[]
for rel in shared:
    current_bytes=(ROOT/rel).read_bytes()
    current=current_bytes.decode('utf-8')
    # 在当前工作区上只增补本轮段落和指定字段，保留其他任务的修改。
    # 所有文件先准备，应用前整体比对字节；若期间有新编辑则终止，不写回旧快照。
    updated=change(rel,current)
    updates.append((rel,current_bytes,updated))
    head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT).decode('utf-8')
    dest=T/'head-increment'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    if '--apply' in sys.argv:
        dest.write_text(change(rel,head),encoding='utf-8')
    before=(T/'before'/rel).read_bytes()
    print(rel, '当前字节与本轮基线一致=',current_bytes==before,
          '改动类型=新增本轮说明和受影响课程字段')

if '--apply' not in sys.argv:
    print('只读预检；未修改共享文档。')
else:
    for rel,current_bytes,updated in updates:
        assert (ROOT/rel).read_bytes()==current_bytes, '预备后发生新编辑，终止：'+rel
    for rel,current_bytes,updated in updates:
        assert (ROOT/rel).read_bytes()==current_bytes, '写入前发生新编辑，终止：'+rel
        (ROOT/rel).write_text(updated,encoding='utf-8')
    print('已在当前工作区内容上同步',len(shared),'份共享入口，保留既有其他改动。')
