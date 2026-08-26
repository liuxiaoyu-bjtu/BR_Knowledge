# -*- coding: utf-8 -*-
# U1-L1 P6 生成脚本：占位版 PPTX（照片类用占位框，框图类原生绘制，代码页浅色高亮）
# 视觉规范 §8.12：16:9 / 白底 #FFFFFF / 主色科技蓝 #2563EB / 微软雅黑 / 页脚仅页码 / 代码页浅底 #F4F6F9 + 高亮 #FFF8E1
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
try:
    from pptx.enum.dml import MSO_DASH_STYLE
except Exception:
    MSO_DASH_STYLE = None
from pptx.oxml.ns import qn

# ---------- 基础常量 ----------
PAGE_W = Inches(13.333)
PAGE_H = Inches(7.5)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
BLUE    = RGBColor(0x25, 0x63, 0xEB)   # 科技蓝 主色
DARK    = RGBColor(0x1F, 0x29, 0x37)   # 主文字
GRAY    = RGBColor(0x60, 0x6A, 0x78)   # 副文字
LIGHT   = RGBColor(0xF4, 0xF6, 0xF9)   # 浅底/代码底
AMBER   = RGBColor(0xFF, 0xF8, 0xE1)   # 高亮行
AMBERBAR= RGBColor(0xF5, 0xA6, 0x23)   # 琥珀色条
PH_FILL = RGBColor(0xEE, 0xF1, 0xF5)   # 占位框底
PH_LINE = RGBColor(0xB8, 0xC0, 0xCC)   # 占位框边
SOFT    = RGBColor(0xE7, 0xEC, 0xF5)   # 浅蓝卡片
CARD    = RGBColor(0xF0, 0xF4, 0xFC)   # 浅蓝卡
FONT    = "Microsoft YaHei"
MONO    = "Consolas"
TOTAL   = 30

OUT = r"d:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/PPT/U1-L1_具身智能概览与连接K1.pptx"

prs = Presentation()
prs.slide_width = PAGE_W
prs.slide_height = PAGE_H
BLANK = prs.slide_layouts[6]

# ---------- 字体助手 ----------
def ea(run, font=FONT):
    rPr = run._r.get_or_add_rPr()
    rPr.set(qn('a:ea'), font)
    rPr.set(qn('a:cs'), font)

def style_run(run, size=14, color=DARK, bold=False, font=FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    ea(run, font)

def set_text(shape, text, size=14, color=DARK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, font=FONT, line_spacing=1.12, runs=None):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.06)
    tf.margin_bottom = Inches(0.06)
    if runs is None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line_spacing
            r = p.add_run()
            r.text = line
            style_run(r, size, color, bold, font)
    else:
        for i, (txt, sz, col, b, fnt) in enumerate(runs):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line_spacing
            r = p.add_run()
            r.text = txt
            style_run(r, sz, col, b, fnt)

# ---------- 形状助手 ----------
def shape(slide, kind, l, t, w, h, fill=None, line=None, line_w=1.0, dash=False):
    sp = slide.shapes.add_shape(kind, l, t, w, h)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
        if dash and MSO_DASH_STYLE is not None:
            try:
                sp.line.dash_style = MSO_DASH_STYLE.DASH
            except Exception:
                pass
    sp.shadow.inherit = False
    return sp

def card(slide, l, t, w, h, text, fill=SOFT, line=None, line_w=1.0,
         size=14, color=DARK, bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
         font=FONT, dashed=False):
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=fill, line=line or fill, line_w=line_w, dash=dashed)
    set_text(sp, text, size=size, color=color, bold=bold, align=align, anchor=anchor, font=font)
    return sp

def arrow(slide, kind, l, t, w, h, fill=BLUE):
    sp = slide.shapes.add_shape(kind, l, t, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp

# ---------- 页面通用元素 ----------
def new_slide():
    return prs.slides.add_slide(BLANK)

def bg(slide):
    shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, PAGE_W, PAGE_H, fill=WHITE)

