# -*- coding: utf-8 -*-
# U1-L3 P6 生成脚本：占位版 PPTX（照片类用占位框，框图类原生绘制，代码页浅色高亮，安全页警示红点缀）
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

OUT = r"d:/A_Project/BoosterRobotics/知识库/05-internal-materials/vocational-planning/03_X课程项目/PPT/U1-L3_基本运动控制_Codex方案二审查版.pptx"

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

def concept_tag(slide, text):
    # 核心概念角标（右下小字）
    set_text(shape(slide, MSO_SHAPE.RECTANGLE, Inches(9.3), Inches(6.55), Inches(3.4), Inches(0.4), fill=None, line=None),
             text, size=13, color=BLUE, bold=True, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

# ---------- L3 专属原生表格 ----------
def draw_velocity_params_table(s):
    rows, cols = 4, 4
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(2.7), Inches(11.5), Inches(3.4))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.4); tbl.columns[1].width = Inches(4.6)
    tbl.columns[2].width = Inches(2.0); tbl.columns[3].width = Inches(2.5)
    data = [
        ("参数", "含义", "单位", "正方向"),
        ("vx", "前后方向速度", "m/s", "正数 = 前进，负数 = 后退"),
        ("vy", "左右方向速度", "m/s", "正数 = 左移，负数 = 右移"),
        ("vyaw", "绕竖直轴转向速度", "rad/s", "正数 = 向左（逆时针）转，负数 = 向右（顺时针）转"),
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

def draw_action_table(s):
    rows, cols = 7, 3
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(2.6), Inches(11.5), Inches(3.9))
    tbl = gf.table
    tbl.columns[0].width = Inches(4.6); tbl.columns[1].width = Inches(3.6); tbl.columns[2].width = Inches(3.3)
    data = [
        ("指令", "动作", "方向"),
        ("set_velocity(0.5, 0, 0)", "前进", "机器人正前方"),
        ("set_velocity(-0.5, 0, 0)", "后退", "机器人正后方"),
        ("set_velocity(0, 0.3, 0)", "左移", "机器人正左方"),
        ("set_velocity(0, -0.3, 0)", "右移", "机器人正右方"),
        ("set_velocity(0, 0, 0.5)", "左转（逆时针）", "绕竖直轴向左"),
        ("set_velocity(0, 0, -0.5)", "右转（顺时针）", "绕竖直轴向右"),
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
            style_run(run, 13, WHITE if r == 0 else DARK, bold=(r == 0 or c == 0), font=(MONO if c == 0 else FONT))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)

def draw_openloop_vs_closed(s):
    rows, cols = 5, 3
    gf = s.shapes.add_table(rows, cols, Inches(0.9), Inches(2.9), Inches(11.5), Inches(3.2))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.6); tbl.columns[1].width = Inches(4.45); tbl.columns[2].width = Inches(4.45)
    data = [
        ("维度", "开环（本课）", "闭环（后续课程）"),
        ("是否测结果", "否，发完即结束", "是，读取实际再修正"),
        ("复杂度", "简单", "较复杂"),
        ("精度", "受干扰大", "能抵消干扰"),
        ("本课定位", "实操采用", "暂不引入（留待 U2 / U4）"),
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

def draw_walk_timing(s):
    y = Inches(3.2); bw = Inches(1.9); bh = Inches(1.7)
    xs = [Inches(0.7), Inches(2.7), Inches(4.7), Inches(6.7), Inches(8.7), Inches(10.7)]
    labels = ["① 进入 prepare\n并手动拉起站稳", "② 人工确认\n直立·空旷·教师监督",
              "③ 进入 walk\n发速度指令", "④ 安全停止\nset_velocity 0,0,0",
              "⑤ 回 prepare\n站立稳定", "⑥ damping\n软态收尾"]
    for i, (lb, x) in enumerate(zip(labels, xs)):
        fillc = WARN if i == 1 else SOFT
        card(s, x, y, bw, bh, lb, fill=fillc, size=12,
             color=(WHITE if i == 1 else DARK), bold=(i == 1))
    for i in range(5):
        arrow(s, MSO_SHAPE.RIGHT_ARROW, Emu(int(xs[i]) + int(bw)), y + Inches(0.6), Inches(0.3), Inches(0.4))

# ---------- 页面生成 ----------
def page_accent(n):
    if n in {25, 26}:
        return AMBERBAR
    if n in {16, 17, 18, 19, 20, 21, 22, 23, 24}:
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
section_tag(s, "第三堂人形机器人课")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.3), fill=None, line=None),
         "基本运动控制", size=46, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(3.7), Inches(11.5), Inches(0.6), fill=None, line=None),
         "—— 让 K1 按指令行走", size=22, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(4.5), Inches(2.2), Inches(0.10), fill=BLUE, line=None)
