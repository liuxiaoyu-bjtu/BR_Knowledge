# -*- coding: utf-8 -*-
# U1-L2 P6 生成脚本：占位版 PPTX（照片类用占位框，框图类原生绘制，代码页浅色高亮，安全页警示红点缀）
# 视觉规范 §8.12：知识蓝 / 实践青绿 / 思考评价橘黄 / 安全警示红
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
TEAL    = RGBColor(0x0E, 0xA5, 0xA4)   # 实践操作主色
TEALBG  = RGBColor(0xCC, 0xFB, 0xF1)   # 实践代码高亮
AMBER   = RGBColor(0xFF, 0xF7, 0xE6)   # 思考/评价浅底
AMBERBAR= RGBColor(0xF5, 0x9E, 0x0B)   # 思考/评价主色
PH_FILL = RGBColor(0xEE, 0xF1, 0xF5)   # 占位框底
PH_LINE = RGBColor(0xB8, 0xC0, 0xCC)   # 占位框边
SOFT    = RGBColor(0xE7, 0xEC, 0xF5)   # 浅蓝卡片
CARD    = RGBColor(0xF0, 0xF4, 0xFC)   # 浅蓝卡
WARN    = RGBColor(0xE5, 0x48, 0x4D)   # 警示红（仅安全页点缀）
WARNBG  = RGBColor(0xFD, 0xE7, 0xE7)   # 警示红浅底
FONT    = "Microsoft YaHei"
MONO    = "Consolas"
TOTAL   = 26

OUT = r"d:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/PPT/U1-L2_运行模式与安全_Codex方案二审查版.pptx"

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

def section_tag(slide, text, color=BLUE):
    if not text:
        return
    w = Inches(min(7.0, 0.35 + 0.18 * len(text)))
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(0.42), w, Inches(0.48),
               fill=color, line=color)
    set_text(sp, text, size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def title_block(slide, title, subtitle=None):
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.02), Inches(12.0), Inches(0.62), fill=None, line=None),
             title, size=32, color=DARK, bold=True, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.66), Inches(12.0), Inches(0.45), fill=None, line=None),
             subtitle if subtitle.lstrip().startswith("——") else "—— " + subtitle, size=18, color=GRAY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)

def page_no(slide, n):
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(11.9), Inches(7.0), Inches(1.2), Inches(0.34), fill=None, line=None),
             "%d / %d" % (n, TOTAL), size=11, color=GRAY, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

def placeholder(slide, l, t, w, h, label=""):
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=PH_FILL, line=PH_LINE, line_w=1.5, dash=True)
    txt = "【配图占位】"
    if label:
        txt += "\n" + label
    set_text(sp, txt, size=14, color=GRAY, bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def bullets(slide, l, t, w, h, items, size=16, color=DARK, gap=1.18, runs_list=None):
    sp = shape(slide, MSO_SHAPE.RECTANGLE, l, t, w, h, fill=None, line=None)
    tf = sp.text_frame
    tf.word_wrap = True
    if runs_list is None:
        for i, it in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = gap
            p.space_after = Pt(6)
            r = p.add_run()
            r.text = "• " + it
            style_run(r, size, color, False)
    else:
        for i, (txt, sz, col, b) in enumerate(runs_list):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = gap
            p.space_after = Pt(6)
            r = p.add_run()
            r.text = txt
            style_run(r, sz, col, b)

def code_block(slide, l, t, w, lines, highlight=None, size=13):
    highlight = highlight or set()
    line_h = Inches(0.36)
    n = len(lines)
    h = Emu(int(line_h * (n + 1)) + int(Inches(0.24)))
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=LIGHT, line=PH_LINE, line_w=1.0)
    shape(slide, MSO_SHAPE.RECTANGLE, l, t, Inches(0.09), h, fill=TEAL, line=None)
    for i in highlight:
        y = Emu(int(t) + int(Inches(0.12)) + i * int(line_h))
        shape(slide, MSO_SHAPE.RECTANGLE, l, y, w, line_h, fill=TEALBG, line=None)
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
    accent = TEAL if kind == "动手试试" else (AMBERBAR if kind == "想一想" else BLUE)
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=CARD, line=accent, line_w=1.0)
    shape(slide, MSO_SHAPE.RECTANGLE, l, t, Inches(0.10), h, fill=accent, line=None)
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, l + Inches(0.25), t + Inches(0.06), w - Inches(0.4), Inches(0.4), fill=None, line=None),
             "【%s】" % kind, size=14, color=accent, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, l + Inches(0.25), t + Inches(0.46), w - Inches(0.45), h - Inches(0.52), fill=None, line=None),
             text, size=13, color=DARK, anchor=MSO_ANCHOR.TOP)