def section_tag(slide, text):
    if not text:
        return
    w = Inches(0.20 + 0.115 * len(text))
    w = min(w, Inches(5.0))
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(0.42), w, Inches(0.42),
               fill=BLUE, line=BLUE)
    set_text(sp, text, size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def title_block(slide, title, subtitle=None):
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.02), Inches(12.0), Inches(0.62), fill=None, line=None),
             title, size=32, color=DARK, bold=True, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.66), Inches(12.0), Inches(0.45), fill=None, line=None),
                 "—— " + subtitle, size=18, color=GRAY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)

def page_no(slide, n):
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(11.9), Inches(7.0), Inches(1.2), Inches(0.34), fill=None, line=None),
             "%d / %d" % (n, TOTAL), size=11, color=GRAY, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

def placeholder(slide, l, t, w, h, label=""):
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=PH_FILL, line=PH_LINE, line_w=1.5, dash=True)
    txt = "【配图占位】"
    if label:
        txt += "\n" + label
    set_text(sp, txt, size=14, color=GRAY, bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def bullets(slide, l, t, w, h, items, size=16, color=DARK, gap=1.18):
    sp = shape(slide, MSO_SHAPE.RECTANGLE, l, t, w, h, fill=None, line=None)
    tf = sp.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = gap
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = "• " + it
        style_run(r, size, color, False)

def code_block(slide, l, t, w, lines, highlight=None, size=13):
    highlight = highlight or set()
    line_h = Inches(0.36)
    n = len(lines)
    h = Emu(int(line_h * (n + 1)) + int(Inches(0.24)))
    # 浅色底
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=LIGHT, line=PH_LINE, line_w=1.0)
    # 左侧琥珀色条
    shape(slide, MSO_SHAPE.RECTANGLE, l, t, Inches(0.09), h, fill=AMBERBAR, line=None)
    # 高亮行
    for i in highlight:
        y = Emu(int(t) + int(Inches(0.12)) + i * int(line_h))
        shape(slide, MSO_SHAPE.RECTANGLE, l, y, w, line_h, fill=AMBER, line=None)
    # 文本
    tb = shape(slide, MSO_SHAPE.RECTANGLE, l, t, w, h, fill=None, line=None)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        r = p.add_run()
        r.text = ln if ln else " "
        style_run(r, size, DARK, False, MONO)
    return h

def hint_card(slide, l, t, w, h, kind, text):
    # kind: 想一想 / 动手试试 / 任务卡
    bar_color = BLUE if kind != "动手试试" else AMBERBAR
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=CARD, line=BLUE, line_w=1.0)
    shape(slide, MSO_SHAPE.RECTANGLE, l, t, Inches(0.10), h, fill=bar_color, line=None)
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, l + Inches(0.25), t + Inches(0.06), w - Inches(0.4), Inches(0.4), fill=None, line=None),
             "【%s】" % kind, size=14, color=BLUE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, l + Inches(0.25), t + Inches(0.46), w - Inches(0.45), h - Inches(0.52), fill=None, line=None),
             text, size=13, color=DARK, anchor=MSO_ANCHOR.TOP)

# ---------- 原生框图 ----------
def draw_timeline(slide):
    x0 = Inches(0.7); y = Inches(3.4); bw = Inches(2.7); bh = Inches(2.0); gap = Inches(0.36)
    nodes = [
        ("符号智能", "1950s–1980s", "智能 = 符号推理"),
        ("行为主义与机器人学", "1980s–2000s", "感知—行动闭环"),
        ("深度学习赋能感知", "2010s", "看得清、听得懂"),
        ("大模型与 VLA", "2020s 至今", "看—想—动一体"),
    ]
    cur = x0
    for i, (name, period, mean) in enumerate(nodes):
        card(slide, cur, y, bw, bh, name + "\n" + period + "\n—\n" + mean, fill=SOFT, size=14, color=DARK, bold=False)
        if i < 3:
            arrow(slide, MSO_SHAPE.RIGHT_ARROW, cur + bw, y + Inches(0.75), gap, Inches(0.5))
        cur = Emu(int(cur) + int(bw) + int(gap))

