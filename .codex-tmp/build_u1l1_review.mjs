import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "D:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/PPT/U1-L1_具身智能概览与连接K1_Codex方案二审查版.pptx";
const PREVIEW_DIR = "D:/A_Project/BoosterRobotics/知识库/.codex-tmp/u1-l1-option2";

const W = 1280;
const H = 720;
const C = {
  white: "#FFFFFF",
  ink: "#17212B",
  body: "#344454",
  muted: "#6B7785",
  blue: "#2563EB",
  blue2: "#DBEAFE",
  blue3: "#EFF6FF",
  cyan: "#0EA5A4",
  cyan2: "#CCFBF1",
  amber: "#F59E0B",
  amber2: "#FFF7E6",
  red: "#E5484D",
  red2: "#FFF1F2",
  line: "#D8E0E8",
  soft: "#F4F6F9",
  darkBlue: "#123A7A",
};
const FONT = "Microsoft YaHei";
const MONO = "Consolas";

const pres = Presentation.create({ slideSize: { width: W, height: H } });
await fs.mkdir(PREVIEW_DIR, { recursive: true });

function addShape(slide, geometry, x, y, w, h, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
  });
}

function addText(slide, text, x, y, w, h, opts = {}) {
  const s = addShape(slide, "textbox", x, y, w, h, "none", "none", 0);
  s.text = text;
  s.text.style = {
    fontSize: opts.size ?? 18,
    color: opts.color ?? C.body,
    bold: opts.bold ?? false,
    fontFamily: opts.fontFamily ?? FONT,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    ...(opts.italic ? { italic: true } : {}),
  };
  return s;
}

function box(slide, text, x, y, w, h, opts = {}) {
  const s = addShape(slide, opts.geometry ?? "roundRect", x, y, w, h, opts.fill ?? C.soft, opts.line ?? opts.fill ?? C.soft, opts.lineWidth ?? 1);
  s.text = text;
  s.text.style = {
    fontSize: opts.size ?? 18,
    color: opts.color ?? C.body,
    bold: opts.bold ?? false,
    fontFamily: opts.fontFamily ?? FONT,
    alignment: opts.align ?? "center",
    verticalAlignment: opts.valign ?? "middle",
  };
  return s;
}

function line(slide, x1, y1, x2, y2, color = C.line, width = 2) {
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  const lineWidth = Math.abs(x2 - x1) || 1;
  const lineHeight = Math.abs(y2 - y1) || 1;
  const s = slide.shapes.add({
    geometry: "line",
    position: { left, top, width: lineWidth, height: lineHeight },
    fill: "none",
    line: { style: "solid", fill: color, width },
  });
  return s;
}

function arrow(slide, x, y, w, h, color = C.blue) {
  return addShape(slide, "rightArrow", x, y, w, h, color, color, 0);
}

function downArrow(slide, x, y, w, h, color = C.blue) {
  return addShape(slide, "downArrow", x, y, w, h, color, color, 0);
}

function sectionTag(slide, text, color = C.blue) {
  box(slide, text, 68, 30, Math.min(480, 24 + text.length * 15), 32, { fill: color, line: color, color: C.white, size: 13, bold: true });
}

function chrome(slide, n, section, title, subtitle, sectionColor = C.blue) {
  slide.background.fill = C.white;
  sectionTag(slide, section, sectionColor);
  addText(slide, title, 68, 82, 1140, 48, { size: 34, bold: true, color: C.ink });
  if (subtitle) addText(slide, `—— ${subtitle}`, 68, 132, 1140, 30, { size: 18, color: C.muted });
  line(slide, 68, 172, 1212, 172, C.line, 1);
  addText(slide, `${n} / 30`, 1130, 680, 82, 22, { size: 11, color: C.muted, align: "right" });
}

function notes(slide, sourceLines) {
  slide.speakerNotes.textFrame.setText(`[Sources]\n${sourceLines.map((x) => `- ${x}`).join("\n")}`);
  slide.speakerNotes.setVisible(true);
}

function bulletList(slide, items, x, y, w, size = 20, color = C.body, gap = 42) {
  items.forEach((item, i) => {
    addShape(slide, "ellipse", x, y + i * gap + 7, 10, 10, C.blue, C.blue, 0);
    addText(slide, item, x + 26, y + i * gap, w - 26, gap, { size, color });
  });
}

function stepRow(slide, num, title, desc, x, y, w, color = C.blue) {
  box(slide, String(num), x, y, 38, 38, { geometry: "ellipse", fill: color, line: color, color: C.white, size: 16, bold: true });
  addText(slide, title, x + 55, y - 2, w - 55, 27, { size: 17, bold: true, color: C.ink });
  addText(slide, desc, x + 55, y + 25, w - 55, 28, { size: 15, color: C.muted });
}

