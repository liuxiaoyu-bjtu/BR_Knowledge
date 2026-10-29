from pathlib import Path
import json
import pprint

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PROJECT = ROOT / '05-internal-materials/vocational-planning/03_X课程项目'
added = []
for number, prefix in [(15, 'U4-L3'), (16, 'U4-L4')]:
    path = next((PROJECT / 'notebooks').glob(prefix + '_*.ipynb'))
    nb = json.loads(path.read_text(encoding='utf-8'))
    for i, cell in enumerate(nb['cells'], 1):
        if not cell.get('id'):
            cell['id'] = f'{prefix.lower()}-cell-{i:02}'
            added.append([path.name, i, cell['id']])
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gen = PROJECT / f'_gen_L{number}.py'
    source = ('# -*- coding: utf-8 -*-\n'
              '"""Notebook完整镜像；重跑前核对学生稿与用户执行记录。"""\n'
              'import json\nfrom pathlib import Path\nNOTEBOOK = '
              + pprint.pformat(nb, width=110, sort_dicts=False)
              + '\nif __name__ in ("__main__", "__gen__"):\n'
              + '    path = Path(__file__).parent / "notebooks" / ' + repr(path.name) + '\n'
              + '    path.write_text(json.dumps(NOTEBOOK, ensure_ascii=False, indent=1)+"\\n", encoding="utf-8")\n')
    gen.write_text(source, encoding='utf-8')
(TASK / '新增cellID.json').write_text(json.dumps(added, ensure_ascii=False, indent=2), encoding='utf-8')
print('为U4两课补齐', len(added), '个cell ID；源代码、输出及既有元数据保留')