def draw_subsystems(slide):
    cx = Inches(6.66); top = Inches(2.5)
    card(slide, cx - Inches(1.3), top, Inches(2.6), Inches(0.9), "K1 人形机器人", fill=BLUE, color=WHITE, bold=True, size=16)
    subs = [("感知子系统", "眼/前庭 · 相机/IMU"), ("计算子系统", "大脑 · 机载算力"),
            ("运动子系统", "肌肉骨骼 · 关节电机"), ("电源子系统", "心脏 · 电池")]
    bw = Inches(2.7); bh = Inches(1.5); y = Inches(4.5)
    xs = [Inches(0.7), Inches(3.85), Inches(7.0), Inches(10.15)]
    for (name, desc), x in zip(subs, xs):
        arrow(slide, MSO_SHAPE.DOWN_ARROW, cx - Inches(0.25), top + Inches(0.9), Inches(0.5), y - top - Inches(0.9))
        card(slide, x, y, bw, bh, name + "\n" + desc, fill=SOFT, size=14, color=DARK)

def draw_sdk(slide):
    cx = Inches(6.66); top = Inches(2.5)
    card(slide, cx - Inches(1.6), top, Inches(3.2), Inches(0.9), "BoosterRobot 统一入口", fill=BLUE, color=WHITE, bold=True, size=15)
    reads = [("robot_info", "读身份"), ("list_joints", "读身体清单"), ("list_actions", "读动作库")]
    bw = Inches(3.4); bh = Inches(1.4); y = Inches(4.6)
    xs = [Inches(0.7), Inches(4.96), Inches(9.23)]
    for (name, desc), x in zip(reads, xs):
        arrow(slide, MSO_SHAPE.DOWN_ARROW, cx - Inches(0.25), top + Inches(0.9), Inches(0.5), y - top - Inches(0.9))
        card(slide, x, y, bw, bh, name + "\n" + desc, fill=SOFT, size=14, color=DARK)

def draw_connect(slide):
    # 左：无线
    lx = Inches(0.7)
    card(slide, lx, Inches(2.5), Inches(5.6), Inches(0.7), "无线方式", fill=BLUE, color=WHITE, bold=True, size=15)
    wnodes = ["① Booster APP 配网", "② 获取 IP / 序列号", "③ BoosterStudio 连接·看状态 / SDK(SSH+IP) 编程"]
    yy = Inches(3.5)
    for i, txt in enumerate(wnodes):
        card(slide, lx + Inches(0.3), yy, Inches(5.0), Inches(0.62), txt, fill=SOFT, size=13, align=PP_ALIGN.LEFT)
        if i < 2:
            arrow(slide, MSO_SHAPE.DOWN_ARROW, lx + Inches(2.6), yy + Inches(0.62), Inches(0.4), Inches(0.35))
        yy = Emu(int(yy) + int(Inches(1.0)))
    # 右：有线
    rx = Inches(6.9)
    card(slide, rx, Inches(2.5), Inches(5.6), Inches(0.7), "有线方式", fill=BLUE, color=WHITE, bold=True, size=15)
    rnodes = ["① 网线直连电脑与 K1", "② 修改电脑网络配置", "③ BoosterStudio 连接"]
    yy = Inches(3.5)
    for i, txt in enumerate(rnodes):
        card(slide, rx + Inches(0.3), yy, Inches(5.0), Inches(0.62), txt, fill=SOFT, size=13, align=PP_ALIGN.LEFT)
        if i < 2:
            arrow(slide, MSO_SHAPE.DOWN_ARROW, rx + Inches(2.6), yy + Inches(0.62), Inches(0.4), Inches(0.35))
        yy = Emu(int(yy) + int(Inches(1.0)))

# ---------- 页面生成 ----------
def make(slide, n, section, title, subtitle, build):
    bg(slide)
    if section:
        section_tag(slide, section)
    else:
        # 封面也放一个浅色小标识
        section_tag(slide, "单元 U1 · 人形机器人初探与运动控制")
    title_block(slide, title, subtitle)
    build(slide)
    page_no(slide, n)