def warn_bar(slide, l, t, w, text):
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, Inches(0.5), fill=WARN, line=WARN)
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, l, t, w, Inches(0.5), fill=None, line=None),
             text, size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ---------- 原生框图 ----------
def draw_four_modes_table(s):
    rows, cols = 5, 4
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(2.7), Inches(11.5), Inches(3.6))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.4); tbl.columns[1].width = Inches(4.6)
    tbl.columns[2].width = Inches(2.3); tbl.columns[3].width = Inches(2.2)
    data = [
        ("模式", "含义", "能否运动", "安全要点"),
        ("damping", "阻尼/软态，关节有阻尼但不支撑站立", "否", "开机默认状态"),
        ("prepare", "准备模式，维持站立就绪姿态", "否（仅就绪）", "行走前必须先到达此模式"),
        ("walk", "行走模式，靠动态平衡维持站立", "是（需配合速度）", "只能由已直立的 prepare 进入"),
        ("custom", "进阶自定义，需单独编程", "取决于编程", "未编程前比 damping 更软，本课不实操"),
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

def draw_manual_vs_program(s):
    rows, cols = 4, 3
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(2.9), Inches(11.5), Inches(3.0))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.2); tbl.columns[1].width = Inches(4.65); tbl.columns[2].width = Inches(4.65)
    data = [
        ("维度", "手动切换（按钮/手柄）", "程序切换（SDK）"),
        ("适用", "人在现场即时操作", "按流程自动执行"),
        ("特点", "直观、响应快", "可复现、可批量、可组合成任务"),
        ("局限", "每次都要人动手", "需提前写好并验证"),
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

def draw_state_machine(s):
    y = Inches(3.0); bw = Inches(2.9); bh = Inches(1.4)
    xs = [Inches(0.9), Inches(5.2), Inches(9.5)]
    states = ["damping\n阻尼软态", "prepare\n准备就绪", "walk\n行走模式"]
    for nm, x in zip(states, xs):
        card(s, x, y, bw, bh, nm, fill=BLUE, color=WHITE, bold=True, size=15)
    # 边标签卡片
    card(s, Inches(3.85), Inches(3.35), Inches(1.5), Inches(0.7), "↔\n可互切", fill=SOFT, size=12)
    card(s, Inches(8.15), Inches(3.35), Inches(1.5), Inches(0.7), "→\n直立后进入", fill=SOFT, size=12)
    card(s, Inches(8.15), Inches(4.45), Inches(1.5), Inches(0.7), "←\n安全停止", fill=SOFT, size=12)
    card(s, Inches(3.85), Inches(4.45), Inches(1.5), Inches(0.7), "↓\n坐下收尾", fill=SOFT, size=12)
    # 严禁直接切换
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(5.0), Inches(3.4), Inches(1.1), fill=WARNBG, line=WARN, line_w=1.5)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(9.0), Inches(5.05), Inches(3.4), Inches(1.0), fill=None, line=None),
             "✕ 严禁 walk → damping\n站立动态平衡态直接切软态会瘫倒", size=13, color=WARN, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