placeholder(s, Inches(0.9), Inches(4.9), Inches(11.5), Inches(1.7), "课程主视觉 / K1 行走场景 或 坐标系示意图")
set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.8), Inches(11.5), Inches(0.4), fill=None, line=None),
         "课时 L3 · 主讲人：__________", size=14, color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
page_no(s, 1)

# 2 本课目标
def p2(s):
    bullets(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.5), [
        "理解自身坐标系与 set_velocity 的三个参数",
        "用 SDK 发出速度指令，让 K1 前进 / 后退 / 转向",
        "认识开环控制的偏差，学会观察与记录",
    ], size=20)
make(new_slide(), 2, "导学", "本课目标", "—— 一节课我们要带走什么", p2)

# 3 互动导入
def p3(s):
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "K1 站立待发 / 行走中 场景图")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(1.4), fill=None, line=None),
             "回顾：上节课我们让 K1 进入 walk，站稳了。", size=18, color=DARK, bold=True)
    hint_card(s, Inches(0.9), Inches(4.0), Inches(6.2), Inches(1.8), "想一想",
              "站立会了，那怎么让它真的走起来、\n往指定的方向走？\n先猜一下，下面揭晓。")
make(new_slide(), 3, "第一部分 · 速度指令与坐标系", "从“能切换”到“能移动”", "—— 怎么告诉机器人往哪走？", p3)

# 4 什么是自身坐标系
def p4(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.0), fill=None, line=None),
             "自身坐标系 = 以机器人自身为原点建立的方向基准。\n\n"
             "前后、左右是“相对于机器人朝向”的，不是固定的“上北下南”——\n"
             "机器人一转身，它的“前”就变了。", size=17, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "机器人坐标轴示意（自身前后左右）")
make(new_slide(), 4, "第一部分 · 速度指令与坐标系", "什么是自身坐标系", "—— 以机器人自己的前后左右为准", p4)

# 5 三个轴的方向
def p5(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.0), fill=None, line=None),
             "三个轴的正方向约定：\n\n"
             "· x 轴：机器人正前方为“前进正方向”\n"
             "· y 轴：机器人左侧为“左移正方向”\n"
             "· yaw：绕竖直轴逆时针（向左）转为正\n\n"
             "记住“正方向”，后面正负号就不会乱。", size=16, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "坐标系正方向标注图（x前 / y左 / yaw左转）")
make(new_slide(), 5, "第一部分 · 速度指令与坐标系", "三个轴的方向", "—— x 前进 · y 左移 · yaw 左转", p5)

# 6 set_velocity 三参数表
def p6(s):
    draw_velocity_params_table(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.4), Inches(11.5), Inches(0.5), fill=None, line=None),
             "一个指令 set_velocity(vx, vy, vyaw)，三个数同时生效，决定往哪走、转多快。", size=14, color=GRAY)
make(new_slide(), 6, "第一部分 · 速度指令与坐标系", "set_velocity 的三个参数", "—— 一个指令，三个数，决定往哪走", p6)

# 7 三参数动作对照
def p7(s):
    draw_action_table(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.6), Inches(11.5), Inches(0.5), fill=None, line=None),
             "正数往哪个方向、负数往哪个方向，一表记牢；三个数可组合（如同时前进 + 左转）。", size=14, color=GRAY)
make(new_slide(), 7, "第一部分 · 速度指令与坐标系", "三参数动作对照", "—— 正数往哪走，负数往哪走", p7)

# 8 速度与移动距离
def p8(s):
    card(s, Inches(0.9), Inches(2.5), Inches(6.2), Inches(1.2),
         "移动距离 = 速度 × 时间\n= 0.5 m/s × 2 s = 1 m", fill=SOFT, size=18, color=DARK, bold=True)
    bullets(s, Inches(0.9), Inches(4.0), Inches(6.2), Inches(2.0), [
        "安全降速：大纲 1 m/s × 2 s，课堂取 0.5 m/s × 2 s",
        "留出反应与急停空间，距离更好控制",
        "转向用角速度 rad/s，约 2 s 转 57°",
    ], size=15, gap=1.2)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.4), "距离估算示意图（0.5 m/s × 2 s = 1 m）")
make(new_slide(), 8, "第一部分 · 速度指令与坐标系", "速度与移动距离", "—— 0.5 m/s × 2 s ≈ 1 m", p8)

