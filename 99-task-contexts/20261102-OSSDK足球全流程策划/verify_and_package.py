from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
OUT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划'
PACKAGE = OUT / 'K1足球全流程_OSSDK策划交付包.zip'

run = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', str(TASK / 'tests'), '-v'],
                     capture_output=True, text=True, encoding='utf-8')
(TASK / '离线检查输出.txt').write_text(run.stdout + run.stderr, encoding='utf-8')
if run.returncode:
    raise RuntimeError(run.stdout + run.stderr)
ast.parse((OUT / 'k1_soccer.py').read_text(encoding='utf-8'))
json.loads((OUT / 'teacher_profile.example.json').read_text(encoding='utf-8'))
md = (OUT / 'K1足球全流程_OSSDK策划案.md').read_text(encoding='utf-8')
for image in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md):
    if not (OUT / image).is_file():
        raise RuntimeError(f'missing_image:{image}')
sections = len(re.findall(r'^## \d+\.', md, re.M))
if sections != 17:
    raise RuntimeError('section_count_mismatch')
for fig in ['01_主流程', '02_球位处理子流程', '03_模块框架', '04_状态转换']:
    for ext in ['dot', 'svg', 'png']:
        if not (OUT / '图示' / f'{fig}.{ext}').is_file():
            raise RuntimeError(f'missing_figure:{fig}.{ext}')
module_tree = ast.parse((OUT / 'k1_soccer.py').read_text(encoding='utf-8'))
imports = [n.module or '' for n in ast.walk(module_tree) if isinstance(n, ast.ImportFrom)]
imports += [alias.name for n in ast.walk(module_tree) if isinstance(n, ast.Import) for alias in n.names]
if any(n.startswith(('rclpy', 'booster_robotics_sdk_python', 'geometry_msgs', 'brain.msg')) for n in imports):
    raise RuntimeError('direct_low_level_dependency')
figqa = json.loads((TASK / 'qa/diagram-bounds.json').read_text(encoding='utf-8'))
if any(item['overflow'] or item['edgeOverlap'] for item in figqa):
    raise RuntimeError('diagram_layout_issues')
assets = [f for f in OUT.rglob('*') if f.is_file() and f != PACKAGE and '__pycache__' not in f.parts]
with zipfile.ZipFile(PACKAGE, 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in assets:
        archive.write(file, Path('OSSDK足球全流程策划') / file.relative_to(OUT))
tests_match = re.search(r'Ran (\d+) tests?', run.stdout + run.stderr)
if tests_match is None:
    raise RuntimeError('missing_test_count')
report = {'offline_tests':int(tests_match.group(1)), 'result':'passed', 'robot_run':False,
          'plan_sections':sections, 'figures':4, 'package_files':len(assets),
          'package_sha256':hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
          'module_sha256':hashlib.sha256((OUT / 'k1_soccer.py').read_bytes()).hexdigest(),
          'forbidden_low_level_imports':[], 'layout_report':'qa/diagram-bounds.json'}
(TASK / '校验结果.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
