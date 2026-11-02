from pathlib import Path
import json, hashlib, re

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
BASE = '05-internal-materials/vocational-planning/03_X课程项目/'
REPORT = BASE + 'PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md'
SUMMARY = '用户明确确认U4-L2、L3、L4的P2、P3通过，三课③④登记；L2此前第16、19格待办按本次P2确认收口，不编造测试输出。三份P4逐页大纲已完成，28/27/29页，共84页，待确认⑤；覆盖90格、30代码格、9项目标、12项检查点、12道思考和9道评价。Notebook及生成器未改，P5未启动。当前24课教学设计、24课PPT内容大纲、21课PPTX。'


def notice(target):
    if target.startswith(BASE):
        link = 'PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md'
    elif target == '05-internal-materials/vocational-planning/README.md':
        link = '03_X课程项目/PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md'
    elif '/02_共创规则与上下文/' in target:
        link = '../03_X课程项目/PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md'
    else:
        link = REPORT
    return f'> **U4后三课P4（2026-11-02）**：{SUMMARY}[逐页大纲与覆盖检查]({link})。下方旧待补验、待④及产物数量保留原日期含义，以本条与当前逐课表为准。\n\n'


def insert_top(s, block):
    if s.startswith('---\n'):
        return s[:4] + '\n' + block + s[4:].lstrip('\n')
    first, rest = s.split('\n', 1)
    return first + '\n\n' + block + rest.lstrip('\n')


def replace_row(s, predicate, replacement):
    lines = s.splitlines()
    ids = [i for i, line in enumerate(lines) if predicate(line)]
    assert len(ids) == 1, (ids, replacement)
    lines[ids[0]] = replacement
    return '\n'.join(lines) + '\n'


