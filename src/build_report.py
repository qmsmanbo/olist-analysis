# -*- coding: utf-8 -*-
"""生成 Olist 项目完整报告（DOCX）· v2 修正列宽与分页"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "output" / "figs"
OUT = BASE / "report" / "Olist项目报告.docx"

NAVY = RGBColor(0x1B, 0x33, 0x58)
ACCENT = RGBColor(0xC0, 0x50, 0x4D)
GREY = RGBColor(0x77, 0x77, 0x77)
DARK = RGBColor(0x33, 0x33, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CN = "微软雅黑"


def set_font(run, size=10.5, bold=False, color=DARK, font=CN):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:eastAsia", "w:ascii", "w:hAnsi"):
        rFonts.set(qn(attr), font)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def vcenter(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    va = OxmlElement("w:vAlign")
    va.set(qn("w:val"), "center")
    tcPr.append(va)


def _insert_tblpr(tblPr, el):
    """tblBorders / tblLayout 必须按 OOXML 顺序插在 tblLook 之前。"""
    look = tblPr.find(qn("w:tblLook"))
    if look is not None:
        look.addprevious(el)
    else:
        tblPr.append(el)


def no_borders(table):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        borders.append(el)
    _insert_tblpr(tblPr, borders)


def fixed_layout(table, widths):
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    _insert_tblpr(tblPr, layout)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(sum(widths) * 567)))
    _insert_tblpr(tblPr, tblW)
    grid = table._tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)


def para(doc, text="", size=10.5, bold=False, color=DARK, align=None,
         space_before=0, space_after=3, line=1.4):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_font(r, size, bold, color)
    return p


def h1(doc, num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{num}  ")
    set_font(r, 16, True, ACCENT)
    r2 = p.add_run(text)
    set_font(r2, 16, True, NAVY)
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "6")
    bottom.set(qn("w:color"), "C0504D")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    set_font(r, 12, True, NAVY)
    return p


def body(doc, text, size=10.5, space_after=5, space_before=0):
    return para(doc, text, size=size, space_after=space_after, space_before=space_before)


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.left_indent = Cm(0.6)
    r = p.add_run("· ")
    set_font(r, size, True, ACCENT)
    r2 = p.add_run(text)
    set_font(r2, size)
    return p


def quote(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.5)
    pf.space_before = Pt(4)
    pf.space_after = Pt(7)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.4
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), "C0504D")
    pBdr.append(left)
    pPr.append(pBdr)
    r = p.add_run(text)
    set_font(r, 10.5, False, NAVY)
    return p


def table(doc, header, rows, widths, font_size=8.5, align_first_left=True,
          highlight_rows=None, row_h=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(h)
        set_font(r, font_size, True, WHITE)
        shade(c, "1B3358")
        vcenter(c)
        p.paragraph_format.keep_with_next = True
    # 表头行禁止跨页拆分
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    trPr.append(OxmlElement("w:tblHeader"))    # 跨页时重复表头
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, val in enumerate(row):
            c = cells[ci]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0.5)
            p.paragraph_format.space_after = Pt(0.5)
            p.paragraph_format.line_spacing = 1.2
            if not (align_first_left and ci == 0):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            is_hi = highlight_rows and ri in highlight_rows
            set_font(r, font_size, is_hi, ACCENT if is_hi else DARK)
            if ri % 2 == 1:
                shade(c, "F5F7FA")
            if row_h:
                pass
    fixed_layout(t, widths)
    # 表后留白
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(2)
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.line_spacing = 0.6
    return t


def image(doc, name, caption, width=16.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True      # 图与图注不分页
    p.add_run().add_picture(str(FIG / name), width=Cm(width))
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(4)
    r = cp.add_run(caption)
    set_font(r, 8.5, False, GREY)


def page_break(doc):
    doc.add_page_break()


def add_page_number(paragraph):
    run = paragraph.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1); run._r.append(it); run._r.append(f2)
    set_font(run, 8.5, False, GREY)


# ============================================================ 文档
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = Cm(1.9)
sec.bottom_margin = Cm(1.8)

footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number(footer_p)

# ------------------------------------------------------------ 封面
for _ in range(3):
    para(doc, "", space_after=0)
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
r = p.add_run("数 据 分 析 项 目 报 告"); set_font(r, 11, True, ACCENT)

p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(10)
r = p.add_run("Olist 巴西电商\n履约与增长分析")
r.font.size = Pt(30); r.font.name = CN; r.bold = True; r.font.color.rgb = NAVY
r._element.get_or_add_rPr()

p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(26)
r = p.add_run("从 155 万行交易数据，看「超时 → 差评 → 不复购」\n如何拖住增长")
set_font(r, 13, False, GREY)

meta = [
    ("数 据", "Brazilian E-Commerce Public Dataset by Olist"),
    ("规 模", "9 张表 / 155 万行 / 2016.09 – 2018.10"),
    ("工 具", "MySQL 8.0 · Python 3.14 · pandas · matplotlib"),
]
t = doc.add_table(rows=3, cols=2)
for i, (k, v) in enumerate(meta):
    c0, c1 = t.rows[i].cells
    p0 = c0.paragraphs[0]; r0 = p0.add_run(k); set_font(r0, 9.5, True, NAVY)
    p1 = c1.paragraphs[0]; r1 = p1.add_run(v); set_font(r1, 9.5, False, DARK)
fixed_layout(t, [2.6, 13.6])
no_borders(t)

for _ in range(7):
    para(doc, "", space_after=0)
p = doc.add_paragraph()
r = p.add_run("2026 年 10 月"); set_font(r, 10, False, GREY)

page_break(doc)

# ------------------------------------------------------------ 摘要
h1(doc, "摘要", "")

quote(doc, "Olist 的增长瓶颈不在获客，在履约。大促把订单量推到月均的 1.5 倍，"
           "物流跟不上，用户给差评、不再回来；而平台本身的复购率只有 4–5%，"
           "补不上缺口——所以增长只能靠一波一波地拉新，形不成复利。")

h2(doc, "三个核心数字")
cards = [
    ("6.7%  →  32.5%", "超时订单只占样本的 6.7%，却贡献了 32.5% 的差评。",
     "超时订单的差评率约 62%，准时订单只有 9.2%——差 6.7 倍。"),
    ("4.29  →  2.11", "准时订单平均 4.29 分；超时 1–3 天掉到 3.29；超 4–7 天崩到 2.11。",
     "超 8 天后见底（1.68），再晚也不会更差。"),
    ("2.52%  vs  3.82%", "首单「超时 + 差评」的客户复购率 2.52%，准时好评组 3.82%。",
     "差异显著（χ²=14.53, p<0.001），但幅度只有 1.3 个百分点。"),
]
t = doc.add_table(rows=3, cols=2)
for i, (num, d1, d2) in enumerate(cards):
    c0, c1 = t.rows[i].cells
    p0 = c0.paragraphs[0]; r0 = p0.add_run(num); set_font(r0, 14, True, ACCENT)
    p1 = c1.paragraphs[0]
    r1 = p1.add_run(d1); set_font(r1, 9.5, False, DARK)
    p1.add_run().add_break()
    r2 = p1.add_run(d2); set_font(r2, 9.5, False, GREY)
    vcenter(c0); vcenter(c1)
fixed_layout(t, [4.8, 11.4])
no_borders(t)
para(doc, "", space_after=4)

h2(doc, "三条建议")
table(doc,
      ["优先级", "建议", "效果", "成本"],
      [["1", "大促期间 ETA 放宽 15%（22.7 → 26 天）", "减 1,100 单超时 / 590 个差评", "零"],
       ["2", "按州设 SLA，取消全国统一承诺", "减 2,190 单超时 / 1,160 个差评", "低"],
       ["3", "超时预警前置到「超时前 1 天」", "减 320 个差评", "中"]],
      widths=[1.8, 7.4, 5.2, 1.8], font_size=9, align_first_left=False)

h2(doc, "报告结构")
body(doc, "1 背景与选题 · 2 数据与口径 · 3 生意盘子 · 4 履约质量 · 5 时效与满意度 · "
          "6 复购验证 · 7 结论与建议 · 8 局限 · 附录")

page_break(doc)

# ------------------------------------------------------------ 1 背景
h1(doc, "1", "背景与选题")
h2(doc, "1.1 数据是什么")
body(doc, "Olist 是巴西的一家电商平台（marketplace），本次分析使用其 2016 年 9 月至 2018 年 10 月的"
          "脱敏交易数据，共 9 张表、约 155 万行，涵盖订单、商品明细、支付、评价、客户、卖家与地理信息。")

h2(doc, "1.2 为什么选这个题：先做「能力矩阵」")
body(doc, "拿到数据后没有直接想「做什么图」，而是列出常见分析主题，逐条判断这份数据是否支撑：")
table(doc,
      ["分析主题", "必需字段", "是否具备", "判定"],
      [["规模与趋势", "金额 + 下单时间", "✓", "可做，但平庸"],
       ["转化漏斗", "浏览 / 加购 / 购买日志", "✗ 只有成单", "做不了"],
       ["留存与复购", "用户唯一标识 + 时间", "△ 复购率仅 4–5%", "做不了主线"],
       ["履约时效", "下单 / 交运 / 送达 / 承诺 四个时间戳", "✓✓", "强项"],
       ["满意度归因", "评分 + 履约字段", "✓✓", "强项"],
       ["毛利 / 广告效率", "成本、曝光、点击、花费", "✗", "做不了"]],
      widths=[3.2, 6.4, 3.6, 3.4], font_size=8.5)

body(doc, "结论：这份数据唯一「字段齐全、且能从头走到尾」的路径是——")
quote(doc, "履约时效 → 满意度 → 复购：有客观过程（时间戳）、有主观结果（评分），"
           "两者能通过 order_id 连接。这是大多数公开数据集不具备的条件。")

h2(doc, "1.3 分析框架")
body(doc, "全文按「现象 → 归因 → 后果 → 建议」四段推进，每章只回答一个问题：")
table(doc,
      ["章节", "要回答的问题", "核心方法"],
      [["第 1 章", "生意怎么样", "建基准、转相对值、看集中度"],
       ["第 2 章", "凭什么做到（履约）", "分布 / 空间 / 时间三维拆分 + 排除法"],
       ["第 3 章", "慢的代价多大", "分箱看形状（非线性）+ 主动证伪"],
       ["第 4 章", "用户真的走了吗", "先诊断测量偏差，再做对比与检验"],
       ["第 5 章", "该做什么", "做减法、按成本效果排序、算钱"]],
      widths=[2.2, 5.4, 9.0], font_size=8.5)

# ------------------------------------------------------------ 2 数据
h1(doc, "2", "数据与口径")
h2(doc, "2.1 九张表的关系")
table(doc,
      ["表", "行数", "一行 = 什么", "在分析中的角色"],
      [["orders", "99,441", "一个订单", "主表，含 4 个时间戳 + 1 个承诺日"],
       ["order_items", "112,650", "订单里的一个商品项", "GMV 唯一来源（price / freight）"],
       ["order_payments", "103,886", "一次支付动作", "支付结构，与金额对账"],
       ["order_reviews", "99,224", "一条评价", "评分（核心因变量）"],
       ["customers", "99,441", "一张订单的客户记录", "customer_unique_id 用于复购"],
       ["products", "32,951", "一个商品", "品类维度"],
       ["sellers", "3,095", "一个卖家", "供给端（本项目未深入）"],
       ["geolocation", "1,000,163", "一条邮编-坐标对", "未使用（成本高、收益低）"],
       ["category_translation", "71", "一个品类的翻译", "品类可读化"]],
      widths=[3.8, 2.4, 4.4, 6.3], font_size=8.5)

h2(doc, "2.2 数据质量问题与处理（均为实测）")
table(doc,
      ["#", "问题", "规模", "影响", "处理"],
      [["1", "物流日期为空字符串", "2,980 行", "严格模式下导入静默丢 3%", "先入字符串再转 NULL"],
       ["2", "review_id 重复", "789 个 ID / 814 行", "单列主键挡掉 814 条", "改复合主键 (review_id, order_id)"],
       ["3", "评论含换行符", "3,852 条", "CSV 解析错行，少 815 条", "只导评分等定长字段"],
       ["4", "品类缺失", "610 个商品", "占比分母差 1.33%", "归入「未标注」，图注说明"],
       ["5", "翻译表缺 2 个品类", "13 个商品", "JOIN 匹配不上", "按葡语意译补齐"],
       ["6", "有支付无明细", "775 单", "INNER JOIN 丢单", "报告说明，不影响 GMV"],
       ["7", "customers 与订单同为 99,441 行", "—", "用 customer_id 算复购率恒为 0", "改用 customer_unique_id"]],
      widths=[0.9, 4.4, 3.4, 4.4, 4.4], font_size=8, align_first_left=False)

h2(doc, "2.3 口径定义")
table(doc,
      ["指标", "定义", "备注"],
      [["样本范围", "order_status = 'delivered'", "96,478 单，占全部订单 97%"],
       ["GMV", "SUM(price)，不含运费", "运费单列为 freight"],
       ["AOV", "总 GMV ÷ 总订单数", "137.04（含运费 159.83）"],
       ["配送天数", "DATEDIFF(delivered, purchase)", "按整天截断"],
       ["超时", "DATEDIFF(delivered, estimated) > 0", "按整天 6.77%；按小时 8.11%"],
       ["复购", "customer_unique_id 名下订单 ≥ 2", "全量 3.12%；控制观察期后 5.51%"],
       ["差评", "review_score ≤ 2", "占比 12.77%"],
       ["时间窗", "2017-01 – 2018-08", "首尾月份不完整，已截断"]],
      widths=[2.6, 7.2, 6.8], font_size=8.5)

# ------------------------------------------------------------ 3 第1章
h1(doc, "3", "生意盘子：先定义什么叫「正常」")
body(doc, "第 1 章的任务不是「介绍数据」，而是为后面三章建立参照系。"
          "它回答三个问题：盘子多大、怎么长的、靠什么撑着。")
table(doc,
      ["观察", "结论"],
      [["规模", "2017-01 至 2018-08 累计 GMV 1,318 万美元、9.6 万单，AOV 137 美元（不含运费）"],
       ["节奏", "月度 GMV 从 11.2 万涨到 83.9 万，20 个月 7.5 倍；2017-11 黑五达 98.8 万（月均 1.5 倍）"],
       ["地域", "SP 一州占 38.4%，前三州合计 63.4%，Top10 覆盖 87.9%"],
       ["品类", "第一名仅 9.33%，Top10 只覆盖 62.5%"],
       ["支付", "信用卡 78.45%；boleto（线下单据）17.97%"]],
      widths=[2.2, 13.8], font_size=8.5)

quote(doc, "地域是收敛的（Top10 88%），品类是发散的（Top10 62.5%）——"
           "资源按州配，品类只能广撒试探。")

image(doc, "ch1_01_monthly_gmv.png", "图 1　月度 GMV 与 AOV：黑五冲高后进入 80–98 万平台期", 14.8)
image(doc, "ch1_02_state.png", "图 2　州 GMV 分布：圣保罗一州占 38.4%", 10.6)

image(doc, "ch1_03_category.png", "图 3　品类 GMV 分布：第一名仅 9.3%，Top10 合计 62.5%", 10.6)

h2(doc, "本章核对数字")
table(doc,
      ["指标", "值", "指标", "值"],
      [["全部订单", "99,441", "宽表行数（有明细）", "98,666"],
       ["已送达订单", "96,478", "GMV（全期）", "13,221,498.11"],
       ["运费合计", "2,198,275.64", "AOV 不含 / 含运费", "137.04 / 159.83"],
       ["20 个月订单", "96,211", "20 个月 GMV", "13,181,027.13"],
       ["月均订单", "4,811", "月均 GMV", "659,051.36"],
       ["2017-11 订单", "7,289", "2017-11 GMV", "987,765.37"]],
      widths=[3.6, 4.4, 4.6, 3.4], font_size=8)

# ------------------------------------------------------------ 4 第2章
h1(doc, "4", "履约质量：问题在哪、有多大")
body(doc, "第 1 章留下的假设是「物流是增长瓶颈」。第 2 章用三个维度定位：慢不慢（分布）、"
          "哪里慢（空间）、什么时候慢（时间）。")
table(doc,
      ["指标", "结果"],
      [["样本", "96,470 单（已送达且有送达时间）"],
       ["配送时长", "均值 12.50 天，中位数 10 天，P90 23 天，最长 210 天"],
       ["分布", "42.8% 落在 8–15 天；4.45% 超过 30 天"],
       ["超时", "6,534 单，超时率 6.77%；超时单平均超 10.6 天，准时单平均提前 13.5 天"],
       ["地域", "SP 8.70 天 / 超时率 4.49%；PA 23.73 天——快慢差 2.7 倍"],
       ["品类", "10.87–13.66 天，超时率 5.00%–7.56%——几乎没有区分度"],
       ["大促", "2018-03 平均 16.24 天、超时率 18.96%，是常态的 5 倍"]],
      widths=[2.2, 13.8], font_size=8.5)

quote(doc, "品类之间几乎没有差异（10.9–13.7 天），而州之间差 2.7 倍——"
           "这一条排除了「某些商品难配送」的解释，把问题锁定在地理上。")

image(doc, "ch2_01_dist.png", "图 4　配送时长分布：近一半订单 8–15 天送达", 11.2)

image(doc, "ch2_02_state.png", "图 5　分州配送表现：快慢差 2.7 倍", 10.4)
image(doc, "ch2_03_monthly.png", "图 6　月度配送与超时率：大促月超时率是常态的 5 倍", 14.2)

h2(doc, "关键发现：承诺收紧的悖论")
body(doc, "如果只看实际天数，结论是「物流在改善」（12.75 → 7.66 天）。"
          "加上承诺天数（ETA）之后，才看到另一件事：")
table(doc,
      ["月份", "实际天数", "承诺天数", "缓冲", "超时率"],
      [["2017-01", "12.75", "40.2", "27.5 天", "2.93%"],
       ["2018-06", "9.16", "28.4", "19.2 天", "1.16%"],
       ["2017-11", "15.07", "23.2", "8.1 天", "12.40%"],
       ["2018-08", "7.66（最快）", "15.8", "8.1 天", "6.19%"]],
      widths=[3.0, 4.2, 3.4, 2.8, 2.6], font_size=9, highlight_rows=[3])

quote(doc, "承诺从 40 天压到 16 天，实际从 12.8 天降到 7.7 天，缓冲从 27 天缩到 8 天。"
           "同样的缓冲下，实际 15 天时超时率 12.4%，实际 7.7 天时只有 6.2%。"
           "超时率不是纯粹的物流问题，而是「承诺 × 履约」的函数。")

image(doc, "ch2_04_promise.png", "图 7　承诺 vs 实际：送得更快，但因为承诺收得更紧，反而更容易超时", 14.4)

# ------------------------------------------------------------ 5 第3章
h1(doc, "5", "时效与满意度：代价是断崖式的")
body(doc, "第 2 章证明「慢」，第 3 章量化「慢的代价」。样本为已送达且有评价的 95,824 单"
          "（覆盖率 99.3%；525 单有多条评价，按订单取平均）。")

h2(doc, "按超时程度分箱：断崖在哪")
table(doc,
      ["分箱", "订单数", "平均分", "差评率", "一星率"],
      [["准时或提前", "89,443", "4.291", "9.23%", "6.58%"],
       ["超 1–3 天", "1,852", "3.291", "32.18%", "25.11%"],
       ["超 4–7 天", "1,748", "2.106", "67.56%", "58.47%"],
       ["超 8–15 天", "1,601", "1.675", "79.95%", "70.14%"],
       ["超 15 天以上", "1,180", "1.728", "78.14%", "69.15%"]],
      widths=[3.6, 3.4, 3.2, 3.2, 3.2], font_size=9, highlight_rows=[4])

bullet(doc, "伤害是跳变的：从准时到超 1 天，平均分掉 1.0，差评率从 9% 跳到 32%")
bullet(doc, "超 8 天见底：1.675 与 1.728 几乎相同，再晚也不会更差")
bullet(doc, "补救窗口只在超时后 1–3 天：4 天后评分已崩到 2.11，补偿换不回评价")

image(doc, "ch3_01_cliff.png", "图 8　断崖曲线：评分是台阶式下跌，不是斜坡", 13.6)

h2(doc, "归因：超时只占 6.7%，却贡献 32.5% 的差评")
table(doc,
      ["类别", "订单数", "其中超时", "超时占比"],
      [["差评（1–2 星）", "12,236", "3,979", "32.52%"],
       ["中评（3 星）", "7,969", "696", "8.73%"],
       ["好评（4–5 星）", "75,619", "1,706", "2.26%"]],
      widths=[4.6, 3.8, 3.8, 3.8], font_size=9)

body(doc, "换算：超时订单的差评率约 62%，准时订单只有 9.2%——差 6.7 倍。")

image(doc, "ch3_02_attrib.png", "图 9　差评/中评/好评中的超时浓度对比", 14.6)

h2(doc, "交叉验证：排除「偏远州用户更挑剔」")
table(doc,
      ["州", "准时组平均分", "超时组平均分", "落差"],
      [["SP", "4.33", "2.55", "−1.78"],
       ["RJ", "4.24", "1.91", "−2.33"],
       ["MG", "4.28", "2.36", "−1.92"],
       ["BA", "4.14", "2.36", "−1.78"],
       ["PA", "4.15", "1.92", "−2.23"]],
      widths=[3.4, 4.6, 4.6, 3.4], font_size=9)

quote(doc, "每个州的准时组都在 4.1–4.4，超时组都在 1.9–2.7。无论哪个州，超时都让评分掉 1.7–2.4 分。"
           "替代解释被排除——这是本章最重要的一步：光有相关不够，要主动反驳最强的反驳。")

image(doc, "ch3_03_state.png", "图 10　分州哑铃图：每个州都掉 1.7–2.4 分", 11.4)

# ------------------------------------------------------------ 6 第4章
h1(doc, "6", "复购验证：因果链闭合了吗")
body(doc, "第 3 章用的是「用户说了什么」（评分），第 4 章用「用户做了什么」（复购）。"
          "样本为首购于 2018-04 前的 71,186 名客户（保证至少 6 个月观察期）。")

h2(doc, "三个测量陷阱（先诊断，再分析）")
table(doc,
      ["陷阱", "现象", "处理"],
      [["右截断", "2018-08 首购的客户只有 2 个月窗口，复购率被低估至 0.81%", "只取首购 ≤ 2018-04"],
       ["拆单", "30.93% 的「第二单」发生在首单后 1 天内——不是复购，是同一笔购买被拆单", "单独报告，不并入复购率"],
       ["地板效应", "整体复购率仅 4–5%，任何因素都拉不开差距", "解读时说明效应受限"]],
      widths=[2.4, 9.2, 4.4], font_size=8.5)

h2(doc, "首单体验 × 是否复购")
table(doc,
      ["分组", "客户数", "复购率"],
      [["准时 · 好评", "52,052", "3.82%"],
       ["准时 · 中评", "5,555", "3.65%"],
       ["准时 · 差评", "7,839", "3.66%"],
       ["超时 · 好评", "1,225", "3.67%"],
       ["超时 · 中评", "538", "3.35%"],
       ["超时 · 差评", "3,371", "2.52%"]],
      widths=[4.8, 4.8, 4.8], font_size=9, highlight_rows=[5])

body(doc, "卡方检验（2×2）：准时 vs 超时 χ²=11.09（p=8.7e-04）；好评 vs 差评 χ²=6.04（p=0.014）；"
          "准时·好评 vs 超时·差评 χ²=14.53（p=1.4e-04）。三项均显著。")

quote(doc, "方向明确、统计显著，但绝对幅度只有 1.3 个百分点（相对 −34%）。"
           "原因是地板效应：平台整体复购率只有 3–5%，体验好坏都很难拉开差距。"
           "这条链成立但不强——它解释了「为什么增长没有复利」，但不足以说「改善体验就能翻倍」。")

image(doc, "ch4_01_cohort.png", "图 11　按首购月份看复购率：2017 年 cohort 有 4.6–5.5%，2018 年下半年只剩 1%", 11.4)

image(doc, "ch4_02_quad.png", "图 12　首单「超时 + 差评」的客户复购率只有准时好评组的 2/3", 10.6)

h2(doc, "一个指标，三个口径")
table(doc,
      ["口径", "数值", "什么时候用"],
      [["数据原样", "3.12%", "和别人对齐、对外沟通"],
       ["剔除同日拆单", "≈ 2.2%", "看真实跨期行为"],
       ["控制观察期（2017 cohort）", "4.6–5.5%", "看长期忠诚度"]],
      widths=[5.8, 3.4, 6.8], font_size=9)

body(doc, "脱离品类谈复购率没有意义：快消月复购 30%+、服饰季度 20–30%、"
          "而家具家居礼品年复购 5% 左右是正常的。真正的问题不是「复购低」，"
          "而是「这门生意只能靠不断拉新」。")

# ------------------------------------------------------------ 7 结论
h1(doc, "7", "结论与建议")

image(doc, "ch5_01_chain.png", "图 13　因果链：一次大促的履约崩塌，如何影响两年后的增长", 15.0)

h2(doc, "三条建议（按单位成本效果排序）")
table(doc,
      ["#", "建议", "依据", "效果", "成本"],
      [["1", "大促期间 ETA 放宽 15%", "缓冲 6.5 天时超时率 19%，缓冲 19 天时仅 1.16%", "减 1,100 单超时 / 590 个差评", "零"],
       ["2", "按州设 SLA", "SP 8.7 天 vs PA 23.7 天，统一承诺两头都不公平", "减 2,190 单超时 / 1,160 个差评", "低"],
       ["3", "超时预警前置 1 天", "超 4 天后评分已崩到 2.11，补救无效", "减 320 个差评", "中"]],
      widths=[0.9, 4.4, 6.2, 4.5, 1.4], font_size=8, align_first_left=False)

quote(doc, "超时率不是物流指标，是承诺管理指标。同样的履约能力，承诺定得松一点，差评就少一半。")

h2(doc, "必须诚实的一段：财务收益很小")
body(doc, "把三条建议折算成 GMV：每减少 1 个差评 ≈ 挽回 0.013 个复购客户；每复购客户 ≈ 205 元；"
          "三条建议共减少约 2,000 个差评 ≈ 5,400 元，占半年 GMV 的 0.04%。")
body(doc, "如果只用 GMV 衡量，这三条不值得做。但这不是结论，是数据边界的暴露——"
          "本数据集没有「转化率」和「卖家留存」，而评分的真实价值恰在这两处："
          "4.3 分与 2.1 分的店铺转化率差多少？评分差导致多少卖家流失？都算不出来。")

# ------------------------------------------------------------ 8 局限
h1(doc, "8", "局限与展望")
table(doc,
      ["局限", "影响", "需要补什么"],
      [["无转化率 / 曝光数据", "无法量化评分的商业价值", "埋点数据（曝光、点击、下单）"],
       ["复购率仅 4–5%", "复购类结论统计功效低", "更长的时间窗"],
       ["观察期右截断", "近期 cohort 复购率被低估", "已用 2018-04 前首购控制"],
       ["无成本数据", "算不出毛利，只能谈 GMV", "财务口径"],
       ["观察性数据", "因果靠控制变量推断，非随机实验", "建议 1 用 A/B 测试验证"]],
      widths=[4.4, 6.4, 5.2], font_size=8.5)

body(doc, "三条建议均需验证：建议 1 用 A/B 测试，建议 2 用分州对照，建议 3 用小流量试点；"
          "成功标准分别是超时率降 50%、偏远州超时率降 30%、预警组差评率降 15 个百分点。", size=10)

h2(doc, "方法与复盘")
bullet(doc, "口径决定结论：超时率按整天 6.77%、按小时 8.11%；复购率 3.12% 与 5.51%。报数先报口径。")
bullet(doc, "相关之后要反驳自己：按州验证，每个州都掉 1.7–2.4 分。")
bullet(doc, "显著不等于重要：复购差异 p<0.001 但只有 1.3 个百分点；财务收益折算仅 5,400 元。")

h2(doc, "复现与数据来源")
body(doc, "环境 MySQL 8.0 + Python 3.14；执行 sql/01_load_all.sql 建库导入，依次运行 sql/02~05，"
          "再由 src/ 下的脚本取数与出图。数据来源：Kaggle，Brazilian E-Commerce Public Dataset by Olist"
          "（9 张表 / 155 万行 / 2016-09 至 2018-10）。", size=10)
body(doc, "字段说明见 docs/data_dictionary.md，数字校验过程见 docs/reconciliation_log.md。", size=10)

doc.save(OUT)
print("saved:", OUT, OUT.stat().st_size // 1024, "KB")
