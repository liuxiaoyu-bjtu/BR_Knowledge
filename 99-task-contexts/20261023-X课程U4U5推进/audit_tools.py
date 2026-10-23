"""本次课程审核用资料读取与离线检查；不连接机器人。"""
from pathlib import Path
import json
import sys
import re
import subprocess
import urllib.request
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '05-internal-materials/vocational-planning'
PROJ = BASE / '03_X课程项目'
CACHE = Path(__file__).parent / 'sdk-pages'
PREFIX = 'https://docs.booster.tech/zh-CN/docs/developer-guide/booster-os-python-sdk/'
PAGES = ['booster-robot-client-reference/audio-manager/' + p + '/' for p in (
    'booster-robot-audio-manager', 'get-system-volume', 'set-system-volume',
    'start-recording', 'stop-recording', 'is-recording', 'get-recording-duration',
    'record-stream', 'play-stream')]
PAGES += ['booster-robot-client-reference/advanced-task-apis/play-sound/']
PAGES += ['vision-and-speech/speech/']
PAGES += ['vision-and-speech/speech/' + p + '/' for p in (
    'recognize-stream', 'chat', 'list-voices', 'synthesize', 'recognize')]

def fetch(url):
    CACHE.mkdir(exist_ok=True)
    key = url.rstrip('/').split('/')[-1]
    target = CACHE / (key + '.html')
    if target.exists():
        raw = target.read_text(encoding='utf-8')
    else:
        raw = urllib.request.urlopen(url, timeout=40).read().decode('utf-8')
        target.write_text(raw, encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')
    article = soup.find('article') or soup.find('main') or soup
    content = article.get_text('\n', strip=True)
    (CACHE / (key + '.txt')).write_text(content, encoding='utf-8')
    links = [{'text': a.get_text(' ', strip=True), 'url': urljoin(url, a['href'])}
             for a in article.find_all('a', href=True) if not a['href'].startswith('#')]
    (CACHE / (key + '.links.json')).write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'url': url, 'text': content, 'links': links}

