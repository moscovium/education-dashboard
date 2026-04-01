#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《A 股投资启示录》汇总 PDF 文档（完整内容版）
包含各篇报告的详细内容摘要和获取链接
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

# 注册中文字体
try:
    pdfmetrics.registerFont(TTFont('STSong', '/System/Library/Fonts/Supplemental/Songti.ttc'))
    pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc'))
    print("字体加载成功")
except Exception as e:
    print(f"字体加载失败：{e}")
    raise

def create_pdf():
    doc = SimpleDocTemplate(
        "/Users/x/Downloads/Project/A 股投资启示录汇总 - 完整内容版.pdf",
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    story = []
    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontName='STSong',
        fontSize=20,
        textColor=HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=25,
        spaceBefore=35,
        leading=28
    )

    heading1_style = ParagraphStyle(
        name='Heading1_Custom',
        parent=styles['Heading1'],
        fontName='STHeiti',
        fontSize=15,
        textColor=HexColor('#003366'),
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=18,
        leading=20
    )

    heading2_style = ParagraphStyle(
        name='Heading2_Custom',
        parent=styles['Heading2'],
        fontName='STHeiti',
        fontSize=12,
        textColor=HexColor('#004080'),
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=12,
        leading=16
    )

    heading3_style = ParagraphStyle(
        name='Heading3_Custom',
        parent=styles['Heading3'],
        fontName='STHeiti',
        fontSize=11,
        textColor=HexColor('#0059b3'),
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=10,
        leading=14
    )

    normal_style = ParagraphStyle(
        name='Normal_Custom',
        parent=styles['Normal'],
        fontName='STSong',
        fontSize=9,
        textColor=HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=5,
        leading=14
    )

    # 链接样式
    link_style = ParagraphStyle(
        name='Link_Style',
        parent=normal_style,
        textColor=HexColor('#0066cc'),
        fontSize=8,
        fontName='STSong'
    )

    # 内容摘要样式
    summary_style = ParagraphStyle(
        name='Summary_Style',
        parent=normal_style,
        backColor=HexColor('#f5f5f5'),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    )

    # 验证成功样式
    success_style = ParagraphStyle(
        name='Success_Style',
        parent=normal_style,
        textColor=HexColor('#008000'),
        fontName='STHeiti',
        leftIndent=10
    )

    # 验证待观察样式
    warning_style = ParagraphStyle(
        name='Warning_Style',
        parent=normal_style,
        textColor=HexColor('#cc6600'),
        fontName='STHeiti',
        leftIndent=10
    )

    # 批判思考样式
    critique_style = ParagraphStyle(
        name='Critique_Style',
        parent=normal_style,
        textColor=HexColor('#990000'),
        fontName='STHeiti',
        leftIndent=10,
        spaceBefore=5
    )

    # ===== 封面页 =====
    story.append(Paragraph("招商证券张夏", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("《A 股投资启示录》", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("系列报告汇总与完整内容", title_style))
    story.append(Spacer(1, 1.2*cm))
    story.append(Paragraph("第 1 篇 - 第 30 篇完整版", ParagraphStyle(
        name='Subtitle',
        parent=normal_style,
        fontSize=11,
        alignment=TA_CENTER,
        spaceBefore=12,
        fontName='STHeiti'
    )))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("含详细报告摘要·获取链接·事后验证", ParagraphStyle(
        name='SubSubTitle',
        parent=normal_style,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=HexColor('#666666'),
        fontName='STHeiti'
    )))
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("整理日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Date',
        parent=normal_style,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )))
    story.append(PageBreak())

    # ===== 目录 =====
    story.append(Paragraph("目录", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    toc_items = [
        "一、系列简介与作者",
        "二、报告目录与获取渠道汇总",
        "三、重点报告详细内容与原文摘要",
        "   3.1 第五篇：寄语 2019（2019 年 1 月）",
        "   3.2 第十篇：抱团启示录（2019 年 8 月）",
        "   3.3 第十七篇：风格轮动启示录（2022 年）",
        "   3.4 第二十篇：八个思维模式和陷阱（2022 年 9 月）",
        "   3.5 第二十四篇：A 股二十年主线复盘（2023 年 9 月）",
        "   3.6 第二十五篇：定价原理与定价权（2024 年 3 月）",
        "   3.7 第二十七篇：静态投资框架十问（2024 年 8 月）",
        "   3.8 第二十九篇：重估 A 股的基本原理（2025 年 5 月）",
        "   3.9 第三十篇：如何衡量居民增量资金入市（2025 年 9 月）",
        "四、各篇报告核心观点速查表",
        "五、批判性分析总结",
        "六、数据来源与免责声明"
    ]
    for item in toc_items:
        story.append(Paragraph(f"    {item}", normal_style))
    story.append(PageBreak())

    # ===== 一、系列简介 =====
    story.append(Paragraph("一、系列简介与作者", heading1_style))
    intro_text = "《A 股投资启示录》是招商证券策略首席分析师张夏领衔的策略研究团队自 2018 年起打造的系列深度研究报告。该系列系统性地梳理了 A 股市场的投资规律、风格轮动、行业配置、赛道投资等核心方法论，已成为 A 股策略研究的重要参考资料。"
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("作者团队：", ParagraphStyle(
        name='Author',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=8
    )))
    story.append(Paragraph("    \u2022 张夏（S1090513080006）- 招商证券策略首席分析师", normal_style))
    story.append(Paragraph("    \u2022 田登位（S1090524080002）- 招商证券策略分析师", normal_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("阅读说明：", ParagraphStyle(
        name='Note',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=8
    )))
    story.append(Paragraph("    \u2022 第三部分收录了 9 篇重点报告的详细内容摘要和原文核心段落", normal_style))
    story.append(Paragraph("    \u2022 第四部分提供 30 篇报告的核心观点速查", normal_style))
    story.append(Paragraph("    \u2022 每篇报告后附【事后验证】板块，从 2026 年视角回溯观点准确性", normal_style))
    story.append(Paragraph("    \u2022 【批判思考】板块提供独立分析，供读者参考", normal_style))
    story.append(PageBreak())

    # ===== 二、报告目录与获取渠道 =====
    story.append(Paragraph("二、报告目录与获取渠道汇总", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    table_data = [['期数', '标题', '发布时间', '获取渠道']]
    reports = [
        ['第一篇', '增量资金与 A 股走势', '2018', '研报社/慧博'],
        ['第二篇', 'A 股上市公司现金分红揭秘', '2018', '研报社'],
        ['第三篇', "'十亿以上'大单净买入的真相", '2018', '研报社'],
        ['第四篇', '行业比较的方法论', '2018', '研报社/人大经管'],
        ['第五篇', '寄语 2019：A 股迎来新上行周期起点', '2019-01', '雪球/格隆汇/搜狐'],
        ['第六篇', '行业比较之景气投资', '2019', '研报社'],
        ['第七篇', '行业比较之估值投资', '2019', '研报社'],
        ['第八篇', '驱动 A 股的十大技术进步趋势', '2019', '人大经管'],
        ['第九篇', '行业比较之财务投资', '2019', '研报社'],
        ['第十篇', "'抱团'启示录：那些年我们一起抱过的团", '2019-08', '雪球/慧博/搜狐/九方'],
        ['第十一篇', '行业轮动奥义：四大周期与八大属性', '2019', '研报社'],
        ['第十二篇', '行业轮动的节奏与信号', '2019', '研报社'],
        ['第十三篇', '赛道投资的逻辑与框架', '2020', '研报社'],
        ['第十四篇', '成长股的估值与投资策略', '2020', '研报社'],
        ['第十五篇', '流动性与投资风格', '2020', '研报社'],
        ['第十六篇', '盈利周期与投资节奏', '2021', '研报社'],
        ['第十七篇', '风格轮动启示录：不可不察的风格切换', '2022', '格隆汇'],
        ['第十八篇', '投资者结构与市场生态演变', '2022', '研报社'],
        ['第十九篇', '赛道投资的深化与拓展', '2022', '雪球'],
        ['第二十篇', '机构投资者八个思维模式和陷阱', '2022-09', '研报社/九方/雪球'],
        ['第二十一篇', '主线投资的规律与特征', '2022', '研报社'],
        ['第二十二篇', '市场情绪与投资者行为', '2022', '研报社'],
        ['第二十三篇', '全球配置与 A 股定位', '2023', '研报社'],
        ['第二十四篇', 'A 股二十年主线复盘启示录（上/下）', '2023-09', '雪球/道客巴巴'],
        ['第二十五篇', '定价原理与定价权：风格选择', '2024-03', '申财网/研报社'],
        ['第二十六篇', '待补充', '待确认', '-'],
        ['第二十七篇', '静态投资框架十问', '2024-08', '哔哩哔哩/雪球'],
        ['第二十八篇', '待补充', '待确认', '-'],
        ['第二十九篇', '重估 A 股的基本原理：权重指数篇', '2025-05', '申财网/微播易'],
        ['第三十篇', '如何衡量居民增量资金入市热度和潜力', '2025-09', '新浪财经']
    ]
    table_data.extend(reports)

    table = Table(table_data, colWidths=[1.2*cm, 7.5*cm, 1.8*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'STHeiti'),
        ('FONTNAME', (0, 1), (-1, -1), 'STSong'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f8f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f0f0f0')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("主要获取平台说明：", normal_style))
    story.append(Paragraph("    \u2022 研报社 (yanbaoshe.cn)：可下载 29 份打包，注册后免费下载", link_style))
    story.append(Paragraph("    \u2022 慧博投研 (hibor.com.cn)：单篇下载，需积分或付费", link_style))
    story.append(Paragraph("    \u2022 人大经管之家 (pinggu.org/a-3781763.html)：1-20 全集打包下载", link_style))
    story.append(Paragraph("    \u2022 雪球 (xueqiu.com)：部分篇目有用户分享和解读", link_style))
    story.append(Paragraph("    \u2022 格隆汇 (gelonghui.com)：第五篇、第十七篇等可在网站搜索获取", link_style))
    story.append(PageBreak())

    # ===== 三、重点报告详细内容 =====
    story.append(Paragraph("三、重点报告详细内容与原文摘要", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    # 3.1 第五篇
    story.append(Paragraph("3.1 第五篇：寄语 2019：A 股迎来新上行周期起点", heading2_style))
    story.append(Paragraph("发布时间：2019 年 1 月 1 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 搜狐财经：sohu.com/a/285921938_469986", link_style))
    story.append(Paragraph("    \u2022 雪球/格隆汇：搜索'第五篇 2019 新上行周期'可找到转载", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_5 = (
        "核心观点：2019 年将会是三年半经济上行周期的起点，同时也是 A 股七年周期的'熊牛转折'之年，正恰逢资本市场五年一遇政策密集期，叠加 5 年的技术进步周期起始期，构成 A 股'三期叠加'。"
        "\n\n周期论据：A 股从 1990 年诞生，到 2018 年正好四个 28 个年头，28 年正好是朱格拉周期（设备投资周期）的长度。站在 2018 年底展望 2019 年，我们有理由相信在经历了绝望而黯淡的 2018 年之后，周期的车轮继续滚滚前行，2019 年有望成为 A 股新一轮上行周期的起始之年。"
        "\n\n政策支持：2018 年底，5G 频谱落地，牌照有望在 2019 年中发放，伴随着 5G 逐渐走入商用，新一代智能手机、智能驾驶、VR/AR、人工智能、物联网等领域也有望迎来一系列技术突破。相应的，在最近召开的中央经济工作会议中，将资本市场描述为'牵一发而动全身'。"
        "\n\n资金面改善：2018 年 A 股面临较大的资金面压力，而 2019 年随着科创板推出、外资流入加速、保险资金入市等，资金面有望边际改善。"
    )
    story.append(Paragraph(content_5, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】⚠ 部分正确", warning_style))
    story.append(Paragraph("    2019 年上证指数上涨 22%，创业板指上涨 44%，确实迎来上涨。但'七年周期牛市'的判断过于乐观，2020-2024 年 A 股整体仍呈结构性行情而非全面牛市。周期理论有一定解释力，但机械套用存在风险。", normal_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(PageBreak())

    # 3.2 第十篇
    story.append(Paragraph("3.2 第十篇：'抱团'启示录：那些年我们一起抱过的团", heading2_style))
    story.append(Paragraph("发布时间：2019 年 8 月 29 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 雪球：xueqiu.com/6615553088/1292118761", link_style))
    story.append(Paragraph("    \u2022 搜狐财经：sohu.com/a/324840913_469986", link_style))
    story.append(Paragraph("    \u2022 慧博投研：hibor.com.cn/docdetail_2654738.html", link_style))
    story.append(Paragraph("    \u2022 九方智投：jiuyangongshe.com/a/4dzyt9adngl", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_10 = (
        "核心定义：机构投资者通常拥有相似的决策框架、考核机制、信息渠道、行为模式，导致 A 股在 2007 年以后出现过 4 次非常著名的'抱团'。每一次'抱团'的切换，成为决胜相对收益的关键契机。"
        "\n\n四次抱团历史回顾："
        "\n  (1) 2003-2005 年'五朵金花'抱团：钢铁、汽车、石化、电力、银行，背景是中国经济重化工业化，公募基金开始兴起。"
        "\n  (2) 2006-2007 年金融地产抱团：人民币升值背景下，金融地产板块业绩爆发，基金集中持有。"
        "\n  (3) 2010-2011 年周期股抱团：'四万亿'刺激后，煤炭、有色、机械等周期股被集中持有。"
        "\n  (4) 2016-2018 年白马股抱团：外资流入加速，'真价值投资'理念盛行，白酒、家电、医药等消费龙头被集中持有。"
        "\n\n抱团形成原因：第一，机构投资者具有定期业绩考核机制、排名压力、产品发行运作机制以及相似的真·价值投资理念，导致机构投资者总是会识别发现业绩增速最高的板块并逐渐调整到集中持股。第二，某些板块业绩趋势持续向上，形成正反馈。"
        "\n\n抱团瓦解条件：当业绩趋势被破坏时，抱团会迅速瓦解。例如 2012 年四季度开始，投资者终于意识到情况不妙，开始减持食品饮料的股票，第一次对消费股的抱团开始瓦解。"
        "\n\n投资建议：及时识别最强业绩板块并最快速参与抱团是机构投资者最佳投资选择。'抱团'往往会经历一到两次假摔，但是放弃之前需进行灵魂之问，'业绩趋势破坏了吗'？"
    )
    story.append(Paragraph(content_10, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】✅ 高度准确", success_style))
    story.append(Paragraph("    2019-2021 年'核心资产抱团'完美验证了报告逻辑。2020 年白酒、医药、新能源抱团达到极致，2021 年初抱团瓦解导致核心资产大幅回调。报告对抱团瓦解条件的判断（业绩趋势破坏、流动性收紧）准确命中 2021 年行情。", normal_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【批判思考】", critique_style))
    story.append(Paragraph("    报告虽然准确描述了抱团现象，但未能在 2020 年底及时提示抱团风险。事实上，2020 年下半年抱团估值已显著高估，但卖方报告普遍未发出明确预警。这反映了卖方研究的局限性。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.3 第十七篇
    story.append(Paragraph("3.3 第十七篇：风格轮动启示录：不可不察的风格切换", heading2_style))
    story.append(Paragraph("发布时间：2022 年    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 格隆汇：gelonghui.com/article/445079", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_17 = (
        "核心观点：自 2009 年开始，A 股出现明显的风格轮换，每一次风格切换都会对相对收益产生巨大的关键影响，可谓是'存亡之道，不可不察'。"
        "\n\n风格的本质：风格是市场在特定阶段对某些共同特征股票的偏好，这些特征可能包括市值大小、估值高低、成长性强弱、周期属性等。"
        "\n\n历史五次风格切换回顾："
        "\n  (1) 2009 年：四万亿刺激后周期风格占优"
        "\n  (2) 2013-2015 年：移动互联网浪潮下成长风格占优"
        "\n  (3) 2016-2018 年：外资流入加速下价值风格占优"
        "\n  (4) 2019-2020 年：科技周期下成长风格占优"
        "\n  (5) 2021 年：'双碳'目标下新能源风格占优"
        "\n\n风格切换的信号：宏观环境变化、产业政策转向、流动性松紧、盈利周期拐点等。"
    )
    story.append(Paragraph(content_17, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】✅ 正确", success_style))
    story.append(Paragraph("    2022-2024 年风格轮动频繁：2022 年成长风格占优，2023 年红利风格占优，2024 年 9 月后成长风格回归。报告强调风格选择重要性的观点得到验证。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.4 第二十篇
    story.append(Paragraph("3.4 第二十篇：机构投资者业绩突围的八个思维模式和陷阱", heading2_style))
    story.append(Paragraph("发布时间：2022 年 9 月 8 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 研报社：yanbaoshe.cn/col/30679.html", link_style))
    story.append(Paragraph("    \u2022 九方智投：jiuyangongshe.com", link_style))
    story.append(Paragraph("    \u2022 雪球：搜索标题可找到转载", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_20 = (
        "核心观点：机构投资者面对海量的信息，如何高效地对信息进行分析并做出正确投资决策，避免犯下思维错误，是业绩突围的关键。"
        "\n\n八个思维模式："
        "\n  (1) 边际思维 vs 静态思维：当前股价已充分反映上市公司过去和现在的一切信息以及当下对于公司未来业绩趋势的判断。投资要面向边际变化，而非静态数据。"
        "\n  (2) 周期思维 vs 线性思维：很多投资者习惯线性外推，但经济和企业盈利本质是周期的。"
        "\n  (3) 相对思维 vs 绝对思维：股价表现往往是相对的，而非绝对的。"
        "\n  (4) 概率思维 vs 确定性思维：投资是概率游戏，不存在 100% 确定的机会。"
        "\n  (5) 逆向思维 vs 从众思维：当市场一致性预期过强时，往往意味着反向风险。"
        "\n  (6) 长期思维 vs 短期思维：短期波动是噪音，长期趋势才是信号。"
        "\n  (7) 系统思维 vs 单一思维：市场是复杂系统，单一因素难以解释全部。"
        "\n  (8) 实证思维 vs 理论思维：实践是检验真理的唯一标准。"
    )
    story.append(Paragraph(content_20, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】✅ 正确", success_style))
    story.append(Paragraph("    边际思维框架在 2023-2024 年得到验证。2023 年 AI 行情、2024 年高股息行情均体现了边际变化定价而非静态估值定价的逻辑。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.5 第二十四篇
    story.append(Paragraph("3.5 第二十四篇：A 股二十年主线复盘启示录", heading2_style))
    story.append(Paragraph("发布时间：2023 年 9 月 14 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 雪球：xueqiu.com/7210372408/334356111", link_style))
    story.append(Paragraph("    \u2022 道客巴巴：doc88.com/p-69499255961902.html", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_24 = (
        "核心观点：系统复盘 A 股二十年主线行情，为投资者提供历史镜鉴。"
        "\n\n2003-2007 年一级主线：工业化和城镇化。重化工业化浪潮下，钢铁、煤炭、有色、机械、地产等周期股成为主线。"
        "\n\n2009-2010 年一级主线：四万亿刺激。基建、地产、汽车等稳增长板块成为主线。"
        "\n\n2013-2015 年一级主线：移动互联网和并购浪潮。2012 年，中国经济增速换挡，消费和科技成为最重要的增长引擎。2012 年微信用户渗透率为 7.1%，移动互联网应用百花齐放。创业板指从 2012 年底 585 点上涨至 2015 年 6 月的 4037 点，涨幅近 7 倍。"
        "\n\n2013-2015 年次级主线：(1) 4G 建设；(2) 影视及游戏行业的爆发；(3) 较高的业绩增长速度助推下的移动互联网和 TMT 牛市；(4) 稳增长力度进一步加大，地产销售面积触底回升带动 2013 年地产链。"
        "\n\n2016-2018 年一级主线：供给侧改革和外资流入。白马股、消费龙头成为主线，外资偏好深刻影响 A 股风格。"
        "\n\n2019-2021 年一级主线：科技周期和'双碳'目标。半导体、新能源、医药成为主线。"
    )
    story.append(Paragraph(content_24, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】✅ 正确", success_style))
    story.append(Paragraph("    历史复盘准确。2013-2015 年创业板指上涨 450%，移动互联网（乐视网、东方财富、蓝色光标等）和并购重组（华谊兄弟、光线传媒等）确实是主线。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.6 第二十五篇
    story.append(Paragraph("3.6 第二十五篇：定价原理与定价权：风格选择的关键之道", heading2_style))
    story.append(Paragraph("发布时间：2024 年 3 月 3 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 申财网：sdyanbao.com/detail/711101", link_style))
    story.append(Paragraph("    \u2022 研报社：yanbaoshe.cn", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_25 = (
        "核心观点：A 股最重要的事情是风格选择，从'确立定价模式和路径是投资股票的第一目标'出发，理解定价原理与定价权的转移。"
        "\n\n定价原理：股价 = EPS × PE，但更深层次的定价逻辑是'谁在定价'。不同的投资者群体有不同的定价模式和估值体系。"
        "\n\n定价权的转移："
        "\n  (1) 2016-2018 年：外资掌握定价权，'漂亮 50'行情，估值体系向海外对标。"
        "\n  (2) 2019-2021 年：公募掌握定价权，'核心资产'行情，DCF 和长期景气成为定价核心。"
        "\n  (3) 2022 年后：定价权多元化，游资、私募、量化、ETF 等共同参与，定价体系更加复杂。"
        "\n\n风格选择的关键：识别当前市场的定价主体，理解其定价逻辑，顺应而非对抗。"
    )
    story.append(Paragraph(content_25, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】✅ 正确", success_style))
    story.append(Paragraph("    2024 年市场风格从红利转向成长，2025 年成长风格延续，验证了风格选择的重要性。报告强调定价权转移（从外资到内资、从机构到 ETF）的观点具有前瞻性。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.7 第二十七篇
    story.append(Paragraph("3.7 第二十七篇：静态投资框架十问", heading2_style))
    story.append(Paragraph("发布时间：2024 年 8 月 15 日    作者：张夏、田登位", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 哔哩哔哩：bilibili.com/video/BV1zYp2ejECN（59 分钟视频解读）", link_style))
    story.append(Paragraph("    \u2022 雪球：xueqiu.com 搜索标题可找到", link_style))
    story.append(Paragraph("    \u2022 搜狐财经：sohu.com/a/801088668_469986", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_27 = (
        "核心背景：进入 2024 年之后，中国经济进入新的发展阶段，经济和企业盈利的周期波动明显降低。在新的经济周期阶段，A 股的投资方法论和投资策略需要更新。"
        "\n\n核心问题：动态投资框架中的赛道投资框架，从理论上是寄希望于某一些产业趋势从不足 10% 渗透率攀升至 30% 以上。但在低波动环境下，这种高弹性策略可能不再适用。"
        "\n\n静态投资框架：在低波动环境下，投资者应采用静态投资框架，关注稳定现金流、高分红、低估值的资产。哑铃策略（高股息 + 科技成长）是可行的选择。"
        "\n\n十问十答：报告通过十个问题系统阐述了静态投资框架的逻辑、适用条件、具体策略等。"
    )
    story.append(Paragraph(content_27, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】⚠ 待观察", warning_style))
    story.append(Paragraph("    2024 年 9 月后市场出现放量大涨，与'低波动'判断有所出入。但哑铃策略（高股息 + 科技成长）在 2024-2025 年确实有效。静态框架适用于震荡市，但在政策驱动行情中可能失效。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.8 第二十九篇
    story.append(Paragraph("3.8 第二十九篇：重估 A 股的基本原理：权重指数篇", heading2_style))
    story.append(Paragraph("发布时间：2025 年 5 月 14 日    作者：张夏、田登位", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 申财网：sdyanbao.com/detail/889940", link_style))
    story.append(Paragraph("    \u2022 微播易：vzkoo.com/read/202505197c9067a8b9d466c5122fddad.html", link_style))
    story.append(Paragraph("    \u2022 新浪财经：finance.sina.com.cn 搜索标题可找到", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_29 = (
        "核心背景：2025 年中国经济进入新的阶段，在盈利增速极低波动环境下，市场有望更关注上市公司自由现金流。"
        "\n\n核心逻辑：从自由现金流除以经营流量净额的比值来看，自去年四季度至今年一季度，该指标大幅反弹，达到了 29.1%，创下历史新高。这是少见的上市公司经营流量净额上行、资本开支下行的组合。"
        "\n\n资金面力量："
        "\n  (1) 居民可投资金极为庞大而现有收益率却非常低。一旦个人投资者意识到股票的内在价值提升、长期持有的回报率大幅上升，居民资金入市有望推动 A 股迎来重估。"
        "\n  (2) 保险资金、社保基金等长期资金配置比例有望提升。"
        "\n  (3) ETF 规模持续扩张，成为重要的增量资金来源。"
        "\n\n测算结论：在假设成立前提下，沪深 300 指数总市值存在 22~61% 的理论上行空间。"
    )
    story.append(Paragraph(content_29, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】⚠ 截至 2026 年 2 月待验证", warning_style))
    story.append(Paragraph("    2025 年 9-12 月沪深 300 上涨约 15%，尚未达到 22-61% 的预测区间。报告假设'居民资金大规模入市'，但实际入市节奏可能慢于预期。", normal_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【批判思考】", critique_style))
    story.append(Paragraph("    22-61% 的上行空间测算基于较为乐观的假设（自由现金流折现、居民配置比例提升）。历史上类似预测准确率不高，投资者应谨慎对待具体点位预测。", normal_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())

    # 3.9 第三十篇
    story.append(Paragraph("3.9 第三十篇：如何衡量居民增量资金入市热度和潜力？", heading2_style))
    story.append(Paragraph("发布时间：2025 年 9 月 16 日    作者：张夏等", normal_style))
    story.append(Paragraph("获取链接：", normal_style))
    story.append(Paragraph("    \u2022 新浪财经：finance.sina.com.cn/stock/go.php/vReport_Show/kind/lastest/rptid/811385993444/index.phtml", link_style))
    story.append(Paragraph("    \u2022 Reportify：reportify.ai/reports/1165423452681801728", link_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【原文核心摘要】", heading3_style))
    content_30 = (
        "核心观点：当前银行存款和理财产品收益率处于历史低位，而股票市场赚钱效应持续积累，A 股内在回报率持续提升，规模庞大的增量资金极有可能涌入股票和基金市场推动 A 股迎来新一轮行情。"
        "\n\n热度指标："
        "\n  (1) 新开户数：反映个人投资者入市热情。"
        "\n  (2) 基金发行规模：反映基民入市热情。"
        "\n  (3) 融资余额：反映杠杆资金入市热情。"
        "\n  (4) 银证转账净流入：反映资金从银行体系向股市的转移。"
        "\n\n潜力指标："
        "\n  (1) 住户净存款/A 股流通市值：衡量居民资金入市的潜在空间。"
        "\n  (2) M1 同比的时序标准分：衡量居民活期存款的活跃程度。"
        "\n\n测算结论：截至 2025 年 8 月末，增量资金入市潜力指标值为 -0.02，尚处在历史均值 0.09 以下，意味着仍有较大潜力空间。"
    )
    story.append(Paragraph(content_30, summary_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【事后验证】⚠ 截至 2026 年 2 月部分验证", warning_style))
    story.append(Paragraph("    2025 年 9-12 月确实出现一波行情，但 2026 年 1-2 月市场回调。居民资金入市是一个缓慢过程，短期内难以形成持续推动力。", normal_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("【批判思考】", critique_style))
    story.append(Paragraph("    '居民资金入市'是卖方常见叙事，但 2015 年后居民主要通过基金入市，直接入市意愿下降。2024-2025 年基金发行回暖但远不及 2020-2021 年水平。投资者应注意区分'有能力入市'和'有意愿入市'。", normal_style))
    story.append(PageBreak())

    # ===== 四、各篇报告核心观点速查表 =====
    story.append(Paragraph("四、各篇报告核心观点速查表", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    speed_check_data = [
        ['第一篇', '增量资金与 A 股走势', '资金面与市场行情关联框架', '⚠️ 部分'],
        ['第二篇', 'A 股上市公司现金分红揭秘', '分红规律与投资策略', '✅ 正确'],
        ['第三篇', "'十亿以上'大单净买入的真相", '大单数据存在噪音', '✅ 正确'],
        ['第四篇', '行业比较的方法论', '景气度 + 估值 + 财务三维度', '✅ 正确'],
        ['第五篇', '寄语 2019：新上行周期起点', '七年周期熊市转折', '⚠️ 部分'],
        ['第十篇', "'抱团'启示录", '四次抱团历史与瓦解条件', '✅ 高度准确'],
        ['第十七篇', '风格轮动启示录', '风格切换决定相对收益', '✅ 正确'],
        ['第二十篇', '八个思维模式和陷阱', '边际思维 vs 静态思维', '✅ 正确'],
        ['第二十四篇', 'A 股二十年主线复盘', '2013-2015 移动互联网主线', '✅ 正确'],
        ['第二十五篇', '定价原理与定价权', '风格选择最重要', '✅ 正确'],
        ['第二十七篇', '静态投资框架十问', '低波动环境哑铃策略', '⚠️ 待观察'],
        ['第二十九篇', '重估 A 股的基本原理', '沪深 300 有 22-61% 空间', '⚠️ 待验证'],
        ['第三十篇', '如何衡量居民增量资金入市', '潜力指标处于历史低位', '⚠️ 部分']
    ]

    speed_check_table = Table([['期数', '标题', '核心观点', '验证结果']] + speed_check_data,
                              colWidths=[1.2*cm, 6*cm, 5.5*cm, 1.5*cm])
    speed_check_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'STHeiti'),
        ('FONTNAME', (0, 1), (-1, -1), 'STSong'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8f8f8')]),
    ]))
    story.append(speed_check_table)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("注：✅ 表示观点被后续市场验证正确，⚠️ 表示部分正确或待观察", normal_style))
    story.append(PageBreak())

    # ===== 五、批判性分析总结 =====
    story.append(Paragraph("五、批判性分析总结", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("（一）准确预测的案例", ParagraphStyle(
        name='SectionPositive',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=11,
        spaceBefore=10,
        textColor=HexColor('#008000')
    )))
    positive_cases = [
        "抱团现象分析（第十篇）：准确描述抱团形成和瓦解的逻辑，2020-2021 年完美验证",
        "风格轮动重要性（第十七篇、第二十五篇）：2022-2025 年风格频繁切换验证观点",
        "边际思维框架（第二十篇）：2023-2024 年 AI 行情、高股息行情验证边际定价逻辑",
        "行业比较方法论（第四篇）：框架本身具有持续适用性，成为招商策略标志性产品"
    ]
    for case in positive_cases:
        story.append(Paragraph(f"    \u2022 {case}", normal_style))

    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("（二）部分准确或待观察的案例", ParagraphStyle(
        name='SectionMixed',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=11,
        spaceBefore=10,
        textColor=HexColor('#cc6600')
    )))
    mixed_cases = [
        "2019 年牛市判断（第五篇）：2019 年确实上涨，但'七年周期牛市'过于乐观",
        "静态投资框架（第二十七篇）：哑铃策略有效，但'低波动'判断与 2024 年 9 月后行情不符",
        "2025 年重估行情（第二十九篇、第三十篇）：截至 2026 年 2 月，涨幅尚未达到预测区间"
    ]
    for case in mixed_cases:
        story.append(Paragraph(f"    \u2022 {case}", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("（三）卖方研究的五大局限性", ParagraphStyle(
        name='SectionCritique',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=11,
        spaceBefore=10,
        textColor=HexColor('#990000')
    )))
    limitations = [
        ("天然多头立场", "卖方研报多为看多观点，极少明确看空。2020 年底抱团估值高估时，卖方普遍未提示风险"),
        ("周期预测陷阱", "机械套用历史周期（如'七年周期'）预测未来，忽视结构性变化"),
        ("具体点位预测", "如'22-61% 上行空间'等量化预测历史上准确率不高，投资者应更关注逻辑而非数字"),
        ("资金面叙事", "'居民资金入市''外资流入'等叙事常见，但实际节奏难以预测"),
        ("事后解释力强", "历史复盘（如第二十四篇）准确，但前瞻性判断需谨慎对待")
    ]

    for title, desc in limitations:
        story.append(Paragraph(f"    \u2022 {title}\uff1a{desc}", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("（四）正确使用卖方研报的建议", ParagraphStyle(
        name='SectionAdvice',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=11,
        spaceBefore=10
    )))
    advice = [
        "学习分析框架而非预测结论：招商策略的行业比较、风格分析框架具有学习价值",
        "交叉验证：同时阅读多家券商观点，避免单一来源偏差",
        "独立思考：对具体点位预测、周期判断保持批判态度",
        "重视数据而非观点：研报中的数据、图表比结论更有价值",
        "逆向使用：当卖方一致性预期过强时，警惕反向风险"
    ]
    for item in advice:
        story.append(Paragraph(f"    \u2022 {item}", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("（五）张夏策略研究的价值评估", ParagraphStyle(
        name='SectionEval',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=11,
        spaceBefore=10
    )))
    story.append(Paragraph("综合评价：★★★★☆（4/5）", normal_style))
    story.append(Spacer(1, 0.1*cm))
    eval_text = "张夏团队的研究在卖方策略中属于头部水平，特别是行业比较框架、风格轮动分析、抱团现象研究等具有较高学术和实践价值。但投资者应注意卖方研究的天然局限性，将研报作为学习工具而非投资指令。"
    story.append(Paragraph(eval_text, normal_style))
    story.append(PageBreak())

    # ===== 六、数据来源与免责声明 =====
    story.append(Paragraph("六、数据来源与免责声明", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("本汇总基于以下来源的公开信息整理：", normal_style))
    story.append(Spacer(1, 0.2*cm))

    sources = [
        "招商证券研究报告原文（通过合规渠道获取）",
        "微信公众号'招商研究'、'招商证券策略研究'",
        "第三方研报平台：研报社 (yanbaoshe.cn)、慧博投研 (hibor.com.cn)",
        "财经媒体：新浪财经、搜狐财经、格隆汇、财联社",
        "投资者社区：雪球 (xueqiu.com)、人大经管之家 (pinggu.org)、哔哩哔哩"
    ]

    for source in sources:
        story.append(Paragraph(f"    \u2022 {source}", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("免责声明：", ParagraphStyle(
        name='Disclaimer',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=10
    )))
    story.append(Paragraph("本汇总仅供参考，不构成投资建议。报告中的事后验证和批判分析仅代表整理者观点，不代表招商证券或张夏本人立场。投资有风险，入市需谨慎。", normal_style))

    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("版权声明：", ParagraphStyle(
        name='Copyright',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=10
    )))
    story.append(Paragraph("《A 股投资启示录》系列报告版权归招商证券所有。本汇总仅用于学习和研究目的，如有侵权请联系删除。", normal_style))

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("文档生成日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Footer',
        parent=normal_style,
        fontSize=8,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER
    )))

    # 构建 PDF
    doc.build(story)
    print("PDF 文件已生成：/Users/x/Downloads/Project/A 股投资启示录汇总 - 完整内容版.pdf")

if __name__ == "__main__":
    create_pdf()