# 1 封面
s = new_slide(); bg(s)
section_tag(s, "第一堂人形机器人课")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.3), fill=None, line=None),
         "具身智能概览与连接 K1", size=46, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(3.7), Inches(11.5), Inches(0.6), fill=None, line=None),
         "—— 从数字大脑到会动的身体", size=22, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(4.5), Inches(2.2), Inches(0.10), fill=BLUE, line=None)
placeholder(s, Inches(0.9), Inches(4.9), Inches(11.5), Inches(1.7), "课程主视觉 / 人形机器人 K1 形象图")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.8), Inches(11.5), Inches(0.4), fill=None, line=None),
         "课时 L1 · 主讲人：__________", size=14, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
page_no(s, 1)

# 2 本课目标
def p2(s):
    bullets(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.5), [
        "认识具身智能与人形机器人的组成",
        "用 BoosterOS SDK 连接 K1，读取它的“身体清单”",
        "理解“用程序操控实体机器人”这件事",
    ], size=20)
make(new_slide(), 2, "导学", "本课目标", "—— 一节课我们要带走什么", p2)

# 3 互动导入
def p3(s):
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "展厅/足球/搬运 短片截图")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(1.4), fill=None, line=None),
             "观看短片，想一想：机器人的“智能”在哪里？", size=18, color=DARK, bold=True)
    hint_card(s, Inches(0.9), Inches(4.0), Inches(6.2), Inches(1.8), "想一想",
              "它只是算得快、生成得快？\n还是能看、能走、能动手？\n把你的判断记下来，下面揭晓。")
make(new_slide(), 3, "第一部分 · 初识具身智能", "机器人的“智能”在哪", "—— 会算，还是会动？", p3)

# 4 什么是具身智能（表格）
def p4(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(5.4), Inches(1.2), fill=None, line=None),
             "智能“长”在能感知、能行动的身体上；人形机器人是其中代表载体。", size=16, color=DARK, bold=True)
    rows, cols = 4, 3
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(3.7), Inches(11.5), Inches(2.8))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.6); tbl.columns[1].width = Inches(4.45); tbl.columns[2].width = Inches(4.45)
    data = [
        ("维度", "离身智能", "具身智能"),
        ("核心", "只会算 / 生成", "既能算，也有身体"),
        ("位置", "藏在屏幕后", "能看 · 能动 · 能交互"),
        ("例子", "豆包 / Seedance / WorkBuddy", "K1"),
    ]
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            cell.text = data[r][c]
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE if r == 0 else (LIGHT if c == 0 else WHITE)
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.CENTER
            run = para.runs[0]
            style_run(run, 14, WHITE if r == 0 else DARK, bold=(r == 0 or c == 0))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_top = Inches(0.04); cell.margin_bottom = Inches(0.04)
make(new_slide(), 4, "第一部分 · 初识具身智能", "什么是具身智能", "—— 从数字大脑到会动的身体", p4)

# 5 发展脉络总览
def p5(s):
    draw_timeline(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(5.8), Inches(12.0), Inches(0.8), fill=None, line=None),
             "智能历经四段：符号推理 → 感知—行动 → 深度学习感知 → 大模型与 VLA。下面 4 页逐一展开。",
             size=14, color=GRAY)
make(new_slide(), 5, "第一部分 · 初识具身智能", "智能是怎么一步步“长”出来的", "—— 四段发展脉络一览", p5)

# 6-9 发展四页
def dev_page(n, sec_title, sub, period, mean, img_label):
    def b(s):
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(0.5), fill=None, line=None),
                 period, size=15, color=BLUE, bold=True)
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(3.0), Inches(6.2), Inches(2.6), fill=None, line=None),
                 mean, size=17, color=DARK)
        placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.2), img_label)
    make(new_slide(), n, "第一部分 · 初识具身智能", sec_title, sub, b)