mode = sys.argv[1]
if mode == 'commit_task':
    import difflib
    task=Path(__file__).parent
    def git(*args):
        r=subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        if r.returncode:
            raise RuntimeError(r.stderr or r.stdout)
        return r.stdout
    if len(sys.argv)<3 or sys.argv[2]!='resume':
        assert not git('diff','--cached','--name-only').strip(), '已有暂存修改，停止提交'
    patch=[]
    shared=[]
    for before in sorted((task/'before-record-updates').rglob('*')):
        if not before.is_file():
            continue
        rel=before.relative_to(task/'before-record-updates').as_posix()
        if rel.endswith('U5-L4_真机问题复评与重构建议.md'):
            continue
        shared.append(rel)
        patch.extend(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(keepends=True),(ROOT/rel).read_text(encoding='utf-8').splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel,n=3))
    (task/'共享文档本轮增量.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
    log=task/'02-产出清单与状态日志.md'
    s=log.read_text(encoding='utf-8')
    s=s.replace('用户手动推送。工作区存在其他任务的大量未提交文件，本轮只处理必要课程产物；本地提交结果在核验后补记。',
        '用户手动推送。本轮本地提交包含U4-L1教学设计、U5-L4新稿、四份反向同步生成器、三份复核/核验记录及本任务记录和离线结果。\n\n共享文件与前序未提交内容交叠，未整体暂存；当前工作区已经更新，其本轮增量另存于`共享文档本轮增量.patch`，随本次提交留档。该补丁以任务开始时工作区为基准，不应再次应用到当前工作区。共享文件范围：\n\n'+'\n'.join('- `'+p+'`' for p in shared)+'\n\n本提交不包含其他任务文件；未执行push。提交标识可用 `git log -1` 查看。')
    log.write_text(s,encoding='utf-8',newline='\n')
    paths=[PROJ/name for name in ('_gen_L17.py','_gen_L18.py','_gen_L19.py','_gen_L20.py','notebooks/U5-L4_语音问答闭环.ipynb','教学设计/U4-L1_转向来宾_教学设计.md','实验验证/U5-L1-L2-L3_P2复核与修改方案.md','实验验证/U5-L4_真机问题复评与重构建议.md','实验验证/U5_语音SDK能力核验记录.md')]
    paths += [task/name for name in ('02-产出清单与状态日志.md','audit_tools.py','revise_courses.py','protected_files_sha256.json','离线检查结果.txt','共享文档本轮增量.patch','U5-L4_cells.md','U5-L4_重构前.ipynb')]
    assert all(p.is_file() for p in paths)
    git('add','--',*[p.relative_to(ROOT).as_posix() for p in paths])
    staged=git('diff','--cached','--name-only').splitlines()
    assert set(staged)=={p.relative_to(ROOT).as_posix() for p in paths}, staged
    # unified diff的空白上下文行以一个空格开头，保留原格式；检查其余交付物。
    git('diff','--cached','--check','--','.',':(exclude)'+(task/'共享文档本轮增量.patch').relative_to(ROOT).as_posix())
    print(git('diff','--cached','--stat'))
    print(git('commit','-m','完成U4-L1教学设计并按SDK复核U5课程与重构L4'))
    print('提交：',git('rev-parse','--short','HEAD').strip())
    print('剩余已暂存：',git('diff','--cached','--name-only').strip() or '无')
    print('共享文档仍在工作区；本轮增量已随提交留档。未推送。')
elif mode == 'git_plan':
    import difflib
    task=Path(__file__).parent
    def git(*args, input=None):
        return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',input=input)
    print('暂存区',git('diff','--cached','--name-only').stdout)
    for before in sorted((task/'before-record-updates').rglob('*')):
        if not before.is_file():
            continue
        rel=before.relative_to(task/'before-record-updates').as_posix()
        head=git('show','HEAD:'+rel)
        if head.returncode:
            print('原未跟踪：',rel)
            continue
        patch=''.join(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(keepends=True),(ROOT/rel).read_text(encoding='utf-8').splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel,n=3))
        check=git('apply','--cached','--check','--whitespace=nowarn','-',input=patch)
        print('本轮增量可独立暂存' if check.returncode==0 else '前序修改交叠',rel)
    for rel in ('AGENTS.md','INDEX.md','05-internal-materials/vocational-planning/README.md'):
        value=git('show','HEAD:'+rel)
        print('HEAD',rel)
        for i,line in enumerate(value.stdout.splitlines(),1):
            if line.startswith('#') or 'U4' in line or 'U5' in line or 'X课程' in line:
                print(i,line[:300])
    for pattern in ('_gen_L17.py','_gen_L18.py','_gen_L19.py','_gen_L20.py','notebooks/U5-L4_*.ipynb','教学设计/U4-L1_*.md','实验验证/U5*.md'):
        for path in sorted(PROJ.glob(pattern)):
            rel=path.relative_to(ROOT).as_posix()
            print('候选',git('status','--short','--',rel).stdout.strip())
    for rel in ('CHANGELOG.md','05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md','05-internal-materials/vocational-planning/03_X课程项目/X课程大纲-v4.md','05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md'):
        content=git('show','HEAD:'+rel).stdout
        print('HEAD相关位置',rel)
        for i,line in enumerate(content.splitlines(),1):
            if i<12 or line.startswith('## 7.') or 'U5-L' in line[:90] or line.startswith('## 单元五') or line.startswith('## 单元六'):
                print(i,line[:260])
elif mode == 'final_audit':
    import difflib
    task = Path(__file__).parent
    def git(*args):
        r=subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        if r.returncode:
            raise RuntimeError(r.stderr)
        return r.stdout
    status=git('status','--porcelain=v1','-z').split('\0')
    print('工作区状态条目：',len([x for x in status if x]))
    print('已暂存：',git('diff','--cached','--name-only'))
    print('分支：',git('branch','--show-current').strip())
    for key in ('user.name','user.email'):
        print(key,git('config','--get',key).strip())
    for rel in sorted((task/'before-record-updates').rglob('*')):
        if not rel.is_file():
            continue
        rp=rel.relative_to(task/'before-record-updates')
        target=ROOT/rp
        if not target.is_file():
            print('备份相对路径未找到：',rp.as_posix())
            continue
        before=rel.read_text(encoding='utf-8').splitlines(keepends=True)
        after=target.read_text(encoding='utf-8').splitlines(keepends=True)
        diff=list(difflib.unified_diff(before,after,fromfile='before/'+rp.as_posix(),tofile='after/'+rp.as_posix(),n=1))
        print('\n本轮增量',rp.as_posix(),'diff行数',len(diff),'是否在HEAD',bool(git('ls-files','--',rp.as_posix()).strip()))
        for line in diff:
            print(line.rstrip()[:600])
    for p in sorted(task.rglob('*')):
        if p.is_file() and 'sdk-pages' not in p.parts and 'before-record-updates' not in p.parts:
            print('任务文件',p.relative_to(ROOT).as_posix(),p.stat().st_size)