def draw_safety_path(s):
    y = Inches(3.5); bw = Inches(2.2); bh = Inches(1.7)
    xs = [Inches(0.7), Inches(3.2), Inches(5.7), Inches(8.2), Inches(10.7)]
    labels = ["① 进入 prepare\n并手动拉起站稳", "② 人工确认\n直立·空旷·教师监督",
              "③ 进入 walk\n本实验不发速度", "④ 安全停止\n回 prepare", "⑤ 坐下/趴好\n后 damping 收尾"]
    for lb, x in zip(labels, xs):
        card(s, x, y, bw, bh, lb, fill=SOFT, size=12, color=DARK)
    for i in range(4):
        arrow(s, MSO_SHAPE.RIGHT_ARROW, Emu(int(xs[i]) + int(bw)), y + Inches(0.6), Inches(0.3), Inches(0.4))

# ---------- 页面生成 ----------
def page_accent(n):
    if n in {26}:
        return AMBERBAR
    if n in {12, 13, 14, 15, 20, 21, 22, 24, 25}:
        return TEAL
    return BLUE

def make(slide, n, section, title, subtitle, build):
    bg(slide)
    if section:
        section_tag(slide, section, page_accent(n))
    else:
        section_tag(slide, "单元 U1 · 人形机器人初探与运动控制")
    title_block(slide, title, subtitle)
    build(slide)
    page_no(slide, n)

# 1 封面
s = new_slide(); bg(s)
section_tag(s, "第二堂人形机器人课")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.3), fill=None, line=None),
         "运行模式与安全", size=46, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(3.7), Inches(11.5), Inches(0.6), fill=None, line=None),
         "—— 让 K1 安全地站起来", size=22, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(4.5), Inches(2.2), Inches(0.10), fill=BLUE, line=None)
placeholder(s, Inches(0.9), Inches(4.9), Inches(11.5), Inches(1.7), "课程主视觉 / K1 四种姿态拼图 或 安全操作场景")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.8), Inches(11.5), Inches(0.4), fill=None, line=None),
         "课时 L2 · 主讲人：__________", size=14, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
page_no(s, 1)

# 2 本课目标
def p2(s):
    bullets(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.5), [
        "认识四种运行模式的物理含义与安全要点",
        "用 SDK 查看并切换运行模式",
        "掌握模式间的安全切换顺序，养成规范操作习惯",
    ], size=20)
make(new_slide(), 2, "导学", "本课目标", "—— 一节课我们要带走什么", p2)

# 3 互动导入
def p3(s):
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "K1 趴姿/站姿/行走 三态拼图")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(1.4), fill=None, line=None),
             "回顾：上节课我们连上了 K1，读到了它的基本参数。", size=18, color=DARK, bold=True)
    hint_card(s, Inches(0.9), Inches(4.0), Inches(6.2), Inches(1.8), "想一想",
              "机器人从趴着，到站起来、准备走——\n底层的控制方式一样吗？\n先猜一下，下面揭晓。")
make(new_slide(), 3, "第一部分 · K1 的运行模式", "从“连上”到“动起来”", "—— 控制方式一样吗？", p3)

# 4 什么是运行模式
def p4(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(2.8), fill=None, line=None),
             "运行模式 = 机器人在某种工作状态下采用的整套控制策略。\n\n趴着、站着、走着，关节的控制目标完全不同——"
             "这决定了它能不能动、怎么动、安不安全。", size=17, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "三种姿态对照（趴 / 站 / 走）")
make(new_slide(), 4, "第一部分 · K1 的运行模式", "什么是运行模式", "—— 不同工作状态，不同控制策略", p4)

# 5 四模式总览表
def p5(s):
    draw_four_modes_table(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.5), Inches(11.5), Inches(0.5), fill=None, line=None),
             "四种模式含义、能否运动、安全要点一表总览；下面 4 页逐一展开。", size=14, color=GRAY)
make(new_slide(), 5, "第一部分 · K1 的运行模式", "K1 的四种运行模式", "—— damping / prepare / walk / custom", p5)

# 6-9 四模式逐页图文（左文右图）
def mode_page(n, sec_title, sub, code_name, meaning, motion, safety, img_label):
    def b(s):
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(0.6), fill=None, line=None),
                 code_name, size=20, color=BLUE, bold=True)
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(3.1), Inches(6.2), Inches(1.2), fill=None, line=None),
                 meaning, size=16, color=DARK)
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(4.4), Inches(6.2), Inches(0.6), fill=None, line=None),
                 "能否运动：" + motion, size=16, color=DARK, bold=True)
        set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.1), Inches(6.2), Inches(0.9), fill=None, line=None),
                 "安全要点：" + safety, size=16, color=DARK)
        placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), img_label)
    make(new_slide(), n, "第一部分 · K1 的运行模式", sec_title, sub, b)

