import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire('C:/Users/yujie/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/placeholder.js');
const {chromium}=require('playwright');
const dir=path.resolve(import.meta.dirname,'../../05-internal-materials/vocational-planning/03_X课程项目/实验验证/OSSDK足球全流程策划/图示');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage();
const report=[];
for(const name of fs.readdirSync(dir).filter(n=>n.endsWith('.svg'))){
 await page.setContent(fs.readFileSync(path.join(dir,name),'utf8'));
 const result=await page.evaluate(()=>{
  const nodes=[];const overflow=[];const edgeOverlap=[];
  for(const node of document.querySelectorAll('g.node')){
   const shapes=[...node.querySelectorAll('polygon,ellipse,path')].map(e=>e.getBBox());
   if(!shapes.length)continue;
   const x=Math.min(...shapes.map(b=>b.x)),y=Math.min(...shapes.map(b=>b.y));
   const right=Math.max(...shapes.map(b=>b.x+b.width)),bottom=Math.max(...shapes.map(b=>b.y+b.height));
   const title=node.querySelector('title').textContent;
   nodes.push({title,x,y,right,bottom});
   for(const text of node.querySelectorAll('text')){
    const b=text.getBBox();
    if(b.x<x-2||b.x+b.width>right+2||b.y<y-3||b.y+b.height>bottom+3)overflow.push({node:title,text:text.textContent});
   }
  }
  for(const edge of document.querySelectorAll('g.edge'))for(const text of edge.querySelectorAll('text')){
   const b=text.getBBox();
   for(const n of nodes){
    const ox=Math.min(b.x+b.width,n.right)-Math.max(b.x,n.x);
    const oy=Math.min(b.y+b.height,n.bottom)-Math.max(b.y,n.y);
    if(ox>10&&oy>5)edgeOverlap.push({edge:edge.querySelector('title').textContent,node:n.title,text:text.textContent});
   }
  }
  return {overflow,edgeOverlap};
 });report.push({file:name,...result});
}
fs.writeFileSync(path.join(import.meta.dirname,'qa','diagram-bounds.json'),JSON.stringify(report,null,2));
process.stdout.write(JSON.stringify(report,null,2));await browser.close();
