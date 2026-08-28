import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const root = "D:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/PPT";
const outDir = "D:/A_Project/BoosterRobotics/知识库/.codex-tmp/artifact-qa-u1-l234";
const decks = [
  `${root}/U1-L2_运行模式与安全_Codex方案二审查版.pptx`,
  `${root}/U1-L3_基本运动控制_Codex方案二审查版.pptx`,
  `${root}/U1-L4_头部步态与预定义动作_Codex方案二审查版.pptx`,
];

await fs.mkdir(outDir, { recursive: true });
for (const deck of decks) {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(deck));
  const name = deck.split("/").pop().replace(".pptx", "");
  const deckDir = `${outDir}/${name}`;
  await fs.mkdir(deckDir, { recursive: true });
  const inspect = await presentation.inspect({ kind: "slide,textbox,shape,table,notes", maxChars: 12000 });
  await fs.writeFile(`${outDir}/${name}.inspect.ndjson`, inspect.ndjson ?? String(inspect));
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(`${outDir}/${name}.webp`, new Uint8Array(await montage.arrayBuffer()));
  for (let i = 0; i < presentation.slides.items.length; i += 1) {
    const slide = presentation.slides.items[i];
    const png = await presentation.export({ slide, format: "png", scale: 1.5 });
    await fs.writeFile(`${deckDir}/slide-${String(i + 1).padStart(2, "0")}.png`, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${deckDir}/slide-${String(i + 1).padStart(2, "0")}.layout.json`, await layout.text());
  }
}
const layoutFiles = [];
for (const deck of decks) {
  const name = deck.split("/").pop().replace(".pptx", "");
  const dir = `${outDir}/${name}`;
  for (const file of await fs.readdir(dir)) if (file.endsWith(".layout.json")) layoutFiles.push(`${dir}/${file}`);
}
const bad = [];
for (const file of layoutFiles) {
  const layout = JSON.parse(await fs.readFile(file, "utf8"));
  for (const element of layout.elements ?? []) {
    const b = element.bbox;
    if (b && (b[0] < -1 || b[1] < -1 || b[0] + b[2] > 1281 || b[1] + b[3] > 721)) bad.push({ file, text: element.textPreview, bbox: b });
  }
}
console.log(`layout_files=${layoutFiles.length} out_of_bounds=${bad.length}`);
if (bad.length) console.log(JSON.stringify(bad.slice(0, 20), null, 2));
console.log(`QA imported ${decks.length} decks with artifact-tool`);