mode_page(6, "模式一 · damping 阻尼软态", "—— 开机默认，关节软、不支撑站立", "damping",
          "关节有阻尼但整体“软”，无法维持站立。", "否", "开机默认状态；也是关机前的收尾状态。", "K1 趴姿实拍")
mode_page(7, "模式二 · prepare 准备就绪", "—— 行走之前的必经状态", "prepare",
          "维持站立就绪姿态，关节变硬但不主动运动。", "否（仅就绪）", "进入 walk 前必须先到达此模式且已直立站稳。", "K1 直立站姿实拍")
mode_page(8, "模式三 · walk 行走模式", "—— 靠动态平衡维持站立", "walk",
          "机器人持续微调关节维持平衡，可配合速度指令行走。", "是（需配合速度）", "只能由已直立的 prepare 进入。", "K1 行走中实拍")
mode_page(9, "模式四 · custom 自定义", "—— 进阶模式，本课不实操", "custom",
          "需自行编程实现控制逻辑；未编程前比 damping 更软。", "取决于编程", "属进阶内容，本课时只作认识。", "进阶编程示意图")

# 10 过渡页
def p10(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "机器人现在是什么模式？\n—— 从手动按钮到程序控制", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "手 / 代码 对比意象")
make(new_slide(), 10, "第二部分 · 用程序查看与切换模式", "机器人现在是什么模式？", "—— 从手动按钮到程序控制", p10)

# 11 手动 vs 程序（表格）
def p11(s):
    draw_manual_vs_program(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.2), Inches(11.5), Inches(0.5), fill=None, line=None),
             "按钮/手柄适合人即时操作；程序适合按流程自动执行、可复现、可批量——这就是学机器人编程的意义。",
             size=14, color=GRAY)
make(new_slide(), 11, "第二部分 · 用程序查看与切换模式", "手动切换 vs 程序切换", "—— 即时操作与流程自动化", p11)

# 12 代码：连接
def p12(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["from boosteros.robots.booster import BoosterRobot",
                "robot = BoosterRobot()",
                "# 建立与 K1 的连接（对应 notebook 2.1）"],
               highlight={1})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(1.0), fill=None, line=None),
             "第一行就建立连接：robot 即这台 K1，之后所有读/写都通过它。", size=15, color=GRAY)
make(new_slide(), 12, "第二部分 · 用程序查看与切换模式", "用代码连接 K1", "—— 第一行：建立连接", p12)

# 13 代码：get_mode
def p13(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["mode = robot.get_mode()",
                "print(mode)   # 如 'damping' / 'prepare' / 'walk'",
                "# 读出的字符串应和机器人实际姿态一致"],
               highlight={0})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.8), Inches(11.5), Inches(0.9), fill=None, line=None),
             "get_mode() 读出当前模式字符串；对照机器人实际姿态验证。", size=15, color=GRAY)
make(new_slide(), 13, "第二部分 · 用程序查看与切换模式", "读取当前运行模式", "—— get_mode() 读出状态", p13)

# 14 观察记录任务
def p14(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.6), fill=None, line=None),
             "不写代码：观察 damping / prepare / walk 三种模式下的姿态、能否运动，"
             "填入实训手册 2.3 表格。同桌交叉核对后签字。", size=17, color=DARK, bold=True)
    hint_card(s, Inches(0.9), Inches(4.2), Inches(11.5), Inches(2.2), "动手试试",
              "观察记录要点：\n\n· 三种模式下 K1 的姿态分别什么样？\n· 哪些能运动、哪些不能？\n· 把“模式—姿态”对应关系真正记牢，再进入下一步实操。")
make(new_slide(), 14, "第二部分 · 用程序查看与切换模式", "观察记录任务", "—— 把“模式—姿态”对应记下来", p14)