dev_page(6, "发展一 · 符号智能", "—— 把智能当作“推理”", "1950s–1980s",
         "智能 = 符号推理（Newell & Simon）。这一时期的机器人多为固定程序、按指令执行，尚无自主学习能力。", "早期计算机 / 逻辑推演机")
dev_page(7, "发展二 · 行为主义与机器人学", "—— 让机器人“感知—行动”", "1980s–2000s",
         "Brooks 提出“无表征”思路：不先建世界模型，而是让真实机器人边感知边行动，形成感知—行动闭环。", "早期移动机器人 照片")
dev_page(8, "发展三 · 深度学习赋能感知", "—— 机器人终于“看得清”", "2010s",
         "AlexNet 带来突破，视觉与语音识别成熟，机器人从此“看得清、听得懂”周围世界。", "神经网络结构 + 摄像头")
dev_page(9, "发展四 · 大模型与 VLA", "—— 看、想、动连成一体", "2020s 至今",
         "大模型带来通用推理，VLA 把“看—想—动”端到端连成一体（如 PaLM-E、RT-2）。", "大模型对话 + 机器人执行任务")

# 10 研究重心总览
def p10(s):
    card(s, Inches(0.9), Inches(2.6), Inches(5.5), Inches(2.6), "前沿方向\n—— 开眼界\n\nVLN / VLA / 世界模型\n等前沿课题先建立印象", fill=SOFT, size=16, color=DARK)
    card(s, Inches(6.9), Inches(2.6), Inches(5.5), Inches(2.6), "应用方向\n—— 能上手\n\n机器人操作 / 运动控制 / 手眼协调\n本课先认识，后续单元动手", fill=SOFT, size=16, color=DARK)
make(new_slide(), 10, "第二部分 · 研究重心与方向", "今天的研究往哪用力", "—— 既要开眼界，也要能上手", p10)

# 11-13 前沿三页
def frontier_page(n, sec_title, sub, desc, img_label):
    def b(s):
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(2.6), fill=None, line=None),
                 desc, size=17, color=DARK)
        placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.2), img_label)
    make(new_slide(), n, "第二部分 · 研究重心与方向", sec_title, sub, b)

frontier_page(11, "前沿一 · 视觉语言导航 VLN", "—— 听懂“去那边把杯子拿来”",
              "理解语言 + 看见环境 + 规划路径：把一句自然语言指令变成可执行的导航。", "机器人按语言指令导航示意图")
frontier_page(12, "前沿二 · 视觉语言动作 VLA", "—— 看见画面，直接输出动作",
              "端到端：画面 + 指令 → 动作。模型直接生成机器人该做的动作序列。", "VLA 端到端框图")
frontier_page(13, "前沿三 · 世界模型", "—— 在脑内先“演一遍”",
              "模拟“如果我这么动会怎样”，在想象中预演后果，再决定真实动作。", "预测 / 模拟示意图")

# 14-16 应用三页
def app_page(n, sec_title, sub, desc, img_label):
    def b(s):
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(0.9), fill=None, line=None),
                 desc, size=18, color=DARK, bold=True)
        placeholder(s, Inches(0.9), Inches(3.5), Inches(11.5), Inches(2.9), img_label)
    make(new_slide(), n, "第二部分 · 研究重心与方向", sec_title, sub, b)

app_page(14, "应用一 · 机器人操作", "—— 稳稳抓放、精准装配", "让机械臂稳定抓取、装配零件，是工厂与仓储的核心能力。", "机械臂抓取 / 装配图")
app_page(15, "应用二 · 运动控制", "—— 在不平地面站稳走好", "双足机器人保持平衡、稳定行走，是“会动”的关键难题。", "双足在不平地面行走图")
app_page(16, "应用三 · 手眼协调", "—— 眼睛看到的，实时修正手的动作", "摄像头反馈实时引导动作，例如对准插孔时不断微调。", "手眼协调闭环示意图")