# 9 互动：引出开环
def p9(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "指令发出去，就万事大吉了？\n—— 机器人真的走到了预想的位置吗？", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "机器人“走歪了”示意")
make(new_slide(), 9, "第二部分 · 开环控制与偏差", "指令发出去，就万事大吉了？", "—— 引出“开环”", p9)

# 10 开环控制是什么（B09）
def p10(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(2.6), fill=None, line=None),
             "开环控制 = 只发出控制指令，不读取执行结果、不做修正。\n\n"
             "本实验发给 K1 速度指令后就结束，不测量它实际走到了哪——\n"
             "这就是“开环”。优点：简单；缺点：无法应对干扰。", size=16, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.0), "开环控制流向（指令 → 执行 → 结束）")
    concept_tag(s, "核心概念 B09 · 开环")
make(new_slide(), 10, "第二部分 · 开环控制与偏差", "开环控制是什么", "—— 发指令，但不测量结果", p10)

# 11 偏差从哪来（A05）
def p11(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(1.6), fill=None, line=None),
             "偏差 = 实际 − 预期（A05）\n\n机器人走出的轨迹，往往和设想的不一样。", size=18, color=DARK, bold=True)
    bullets(s, Inches(0.9), Inches(4.2), Inches(6.2), Inches(1.8), [
        "来源：地面不平整 / 轮子打滑",
        "来源：参数误差 / 惯性",
        "实际轨迹 ≠ 预期直线",
    ], size=15, gap=1.2)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.0), "预期直线 vs 实际偏斜轨迹对照图")
    concept_tag(s, "核心概念 A05 · 偏差")
make(new_slide(), 11, "第二部分 · 开环控制与偏差", "偏差从哪来", "—— 实际轨迹，往往不等于预期", p11)

# 12 开环 vs 闭环
def p12(s):
    draw_openloop_vs_closed(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(6.3), Inches(11.5), Inches(0.5), fill=None, line=None),
             "本课采用开环；闭环“测结果再修正”留待后续课程，是消除偏差的办法。", size=14, color=GRAY)
make(new_slide(), 12, "第二部分 · 开环控制与偏差", "开环 vs 闭环", "—— 本课只做开环，闭环留待后续", p12)

# 13 为什么观察偏差
def p13(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(2.6), fill=None, line=None),
             "本课目标不是“绝对精准”，而是建立一套习惯：\n\n"
             "发指令 → 测偏差 → 做记录。\n\n"
             "今天测量到的偏差，正是后续课程引入传感器闭环时的输入。", size=16, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.0), "偏差记录 → 后续改进 链路示意")
make(new_slide(), 13, "第二部分 · 开环控制与偏差", "为什么本课要观察偏差", "—— 先会测量，才有改进", p13)

# 14 过渡：安全
def p14(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.6), fill=None, line=None),
             "动手前，先守规矩\n—— 接下来 K1 会真的动起来，比“原地切换”更需谨慎", size=30, color=DARK, bold=True)
    placeholder(s, Inches(9.0), Inches(1.2), Inches(3.3), Inches(2.0), "空旷场地 + 监督 场景剪影")
make(new_slide(), 14, "第三部分 · 运动实验与安全", "动手前，先守规矩", "—— 真机移动的安全底线", p14)

# 15 实验安全规范（警示红点缀）
def p15(s):
    warn_bar(s, Inches(0.9), Inches(2.4), Inches(11.5), "⚠ 安全提示：真机移动，安全优先")
    bullets(s, Inches(0.9), Inches(3.3), Inches(11.5), Inches(3.0), [
        "① 场地空旷、无易撞物，远离台阶与电源",
        "② 教师与同伴在场，保持安全距离",
        "③ 明确急停与收尾手势，人人知晓",
        "④ 发指令前先预判轨迹，确认路径无阻挡",
    ], size=18, gap=1.3, color=DARK)
make(new_slide(), 15, "第三部分 · 运动实验与安全", "实验安全规范", "—— 空旷 · 在场 · 有预案", p15)

# 16 代码：连接与确认模式
def p16(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["from boosteros.robots.booster import BoosterRobot",
                "robot = BoosterRobot()              # 建立与 K1 的连接（对应 notebook 2.1，cell-7）",
                "mode = robot.get_mode()             # 读取当前运行模式（对应 notebook 2.2，cell-9）",
                "print(mode)   # 确认当前为已直立的 'prepare'"],
               highlight={1, 2})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.8), Inches(11.5), Inches(0.9), fill=None, line=None),
             "先连上、再确认它已经站好（prepare），才进入运动指令环节。", size=15, color=GRAY)
make(new_slide(), 16, "第三部分 · 运动实验与安全", "实验准备：连接与确认模式", "—— 先连上，再确认它站好了", p16)