# 15 代码：趴姿切换
def p15(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["# 趴姿最安全：即使切换失败也不会摔倒",
                'robot.set_mode("prepare")   # 关节变硬，进入准备就绪',
                'robot.set_mode("damping")   # 回到软态收尾',
                "# 体会两种模式下关节硬度的不同"],
               highlight={1, 2})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.8), Inches(11.5), Inches(0.9), fill=None, line=None),
             "set_mode() 切换模式；趴姿下练，最安全，先建立“模式—姿态”的直观体感。", size=15, color=GRAY)
make(new_slide(), 15, "第二部分 · 用程序查看与切换模式", "趴姿下切换模式", "—— damping ↔ prepare 练手", p15)

# 16 过渡页
def p16(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "能切换了，是不是就能随便切？\n—— 模式之间有安全顺序", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "状态机剪影 虚化背景")
make(new_slide(), 16, "第三部分 · 安全切换与行走", "能切换了，是不是就能随便切？", "—— 模式之间有安全顺序", p16)

# 17 状态机
def p17(s):
    draw_state_machine(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.4), Inches(11.5), Inches(0.6), fill=None, line=None),
             "允许路径：damping↔prepare、prepare→walk、walk→prepare；prepare→damping 收尾。严禁 walk→damping。",
             size=14, color=GRAY)
make(new_slide(), 17, "第三部分 · 安全切换与行走", "运行模式状态机", "—— 哪些能切，哪些不能切", p17)

# 18 安全红线（警示红点缀）
def p18(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.3), Inches(7.4), Inches(0.8), fill=None, line=None),
             "严禁  walk  →  damping", size=34, color=WARN, bold=True)
    bullets(s, Inches(0.9), Inches(3.3), Inches(7.4), Inches(2.2), [
        "机器人瞬间瘫倒",
        "可能伤及邻近人员",
        "损坏物品与机器人本体",
    ], size=16, color=DARK, gap=1.25)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.7), Inches(7.4), Inches(0.7), fill=None, line=None),
             "正确做法：停止行走必须先回 prepare，确认坐下/趴好后再 damping。", size=14, color=WARN, bold=True)
    placeholder(s, Inches(8.7), Inches(2.3), Inches(4.0), Inches(4.0), "瘫倒后果警示示意（警示红点缀）")
make(new_slide(), 18, "第三部分 · 安全切换与行走", "安全红线", "—— 严禁 walk → damping", p18)

# 19 行走安全路径
def p19(s):
    draw_safety_path(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.8), fill=None, line=None),
             "五步时序，每步之间留“人工窗口”：必须人工确认、人工操作，不可连续一键跑完。", size=14, color=GRAY)
make(new_slide(), 19, "第三部分 · 安全切换与行走", "行走安全路径", "—— 四步时序，每步之间留人工窗口", p19)

# 20 代码：步骤 1
def p20(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ['# 步骤 1：进入准备模式（对应 notebook 4.2）',
                'robot.set_mode("prepare")',
                "# 随后手动把机器人拉起到 STAND 直立站稳"],
               highlight={1})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.4), Inches(11.5), Inches(0.9), fill=None, line=None),
             "先站稳，再谈行走：必须人工把机器人拉起、确认直立站稳，才能进入下一步。", size=15, color=GRAY)
make(new_slide(), 20, "第三部分 · 安全切换与行走", "步骤 1 · 进入准备模式", "—— 先站稳，再谈行走", p20)

# 21 代码：步骤 2（警示红）
def p21(s):
    warn_bar(s, Inches(0.9), Inches(2.4), Inches(11.5), "⚠ 人工确认后方可运行：直立站稳 · 周围空旷 · 教师监督")
    code_block(s, Inches(0.9), Inches(3.15), Inches(11.5),
               ['# 步骤 2：确认后进入行走（对应 notebook 4.2）',
                'robot.set_mode("walk")   # 本实验不发速度，机器人原地'],
               highlight={1})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.4), Inches(11.5), Inches(0.9), fill=None, line=None),
             "只有确认已直立站稳、周围空旷、教师在场，才运行此 cell；本实验不发速度。", size=15, color=WARN, bold=True)
