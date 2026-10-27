"""更新审核入口，并只为本轮新增内容生成相对HEAD的导航补丁。"""
from pathlib import Path
import difflib
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
PROJ_REL = '05-internal-materials/vocational-planning/03_X课程项目'
REPORT = 'U4-L2-L4_距离实验复评与文字校对.md'
ENTRIES = {
    'AGENTS.md': '> **U4-L2～L4更新（2026-10-26）**：已复评距离实验并校对三课全文，直接修订42格Markdown；代码与120格顺序不变，生成器反向同步。L2建议以独立里程计核对与视觉标定为主线，实验前移、1.2米视野及控制代码调整待按方案实施；三课真机确认②仍待完成。入口：`05-internal-materials/vocational-planning/03_X课程项目/实验验证/' + REPORT + '`。',
    'INDEX.md': '> U4距离实验 / 框高估距 / 框面积与距离 / 指定位移 / U4与U7分工：[L2～L4复评与文字校对](05-internal-materials/vocational-planning/03_X课程项目/实验验证/' + REPORT + ')（2026-10-26；策略2主线建议、官方SDK核验、42格文字修订，实验结构与代码未变）。',
    'CHANGELOG.md': '''## 2026-10-26 · U4距离实验复评与三课文字校对

- 复评L2两种实验策略，建议独立核对里程计、独立视觉标定后再做有条件的联合核查；指出1.2米全身裁切、标定姿态变化及未知起步间距的条件问题。
- 核对官方运动接口：set_velocity配合get_odom可按估计位移停止，reset_odom只改参考位姿；未发现公开的直接距离行走接口。保存来源正文与导航。
- 审读L2～L4全部120格，修订42格Markdown，补公式、操作、结果解释与记录；同步5秒仅作思考条件、语音未在U4实现的口径。33格代码、格号和执行信息保持不变，三份生成器从主稿回写。
- 明确U4-L3侧重读数参与控制，U7-L1侧重订阅与时序观察。实验结构和控制代码的待实施项另附清单，三课②未通过；本地提交，推送由用户手动完成。''',
    '05-internal-materials/vocational-planning/README.md': '> **U4-L2～L4更新（2026-10-26）**：[距离实验复评与文字校对](03_X课程项目/实验验证/' + REPORT + ')已完成；120格完整审读，42格Markdown修订，代码与格序保留，生成器反向同步。L2推荐策略2主线及有条件联合核查；实验前移和代码调整待实施，三课真机确认②仍待完成。',
    PROJ_REL + '/X课程大纲-v4.md': '> **U4距离实验审核（2026-10-26）**：[复评与文字校对](实验验证/' + REPORT + ')指出1.2米处框截断、拍摄姿态变化、已知起步间距与自主测距的区别，建议策略2主线。三课文字已校对，实验与代码未变；课程主线和标题调整留待方案确定，未登记新确认。',
    PROJ_REL + '/X课程开发计划-v4.md': '> **U4-L2～L4文字校对（2026-10-26）**：120格审读完成，42格Markdown修订，33格代码与格序不变，生成器已回写。三课仍待真机确认②；L2实验顺序、视觉标定范围与控制代码修改待实施。方案及补验项见[复评记录](实验验证/' + REPORT + ')。',
    '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md': '> **U4复评记录（2026-10-26）**：三课文字校对完成，代码和阶段不变。里程计参考位姿重置不等于移动；框高逆比换算要求目标范围完整且拍摄姿态相近，1.2米能否满足须实图确认；5秒不作转向硬性验收。L2实验前移及代码修订另列方案，未改变本文件已有流程规则。见[距离实验复评与文字校对](../03_X课程项目/实验验证/' + REPORT + ')。',
}


def main():
    patch = []
    workspace_patch = []
    for rel, note in ENTRIES.items():
        path = ROOT / rel
        text = path.read_text(encoding='utf-8')
        heading = re.search(r'^# [^\n]+\n', text, re.MULTILINE).group(0)
        addition = '\n' + note + '\n'
        if note not in text:
            updated = text.replace(heading, heading + addition, 1)
            path.write_text(updated, encoding='utf-8', newline='\n')
        else:
            updated = text
        base = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
        assert heading in base, rel
        target = base.replace(heading, heading + addition, 1)
        patch.extend(difflib.unified_diff(base.splitlines(keepends=True), target.splitlines(keepends=True),
                                        fromfile='a/' + rel, tofile='b/' + rel))
        before_current = updated.replace(addition, '', 1)
        workspace_patch.extend(difflib.unified_diff(before_current.splitlines(keepends=True), updated.splitlines(keepends=True),
                                                  fromfile='a/' + rel, tofile='b/' + rel))
    (TASK / '导航本轮增量.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    (TASK / '工作区导航增量.patch').write_text(''.join(workspace_patch), encoding='utf-8', newline='\n')
    (TASK / '导航清单.json').write_text(json.dumps(list(ENTRIES), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('导航记录', len(ENTRIES), '个；已隔离其他任务原有改动。')


if __name__ == '__main__':
    main()
