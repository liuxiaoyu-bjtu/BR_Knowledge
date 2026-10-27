"""抓取用户指定SDK站的运动接口和相关页面；只读取网页。"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import urllib.request

TASK = Path(__file__).resolve().parent
OUT = TASK / 'sdk-evidence'
BASE = 'https://docs.booster.tech'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
        self.text = []
        self.article = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.links.add(attrs['href'])
        if tag == 'article':
            self.article = True
        if self.article and tag in ['p', 'li', 'h1', 'h2', 'h3', 'tr', 'br', 'pre', 'div']:
            self.text.append('\n')
    def handle_endtag(self, tag):
        if tag == 'article':
            self.article = False
    def handle_data(self, data):
        if self.article:
            self.text.append(data)


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read().decode('utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    overview = BASE + '/zh-CN/docs/developer-guide/booster-os-python-sdk/sdk-overview/'
    raw = fetch(overview)
    nav = Page()
    nav.feed(raw)
    (OUT / 'sdk-overview.html').write_text(raw, encoding='utf-8')
    relevant = sorted({BASE + u if u.startswith('/') else u for u in nav.links
                       if '/booster-os-python-sdk/' in u and '#' not in u})
    if not relevant:
        raise RuntimeError('官方入口未返回SDK导航，请保留返回内容并核实站点状态。')
    seeds = [u for u in relevant if any(x in u for x in [
        '/motion-control-apis/overview/', '/advanced-task-apis/overview/',
        '/sensor-and-state-snapshot-apis/get-image/'])]
    seed_content = {}
    for url in seeds:
        content = fetch(url)
        seed_content[url] = content
        page = Page()
        page.feed(content)
        relevant.extend(BASE + u if u.startswith('/') else u for u in page.links
                        if '/booster-os-python-sdk/' in u and '#' not in u)
    relevant = sorted(set(relevant))
    (OUT / 'sdk-urls.json').write_text(json.dumps(relevant, ensure_ascii=False, indent=2), encoding='utf-8')
    print('SDK中文页面数', len(relevant))
    candidates = [u for u in relevant if re.search(r'(velocity|odom|move|walk|motion|navigate|trajectory|booster-robot/|booster-robot-client-reference/$)', u)]
    for url in candidates:
        print(url)
    selected = [overview] + seeds + [u for u in relevant if any(f'/{part}/' in u for part in
                ['set-velocity', 'get-odom', 'reset-odom', 'booster-robot', 'task-handle',
                 'odom-state', 'do-action', 'set-head-angle'])]
    records = []
    for index, url in enumerate(selected):
        raw = seed_content[url] if url in seed_content else fetch(url)
        page = Page()
        page.feed(raw)
        stem = f'{index:02d}-' + url.rstrip('/').rsplit('/', 1)[-1]
        text = re.sub(r'\n[ \t]*\n+', '\n\n', ''.join(page.text)).strip()
        (OUT / f'{stem}.txt').write_text(url + '\n\n' + text + '\n', encoding='utf-8')
        records.append({'url': url, 'text_file': f'{stem}.txt', 'links': sorted(page.links)})
        print('SAVED', stem, len(text))
    (OUT / 'pages.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