def transform(rel, s):
    s = s.replace('\r\n', '\n')
    if rel == 'CHANGELOG.md':
        block = f'## 2026-11-02｜U4后三课P2、P3确认与P4逐页大纲\n\n{SUMMARY}\n\n三课③④依据为用户本次明确确认。L2两格不再作为阶段阻碍；不回填真机执行记录、不修改运动参数和控制程序。三份已确认教学设计只更新状态，P5-B仍在课件成品后回填实际投影定位。\n\n[覆盖与审阅入口]({REPORT})。本轮仅本地提交，推送由用户手动进行。\n\n'
        return insert_top(s, block)
    if rel in ['AGENTS.md', 'INDEX.md', 'README.md', '05-internal-materials/vocational-planning/README.md'] or rel.endswith('notebook开发规则.md') or rel in [BASE+'X课程开发计划-v4.md', BASE+'X课程当前进度.md']:
        s = insert_top(s, notice(rel))
    if rel.endswith('notebook开发规则.md'):
        for code, name, cells, count, pages in [('U4-L2','走近来宾',37,10,28),('U4-L3','跟住来宾',23,8,27),('U4-L4','接待来宾',30,12,29)]:
            s=replace_row(s, lambda line,c=code: line.startswith('| `03_X课程项目/notebooks/'+c+'_'), f'| `03_X课程项目/notebooks/{code}_{name}.ipynb` | U4·L{code[-1]} | 🟢 **P2、P3经用户确认通过，③④登记；P4完成待⑤（2026-11-02）** | {cells}格/{count}代码；{pages}页大纲及全格、目标、评价映射完成。Notebook和生成器未改；P5未启动。 |')
    elif rel == BASE + 'X课程当前进度.md':
        s=s.replace('| P4完成、尚未进入P5 | 0 | U5-L4与U6四课已按用户授权推进P5 |', '| P4完成、待确认⑤ | 3 | U4-L2、L3、L4；28/27/29页大纲，③④已通过 |')
        s=s.replace('| P3教师稿已编，P2待定向补验 | 1 | U4-L2；第16、19格补验后再登记③，④未通过 |\n', '')
        s=s.replace('| P3教师稿已完成，待④ | 2 | U4-L3、L4；评价专项补审完成 |\n', '')
        for code,name,pages in [('U4-L2','走近来宾',28),('U4-L3','跟住来宾',27),('U4-L4','接待来宾',29)]:
            detail = 'L2此前两格待办按用户P2确认收口；未补造输出' if code=='U4-L2' else '原代码及执行信息保留；真实课件素材按需补入'
            row=f'| [{code} {name}](notebooks/{code}_{name}.ipynb) | P4逐页大纲{pages}页完成，待⑤ | P2、P3经用户明确确认通过，③④登记（2026-11-02） | 审阅[P4内容大纲](PPT内容设计/{code}_{name}_PPT内容大纲.md)，确认⑤后进入P5 | {detail}；P5未启动 |'
            s=replace_row(s,lambda line,c=code:line.startswith('| ['+c+' '),row)
        s=replace_row(s, lambda line:line.startswith('| 教学设计 |'), '| 教学设计 | 24 | U1～U6各四课；U4后三课③④本次通过；总草案和副本不重复计课 |')
        s=replace_row(s, lambda line:line.startswith('| PPT内容大纲 |'), '| PPT内容大纲 | 24 | 新增U4-L2、L3、L4共84页，待⑤；覆盖检查文档不计为课程大纲 |')
        s=replace_row(s, lambda line:line.startswith('| 正式版目录 |'), '| 正式版目录 | 4 | 实际已有U1-L1～L4的_教学课件；文件存在与独立⑥确认分开 |')
    elif rel == BASE + 'X课程开发计划-v4.md':
        s=replace_row(s,lambda line:line.startswith('| **U4** | **视觉引导'), '| **U4** | **视觉引导自主接近（综合实训）** | **4** | 4 notebook（四课P2通过；后三课本次用户明确确认） | 4（四课④通过） | 4（L1既有大纲；L2/L3/L4为28/27/29页，待⑤） | 1（L1为28页审查版，⑥待审；后三课未启动） |')
        for code,name,cells,count,pages in [('U4-L2','走近来宾',37,10,28),('U4-L3','跟住来宾',23,8,27),('U4-L4','接待来宾',30,12,29)]:
            s=replace_row(s, lambda line,c=code:line.startswith('| **U4** | **L'+c[-1]+'**'), f'| **U4** | **L{code[-1]}** | **{name}（'+{'U4-L2':'距离估计与核对','U4-L3':'闭环与视觉伺服','U4-L4':'视觉跟随与流程联调'}[code]+f'）** | {cells}格/{count}代码；用户确认P2、P3通过，③④登记；P4大纲{pages}页完成待⑤ | `{code}_{name}` |')
        s=s.replace('## 十三、下一步（2026-10-28更新）', '## 十三、下一步（2026-11-02更新）')
        s=s.replace('五课教学设计确认④已通过，P4逐页大纲已产出，待确认⑤后进入P5。以下其他课程安排沿用已有范围。', 'U4-L2、L3、L4的P2、P3已由用户确认通过，P4逐页大纲28/27/29页完成，待确认⑤。U5-L4与U6四课已进入P5审查稿阶段，待⑥；旧五课P4待⑤说法不再作为当前进度。')
        s=s.replace('3. U4-L1确认④通过；用户明确授权启动P5。27页审查版、成品检查和P5-B回填已完成，确认⑥待审；现场图像及运行记录待补。纵向自主编程课内交思路、课后由教师安排验证；其余三课仍待真机确认②。', '3. U4-L1现为28页P5审查版，确认⑥待审；现场图像及运行记录按原清单补充。U4-L2、L3、L4已确认③④，P4共84页待⑤；Notebook和生成器不变，不新增运动验证。三课确认⑤后才制作P5，并在P5-B回填实际投影页码。')
    elif '/教学设计/U4-L' in rel:
        s=re.sub(r'(?m)^> 2026-10-30：[^\n]+$', '> 2026-11-02：用户明确确认P2、P3通过，③④登记；P4大纲已完成，待确认⑤，尚未进入P5。', s, count=1)
        if 'U4-L2_' in rel:
            s=s.replace('第16、19格新增停止路径仍待用户定向真机补验；补验完成前，本教师稿不作为这两格已通过P2的证明。', '第16、19格停止路径随本次用户明确确认登记P2通过；保留现有程序和原执行记录，不另补写测试输出。')
            s=s.replace('保留参数、程序版本、退出原因和待补验清单。', '保留参数、程序版本、退出原因和个人尚未完成的实操清单。')
    elif rel.endswith('U4-L2-L3-L4_P2复核与定稿记录.md'):
        s=insert_top(s, '> **当前状态（2026-11-02）**：用户明确确认三课P2、P3通过，③④登记，L2第16、19格旧待办按本次P2确认收口。三课P4大纲已完成待⑤，详见[覆盖检查](../PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md)。以下为2026-10-30审定过程，保留历史依据；未补造真机测试过程或输出。\n\n')
    elif rel.endswith('全课学习评价补齐与U4后三课P3覆盖记录.md'):
        s=insert_top(s, '> **阶段更新（2026-11-02）**：用户已确认U4-L2、L3、L4的P2、P3通过，③④登记。L2不再停留在P2待补验；三课P4共84页完成、待⑤，详见[逐页覆盖](../PPT内容设计/U4-L2-L3-L4_P4覆盖检查记录.md)。下文待补验、待④说法是2026-10-30状态。\n\n')
    return s


def main():
    baseline=json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
    changed=[]
    for rel, meta in baseline.items():
        if rel.endswith('.ipynb') or re.search(r'/_gen_L\d+\.py$',rel):
            continue
        f=ROOT/rel
        assert hashlib.sha256(f.read_bytes()).hexdigest()==meta['sha256'], '基线后出现其他改动，先核对：'+rel
        before=f.read_text(encoding='utf-8')
        after=transform(rel,before)
        assert after!=before, rel
        f.write_text(after,encoding='utf-8')
        # 共享文档以HEAD叠加本轮变换，提交不夹带原有改动。
        original=TASK/'head'/rel
        if original.exists():
            inc=TASK/'head-increment'/rel;inc.parent.mkdir(parents=True,exist_ok=True)
            inc.write_text(transform(rel,original.read_text(encoding='utf-8')),encoding='utf-8')
        changed.append(rel)
    (TASK/'本轮修改清单.json').write_text(json.dumps({'modified':changed},ensure_ascii=False,indent=2),encoding='utf-8')
    print('阶段与导航同步：',len(changed),'份；6份Notebook/生成器保留。')


if __name__=='__main__':main()
