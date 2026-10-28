from pathlib import Path
import hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[2]
TASK=Path(__file__).resolve().parent
CP=Path('05-internal-materials/vocational-planning/03_X课程项目')
LESSONS={'U5-L4':'语音会话管理','U6-L1':'动作的来源','U6-L2':'动作录制与回放','U6-L3':'视频动作训练','U6-L4':'动作编排'}
SHARED=['AGENTS.md','INDEX.md','CHANGELOG.md','05-internal-materials/vocational-planning/README.md','05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md',str(CP/'X课程当前进度.md'),str(CP/'X课程开发计划-v4.md'),str(CP/'实验验证/U5-L4_U6_P3教学设计覆盖检查记录.md')]
assert not (TASK/'输入指纹.json').exists()
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip(),'已有暂存，暂停处理'
paths=[ROOT/p for p in SHARED]
for key,title in LESSONS.items():
    paths+=list((ROOT/CP/'notebooks').glob(key+'_*.ipynb'))
    paths.append(ROOT/CP/'教学设计'/f'{key}_{title}_教学设计.md')
paths += [ROOT/CP/f'_gen_L{i}.py' for i in range(20,25)]
manifest={}
for p in paths:
    rel=p.relative_to(ROOT).as_posix(); raw=p.read_bytes()
    target=TASK/'before'/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    manifest[rel]=hashlib.sha256(raw).hexdigest()
    result=subprocess.run(['git','show','HEAD:'+rel],cwd=ROOT,capture_output=True)
    if result.returncode==0:
        out=TASK/'head'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(result.stdout)
(TASK/'输入指纹.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(TASK/'before'/'git-status.z').write_bytes(subprocess.check_output(['git','status','--porcelain','-z'],cwd=ROOT))
print('已保存',len(manifest),'份输入基线；暂存区为空')