# 17 过渡页
def p17(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "回到我们手边的这台 K1\n—— 它到底由什么组成？", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "虚化 K1 背景图")
make(new_slide(), 17, "第三部分 · 认识 K1 与开发工具", "回到我们手边的这台 K1", "—— 它到底由什么组成？", p17)

# 18 四大子系统
def p18(s):
    draw_subsystems(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.3), Inches(11.5), Inches(0.6), fill=None, line=None),
             "K1 = 感知 + 计算 + 运动 + 电源 四大子系统协同。本课从计算入口与运动清单两端切入认识它。",
             size=14, color=GRAY)
make(new_slide(), 18, "第三部分 · 认识 K1 与开发工具", "人形机器人的系统组成", "—— 感知、计算、运动、电源", p18)

# 19 走近 K1（一）
def p19(s):
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.6), "K1 全身图 + 关节/传感器标注")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.4), fill=None, line=None),
             "Booster Robot 公司的人形机器人：\n\n· 身高约 1.3 m，22 个关节自由度\n· 头部相机、IMU 等传感器\n· 有芯片、有操作系统（BoosterOS）\n· 可被连接、被编程",
             size=16, color=DARK)
make(new_slide(), 19, "第三部分 · 认识 K1 与开发工具", "走近 K1（一）", "—— 外观、硬件与“身体参数”", p19)

# 20 走近 K1（二）
def p20(s):
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.6), "K1 执行动作 / 结构爆炸图")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.4), fill=None, line=None),
             "本课的操作对象：\n\n· 可连接、可读取信息\n· 后续单元才驱动它运动\n· 本课时先“只读认识”它的身份与身体清单",
             size=16, color=DARK)
make(new_slide(), 20, "第三部分 · 认识 K1 与开发工具", "走近 K1（二）", "—— 它能做什么，我们能对它做什么", p20)

# 21 过渡页
def p21(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "看完了它的“身体”，怎么用一行代码让它听话？", size=28, color=DARK, bold=True)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(4.6), Inches(11.3), Inches(0.6), fill=None, line=None),
             "—— 从手动到程序控制", size=20, color=GRAY)
make(new_slide(), 21, "第三部分 · 认识 K1 与开发工具", "怎么用一行代码让它“听话”", "—— 从手动到程序控制", p21)

# 22 SDK
def p22(s):
    draw_sdk(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.3), Inches(11.5), Inches(0.6), fill=None, line=None),
             "SDK（BoosterOS）是 Booster Robot 提供的开发工具包；BoosterRobot 是代码版遥控器（统一入口）。",
             size=14, color=GRAY)
make(new_slide(), 22, "第三部分 · 认识 K1 与开发工具", "SDK 是什么", "—— 操作机器人的“说明书+钥匙”", p22)

# 23 连接
def p23(s):
    draw_connect(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(6.8), Inches(12.0), Inches(0.5), fill=None, line=None),
             "K1 是实体机器人（有芯片/OS）；电脑经网络 SSH 远程连接编程。两种连接方式均可。", size=13, color=GRAY)
make(new_slide(), 23, "第三部分 · 认识 K1 与开发工具", "K1 与电脑怎么连上", "—— 无线 / 有线两种方式", p23)

# 24 演示 Studio
def p24(s):
    steps = ["① 开机", "② 配网 / 接网线", "③ 查 IP / 序列号", "④ BoosterStudio 连接", "⑤ 看实时画面"]
    yy = Inches(2.5)
    for i, st in enumerate(steps):
        card(s, Inches(0.9), yy, Inches(6.0), Inches(0.6), st, fill=SOFT, size=15, align=PP_ALIGN.LEFT)
        if i < 4:
            arrow(s, MSO_SHAPE.DOWN_ARROW, Inches(3.7), yy + Inches(0.6), Inches(0.4), Inches(0.3))
        yy = Emu(int(yy) + int(Inches(0.9)))
    placeholder(s, Inches(7.4), Inches(2.5), Inches(5.2), Inches(3.6), "BoosterStudio 界面三步标注")