function codeBlock(slide, lines, x, y, w, h, highlights = [], accent = C.blue, accentSoft = C.blue3) {
  addShape(slide, "roundRect", x, y, w, h, C.soft, C.line, 1);
  addShape(slide, "rect", x, y, 9, h, accent, accent, 0);
  const lineH = 34;
  highlights.forEach((i) => addShape(slide, "rect", x + 10, y + 14 + i * lineH, w - 20, 28, accentSoft, accentSoft, 0));
  lines.forEach((t, i) => addText(slide, t || " ", x + 28, y + 12 + i * lineH, w - 48, 28, { size: 16, color: C.ink, fontFamily: MONO }));
}

function photoLikeFrame(slide, x, y, w, h, label, accent = C.blue) {
  addShape(slide, "roundRect", x, y, w, h, C.blue3, C.line, 1);
  addShape(slide, "rect", x, y + h - 8, w, 8, accent, accent, 0);
  addText(slide, label, x + 24, y + h / 2 - 38, w - 48, 76, { size: 18, color: C.darkBlue, bold: true, align: "center", valign: "middle" });
}

function smallLabel(slide, text, x, y, w, color = C.blue) {
  box(slide, text, x, y, w, 28, { fill: C.blue3, line: C.blue2, color, size: 13, bold: true });
}