make(new_slide(), 21, "第三部分 · 安全切换与行走", "步骤 2 · 确认后进入行走", "—— 人工确认窗口，不可跳过", p21)

# 22 代码：步骤 3-4（警示红）
def p22(s):
    warn_bar(s, Inches(0.9), Inches(2.4), Inches(11.5), "⚠ 先回 prepare 安全停止，再软态收尾")
    code_block(s, Inches(0.9), Inches(3.15), Inches(11.5),
               ['# 步骤 3：安全停止，回到准备模式',
                'robot.set_mode("prepare")',
                '# 步骤 4：确认已坐下/趴好后，软态收尾',
                'robot.set_mode("damping")'],
               highlight={1, 3})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.9), Inches(11.5), Inches(0.8), fill=None, line=None),
             "停止行走必须先回 prepare；确认已坐下/趴好，才切 damping 收尾，杜绝 walk→damping。", size=15, color=WARN, bold=True)
make(new_slide(), 22, "第三部分 · 安全切换与行走", "步骤 3–4 · 安全停止与收尾", "—— 先回 prepare，再软态收尾", p22)

# 23 过渡页
def p23(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "不写代码，也能让它动\n—— 换控制方式，不换安全原则", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "手柄剪影")
make(new_slide(), 23, "第四部分 · 手柄手动遥控", "不写代码，也能让它动", "—— 换控制方式，不换安全原则", p23)

# 24 演示页：手柄
def p24(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.4), fill=None, line=None),
             "操作目标：用手柄直接遥控 K1 完成准备 / 行走 / 停止。\n\n"
             "前置：手柄与机器人配对、K1 已开机、站位在安全区。\n\n"
             "关键步骤：先 prepare 直立 → 推摇杆行走 → 回 prepare 停止。\n\n"
             "安全要点：安全顺序与程序控制完全一致，禁止 walk→damping。", size=15, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.2), "手柄按键标注（左摇杆/右摇杆/模式键/急停）")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(7.4), Inches(5.8), Inches(5.2), Inches(0.5), fill=None, line=None),
             "详细图示见附件《K1 手柄遥控操作图示》", size=13, color=BLUE, bold=True)
make(new_slide(), 24, "第四部分 · 手柄手动遥控", "用手柄操控 K1", "—— 按键布局与操作流程", p24)

# 25 分组实操任务卡
def p25(s):
    hint_card(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.6), "动手试试",
              "分组轮换，在监督下完成一次完整操控：\n\n"
              "· 每组：prepare → 直立站稳 → walk → 回 prepare\n"
              "· 每组指定 1 名安全员，全程盯守，禁止 walk → damping\n"
              "· 教师先完整示范一遍，再放手让学生操作\n"
              "· 操作前确认周围空旷、站位安全")
make(new_slide(), 25, "第四部分 · 手柄手动遥控", "分组实操任务卡", "—— 在监督下完成一次完整操控", p25)

# 26 小结与评价
def p26(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.3), Inches(11.5), Inches(0.5), fill=None, line=None),
             "带走三件东西：① 四种模式　② 程序切换　③ 安全切换顺序", size=16, color=DARK, bold=True)
    card(s, Inches(0.9), Inches(3.1), Inches(11.5), Inches(0.6), "学习评价（与实训手册一致）", fill=AMBERBAR, line=AMBERBAR, color=WHITE, bold=True, size=15)
    bullets(s, Inches(1.0), Inches(3.9), Inches(11.3), Inches(2.6), [
        "判断：walk 模式可以由 damping 直接切换进入。（　）",
        "填空：停止行走时，必须先回到 ________ 模式，再收尾到 damping。",
        "选择：进入 walk 前，机器人必须处于（　）A. damping 软态　B. prepare 且已直立站稳　C. custom",
    ], size=15, gap=1.1)
make(new_slide(), 26, "第五部分 · 小结与评价", "本课小结与学习评价", "—— 带走三件东西，测一测", p26)

prs.save(OUT)
print("DONE: %s  slides=%d" % (OUT, len(prs.slides._sldIdLst)))
