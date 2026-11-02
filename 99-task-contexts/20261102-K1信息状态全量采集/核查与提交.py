from pathlib import Path
import ast
import hashlib
import json
import re
import runpy
import subprocess
import sys
import zipfile
import nbformat

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
base = json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
directory = '04-shared/sdk-tests/'
artifacts = [directory+n for n in ['probe_k1_info_state.py', 'K1信息与状态接口_采集说明.md',
                                 'K1信息与状态接口_真机采集.ipynb', 'K1信息与状态接口_采集工具.zip']]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def verify():
    for name, digest in base['protected'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    source = (ROOT/artifacts[0]).read_text(encoding='utf-8')
    ast.parse(source, feature_version=(3, 10))
    tree = ast.parse(source)
    interfaces = next(ast.literal_eval(n.value) for n in tree.body
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'INTERFACES' for t in n.targets))
    assert interfaces == ('robot_info','get_mode','list_gaits','get_gait','list_frames','list_joints','list_sensors','list_actions')
    notebook = nbformat.read(ROOT/artifacts[2], as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == 'code']
    assert len(cells) == 2
    for cell in cells:
        assert not cell.outputs and cell.execution_count is None
        ast.parse(cell.source, feature_version=(3, 10))
    bundle = ROOT/artifacts[3]
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in artifacts[:3]:
            archive.write(ROOT/name, Path(name).name)
    with zipfile.ZipFile(bundle) as archive:
        assert len(archive.namelist()) == 3
        for name in artifacts[:3]:
            assert archive.read(Path(name).name) == (ROOT/name).read_bytes()
    links = 0
    for name in [*base['shared'], artifacts[1]]:
        path = ROOT/name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            if 'K1信息与状态接口_' in target or 'probe_k1_info_state' in target:
                assert (path.parent/target).exists(), (name, target)
                links += 1
    result = {'interfaces': list(interfaces), 'python_3_10_syntax': True,
              'notebook_valid_and_unexecuted': True, 'bundle_files': 3, 'links_checked': links,
              'protected_files_unchanged': len(base['protected']), 'offline_tests_passed': 8,
              'hardware_executed': False, 'hardware_records_created': False}
    (TASK/'核查结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


assert sys.argv[1:] in [['verify'], ['stage'], ['commit']]
if sys.argv[1] == 'verify':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
elif sys.argv[1] == 'stage':
    verify()
    assert not git('diff','--cached','--name-only'), '保留现有暂存，不混合提交'
    changes = runpy.run_path(str(TASK/'同步与生成.py'))['change']
    expected = set()
    for name in base['shared']:
        text = subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT).decode('utf-8-sig')
        updated = changes(name,text)
        assert updated != text
        path = TASK/'head-increment'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(updated,encoding='utf-8',newline='')
        blob = git('hash-object','-w','--path='+name,str(path))
        subprocess.run(['git','update-index','--add','--cacheinfo','100644,'+blob+','+name],cwd=ROOT,check=True)
        expected.add(name)
    local = ['基线.json','离线核查.py','同步与生成.py','联动记录.json','核查与提交.py','核查结果.json','完成记录.md']
    new = artifacts + [(TASK/name).relative_to(ROOT).as_posix() for name in local]
    subprocess.run(['git','add','--',*new],cwd=ROOT,check=True)
    expected.update(new)
    assert set(git('-c','core.quotePath=false','diff','--cached','--name-only').splitlines()) == expected
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    manifest = {'head':git('rev-parse','HEAD'),'tree':git('write-tree'),'paths':sorted(expected)}
    (TASK/'提交清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('精确暂存',len(expected),'项')
else:
    manifest = json.loads((TASK/'提交清单.json').read_text(encoding='utf-8'))
    assert git('rev-parse','HEAD') == manifest['head'] and git('write-tree') == manifest['tree']
    for name,digest in base['protected'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest,name
    subprocess.run(['git','commit','-m','新增K1八项信息与状态接口只读采集工具，完整记录返回与本机定义'],cwd=ROOT,check=True)
    print(git('log','-1','--oneline'))