# 17 进入行走态时序（人工确认红点缀）
def p17(s):
    warn_bar(s, Inches(0.9), Inches(2.4), Inches(11.5), "⚠ 人工确认节点不可跳过：直立站稳 · 周围空旷 · 教师监督")
    draw_walk_timing(s)
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.9), fill=None, line=None),
             "六步时序，② 人工确认不可连点跳过；必须先站稳、确认环境，才发 walk。对应 notebook 3.2（cell-15 / cell-17）。",
             size=14, color=GRAY)
make(new_slide(), 17, "第三部分 · 运动实验与安全", "进入行走态（多步 + 人工窗口）", "—— 确认后才发 walk，不可连点", p17)

# 18 代码：前进
def p18(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["# 对应 notebook 3.3（cell-19）",
                "robot.set_velocity(0.5, 0, 0)   # 前进 0.5 m/s",
                "# 约 2 秒后",
                "robot.set_velocity(0, 0, 0)     # 速度归零，停止"],
               highlight={1, 3})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.9), fill=None, line=None),
             "人工确认后再运行；vx 取正值即前进。运行约 2 秒后归零停止，测量实际落点。", size=15, color=GRAY)
make(new_slide(), 18, "第三部分 · 运动实验与安全", "代码 · 前进", "—— set_velocity(0.5, 0, 0)", p18)

# 19 代码：后退
def p19(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["# 对应 notebook 3.4（cell-21）",
                "robot.set_velocity(-0.5, 0, 0)  # 后退 0.5 m/s",
                "# 约 2 秒后",
                "robot.set_velocity(0, 0, 0)     # 停止"],
               highlight={1, 3})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.9), fill=None, line=None),
             "vx 取负值即后退；后退前务必确认后方空旷，再运行本 cell。", size=15, color=GRAY)
make(new_slide(), 19, "第三部分 · 运动实验与安全", "代码 · 后退", "—— set_velocity(-0.5, 0, 0)", p19)

# 20 代码：左转与右转
def p20(s):
    code_block(s, Inches(0.9), Inches(2.6), Inches(11.5),
               ["# 对应 notebook 3.5（cell-23 / cell-24）",
                "robot.set_velocity(0, 0, 0.5)   # 向左转（逆时针）0.5 rad/s",
                "robot.set_velocity(0, 0, 0)     # 停止",
                "robot.set_velocity(0, 0, -0.5)  # 向右转（顺时针）0.5 rad/s",
                "robot.set_velocity(0, 0, 0)     # 停止"],
               highlight={1, 3})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.8), Inches(11.5), Inches(0.9), fill=None, line=None),
             "vyaw 正数左转（逆时针）、负数右转（顺时针）；转约 90° 后归零，测量实际转角。", size=15, color=GRAY)
make(new_slide(), 20, "第三部分 · 运动实验与安全", "代码 · 左转与右转", "—— set_velocity(0, 0, ±0.5)", p20)

# 21 代码：停止与安全收尾（警示红）
def p21(s):
    warn_bar(s, Inches(0.9), Inches(2.4), Inches(11.5), "⚠ 先停，再回 prepare，最后 damping 收尾")
    code_block(s, Inches(0.9), Inches(3.15), Inches(11.5),
               ["# 对应 notebook 3.6（cell-26 / cell-28）",
                "robot.set_velocity(0, 0, 0)     # 速度归零，停止行走",
                'robot.set_mode("prepare")       # 安全停止，回到站立稳定',
                "# 确认已坐下 / 趴好后",
                'robot.set_mode("damping")       # 软态收尾'],
               highlight={1, 2, 4})
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.9), Inches(11.5), Inches(0.8), fill=None, line=None),
             "停止行走必须先回 prepare；确认已坐下/趴好，才切 damping 收尾，杜绝 walk→damping。", size=15, color=WARN, bold=True)
make(new_slide(), 21, "第三部分 · 运动实验与安全", "代码 · 停止与安全收尾", "—— 先停，再回 prepare，最后 damping", p21)

# 22 观察记录任务
def p22(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.4), fill=None, line=None),
             "不写代码：每组按指令移动后，测量实际落点，填入实训手册 §四 偏差表"
             "（预期位置 / 实际位置 / 偏差方向与大小）。", size=17, color=DARK, bold=True)
    hint_card(s, Inches(0.9), Inches(4.0), Inches(11.5), Inches(2.4), "动手试试",
              "观察记录要点：\n\n"
              "· 每个方向测一次：前进 / 后退 / 左转 / 右转\n"
              "· 直线是否偏向一侧？停止时有没有多走一点？转向后位置有没有平移？\n"
              "· 把偏差写成具体数字，同桌交叉核对后签字。")