// 1
{
  const s = pres.slides.add();
  s.background.fill = C.white;
  box(s, "第一堂人形机器人课", 72, 36, 190, 32, { fill: C.blue, line: C.blue, color: C.white, size: 13, bold: true });
  addText(s, "具身智能概览与连接 K1", 72, 200, 760, 70, { size: 46, bold: true, color: C.ink });
  addText(s, "—— 从数字大脑到会动的身体", 72, 280, 680, 36, { size: 22, color: C.muted });
  addShape(s, "rect", 72, 350, 110, 8, C.blue, C.blue, 0);
  addText(s, "单元 U1 · 人形机器人初探与运动控制", 72, 610, 500, 28, { size: 16, color: C.muted });
  addText(s, "课时 L1 · 主讲人：__________", 72, 642, 500, 28, { size: 15, color: C.muted });
  // editable hero silhouette: an abstract robot body, deliberately not a fake product photo
  box(s, "K1", 918, 194, 150, 78, { fill: C.blue, line: C.blue, color: C.white, size: 30, bold: true });
  line(s, 993, 273, 993, 316, C.blue, 5);
  box(s, "感知", 860, 320, 120, 52, { fill: C.blue3, line: C.blue, color: C.blue, size: 16, bold: true });
  box(s, "计算", 1005, 320, 120, 52, { fill: C.soft, line: C.line, color: C.body, size: 16, bold: true });
  line(s, 920, 372, 920, 420, C.line, 4); line(s, 1065, 372, 1065, 420, C.line, 4);
  box(s, "运动", 860, 425, 120, 52, { fill: C.blue3, line: C.blue2, color: C.darkBlue, size: 16, bold: true });
  box(s, "电源", 1005, 425, 120, 52, { fill: C.soft, line: C.line, color: C.body, size: 16, bold: true });
  addText(s, "可编辑结构示意", 890, 505, 205, 24, { size: 13, color: C.muted, align: "center" });
  addText(s, "1 / 30", 1130, 680, 82, 22, { size: 11, color: C.muted, align: "right" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：01-booster-kb/07-tech-platform/_tech-overview.md"]);
}

// 2
{
  const s = pres.slides.add(); chrome(s, 2, "导学", "本课目标", "一节课我们要带走什么");
  const ys = [250, 350, 450];
  const titles = ["认识具身智能", "连接一台 K1", "建立开发范式"];
  const desc = ["说清楚“数字大脑”和“有身体的智能”有什么不同。", "用 BoosterOS SDK 读取身份、关节、动作和状态信息。", "理解：电脑经网络连接实体机器人，SDK 提供程序接口。"];
  ys.forEach((y, i) => { box(s, String(i + 1), 120, y, 54, 54, { geometry: "ellipse", fill: C.blue, line: C.blue, color: C.white, size: 22, bold: true }); addText(s, titles[i], 210, y - 4, 320, 32, { size: 24, bold: true, color: C.ink }); addText(s, desc[i], 210, y + 34, 820, 34, { size: 17, color: C.body }); });
  addShape(s, "rect", 120, 540, 1020, 1, C.line, C.line, 0);
  addText(s, "今天先读懂、连上、看清楚；暂不下发运动指令。", 120, 570, 1020, 32, { size: 18, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/教学设计/U1-L1_具身智能概览与连接K1_教学设计.md"]);
}

// 3
{
  const s = pres.slides.add(); chrome(s, 3, "第一部分 · 初识具身智能", "机器人的“智能”在哪", "会算，还是会动？");
  photoLikeFrame(s, 730, 225, 440, 300, "短片画面\n展厅 · 足球 · 搬运", C.blue);
  addText(s, "先看一个任务：\n机器人把杯子稳稳送到指定位置。", 100, 250, 540, 110, { size: 25, bold: true, color: C.ink });
  box(s, "【想一想】\n它需要哪些能力？\n只会生成答案，够不够？", 100, 420, 540, 140, { fill: C.amber2, line: C.amber, color: C.body, size: 19, bold: true, align: "left", valign: "middle" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：03-cross-reference/theory-to-product.md"]);
}

// 4
{
  const s = pres.slides.add(); chrome(s, 4, "第一部分 · 初识具身智能", "什么是具身智能", "从数字大脑到会动的身体");
  addText(s, "智能不只存在于模型里，也存在于身体与环境的真实交互中。", 100, 220, 1080, 42, { size: 25, bold: true, color: C.ink, align: "center" });
  const cols = [100, 475, 850];
  ["离身智能", "具身智能", "课堂中的 K1"].forEach((t, i) => box(s, t, cols[i], 315, 280, 48, { fill: i === 1 ? C.blue : C.soft, line: i === 1 ? C.blue : C.line, color: i === 1 ? C.white : C.ink, size: 19, bold: true }));
  box(s, "屏幕中的模型\n擅长计算、生成、推理", 100, 390, 280, 120, { fill: C.soft, line: C.line, color: C.body, size: 18 });
  box(s, "身体 + 感知 + 行动\n在环境中完成任务", 475, 390, 280, 120, { fill: C.blue3, line: C.blue2, color: C.darkBlue, size: 18, bold: true });
  box(s, "K1\n有芯片、有系统、能被编程", 850, 390, 280, 120, { fill: C.blue3, line: C.blue, color: C.blue, size: 18, bold: true });
  addText(s, "关键区别：能否通过身体感知世界，并用行动改变世界。", 100, 570, 1080, 30, { size: 18, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：02-embodied-ai-edu/01-theory/what-is-embodied-ai-edu.md"]);
}

// 5 timeline
{
  const s = pres.slides.add(); chrome(s, 5, "第一部分 · 初识具身智能", "智能是怎么一步步“长”出来的", "四段发展脉络一览");
  const xs = [90, 370, 650, 930];
  const names = ["符号智能", "行为主义与机器人学", "深度学习赋能感知", "大模型与 VLA"];
  const years = ["1950s–1980s", "1980s–2000s", "2010s", "2020s 至今"];
  const means = ["智能 = 符号推理", "感知—行动闭环", "看得清、听得懂", "看—想—动一体"];
  xs.forEach((x, i) => { if (i < 3) arrow(s, x + 230, 345, 36, 28, C.blue); box(s, `${names[i]}\n${years[i]}\n\n${means[i]}`, x, 290, 220, 160, { fill: i === 3 ? C.blue3 : C.soft, line: i === 3 ? C.blue2 : C.line, color: C.ink, size: 17, bold: i === 3 }); });
  addText(s, "每一次进步，都让机器人更接近“理解环境并采取行动”。", 90, 520, 1080, 34, { size: 20, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

function developmentSlide(n, title, subtitle, period, key, side, accent) {
  const s = pres.slides.add(); chrome(s, n, "第一部分 · 初识具身智能", title, subtitle, accent);
  smallLabel(s, period, 95, 230, 170, accent);
  addText(s, key, 95, 290, 530, 160, { size: 25, bold: true, color: C.ink });
  addText(s, side, 95, 470, 530, 70, { size: 18, color: C.body });
  photoLikeFrame(s, 745, 220, 395, 300, "概念图示\n可替换为课堂配图", accent);
  addText(s, "这一阶段留下的关键词", 745, 550, 395, 26, { size: 15, color: C.muted, align: "center" });
  box(s, title.split("·")[1]?.trim() ?? title, 805, 580, 275, 42, { fill: accent === C.amber ? C.amber2 : C.blue3, line: accent, color: accent, size: 17, bold: true });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}
developmentSlide(6, "发展一 · 符号智能", "把智能当作“推理”", "1950s–1980s", "早期人工智能把智能理解为符号推理。\n机器人按固定程序执行任务，尚不具备自主学习能力。", "代表人物：Newell & Simon\n认识重点：规则能解决什么，不能解决什么。", C.blue);
developmentSlide(7, "发展二 · 行为主义与机器人学", "让机器人“感知—行动”", "1980s–2000s", "机器人开始进入真实环境：\n边感知、边行动，用反馈形成闭环。", "代表思路：Brooks 的“无表征”\n认识重点：身体和环境进入智能系统。", C.blue);
developmentSlide(8, "发展三 · 深度学习赋能感知", "机器人终于“看得清”", "2010s", "视觉与语音识别能力快速提升，\n机器人开始更可靠地识别环境和人的指令。", "代表突破：AlexNet\n认识重点：感知能力是行动的入口。", C.blue);
developmentSlide(9, "发展四 · 大模型与 VLA", "看、想、动连成一体", "2020s 至今", "大模型提供更强的通用推理，\nVLA 尝试把视觉、语言和动作连接起来。", "代表方向：PaLM-E、RT-2\n认识重点：从单点能力走向任务级行为。", C.blue);

// 10
{
  const s = pres.slides.add(); chrome(s, 10, "第二部分 · 研究重心与方向", "今天的研究往哪用力", "既要开眼界，也要能上手");
  box(s, "前沿方向", 120, 240, 460, 52, { fill: C.blue, line: C.blue, color: C.white, size: 22, bold: true });
  addText(s, "VLN · VLA · 世界模型", 120, 330, 460, 42, { size: 27, bold: true, color: C.ink, align: "center" });
  addText(s, "回答：智能如何理解更复杂的环境与任务？", 120, 400, 460, 55, { size: 18, color: C.body, align: "center" });
  box(s, "应用方向", 700, 240, 460, 52, { fill: C.darkBlue, line: C.darkBlue, color: C.white, size: 22, bold: true });
  addText(s, "机器人操作 · 运动控制 · 手眼协调", 700, 330, 460, 42, { size: 23, bold: true, color: C.ink, align: "center" });
  addText(s, "回答：智能如何稳定地完成真实任务？", 700, 400, 460, 55, { size: 18, color: C.body, align: "center" });
  line(s, 580, 330, 700, 330, C.line, 3); arrow(s, 620, 316, 44, 28, C.blue);
  addText(s, "方向不同，问题相同：让机器人更好地理解并行动。", 120, 545, 1040, 34, { size: 19, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/教学设计/U1-L1_具身智能概览与连接K1_教学设计.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

function researchSlide(n, title, subtitle, desc, flow, accent) {
  const s = pres.slides.add(); chrome(s, n, "第二部分 · 研究重心与方向", title, subtitle, accent);
  addText(s, desc, 100, 230, 490, 100, { size: 23, bold: true, color: C.ink });
  flow.forEach((f, i) => { const x = 710 + (i % 2) * 190; const y = 245 + Math.floor(i / 2) * 110; box(s, f, x, y, 150, 60, { fill: i === flow.length - 1 ? accent : C.blue3, line: i === flow.length - 1 ? accent : C.blue2, color: i === flow.length - 1 ? C.white : C.darkBlue, size: 17, bold: true }); if (i < flow.length - 1) { if (i % 2 === 0) arrow(s, x + 155, y + 16, 30, 24, accent); else downArrow(s, x + 62, y + 68, 24, 28, accent); } });
  addText(s, "核心问题", 100, 390, 150, 28, { size: 15, color: accent, bold: true });
  addText(s, desc.replace("：", "：\n"), 100, 430, 520, 100, { size: 18, color: C.body });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}
researchSlide(11, "前沿一 · 视觉语言导航 VLN", "听懂“去那边把杯子拿来”", "语言 + 环境 + 路径", ["语言指令", "看见环境", "规划路径", "到达目标"], C.blue);
researchSlide(12, "前沿二 · 视觉语言动作 VLA", "看见画面，直接输出动作", "画面 + 指令 → 动作", ["图像", "语言", "模型推理", "动作序列"], C.blue);
researchSlide(13, "前沿三 · 世界模型", "在脑内先“演一遍”", "预测行动后果", ["当前状态", "假设动作", "预测结果", "选择行动"], C.blue);

function applicationSlide(n, title, subtitle, desc, accent, visual) {
  const s = pres.slides.add(); chrome(s, n, "第二部分 · 研究重心与方向", title, subtitle, accent);
  addText(s, desc, 100, 225, 1080, 42, { size: 24, bold: true, color: C.ink, align: "center" });
  box(s, visual[0], 120, 345, 240, 110, { fill: C.blue3, line: accent, color: C.darkBlue, size: 19, bold: true });
  arrow(s, 390, 385, 45, 28, accent);
  box(s, visual[1], 470, 345, 240, 110, { fill: C.soft, line: C.line, color: C.body, size: 19, bold: true });
  arrow(s, 740, 385, 45, 28, accent);
  box(s, visual[2], 820, 345, 240, 110, { fill: accent, line: accent, color: C.white, size: 19, bold: true });
  addText(s, "应用方向的共同目标：让感知结果真正转化为稳定动作。", 120, 535, 1040, 32, { size: 18, color: accent, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：03-cross-reference/theory-to-product.md"]);
}
applicationSlide(14, "应用一 · 机器人操作", "稳稳抓放、精准装配", "让机器人把“看见目标”变成“完成操作”。", C.blue, ["识别目标", "规划抓取", "稳定放置"]);
applicationSlide(15, "应用二 · 运动控制", "在不平地面站稳走好", "让机器人在运动中保持姿态、速度与方向。", C.blue, ["读取状态", "调整速度", "稳定行走"]);
applicationSlide(16, "应用三 · 手眼协调", "眼睛看到的，实时修正手的动作", "让视觉反馈持续修正动作误差。", C.blue, ["视觉反馈", "误差判断", "动作修正"]);

// 17
{
  const s = pres.slides.add(); chrome(s, 17, "第三部分 · 认识 K1 与开发工具", "回到我们手边的这台 K1", "它到底由什么组成？");
  addText(s, "前面认识了“智能”与“研究方向”。\n现在回到一台真实的人形机器人：K1。", 110, 270, 650, 130, { size: 28, bold: true, color: C.ink });
  box(s, "它的身体由哪些系统组成？", 110, 470, 580, 72, { fill: C.blue3, line: C.blue2, color: C.darkBlue, size: 22, bold: true });
  box(s, "K1", 870, 260, 180, 80, { fill: C.blue, line: C.blue, color: C.white, size: 30, bold: true });
  line(s, 960, 340, 960, 390, C.blue, 5);
  box(s, "感知", 820, 410, 130, 52, { fill: C.blue3, line: C.blue, color: C.blue, size: 18, bold: true });
  box(s, "计算", 970, 410, 130, 52, { fill: C.blue3, line: C.blue, color: C.blue, size: 18, bold: true });
  box(s, "运动", 820, 485, 130, 52, { fill: C.blue3, line: C.blue2, color: C.darkBlue, size: 18, bold: true });
  box(s, "电源", 970, 485, 130, 52, { fill: C.soft, line: C.line, color: C.body, size: 18, bold: true });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 18
{
  const s = pres.slides.add(); chrome(s, 18, "第三部分 · 认识 K1 与开发工具", "人形机器人的系统组成", "感知、计算、运动、电源");
  box(s, "K1 人形机器人", 515, 220, 250, 62, { fill: C.blue, line: C.blue, color: C.white, size: 22, bold: true });
  const items = [[100, 390, "感知子系统", "相机 · IMU\n获取环境与姿态信息", C.blue3, C.blue], [400, 390, "计算子系统", "机载算力\n处理数据与任务逻辑", C.soft, C.line], [700, 390, "运动子系统", "关节 · 电机\n把指令变成动作", C.blue3, C.darkBlue], [1000, 390, "电源子系统", "电池 · 供电\n让系统持续运行", C.soft, C.line]];
  items.forEach(([x, y, t, d, f, lc]) => { line(s, 640, 282, x + 105, y, lc, 3); box(s, `${t}\n${d}`, x, y, 210, 125, { fill: f, line: lc, color: C.ink, size: 17, bold: true }); });
  addText(s, "四个子系统协同，才形成完整的感知—决策—行动链路。", 110, 585, 1060, 32, { size: 19, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：01-booster-kb/02-products/booster-k1.md"]);
}

// 19
{
  const s = pres.slides.add(); chrome(s, 19, "第三部分 · 认识 K1 与开发工具", "走近 K1（一）", "外观、硬件与“身体参数”");
  photoLikeFrame(s, 760, 220, 350, 330, "K1 全身实拍\n建议替换为公司产品图", C.blue);
  addText(s, "Booster Robot 公司的人形机器人", 100, 230, 560, 38, { size: 26, bold: true, color: C.ink });
  bulletList(s, ["约 1.3 m 级人形机器人", "22 个关节自由度", "头部相机、IMU 等传感器", "有芯片、有操作系统 BoosterOS"], 120, 315, 570, 20);
  box(s, "身体参数不是“背诵题”\n它们决定了程序可以读取和控制什么。", 100, 500, 560, 82, { fill: C.blue3, line: C.blue2, color: C.darkBlue, size: 18, bold: true, align: "left" });
  notes(s, ["知识库：01-booster-kb/02-products/booster-k1.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 20
{
  const s = pres.slides.add(); chrome(s, 20, "第三部分 · 认识 K1 与开发工具", "走近 K1（二）", "它能做什么，我们能对它做什么");
  addText(s, "今天的任务是“只读认识”", 100, 235, 550, 40, { size: 28, bold: true, color: C.ink });
  const rows = [["连接", "让电脑找到这台 K1", C.blue3], ["读取", "查看身份、关节、动作与状态", C.soft], ["理解", "把返回数据和机器人身体对应起来", C.blue3]];
  rows.forEach(([a, b, f], i) => { box(s, a, 120, 335 + i * 78, 120, 52, { fill: f, line: C.line, color: C.ink, size: 19, bold: true }); addText(s, b, 275, 345 + i * 78, 420, 30, { size: 19, color: C.body }); });
  box(s, "本课不下发运动指令\n先建立“我连的是谁、我读到了什么”的工程习惯。", 760, 300, 350, 170, { fill: C.red2, line: C.red, color: C.red, size: 20, bold: true });
  addText(s, "看清楚，再动手。", 760, 520, 350, 34, { size: 22, color: C.red, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb"]);
}

// 21
{
  const s = pres.slides.add(); chrome(s, 21, "第三部分 · 认识 K1 与开发工具", "怎么用一行代码让它“听话”", "从手动到程序控制");
  addText(s, "看完了“身体”，下一步是找到程序入口。", 120, 255, 1040, 40, { size: 28, bold: true, color: C.ink, align: "center" });
  box(s, "人手操作", 170, 390, 230, 76, { fill: C.soft, line: C.line, color: C.body, size: 23, bold: true });
  arrow(s, 440, 414, 80, 28, C.blue);
  box(s, "程序接口", 540, 390, 230, 76, { fill: C.blue3, line: C.blue, color: C.blue, size: 23, bold: true });
  arrow(s, 810, 414, 80, 28, C.blue);
  box(s, "机器人行动", 900, 390, 230, 76, { fill: C.blue3, line: C.blue, color: C.blue, size: 23, bold: true });
  addText(s, "SDK 把复杂的通信与设备能力，整理成可以调用的程序接口。", 150, 535, 980, 34, { size: 19, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 22
{
  const s = pres.slides.add(); chrome(s, 22, "第三部分 · 认识 K1 与开发工具", "SDK 是什么", "操作机器人的“说明书 + 钥匙”");
  box(s, "BoosterRobot\n统一入口", 505, 220, 270, 72, { fill: C.blue, line: C.blue, color: C.white, size: 22, bold: true });
  const xs = [120, 510, 900];
  const vals = [["robot_info", "读身份", C.blue3, C.blue], ["list_joints()", "读身体清单", C.soft, C.blue], ["list_actions()", "读动作库", C.blue3, C.blue]];
  vals.forEach(([a, b, f, lc], i) => { downArrow(s, 625, 305, 28, 55, lc); box(s, `${a}\n${b}`, xs[i], 390, 260, 100, { fill: f, line: lc, color: C.ink, size: 18, bold: true }); });
  addText(s, "先通过统一入口读取信息，再决定下一步怎么开发。", 110, 555, 1060, 34, { size: 19, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 23
{
  const s = pres.slides.add(); chrome(s, 23, "第三部分 · 认识 K1 与开发工具", "K1 与电脑怎么连上", "无线 / 有线两种方式");
  box(s, "无线方式", 95, 220, 470, 48, { fill: C.blue, line: C.blue, color: C.white, size: 20, bold: true });
  stepRow(s, 1, "Booster APP 配网", "让 K1 接入网络", 120, 300, 400, C.blue);
  stepRow(s, 2, "获取 IP / 序列号", "确认连接目标", 120, 390, 400, C.blue);
  stepRow(s, 3, "BoosterStudio 连接", "查看状态；编程传文件走 SSH + IP", 120, 480, 400, C.blue);
  box(s, "有线方式", 715, 220, 470, 48, { fill: C.darkBlue, line: C.darkBlue, color: C.white, size: 20, bold: true });
  stepRow(s, 1, "网线直连电脑与 K1", "建立物理连接", 740, 300, 400, C.blue);
  stepRow(s, 2, "修改电脑网络配置", "让两端处于可通信网络", 740, 390, 400, C.blue);
  stepRow(s, 3, "BoosterStudio 连接", "查看状态并开始开发", 740, 480, 400, C.blue);
  addText(s, "K1 是实体机器人；电脑通过网络远程连接它，SSH 是编程通信方式。", 100, 590, 1080, 30, { size: 17, color: C.blue, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/02_共创规则与上下文/notebook开发规则.md", "知识库：01-booster-kb/07-tech-platform/booster-studio.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 24
{
  const s = pres.slides.add(); chrome(s, 24, "第四部分 · 动手连接与读取", "用 BoosterStudio 先连上", "图形界面建立第一印象", C.cyan);
  const labels = [["开机", "K1 进入可连接状态"], ["配网 / 接网线", "选择无线或有线方式"], ["查 IP / 序列号", "核对自己的设备"], ["BoosterStudio 连接", "建立开发入口"], ["看实时画面", "确认连接成功"]];
  labels.forEach(([a, b], i) => { stepRow(s, i + 1, a, b, 105, 225 + i * 66, 500, C.cyan); if (i < 4) downArrow(s, 300, 265 + i * 66, 22, 20, C.line); });
  photoLikeFrame(s, 745, 225, 390, 320, "BoosterStudio 连接界面\n建议替换为实际截图", C.cyan);
  box(s, "演示观察点\n连接状态 · 实时画面 · 机器人模式", 745, 575, 390, 62, { fill: C.cyan2, line: C.cyan, color: C.cyan, size: 16, bold: true });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-studio.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 25
{
  const s = pres.slides.add(); chrome(s, 25, "第四部分 · 动手连接与读取", "实操任务卡", "分组连接，记好“身份证”", C.cyan);
  box(s, "【动手试试】", 100, 220, 210, 48, { fill: C.cyan, line: C.cyan, color: C.white, size: 20, bold: true });
  addText(s, "每组完成一次连接，并记录属于自己的 K1。", 100, 295, 780, 36, { size: 25, bold: true, color: C.ink });
  const tasks = ["记录 IP 地址：________________", "记录序列号：________________", "在 BoosterStudio 中核对设备", "连接成功后举手，等待教师确认"];
  tasks.forEach((t, i) => { box(s, "□", 115, 375 + i * 50, 30, 30, { geometry: "rect", fill: C.white, line: C.cyan, color: C.cyan, size: 19, bold: true }); addText(s, t, 165, 373 + i * 50, 620, 32, { size: 19, color: C.body }); });
  box(s, "多机同场\n先核对序列号，再开始操作。", 880, 300, 260, 150, { fill: C.red2, line: C.red, color: C.red, size: 21, bold: true });
  addText(s, "完成标准：连得上、认得准、记得清。", 880, 500, 260, 34, { size: 18, color: C.cyan, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/教学设计/U1-L1_具身智能概览与连接K1_教学设计.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md"]);
}

// 26
{
  const s = pres.slides.add(); chrome(s, 26, "第四部分 · 动手连接与读取", "用代码连接 K1", "第一行：建立连接", C.cyan);
  codeBlock(s, ["from boosteros.robots.booster import BoosterRobot", "", "robot = BoosterRobot()", "print(\"已连接 K1，开始探索 🤖\")"], 100, 240, 1080, 190, [2], C.cyan, C.cyan2);
  box(s, "BoosterRobot()", 145, 495, 255, 58, { fill: C.cyan2, line: C.cyan, color: C.ink, size: 21, bold: true });
  arrow(s, 440, 510, 60, 26, C.cyan);
  box(s, "建立连接", 520, 495, 220, 58, { fill: C.cyan, line: C.cyan, color: C.white, size: 21, bold: true });
  arrow(s, 780, 510, 60, 26, C.cyan);
  box(s, "robot 对象", 880, 495, 220, 58, { fill: C.cyan2, line: C.cyan, color: C.cyan, size: 21, bold: true });
  addText(s, "对应 notebook：步骤 1", 100, 600, 1080, 28, { size: 15, color: C.muted, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb"]);
}

// 27
{
  const s = pres.slides.add(); chrome(s, 27, "第四部分 · 动手连接与读取", "读取它的“身份证”", "型号 · 序列号 · 固件版本", C.cyan);
  codeBlock(s, ["info = robot.robot_info", "print(f\"机器人的元信息：{info}\")", "", "print(\"型号：    \", info.model)", "print(\"序列号：  \", info.serial_number)", "print(\"固件版本：\", info.firmware_version)"], 100, 220, 1080, 245, [0, 4, 5], C.cyan, C.cyan2);
  box(s, "serial_number", 165, 455, 300, 62, { fill: C.cyan2, line: C.cyan, color: C.ink, size: 21, bold: true });
  arrow(s, 505, 472, 65, 28, C.cyan);
  box(s, "多机区分的“身份证号”", 610, 455, 380, 62, { fill: C.cyan2, line: C.cyan, color: C.cyan, size: 21, bold: true });
  addText(s, "重点：serial_number 是多机环境区分设备的字段；字段值以当前设备真实返回为准。", 100, 570, 1080, 44, { size: 17, color: C.muted, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb"]);
}

// 28
{
  const s = pres.slides.add(); chrome(s, 28, "第四部分 · 动手连接与读取", "浏览关节清单", "22 个关节与它们的“身体结构”", C.cyan);
  codeBlock(s, ["joints = robot.list_joints()", "print(f\"关节总数：{len(joints)}\")", "print(f\"list_joints{joints}\")", "", "for j in joints:", "    print(f\"{j.name:<20} 限位: [{j.limits.min:.3f}, {j.limits.max:.3f}] rad  最大速度: {j.max_velocity:.3f} rad/s\")"], 100, 215, 650, 255, [0, 5], C.cyan, C.cyan2);
  box(s, "j.name", 835, 250, 230, 48, { fill: C.cyan, line: C.cyan, color: C.white, size: 18, bold: true });
  box(s, "关节名称", 835, 315, 230, 58, { fill: C.cyan2, line: C.cyan, color: C.cyan, size: 18, bold: true });
  box(s, "j.limits", 835, 405, 230, 48, { fill: C.cyan, line: C.cyan, color: C.white, size: 18, bold: true });
  box(s, "活动范围", 835, 470, 230, 58, { fill: C.cyan2, line: C.cyan, color: C.cyan, size: 18, bold: true });
  addText(s, "先看总数，再看每个关节的名称、限位和最大速度；数量以实际返回为准。", 100, 565, 1080, 30, { size: 17, color: C.cyan, bold: true, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb"]);
}

// 29
{
  const s = pres.slides.add(); chrome(s, 29, "第四部分 · 动手连接与读取", "浏览动作库与当前状态", "它会哪些动作，现在什么状态", C.cyan);
  codeBlock(s, ["actions = robot.list_actions()", "print(f\"预定义动作总数：{len(actions)}\")", "print(f\"预定义动作内容：{actions}\")", "", "for a in actions:", "    dur = f\"{a.duration:.1f}s\" if a.duration is not None else \"-\"", "    print(f\"动作名称：{a.id:<25} 类型：{a.type:<15} 时长：{dur:<8} 可中断：{'是' if a.interruptible else '否'}\")", "", "print(\"当前模式：\", robot.get_mode())", "print(\"电池信息：\", robot.get_battery())"], 100, 205, 650, 350, [0, 8, 9], C.cyan, C.cyan2);
  const rows = [["list_actions()", "动作库", C.cyan2, C.cyan], ["get_mode()", "当前模式", C.cyan2, C.cyan], ["get_battery()", "电池状态", C.cyan2, C.cyan]];
  rows.forEach(([a, b, f, lc], i) => { box(s, a, 840, 245 + i * 95, 230, 42, { fill: lc, line: lc, color: C.white, size: 17, bold: true }); box(s, b, 840, 295 + i * 95, 230, 42, { fill: f, line: lc, color: C.ink, size: 16, bold: true }); });
  addText(s, "只读接口的价值：先知道系统“有什么、在哪里、处于什么状态”。", 100, 585, 1080, 30, { size: 17, color: C.cyan, bold: true, align: "center" });
  notes(s, ["知识库：01-booster-kb/07-tech-platform/booster-sdk.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb"]);
}

// 30
{
  const s = pres.slides.add(); chrome(s, 30, "第五部分 · 小结与评价", "本课小结与学习评价", "带走三件东西，测一测", C.amber);
  addText(s, "身份证", 105, 220, 300, 40, { size: 25, bold: true, color: C.amber, align: "center" });
  addText(s, "serial_number", 105, 270, 300, 32, { size: 19, color: C.body, align: "center", fontFamily: MONO });
  addText(s, "身体清单", 490, 220, 300, 40, { size: 25, bold: true, color: C.amber, align: "center" });
  addText(s, "list_joints()", 490, 270, 300, 32, { size: 19, color: C.body, align: "center", fontFamily: MONO });
  addText(s, "连接工具", 875, 220, 300, 40, { size: 25, bold: true, color: C.amber, align: "center" });
  addText(s, "BoosterStudio / SDK", 875, 270, 300, 32, { size: 18, color: C.body, align: "center", fontFamily: MONO });
  line(s, 90, 340, 1190, 340, C.line, 1);
  box(s, "评价题", 95, 380, 150, 46, { fill: C.amber, line: C.amber, color: C.white, size: 19, bold: true });
  addText(s, "1. 本实验全部为只读操作，不涉及机器人任何运动，可以放心运行。（    ）", 105, 455, 1070, 30, { size: 17, color: C.body });
  addText(s, "2. robot.robot_info 中，用于多机环境区分设备的字段是 ______。", 105, 500, 1070, 30, { size: 17, color: C.body });
  addText(s, "3. list_actions() 返回的动作信息中，可作为 do_action() 参数的字段是（    ）", 105, 545, 1070, 30, { size: 17, color: C.body });
  addText(s, "A. type    B. id    C. duration    D. interruptible", 105, 580, 1070, 26, { size: 15, color: C.muted });
  addText(s, "下一步：让机器人真正动起来。", 105, 610, 1070, 30, { size: 19, color: C.amber, bold: true, align: "center" });
  notes(s, ["知识库：05-internal-materials/vocational-planning/03_X课程项目/PPT内容设计/U1-L1_具身智能概览与连接K1_PPT内容大纲.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/教学设计/U1-L1_具身智能概览与连接K1_教学设计.md", "知识库：05-internal-materials/vocational-planning/03_X课程项目/notebooks/U1-L1_具身智能概览与连接K1.ipynb", "答案：1. √；2. serial_number；3. B. id"]);
}

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

for (const [i, slide] of pres.slides.items.entries()) {
  await writeBlob(`${PREVIEW_DIR}/slide-${String(i + 1).padStart(2, "0")}.png`, await pres.export({ slide, format: "png", scale: 1 }));
}
await writeBlob(`${PREVIEW_DIR}/montage.webp`, await pres.export({ format: "webp", montage: true, scale: 1 }));
const pptx = await PresentationFile.exportPptx(pres);
await pptx.save(OUT);
console.log(`WROTE ${OUT} (${pres.slides.items.length} slides)`);
