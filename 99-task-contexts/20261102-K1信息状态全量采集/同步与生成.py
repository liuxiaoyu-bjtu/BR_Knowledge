from pathlib import Path
import hashlib
import json
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
LINK = '04-shared/sdk-tests/K1信息与状态接口_采集说明.md'
NOTE = ('新增K1信息与状态八项只读采集脚本与Jupyter入口，保存完整清单/嵌套字段、'
        '类型与repr、本机定义、异常、SDK/固件来源和逐项记录，自动打包。'
        'list_frames空结果短暂重读；已有robot可复用。当前仅离线核查，真机由用户运行并反馈；'
        '尚未生成K1实测补充或新增课程确认。')


def change(name, text):
    if name == 'AGENTS.md':
        head = '# AGENTS.md — 面向 AI Agent 的知识库使用指南 + 内容总览'
        return text.replace(head, head + f'\n\n> **K1信息状态采集（2026-11-02）**：{NOTE}[运行说明]({LINK})。', 1)
    if name == 'INDEX.md':
        head = '# 全局关键词索引'
        return text.replace(head, head + '\n\n> K1信息与状态全量采集 / robot_info / get_mode / '
            'list_gaits / get_gait / list_frames / list_joints / list_sensors / list_actions：'
            f'[运行说明]({LINK})、[脚本](04-shared/sdk-tests/probe_k1_info_state.py)'
            '（八项只读、完整字段与结果打包；真机记录待用户反馈）。', 1)
    if name == 'CHANGELOG.md':
        head = '# 更新日志'
        return text.replace(head, head + '\n\n## 2026-11-02 · K1信息与状态接口采集工具\n\n'
            + NOTE + f'[运行说明]({LINK})。本次未调用真实机器人，未将模拟测试写作真机通过。', 1)
    if name == '04-shared/sdk-tests/_README.md':
        row = '| `probe_detection_classes.py`'
        location = text.index(row)
        return text[:location] + ('| [probe_k1_info_state.py](probe_k1_info_state.py) / '
            '[Jupyter入口](K1信息与状态接口_真机采集.ipynb) | K1八项信息与状态只读采集；'
            '完整字段、版本、异常、本机定义与ZIP；[运行说明](K1信息与状态接口_采集说明.md) | '
            '`robot_info` / `get_mode` / `list_gaits` / `get_gait` / `list_frames` / '
            '`list_joints` / `list_sensors` / `list_actions` | '
            '`python3 probe_k1_info_state.py --tester xy`；真机待运行 |\n') + text[location:]
    if name == '01-booster-kb/07-tech-platform/_index.md':
        head = '## 使用指南'
        return text.replace(head, f'## K1实机信息采集\n\n[{LINK.split("/")[-1]}](../../{LINK})：'
            + NOTE + '\n\n' + head, 1)
    if name == '01-booster-kb/07-tech-platform/booster-sdk.md':
        head = '### 2.2 信息与状态获取'
        return text.replace(head, head + '\n\n> **K1实际清单采集**：'
            f'[脚本、Jupyter入口与运行说明](../../{LINK})'
            '一次保存下列八项接口的完整返回值与本机定义。实际坐标系、关节、传感器、步态与动作清单'
            '以对应机器人和SDK/固件版本的记录为准；真机结果尚待反馈，本段不新增实测结论。', 1)
    raise ValueError(name)


if __name__ == '__main__':
    notebook = nbf.v4.new_notebook()
    notebook.cells = [
        nbf.v4.new_markdown_cell('''# K1 信息与状态接口：真机采集

本 Notebook 调用同目录的 `probe_k1_info_state.py`，采集截图中的八项接口。全部列表与嵌套字段会自动保存，无需手抄记录表。

将这两个文件放在同一工作目录，依次运行两格代码即可。保持机器人当前状态，本次只查询信息。'''),
        nbf.v4.new_code_cell('''import probe_k1_info_state as probe

TESTER = "xy"  # 可修改为测试人
NOTE = ""      # 可选：本次配件、状态或其它现场信息
OUTPUT_ROOT = None  # 留空时保存在当前目录的“K1信息状态测试结果”中

print("采集脚本：", probe.__file__)
print("当前内核是否已有robot：", "robot" in globals())'''),
        nbf.v4.new_markdown_cell('''## 运行采集

下格优先复用当前内核中名为 `robot` 的连接；没有时由模块创建并缓存，重跑仍会复用。每次采集另建结果目录。

`list_frames()`刚连接时若为空，程序会在五秒窗口内重读，保存所有尝试。单项报错会继续其他项。运行结束打印 ZIP 的绝对路径。'''),
        nbf.v4.new_code_cell('''result_dir = probe.collect(
    robot=globals().get("robot"),
    output_root=OUTPUT_ROOT,
    tester=TESTER,
    note=NOTE,
)
print("本次结果目录：", result_dir)'''),
        nbf.v4.new_markdown_cell('''## 保存与反馈

反馈程序最后打印的 ZIP 即可。`采集汇总.md`可直接阅读，`原始记录.json`保留完整返回与异常，`SDK接口定义.txt`保留本机定义。

没有手工记录表需要填写。首次返回为空或有报错时照实反馈结果，助手根据记录分析。本次未执行动作或查询任意两帧之间的变换，不能由清单推定这些功能已验证。'''),
    ]
    notebook.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                         'language_info': {'name': 'python', 'version': '3.10'}}
    target = ROOT/'04-shared/sdk-tests/K1信息与状态接口_真机采集.ipynb'
    assert not target.exists()
    nbf.write(notebook, target)
    base = json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
    changes = []
    for name, digest in base['shared'].items():
        path = ROOT/name
        old = path.read_bytes()
        assert hashlib.sha256(old).hexdigest() == digest, name
        new = change(name, old.decode('utf-8-sig'))
        assert new != old.decode('utf-8-sig'), name
        path.write_text(new, encoding='utf-8', newline='')
        changes.append({'path': name, 'before': digest, 'after': hashlib.sha256(path.read_bytes()).hexdigest()})
    (TASK/'联动记录.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Notebook与六份导航/技术说明已更新，真机结果保持待反馈。')