make(new_slide(), 22, "第三部分 · 运动实验与安全", "观察记录任务", "—— 把“预期”和“实际”的差记下来", p22)

# 23 拓展：场地布置与测量
def p23(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.4), Inches(6.2), Inches(3.2), fill=None, line=None),
             "要让偏差测得准，场地和测量方法本身就要规范：\n\n"
             "· 长边 ≥ 5 米、宽边 ≥ 4 米，地面平整\n"
             "· 贴起点线、每 0.5 米刻度线、安全边界线\n"
             "· 贴 30° / 60° / 90° 角度参照线\n"
             "· 每次实验前拍照、实验后复位标记", size=15, color=DARK)
    placeholder(s, Inches(7.4), Inches(2.4), Inches(5.2), Inches(3.2), "场地布置示意图（起点/刻度/边界/角度线）")
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(7.4), Inches(5.8), Inches(5.2), Inches(0.5), fill=None, line=None),
             "详细图示见附件《K1 运动实验场地布置与测量图示》", size=13, color=BLUE, bold=True)
make(new_slide(), 23, "第四部分 · 拓展与评价", "拓展：场地布置与测量", "—— 见附件《K1 运动实验场地布置与测量图示》", p23)

# 24 分组实操任务卡
def p24(s):
    hint_card(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(3.8), "动手试试",
              "分组轮换，在监督下完成一次完整移动：\n\n"
              "· 每组：prepare → 确认 → 前进 → 后退 → 左转 → 右转 → 停止收尾\n"
              "· 每组指定 1 名安全员，全程盯守\n"
              "· 教师先完整示范一遍，再放手让学生操作\n"
              "· 每个方向运行约 2 秒后归零；操作前确认周围空旷、站位安全")
make(new_slide(), 24, "第四部分 · 拓展与评价", "分组实操任务卡", "—— 在监督下完成一次完整移动", p24)

# 25 本课小结（三卡）
def p25(s):
    card(s, Inches(0.9), Inches(2.8), Inches(3.6), Inches(3.0),
         "① 自身坐标系\n\nx 前 · y 左 · yaw 左转\n\n机器人朝向变了，\n“前”也跟着变", fill=CARD, size=16, color=DARK)
    card(s, Inches(4.85), Inches(2.8), Inches(3.6), Inches(3.0),
         "② set_velocity 三参数\n\nvx 前后 · vy 左右\nvyaw 转向\n\n正方向约定要记牢", fill=CARD, size=16, color=DARK)
    card(s, Inches(8.8), Inches(2.8), Inches(3.6), Inches(3.0),
         "③ 开环与偏差\n\n发指令、测偏差、做记录\n\n偏差 = 实际 − 预期（A05）", fill=CARD, size=16, color=DARK)
make(new_slide(), 25, "第四部分 · 拓展与评价", "本课小结", "—— 带走三件东西", p25)

# 26 学习评价
def p26(s):
    set_text(shape(s, MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.3), Inches(11.5), Inches(0.5), fill=None, line=None),
             "带走三件东西：① 自身坐标系　② 三参数与方向　③ 开环与偏差", size=16, color=DARK, bold=True)
    card(s, Inches(0.9), Inches(3.1), Inches(11.5), Inches(0.6), "学习评价（与实训手册一致）", fill=AMBERBAR, line=AMBERBAR, color=WHITE, bold=True, size=15)
    bullets(s, Inches(1.0), Inches(3.95), Inches(11.3), Inches(3.0), [
        "判断：发送速度指令前，必须先让 K1 进入 walk 模式，且在 prepare 下已 STAND 直立站稳。（　）",
        "填空：set_velocity(vx, vy, vyaw) 中，vx 取正值表示 ______，vyaw 取正值表示 ______。",
        "选择：本实验属于开环控制，下列对“开环”的描述正确的是（　）。A. 发出指令后持续读取实际位置并自动修正误差　B. 发出指令后不读取实际结果，也不自动纠正偏差　C. 必须保持电路闭合才能运动　D. 机器人只能走直线，不能转向",
        "选择：停止运动并收尾时，下列顺序安全且正确的是（　）。A. walk 直接切 damping　B. 直接关闭电源　C. set_velocity(0,0,0) → prepare → 坐下/趴好 → damping　D. 先切 damping，再把速度归零",
    ], size=13, gap=1.05)
make(new_slide(), 26, "第四部分 · 拓展与评价", "学习评价", "—— 测一测，带得走多少", p26)

prs.save(OUT)
print("DONE: %s  slides=%d" % (OUT, len(prs.slides._sldIdLst)))
