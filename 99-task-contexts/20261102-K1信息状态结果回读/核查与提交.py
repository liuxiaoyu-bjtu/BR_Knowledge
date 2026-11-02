from pathlib import Path
import hashlib
import json
import re
import runpy
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
base = json.loads((TASK/'基线.json').read_text(encoding='utf-8'))
scope = runpy.run_path(str(TASK/'整理与同步.py'))
DIRECTORY = ROOT/scope['RESULT']
DOCUMENT = ROOT/scope['DOCUMENT']


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    for group in ('protected','evidence'):
        for name,digest in base[group].items():
            assert sha(ROOT/name) == digest, name
    raw = json.loads((DIRECTORY/'原始记录.json').read_text(encoding='utf-8'))
    assert raw['completed'] is True
    names = ('robot_info','get_mode','list_gaits','get_gait','list_frames','list_joints','list_sensors','list_actions')
    assert tuple(raw['interfaces']) == names
    outcomes = {}
    values = {}
    for name in names:
        row = raw['interfaces'][name]
        assert len(row['attempts']) == 1
        assert row == json.loads((DIRECTORY/'分接口'/(name+'.json')).read_text(encoding='utf-8'))
        selected = row['attempts'][row['selected_attempt']]
        outcomes[name] = {'status':selected['status'],'count':selected.get('item_count')}
        if name == 'robot_info':
            assert selected['status'] == 'error' and 'code = 100' in selected['error']
            assert 'GetRobotInfo()' in selected['traceback']
        else:
            assert selected['status'] == 'returned' and selected['export_warnings'] == []
            values[name] = selected['value']
    assert len(values) == 7
    assert values['get_mode'] == 'walk' and values['get_gait'] == 'default'
    assert values['list_gaits'] == ['default','soccer']
    assert [len(values[n]) for n in ('list_frames','list_joints','list_sensors','list_actions')] == [28,22,2,10]
    assert sha(DIRECTORY/'测试脚本.py') == raw['script_sha256']
    with zipfile.ZipFile(next(DIRECTORY.glob('*.zip'))) as archive:
        assert len(archive.namelist()) == 12
        for name in archive.namelist():
            assert archive.read(name) == (DIRECTORY/name).read_bytes(),name
    document = DOCUMENT.read_text(encoding='utf-8')
    assert document == scope['build_document'](raw)
    block = re.search(r'```text\n(.*?)\n```',document,re.S).group(1).splitlines()
    assert block == values['list_frames']
    table = [row.split('|')[1:-1] for row in document.splitlines() if re.match(r'^\| \d+ \|',row)]
    assert len(table) == 22
    for row,joint in zip(table,values['list_joints']):
        assert row[1].strip().strip('`') == joint['name']
        expected = [joint['limits']['min'],joint['limits']['max'],joint['max_torque'],joint['max_velocity']]
        assert all(abs(float(cell)-number) <= 0.00000051 for cell,number in zip(row[2:],expected))
    assert '本次未取得' in document and 'return self._gait' in document
    links=0
    for path in [DOCUMENT,*[ROOT/name for name in base['shared']]]:
        text=path.read_text(encoding='utf-8-sig')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if path == DOCUMENT or 'booster-sdk-k1-info-state' in target or 'K1信息状态_20261102_154403_101875' in target:
                assert (path.parent/target).exists(),(path,target)
                links+=1
    report={'test_directory':scope['RESULT'],'sdk_version':raw['environment']['boosteros_version'],
            'collected_at':raw['started_at'],'firmware_from_this_run':None,
            'outcomes':outcomes,'raw_files_preserved':len(base['evidence']),
            'protected_files_preserved':len(base['protected']),
            'split_json_matches':8,'script_hash_matches':True,'zip_entries_match':12,
            'document_names_order_fields_checked':True,'links_checked':links,
            'hardware_rerun':False,'course_changes':False}
    (TASK/'回读核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


assert sys.argv[1:] in [['verify'],['stage'],['commit']]
if sys.argv[1] == 'verify':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
elif sys.argv[1] == 'stage':
    verify()
    local=['基线.json','整理与同步.py','联动记录.json','核查与提交.py','回读核对.json','完成记录.md']
    new=[scope['DOCUMENT'],*base['evidence'],*[(TASK/name).relative_to(ROOT).as_posix() for name in local]]
    owned=set(base['shared']) | set(new)
    staged=set(git('-c','core.quotePath=false','diff','--cached','--name-only').splitlines())
    assert not staged or staged == owned, '暂存区有其它修改，不合并提交'
    expected=set()
    for name in base['shared']:
        old=subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT).decode('utf-8-sig')
        updated=scope['change'](name,old)
        assert updated != old,name
        path=TASK/'head-increment'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(updated,encoding='utf-8',newline='')
        blob=git('hash-object','-w','--path='+name,str(path))
        subprocess.run(['git','update-index','--add','--cacheinfo','100644,'+blob+','+name],cwd=ROOT,check=True)
        expected.add(name)
    subprocess.run(['git','add','--',*new],cwd=ROOT,check=True)
    expected.update(new)
    assert set(git('-c','core.quotePath=false','diff','--cached','--name-only').splitlines()) == expected
    # 本机源码证据自带结尾空行，按原样保留；编辑产物单独检查空白格式。
    subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)'+scope['RESULT']+'/**'],cwd=ROOT,check=True)
    manifest={'head':git('rev-parse','HEAD'),'tree':git('write-tree'),'paths':sorted(expected)}
    (TASK/'提交清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('精确暂存',len(expected),'项')
else:
    manifest=json.loads((TASK/'提交清单.json').read_text(encoding='utf-8'))
    assert git('rev-parse','HEAD') == manifest['head'] and git('write-tree') == manifest['tree']
    for group in ('protected','evidence'):
        for name,digest in base[group].items():
            assert sha(ROOT/name) == digest,name
    subprocess.run(['git','commit','-m','依据K1真机记录补齐八项信息状态接口专用清单与使用说明'],cwd=ROOT,check=True)
    assert not git('diff','--cached','--name-only')
    print(git('log','-1','--oneline'))