elif mode == 'review_git':
    paths=['AGENTS.md','INDEX.md','CHANGELOG.md','05-internal-materials/vocational-planning/README.md',
           '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
           '05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md',
           '05-internal-materials/vocational-planning/03_X课程项目/X课程大纲-v4.md']
    r=subprocess.run(['git','-c','core.quotepath=false','diff','--numstat','--',*paths],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    print(r.stdout)
    for p in sorted(PROJ.glob('_gen_L1[7-9].py'))+list(PROJ.glob('_gen_L20.py')):
        print(p.name,'\n'+'\n'.join(p.read_text(encoding='utf-8').splitlines()[-5:]))
    for key in ('task-handle','task-status','chat'):
        p=CACHE/(key+'.txt')
        if p.is_file():
            lines=p.read_text(encoding='utf-8').splitlines()
            for i,line in enumerate(lines):
                if re.search('def |->|status:|CANCELLING|wait\(|cancel\(',line):
                    print(key, '\n'.join(lines[max(0,i-2):min(len(lines),i+4)]))
elif mode == 'inspect':
    for p in PROJ.rglob('_gen_L*.py'):
        if p.stem in ('_gen_L17','_gen_L18','_gen_L19','_gen_L20'):
            print('\nGENERATOR',p.relative_to(ROOT).as_posix())
            lines=p.read_text(encoding='utf-8').splitlines()
            print('\n'.join(lines[:30]+['...']+lines[-35:]))
    print('\nGIT STATUS')
    print(subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8').stdout)
    print('\nNESTED INSTRUCTIONS')
    for p in BASE.rglob('AGENTS.md'):
        print(p.relative_to(ROOT).as_posix())
elif mode == 'inventory':
    for p in PROJ.rglob('*'):
        if p.is_file() and (p.suffix in ('.md', '.py', '.ipynb')):
            print(p.relative_to(ROOT).as_posix())
elif mode == 'status':
    print(subprocess.run(['git', 'status', '--short'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout)
    for rel in ('AGENTS.md', 'INDEX.md', '05-internal-materials/vocational-planning/README.md',
                '05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',
                '05-internal-materials/vocational-planning/03_X课程项目/X课程开发计划-v4.md'):
        print('\nFILE ' + rel)
        for i, line in enumerate((ROOT/rel).read_text(encoding='utf-8').splitlines(), 1):
            if ('U4' in line or 'U5' in line) and (i < 260 or rel == 'INDEX.md'):
                print(f'{i}: {line}')
elif mode == 'apply':
    import runpy
    runpy.run_path(str(Path(__file__).parent / 'revise_courses.py'), run_name='__main__')
elif mode == 'find':
    target = ROOT / sys.argv[2]
    lines = target.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if re.search(sys.argv[3], line):
            print('\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-2), min(len(lines),i+4))))
elif mode == 'fetch':
    urls = [PREFIX + p for p in PAGES] if len(sys.argv) == 2 else sys.argv[2:]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(fetch, urls):
            print(json.dumps(result, ensure_ascii=False))
elif mode == 'read':
    for rel in sys.argv[2:]:
        target = ROOT / rel
        print('\nFILE ' + rel)
        if target.suffix == '.ipynb':
            for i, c in enumerate(json.loads(target.read_text(encoding='utf-8'))['cells'], 1):
                print(f'\nCELL {i} {c["cell_type"]}\n' + ''.join(c['source']))
        else:
            print(target.read_text(encoding='utf-8'))
elif mode == 'cells':
    target = PROJ / 'notebooks' / sys.argv[2]
    cells = json.loads(target.read_text(encoding='utf-8'))['cells']
    start, end = map(int, sys.argv[3:5])
    for i, c in enumerate(cells, 1):
        if start <= i <= end:
            print(f'\nCELL {i} {c["cell_type"]}\n' + ''.join(c['source']))
elif mode == 'lines':
    target = ROOT / sys.argv[2]
    start, end = map(int, sys.argv[3:5])
    for i, line in enumerate(target.read_text(encoding='utf-8').splitlines(), 1):
        if start <= i <= end:
            print(f'{i}: {line}')
