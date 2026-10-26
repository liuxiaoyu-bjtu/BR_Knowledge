"""检查审核引用、原稿指纹和链接，并保存共享文档的本轮增量。"""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
REPORT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/U7_文字表达与阅读衔接审核.md'
EXPECTED = [
    '98da432eafb2eed778204b6f44f3e5d5c832333cdee75eba4cd241bbb17dbec7',
    'bb6e777478e39f8d5cc41e35224f84564bfdb061f69f47fa9e1fed4b445654dc',
    '9e126a63da46545ccce85808026de7f061fb67f9d136b967190868883b040e94',
    '373cf8ece0e07358e39af8d027034d8303b8bb7a7b5d20d87088b901b80d9d97',
]


def main():
    manifest = json.loads((TASK / '输入与审核清单.json').read_text(encoding='utf-8'))
    assert [x['sha256'] for x in manifest['inputs']] == EXPECTED
    results = []
    sources = {}
    for item in manifest['inputs'] + manifest['generators']:
        path = ROOT / item['path']
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert sha == item['sha256'], f'原稿已变化：{path}'
        results.append({'path': item['path'], 'sha256': sha, 'unchanged': True})
        if path.suffix == '.ipynb':
            doc = json.loads(path.read_text(encoding='utf-8'))
            assert item['reviewed_cells'] == list(range(1, len(doc['cells']) + 1))
            assert item['cells'] == len(doc['cells'])
            assert item['code_cells'] == sum(c['cell_type'] == 'code' for c in doc['cells'])
            sources[path.stem[3:5]] = doc
    assert sum(x['cells'] for x in manifest['inputs']) == 56
    assert sum(x['code_cells'] for x in manifest['inputs']) == 16
    counts = dict(Counter(x['scope'] for x in manifest['issues']))
    assert counts == {'A': 16, 'C': 1, 'B': 16}
    assert len(manifest['issues']) == 33
    report = REPORT.read_text(encoding='utf-8')
    for issue in manifest['issues']:
        assert report.count(f'#### {issue["id"]}｜') == 1
        doc = sources[issue['lesson']]
        for q in issue['quotes']:
            assert q['text'] in ''.join(doc['cells'][q['cell'] - 1]['source'])
    assert 'A类16项' in report and 'B类16项' in report and 'C类1项' in report
    for filename in ['audit.py', 'verify.py']:
        path = TASK / filename
        compile(path.read_text(encoding='utf-8'), str(path), 'exec')

    links = []
    missing = []
    for source in [REPORT, TASK / '02-产出清单与状态日志.md']:
        for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            target = match.group(1)
            if '://' in target or target.startswith('#'):
                continue
            dest = (source.parent / target.split('#')[0]).resolve()
            # 本次校验即将生成的两个文件。
            generated = dest in [TASK / '校验结果.json', TASK / '共享文档本轮增量.patch']
            if not dest.exists() and not generated:
                missing.append(str(dest))
            links.append({'source': source.relative_to(ROOT).as_posix(), 'target': target,
                          'exists_or_generated': dest.exists() or generated})
    assert not missing, f'缺失链接：{missing}'

    patch_parts = []
    markers = {
        'AGENTS.md': '  - U7四课于2026-10-26完成文字表达与阅读衔接审核',
        'INDEX.md': '| X课程 U7 / 去AI化 / 文字表达',
        '05-internal-materials/vocational-planning/README.md': '- **U7文字审核（2026-10-26）**：',
    }
    for rel in manifest['shared']:
        after = (ROOT / rel).read_text(encoding='utf-8')
        # 共享文件有其他任务同时编辑。仅提取本轮新增记录，保留其他任务全部内容。
        if rel == 'CHANGELOG.md':
            matches = list(re.finditer(r'^## 2026-10-26 · U7四课文字表达与阅读衔接审核\n.*?(?=^## |\Z)',
                                      after, flags=re.MULTILINE | re.DOTALL))
            assert len(matches) == 1
            addition = matches[0].group(0)
        else:
            matches = [line for line in after.splitlines(keepends=True) if line.startswith(markers[rel])]
            assert len(matches) == 1, rel
            addition = matches[0]
        before = after.replace(addition, '', 1)
        patch_parts.extend(difflib.unified_diff(before.splitlines(keepends=True),
                                              after.splitlines(keepends=True),
                                              fromfile=f'a/{rel}', tofile=f'b/{rel}'))
    patch = TASK / '共享文档本轮增量.patch'
    patch.write_text(''.join(patch_parts), encoding='utf-8', newline='\n')
    proc = subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)], cwd=ROOT,
                          capture_output=True, encoding='utf-8')
    assert proc.returncode == 0, proc.stderr
    output = {'date': '2026-10-26', 'reviewed_cells': 56, 'markdown_cells': 40,
              'code_cells': 16, 'issues': 33, 'issue_categories': counts,
              'input_files': results, 'quotes_valid': True, 'links': links,
              'scripts_syntax_valid': True, 'shared_patch_reverse_check': 'passed',
              'shared_patch_excludes_concurrent_edits': True,
              'robot_execution': False, 'notebook_or_generator_modified': False,
              'stage_changed': False}
    (TASK / '校验结果.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'reviewed_cells': 56, 'issues': 33, 'categories': counts,
                      'unchanged_files': len(results), 'checked_links': len(links),
                      'patch_check': 'passed'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
