import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const require = createRequire('C:/Users/yujie/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/placeholder.js');
const { instance } = require('@viz-js/viz');
const { chromium } = require('playwright');
const { marked } = await import(pathToFileURL(require.resolve('marked')).href);
const root = path.resolve(import.meta.dirname, '../..');
const out = path.join(root, '05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划');
const figures = path.join(out, '图示');
const qa = path.join(import.meta.dirname, 'qa');
const htmlOnly = process.argv.includes('--html-only');
fs.mkdirSync(qa, { recursive: true });
const viz = await instance();
for (const name of fs.readdirSync(figures).filter(n => !htmlOnly && n.endsWith('.dot'))) {
  const source = fs.readFileSync(path.join(figures, name), 'utf8');
  const result = viz.render(source, { format: 'svg', engine: 'dot' });
  if (result.status !== 'success') throw new Error(JSON.stringify(result.errors));
  if (result.errors.length) process.stdout.write(name + ': ' + JSON.stringify(result.errors) + '\n');
  fs.writeFileSync(path.join(figures, name.replace('.dot', '.svg')), result.output);
}
const mdfile = path.join(out, 'K1足球全流程_OSSDK策划案.md');
const source = fs.readFileSync(mdfile, 'utf8');
let content = marked.parse(source);
content = content.replace(/<img src="([^"]+)" alt="([^"]*)">/g, (_, src, alt) => {
  const svg = fs.readFileSync(path.join(out, decodeURI(src)), 'utf8').replace(/<\?xml[^>]+>/, '').replace(/<!DOCTYPE[\s\S]+?>/, '');
  return `<figure><a href="${src}" target="_blank" title="打开矢量原图">${svg}</a><figcaption>${alt} · 点击打开矢量图</figcaption></figure>`;
});
const headings = [];
content = content.replace(/<h2>(.*?)<\/h2>/g, (_, title) => {const id = 'section-' + headings.length; headings.push({id,title}); return `<h2 id="${id}">${title}</h2>`;});
const html = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>K1足球全流程与OS SDK课程应用策划案</title><style>
:root{color-scheme:light;--ink:#203b50;--blue:#245780;--line:#d9e4ec}*{box-sizing:border-box}body{margin:0;background:#f3f6f9;color:#253b4a;font-family:"Microsoft YaHei","Segoe UI",sans-serif;font-size:15px;line-height:1.85}aside{position:fixed;inset:0 auto 0 0;width:246px;padding:30px 20px;background:#153c57;color:white;overflow:auto}aside h3{font-size:20px;line-height:1.5;margin:0 0 20px}aside p{font-size:12px;color:#c4dae8}aside a{display:block;color:#dceaf3;text-decoration:none;padding:7px 0;font-size:13px;line-height:1.5}main{margin:24px 30px 50px 272px;padding:38px 45px;background:white;border:1px solid var(--line);max-width:1420px}h1{font-size:30px;line-height:1.45;color:var(--ink);margin-top:0}h2{font-size:23px;color:var(--blue);margin-top:50px;padding-bottom:9px;border-bottom:2px solid #e7eef4;scroll-margin:20px}h3{font-size:18px;color:#306e6a;margin-top:28px}p{margin:14px 0}a{color:#21638a}code{font-family:Consolas,monospace;background:#eef3f7;padding:2px 4px;font-size:.92em}pre{background:#122c3d;color:#e4f0f8;border-radius:5px;padding:18px;overflow:auto;line-height:1.65}pre code{background:none;padding:0}table{border-collapse:collapse;width:100%;font-size:13px;margin:20px 0;line-height:1.75}th,td{border:1px solid var(--line);padding:10px 12px;vertical-align:top;overflow-wrap:anywhere}th{background:#eaf1f7;text-align:left;color:#204766}tbody tr:nth-child(even){background:#f8fbfd}figure{margin:24px 0;background:#fff;border:1px solid var(--line);padding:18px;overflow:auto;text-align:center}figure svg{width:auto;max-width:100%;height:auto;max-height:none}figcaption{font-size:12px;color:#587080;padding:10px}.badge{padding:10px 15px;background:#fff4dc;border-left:4px solid #c89025;margin-bottom:20px;font-size:13px}@media(max-width:1000px){aside{position:static;width:auto}aside nav{display:none}main{margin:15px;padding:22px;max-width:none}table{font-size:12px}}@media print{aside{display:none}main{margin:0;border:0;padding:0}figure{break-inside:avoid}h2,h3{break-after:avoid}}
</style><aside><h3>K1足球应用<br>OS SDK策划案</h3><p>2026-11-02初版<br>2026-11-03补充复核<br>设计与离线程序草案</p><nav>${headings.map(h=>`<a href="#${h.id}">${h.title}</a>`).join('')}</nav><p>标准流程图 · 模块框架 · 状态转换<br>配套 k1_soccer.py</p></aside><main><div class="badge">尚未进行本方案真机验证。第17节补充策略比较、可选JSON、SDK封装分工与开发者案例。</div>${content}</main></html>`;
const htmlfile = mdfile.replace('.md', '.html');
fs.writeFileSync(htmlfile, html);
const browser = await chromium.launch({ headless:true, executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' });
const page = await browser.newPage({ viewport:{width:1600,height:1000}, deviceScaleFactor:1.5 });
for (const name of fs.readdirSync(figures).filter(n=>!htmlOnly && n.endsWith('.svg'))) {
  const svg = fs.readFileSync(path.join(figures,name),'utf8');
  await page.setContent(`<style>body{margin:0;padding:15px;background:white}svg{display:block;max-width:1500px;width:auto;height:auto}</style>${svg}`);
  await page.locator('svg').screenshot({path:path.join(figures,name.replace('.svg','.png'))});
}
await page.goto(pathToFileURL(htmlfile).href);
await page.screenshot({path:path.join(qa,'策划案首页.png')});
await page.locator('#section-6').scrollIntoViewIfNeeded();
await page.screenshot({path:path.join(qa,'图示章节.png')});
await page.locator('#section-16').scrollIntoViewIfNeeded();
await page.screenshot({path:path.join(qa,'补充复核.png')});
const check = await page.evaluate(() => ({scrollWidth:document.documentElement.scrollWidth, innerWidth:innerWidth, figures:document.querySelectorAll('figure svg').length, tables:document.querySelectorAll('table').length, title:document.title}));
fs.writeFileSync(path.join(qa,'render.json'), JSON.stringify(check,null,2));
await browser.close();
process.stdout.write(JSON.stringify(check) + '\n');