make(new_slide(), 24, "第四部分 · 动手连接与读取", "用 BoosterStudio 先连上", "—— 图形界面建立第一印象", p24)

# 25 实操任务卡
def p25(s):
    hint_card(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.4), "任务卡",
              "分组连接 K1，记录它的“身份证”：\n\n· 记下 IP 地址：________________\n· 记下序列号：________________\n· 多机同场时，按序列号核对，防止连错机器\n\n完成后举手，教师巡场确认连接成功。")
make(new_slide(), 25, "第四部分 · 动手连接与读取", "实操任务卡", "—— 分组连接，记好“身份证”", p25)

# 26 代码：建立连接
def p26(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["from boosteros.robot import BoosterRobot",
                "robot = BoosterRobot()",
                "# 建立与 K1 的连接（对应 notebook 步骤 1）"],
               highlight={1})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.0), Inches(11.5), Inches(1.0), fill=None, line=None),
             "第一行就建立连接：把 BoosterRobot 当“代码版遥控器”，robot 即这台 K1。", size=15, color=GRAY)
make(new_slide(), 26, "第四部分 · 动手连接与读取", "用代码连接 K1", "—— 第一行：建立连接", p26)

# 27 代码：读身份证
def p27(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["info = robot.robot_info",
                "print(info.model, info.serial_number, info.firmware_version)",
                "serial = info.serial_number   # 多机区分的“身份证号”"],
               highlight={1, 2})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.4), Inches(11.5), Inches(0.9), fill=None, line=None),
             "重点：serial_number 即“身份证号”，多台 K1 同场时用它区分。", size=15, color=GRAY)
make(new_slide(), 27, "第四部分 · 动手连接与读取", "读取它的“身份证”", "—— 型号·序列号·固件版本", p27)

# 28 代码：关节清单
def p28(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["joints = robot.list_joints()",
                "for j in joints:",
                "    print(j.name, j.limits, j.max_velocity)",
                "# 共 22 个关节，对应身体各部位"],
               highlight={0, 2})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.8), fill=None, line=None),
             "list_joints() 返回 22 个关节；limits / max_velocity 描述每个关节的活动范围与速度上限。", size=15, color=GRAY)
make(new_slide(), 28, "第四部分 · 动手连接与读取", "浏览关节清单", "—— 22 个关节与它们的“身体结构”", p28)

# 29 代码：动作库与状态
def p29(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["actions = robot.list_actions()   # id/type/duration/interruptible",
                "mode = robot.get_mode()",
                "battery = robot.get_battery()",
                "# 它会哪些动作？现在什么状态？"],
               highlight={0, 1, 2})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.8), fill=None, line=None),
             "list_actions() 看动作库；get_mode()/get_battery() 看当前模式与电量。", size=15, color=GRAY)
make(new_slide(), 29, "第四部分 · 动手连接与读取", "浏览动作库与当前状态", "—— 它会哪些动作，现在什么状态", p29)

# 30 小结与评价
def p30(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.3), Inches(11.5), Inches(0.5), fill=None, line=None),
             "带走三件东西：① 身份证（序列号）② 身体清单（22 关节）③ 连接工具（Studio / SDK）", size=16, color=DARK, bold=True)
    card(s, Inches(0.9), Inches(3.1), Inches(11.5), Inches(0.6), "学习评价（与实训手册一致）", fill=BLUE, color=WHITE, bold=True, size=15)
    bullets(s, Inches(1.0), Inches(3.9), Inches(11.3), Inches(2.6), [
        "判断：K1 是实体机器人，有芯片和操作系统。（　）",
        "填空：区分多台 K1 的“身份证号”是 ________。",
        "选择：电脑与 K1 的远程连接方式基于（　）A.蓝牙　B.SSH 网络　C.U盘",
    ], size=15, gap=1.1)
make(new_slide(), 30, "第五部分 · 小结与评价", "本课小结与学习评价", "—— 带走三件东西，测一测", p30)

prs.save(OUT)
print("DONE: %s  slides=%d" % (OUT, len(prs.slides._sldIdLst)))
