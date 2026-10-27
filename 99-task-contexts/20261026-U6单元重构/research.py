"""读取正式示教、轨迹与动作接口，保存官方正文及链接。"""
from pathlib import Path
import importlib.util
import json
import re

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
helper = ROOT / '99-task-contexts/20261026-U4后续三课审核/research.py'
spec = importlib.util.spec_from_file_location('sdk_page_reader', helper)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
BASE = 'https://docs.booster.tech'
SDK = BASE + '/zh-CN/docs/developer-guide/booster-os-python-sdk/'


def main():
    dest = TASK / 'sdk-evidence'
    dest.mkdir(parents=True, exist_ok=True)
    old_links = json.loads((ROOT / '99-task-contexts/20261026-U4后续三课审核/sdk-evidence/sdk-urls.json').read_text(encoding='utf-8'))
    queue = [u for u in old_links if any(x in u for x in [
        '/hand-guiding-manager/overview/', '/advanced-task-apis/execute-trajectory/',
        '/advanced-task-apis/do-action/', '/tasks-and-subscriptions/task-handle/',
        '/trajectory-data/trajectory-meta/'])]
    done, pages = set(), []
    wanted = ['hand-guiding-manager/', '/trajectory-data/', '/task-status/',
              '/task-info/', '/list-actions/']
    while queue:
        url = queue.pop(0)
        if url in done:
            continue
        done.add(url)
        raw = reader.fetch(url)
        p = reader.Page()
        p.feed(raw)
        body = re.sub(r'\n[ \t]*\n+', '\n\n', ''.join(p.text)).strip()
        assert 'BoosterOS' in body and len(body) > 80, url
        name = f'{len(pages):02d}-' + url.rstrip('/').rsplit('/', 1)[-1] + '.txt'
        (dest / name).write_text(url + '\n\n' + body + '\n', encoding='utf-8')
        pages.append({'url': url, 'file': name, 'links': sorted(p.links)})
        for link in sorted(p.links):
            full = BASE + link if link.startswith('/') else link
            if full.startswith(SDK) and '#' not in full and any(x in full for x in wanted) and full not in done:
                queue.append(full)
        print(name, len(body))
    (dest / 'pages.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
