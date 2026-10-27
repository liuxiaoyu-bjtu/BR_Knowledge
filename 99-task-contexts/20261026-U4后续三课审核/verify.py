"""静态核验文字修订、Notebook保留项与生成器源，不运行机器人。"""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
REPORT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U4-L2-L4_距离实验复评与文字校对.md'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((TASK / '修订清单.json').read_text(encoding='utf-8'))
    results = []
    total, total_code, changes = 0, 0, 0
    for item in manifest['lessons']:
        path = ROOT / item['notebook']
        before = TASK / 'before' / item['notebook']
        assert digest(before) == item['before_sha256']
        assert digest(path) == item['after_sha256'], f'输入已变化：{path}'
        old = json.loads(before.read_text(encoding='utf-8'))
        doc = json.loads(path.read_text(encoding='utf-8'))
        assert len(doc['cells']) == len(old['cells']) == item['cells']
        assert {k: v for k, v in old.items() if k != 'cells'} == {k: v for k, v in doc.items() if k != 'cells'}
        actual_changes = []
        for number, (a, b) in enumerate(zip(old['cells'], doc['cells']), start=1):
            assert {k: v for k, v in a.items() if k != 'source'} == {k: v for k, v in b.items() if k != 'source'}
            if a['cell_type'] == 'code':
                assert a == b, (item['lesson'], number)
                ast.parse(''.join(b['source']))
            if a['source'] != b['source']:
                actual_changes.append(number)
        assert actual_changes == [x['cell'] for x in item['changes']]
        generator = ROOT / item['generator']
        tree = ast.parse(generator.read_text(encoding='utf-8'))
        cells = []
        for node in tree.body:
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name)
                    and node.value.func.value.id == 'cells' and node.value.func.attr == 'append'):
                call = node.value.args[0]
                kind = 'markdown' if call.func.id == 'md' else 'code'
                cells.append((kind, ast.literal_eval(call.args[0])))
        assert cells == [(c['cell_type'], ''.join(c['source'])) for c in doc['cells']], generator
        code_count = sum(c['cell_type'] == 'code' for c in doc['cells'])
        total += len(doc['cells'])
        total_code += code_count
        changes += len(actual_changes)
        results.append({'lesson': item['lesson'], 'cells': len(doc['cells']), 'code_cells_unchanged': code_count,
                        'changed_markdown_cells': actual_changes, 'generator_matches': True,
                        'notebook_sha256': digest(path), 'generator_sha256': digest(generator)})
    assert (total, total_code, changes) == (120, 33, 42)
    for name in ['research.py', 'revise.py', 'records.py', 'verify.py']:
        ast.parse((TASK / name).read_text(encoding='utf-8'))
    links_checked = 0
    for source in [REPORT, TASK / '02-产出清单与状态日志.md']:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            dest = (source.parent / target).resolve()
            assert dest.exists() or dest == TASK / '校验结果.json', dest
            links_checked += 1
    pages = json.loads((TASK / 'sdk-evidence/pages.json').read_text(encoding='utf-8'))
    for part in ['set-velocity', 'get-odom', 'reset-odom']:
        page = next(x for x in pages if '/' + part + '/' in x['url'])
        body = (TASK / 'sdk-evidence' / page['text_file']).read_text(encoding='utf-8')
        assert 'BoosterRobot.' in body and '接口签名' in body
    for name, args in [('工作区导航增量.patch', ['--reverse', '--check']),
                       ('导航本轮增量.patch', ['--cached', '--check'])]:
        proc = subprocess.run(['git', 'apply', *args, str(TASK / name)], cwd=ROOT, capture_output=True, encoding='utf-8')
        assert proc.returncode == 0, proc.stderr
    output = {'date': manifest['date'], 'reviewed_cells': total, 'code_cells_unchanged': total_code,
              'changed_markdown_cells': changes, 'lessons': results,
              'cell_order_ids_metadata_execution_preserved': True, 'generator_static_match': True,
              'syntax_checks': 'passed', 'report_links_checked': links_checked,
              'official_sdk_pages_checked': ['set_velocity', 'get_odom', 'reset_odom'],
              'navigation_patch_checks': 'passed', 'robot_commands_executed': False,
              'stage_confirmation_changed': False}
    (TASK / '校验结果.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cells': total, 'unchanged_code_cells': total_code, 'changed_md_cells': changes,
                      'generator_static_match': True, 'navigation_patch_check': 'passed'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
