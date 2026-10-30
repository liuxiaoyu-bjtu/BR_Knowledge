from pathlib import Path
import json,subprocess,re
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent;P=R/'05-internal-materials/vocational-planning/03_X课程项目'
assert not subprocess.check_output(['git','diff','--cached','--name-only']).strip(),'已有暂存项，先核对归属'

def put(rel, data):
    # 所有写入均是本地Git对象与精确指定的索引项，不推送。
    blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=data).decode().strip()
    subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,rel],check=True)

selected=set(json.loads((T/'学材变更清单.json').read_text(encoding='utf-8'))['files'])
selected.add((P/'notebooks/U5-L2/U5-L2_语音合成.ipynb').relative_to(R).as_posix())
selected.add((P/'notebooks/_外挂附件清单.md').relative_to(R).as_posix())
selected.add((T/'发放副本核对.json').relative_to(R).as_posix())
for code in ['U4-L1','U5-L1','U5-L2','U5-L3']:
    selected.add(next((P/'教学设计').glob(code+'*')).relative_to(R).as_posix())
    selected.add(next((P/'PPT内容设计').glob(code+'*_PPT内容大纲.md')).relative_to(R).as_posix())
    selected.add(next((P/'PPT').glob(code+'*_Codex审查版.pptx')).relative_to(R).as_posix())
for code in ['U4-L2','U4-L3','U4-L4']:
    selected.add(next((P/'教学设计').glob(code+'*')).relative_to(R).as_posix())
src=P/'PPT/U4L1_U5L1-L3_Codex源文件'
for name in ['build.py','content.py','manifest.json','README.md','U4-L1_U5-L1-L3_P5交付检查记录.md']:
    selected.add((src/name).relative_to(R).as_posix())
for f in list(src.glob('*_page-map.json'))+list(src.glob('*_成品文字提取.md')):
    selected.add(f.relative_to(R).as_posix())
for f in [P/'实验验证/全课学习评价补齐与U4后三课P3覆盖记录.md',P/'实验验证/U4-L2-L3-L4_P2复核与定稿记录.md',P/'PPT内容设计/U4-L1_U5-L1-L3_P4覆盖检查记录.md']:
    selected.add(f.relative_to(R).as_posix())
for name in ['补齐学材.py','编写U4教学设计.py','同步四课教案课件.py','同步记录.py','离线核查.py','离线核查结果.json','课件结构校验.json','课件导出检查.ps1','暂存本轮.py','完成记录.md']:
    selected.add((T/name).relative_to(R).as_posix())
for f in [T/'qa-render/bounds.json']+list((T/'qa-render').glob('*-contact.jpg')):
    selected.add(f.relative_to(R).as_posix())
for code,number in [('U4-L1',26),('U5-L1',27),('U5-L2',27),('U5-L3',27)]:
    selected.add((T/'qa-render'/code/f'slide-{number:02}.png').relative_to(R).as_posix())

partial=[]
for rel in sorted(selected):
    f=R/rel
    if f.name=='U6-L3_视频动作训练.ipynb':
        # 保留用户已在工作区重开发的17格稿，只暂存本轮检查点格式。
        head=json.loads(subprocess.check_output(['git','show','HEAD:'+rel]))
        changed=0
        for c in head['cells']:
            if c['cell_type']!='markdown':continue
            s=''.join(c['source'])
            def fmt(m):return m.group(1)+re.sub(r'(?m)^- (?!\[__\])','- [__] ',m.group(2))
            new=re.sub(r'(^### [^\n]*检查点[^\n]*\n)([\s\S]*?)(?=\n### |\Z)',fmt,s,flags=re.M)
            if s!=new:c['source']=new.splitlines(keepends=True);changed+=1
        assert changed==1
        data=(json.dumps(head,ensure_ascii=False,indent=1)+'\n').encode('utf-8')
        target=T/'head-increment'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);partial.append(rel)
    elif f.name=='_外挂附件清单.md':
        data=(T/'head-increment'/rel).read_bytes();partial.append(rel)
    else:
        data=f.read_bytes()
        if f.suffix in ('.md','.json','.py','.ipynb','.ps1'):data=data.replace(b'\r\n',b'\n')
    put(rel,data)

for rel in json.loads((T/'共享文件清单.json').read_text(encoding='utf-8')):
    put(rel,(T/'head-increment'/rel).read_bytes().replace(b'\r\n',b'\n'));partial.append(rel);selected.add(rel)

(T/'暂存文件清单.json').write_text(json.dumps({'files':sorted(selected),'partial':partial},ensure_ascii=False,indent=2),encoding='utf-8')
print('精确暂存',len(selected),'项；共享文档及U6-L3使用本轮增量。')
