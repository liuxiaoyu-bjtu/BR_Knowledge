"""只插入本任务入口；同一操作用于工作区和隔离提交版本。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md'
TAG = 'OS SDK足球全流程策划（2026-11-02）'


def update(name: str, text: str) -> str:
    if TAG in text:
        return text
    if name == 'AGENTS.md':
        heading = next(line for line in text.splitlines() if line.startswith('# AGENTS.md'))
        body = f'> **{TAG}**：用户认可技术方向后，已形成详细策划案、旧程序到OS SDK映射与能力标准、单文件k1_soccer.py草案、教师配置示例及4幅标准图示，32项离线检查通过。默认只观察；视觉米制球位、动态供数和完整踢出仍待真机，不延伸已有确认。正式U7由用户在“X课程→U7开发-分支”启动，现有Notebook及控制附件未改。[策划案与程序]({PLAN})。'
    elif name == 'INDEX.md':
        heading = '# 全局关键词索引'
        body = f'> **{TAG}**：能力迁移映射 / 单文件k1_soccer.py / 先转头后转身 / 标准流程图 / 球心与地面平面 / 当前身体坐标 / U7分支交接：[详细策划案]({PLAN})。附4幅图与程序草案；32项离线检查通过，未做新方案真机验证。'
    elif name == 'CHANGELOG.md':
        heading = '# 更新日志'
        body = f'## {TAG}\n\n按用户认可方向，形成[详细策划案]({PLAN})：旧程序到OS SDK映射、课程能力标准、坐标与时间约定、U7承接安排，以及主流程、球位子流程、模块框架和状态转换4幅图。配套单文件k1_soccer.py与未核实教师配置示例，32项合成数据/模拟SDK检查通过，HTML与图示已渲染检查。默认只观察；未运行机器人，未修改学生Notebook、既有控制附件或确认节点。提供用户指定U7分支的启动提示。'
    elif name == '05-internal-materials/vocational-planning/README.md':
        heading = '# vocational-planning 目录说明'
        body = '> **' + TAG + '**：[策划案、单文件程序及4幅图](03_X课程项目/实验验证/OSSDK足球全流程策划/K1足球全流程_OSSDK策划案.md)已形成，包含迁移映射、能力标准、坐标/时间约定与U7承接安排。32项离线检查通过，真机定位及完整踢出未验证。正式课程留待用户指定U7分支启动，当前Notebook未改。'
    elif name == '01-booster-kb/07-tech-platform/_index.md':
        heading = '# 技术平台'
        body = '> **' + TAG + '**：[课程策划与应用草案](../../' + PLAN + ')提供旧SDK到OS SDK映射、单文件状态机/选球/定位/退出和4幅图。属于课程应用，不计作SDK新增API；32项离线检查通过，真机视觉定位和踢出仍待核实。'
    else:
        raise ValueError(name)
    if heading not in text:
        raise ValueError(f'heading_missing:{name}')
    return text.replace(heading, heading + '\n\n' + body, 1)


if __name__ == '__main__':
    for name in ['AGENTS.md', 'INDEX.md', 'CHANGELOG.md',
                 '05-internal-materials/vocational-planning/README.md',
                 '01-booster-kb/07-tech-platform/_index.md']:
        file = ROOT / name
        text = file.read_text(encoding='utf-8-sig')
        newline = '\r\n' if b'\r\n' in file.read_bytes() else '\n'
        file.write_bytes(update(name, text).replace('\n', newline).encode('utf-8'))
        print('updated', name)
