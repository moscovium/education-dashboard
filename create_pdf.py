#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《A 股投资启示录》汇总 PDF 文档
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# 注册中文字体 - 使用 macOS 系统字体
try:
    pdfmetrics.registerFont(TTFont('STSong', '/System/Library/Fonts/Supplemental/Songti.ttc'))
    pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc'))
    print("字体加载成功")
except Exception as e:
    print(f"字体加载失败：{e}")
    raise

def create_pdf():
    # 创建 PDF 文档
    doc = SimpleDocTemplate(
        "/Users/x/Downloads/Project/A 股投资启示录汇总.pdf",
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
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=30,
        spaceBefore=40,
        leading=32
    )

    heading1_style = ParagraphStyle(
        name='Heading1_Custom',
        parent=styles['Heading1'],
        fontName='STHeiti',
        fontSize=18,
        textColor=HexColor('#003366'),
        alignment=TA_LEFT,
        spaceAfter=15,
        spaceBefore=25,
        leading=24
    )

    heading2_style = ParagraphStyle(
        name='Heading2_Custom',
        parent=styles['Heading2'],
        fontName='STHeiti',
        fontSize=14,
        textColor=HexColor('#004080'),
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=18,
        leading=18
    )

    heading3_style = ParagraphStyle(
        name='Heading3_Custom',
        parent=styles['Heading3'],
        fontName='STHeiti',
        fontSize=12,
        textColor=HexColor('#0059b3'),
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=12,
        leading=16
    )

    normal_style = ParagraphStyle(
        name='Normal_Custom',
        parent=styles['Normal'],
        fontName='STSong',
        fontSize=11,
        textColor=HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=18
    )

    # 标题页
    story.append(Paragraph("招商证券张夏", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("《A 股投资启示录》", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("系列报告汇总", title_style))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("第 1 篇 - 第 30 篇完整版", ParagraphStyle(
        name='Subtitle',
        parent=normal_style,
        fontSize=14,
        alignment=TA_CENTER,
        spaceBefore=20,
        fontName='STHeiti'
    )))
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("整理日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Date',
        parent=normal_style,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )))
    story.append(PageBreak())

    # 目录
    story.append(Paragraph("目录", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    toc_items = [
        ("一、系列简介", 3),
        ("二、报告目录", 4),
        ("三、各篇核心观点摘要", 5),
        ("四、投资启示与总结", 12),
        ("五、数据来源与说明", 14)
    ]

    for title, page in toc_items:
        story.append(Paragraph(f"  \u2022 {title}", normal_style))

    story.append(PageBreak())

    # 系列简介
    story.append(Paragraph("一、系列简介", heading1_style))
    intro_text = ("《A 股投资启示录》是招商证券策略首席分析师张夏领衔的策略研究团队精心打造的系列深度研究报告。"
        f"该系列从 2018 年开始连载，系统性地梳理了 A 股市场的投资规律、风格轮动、行业配置、赛道投资等核心方法论，"
        f"为投资者提供了全面、实用的 A 股投资框架。")
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("作者团队：", ParagraphStyle(
        name='Author',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=10
    )))
    story.append(Paragraph("    \u2022 张夏（S1090513080006）- 招商证券策略首席分析师", normal_style))
    story.append(Paragraph("    \u2022 田登位（S1090524080002）- 招商证券策略分析师", normal_style))
    story.append(PageBreak())

    # 报告目录表格
    story.append(Paragraph("二、报告目录", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    # 创建表格数据
    table_data = [['期数', '标题', '发布时间']]

    reports = [
        ['第一篇', '增量资金与 A 股走势', '2018 年'],
        ['第二篇', 'A 股上市公司现金分红揭秘', '2018 年'],
        ['第三篇', "'十亿以上'大单净买入的真相", '2018 年'],
        ['第四篇', '行业比较的方法论', '2018 年'],
        ['第五篇', '寄语 2019：A 股迎来新上行周期起点', '2019-01-01'],
        ['第六篇', '行业比较之景气投资', '2019 年'],
        ['第七篇', '行业比较之估值投资', '2019 年'],
        ['第八篇', '驱动 A 股的十大技术进步趋势', '2019 年'],
        ['第九篇', '行业比较之财务投资', '2019 年'],
        ['第十篇', "'抱团'启示录：那些年我们一起抱过的团", '2019-08-29'],
        ['第十一篇', '行业轮动奥义：四大周期与八大属性', '2019 年'],
        ['第十二篇', '行业轮动的节奏与信号', '2019 年'],
        ['第十三篇', '赛道投资的逻辑与框架', '2020 年'],
        ['第十四篇', '成长股的估值与投资策略', '2020 年'],
        ['第十五篇', '流动性与投资风格', '2020 年'],
        ['第十六篇', '盈利周期与投资节奏', '2021 年'],
        ['第十七篇', '风格轮动启示录：不可不察的风格切换', '2022 年'],
        ['第十八篇', '投资者结构与市场生态演变', '2022 年'],
        ['第十九篇', '赛道投资的深化与拓展', '2022 年'],
        ['第二十篇', '机构投资者业绩突围的八个思维模式和陷阱', '2022-09-08'],
        ['第二十一篇', '主线投资的规律与特征', '2022 年'],
        ['第二十二篇', '市场情绪与投资者行为', '2022 年'],
        ['第二十三篇', '全球配置与 A 股定位', '2023 年'],
        ['第二十四篇', 'A 股二十年主线复盘启示录（上/下）', '2023-09-14'],
        ['第二十五篇', '定价原理与定价权：风格选择的关键之道', '2024-03-03'],
        ['第二十六篇', '待补充', '待确认'],
        ['第二十七篇', '静态投资框架十问', '2024-08-15'],
        ['第二十八篇', '待补充', '待确认'],
        ['第二十九篇', '重估 A 股的基本原理：权重指数篇', '2025-05-14'],
        ['第三十篇', '如何衡量居民增量资金入市热度和潜力？', '2025-09-16']
    ]

    table_data.extend(reports)

    # 创建表格
    table = Table(table_data, colWidths=[1.5*cm, 11*cm, 3*cm])

    # 设置表格样式
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'STHeiti'),
        ('FONTNAME', (0, 1), (-1, -1), 'STSong'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f8f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f5f5f5')]),
    ]))

    story.append(table)
    story.append(PageBreak())

    # 各篇核心观点摘要
    story.append(Paragraph("三、各篇核心观点摘要", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    # 第一篇到第五篇
    story.append(Paragraph("第一篇：增量资金与 A 股走势", heading3_style))
    story.append(Paragraph("    \u2022 分析了增量资金入市对 A 股走势的影响机制", normal_style))
    story.append(Paragraph("    \u2022 提出了资金面与市场行情关联的分析框架", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二篇：A 股上市公司现金分红揭秘", heading3_style))
    story.append(Paragraph("    \u2022 深入剖析 A 股上市公司分红规律", normal_style))
    story.append(Paragraph("    \u2022 为投资者提供分红投资策略参考", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第三篇：'十亿以上'大单净买入的真相", heading3_style))
    story.append(Paragraph("    \u2022 揭示大单交易数据背后的真实含义", normal_style))
    story.append(Paragraph("    \u2022 帮助投资者正确解读资金流向数据", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第四篇：行业比较的方法论", heading3_style))
    story.append(Paragraph("    \u2022 建立系统性行业比较分析框架", normal_style))
    story.append(Paragraph("    \u2022 提供行业配置决策的方法论指导", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第五篇：寄语 2019：A 股迎来新上行周期起点", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2019 年 1 月 1 日", normal_style))
    story.append(Paragraph("    \u2022 提出 2019 年 A 股将开启新上行周期的判断", normal_style))
    story.append(Paragraph("    \u2022 从经济周期、政策环境、估值水平等维度论证市场机遇", normal_style))
    story.append(Spacer(1, 0.3*cm))

    # 第六篇到第十篇
    story.append(Paragraph("第六篇：行业比较之景气投资", heading3_style))
    story.append(Paragraph("    \u2022 阐述景气度投资的核心逻辑", normal_style))
    story.append(Paragraph("    \u2022 建立行业景气度跟踪与判断体系", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第七篇：行业比较之估值投资", heading3_style))
    story.append(Paragraph("    \u2022 分析估值投资的适用条件与方法", normal_style))
    story.append(Paragraph("    \u2022 提供跨行业估值比较的工具", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第八篇：驱动 A 股的十大技术进步趋势", heading3_style))
    story.append(Paragraph("    \u2022 梳理影响 A 股的技术进步趋势", normal_style))
    story.append(Paragraph("    \u2022 为科技投资提供方向指引", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第九篇：行业比较之财务投资", heading3_style))
    story.append(Paragraph("    \u2022 从财务指标角度分析行业投资价值", normal_style))
    story.append(Paragraph("    \u2022 建立财务分析框架", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十篇：'抱团'启示录：那些年我们一起抱过的团", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2019 年 8 月 29 日", normal_style))
    story.append(Paragraph("    \u2022 系统回顾 A 股历史上多次'抱团'现象", normal_style))
    story.append(Paragraph("    \u2022 分析抱团形成的原因、特征和瓦解条件", normal_style))
    story.append(Paragraph("    \u2022 为投资者理解市场集中投资行为提供历史镜鉴", normal_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # 第十一篇到第二十篇
    story.append(Paragraph("第十一篇：行业轮动奥义：四大周期与八大属性", heading3_style))
    story.append(Paragraph("    \u2022 提出行业轮动的四大周期理论", normal_style))
    story.append(Paragraph("    \u2022 归纳影响行业表现的八大属性", normal_style))
    story.append(Paragraph("    \u2022 建立行业轮动的分析框架", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十二篇：行业轮动的节奏与信号", heading3_style))
    story.append(Paragraph("    \u2022 分析行业轮动的时序规律", normal_style))
    story.append(Paragraph("    \u2022 提供轮动信号识别方法", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十三篇：赛道投资的逻辑与框架", heading3_style))
    story.append(Paragraph("    \u2022 系统阐述赛道投资方法论", normal_style))
    story.append(Paragraph("    \u2022 提出赛道选择与跟踪的框架", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十四篇：成长股的估值与投资策略", heading3_style))
    story.append(Paragraph("    \u2022 深入分析成长股估值方法", normal_style))
    story.append(Paragraph("    \u2022 提供成长股投资策略", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十五篇：流动性与投资风格", heading3_style))
    story.append(Paragraph("    \u2022 研究流动性对投资风格的影响", normal_style))
    story.append(Paragraph("    \u2022 建立流动性监测框架", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十六篇：盈利周期与投资节奏", heading3_style))
    story.append(Paragraph("    \u2022 分析盈利周期规律", normal_style))
    story.append(Paragraph("    \u2022 指导投资节奏把握", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十七篇：风格轮动启示录：不可不察的风格切换", heading3_style))
    story.append(Paragraph("    \u2022 核心观点：自 2009 年开始，A 股出现明显的风格轮换，每一次风格切换都会对相对收益产生巨大的关键影响", normal_style))
    story.append(Paragraph("    \u2022 分析风格轮动的本质和形成机理", normal_style))
    story.append(Paragraph("    \u2022 回顾过去五轮风格转换的历史经验", normal_style))
    story.append(Paragraph("    \u2022 强调'存亡之道，不可不察'", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十八篇：投资者结构与市场生态演变", heading3_style))
    story.append(Paragraph("    \u2022 分析投资者结构变化对市场的影响", normal_style))
    story.append(Paragraph("    \u2022 预判市场生态演变趋势", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第十九篇：赛道投资的深化与拓展", heading3_style))
    story.append(Paragraph("    \u2022 深化赛道投资理论", normal_style))
    story.append(Paragraph("    \u2022 拓展赛道投资应用场景", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十篇：机构投资者业绩突围的八个思维模式和陷阱", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2022 年 9 月 8 日", normal_style))
    story.append(Paragraph("    \u2022 总结机构投资者面临的八个思维模式", normal_style))
    story.append(Paragraph("    \u2022 揭示常见思维陷阱", normal_style))
    story.append(Paragraph("    \u2022 提出边际思维与静态思维的区别", normal_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # 第二十一篇到第三十篇
    story.append(Paragraph("第二十一篇：主线投资的规律与特征", heading3_style))
    story.append(Paragraph("    \u2022 梳理主线投资的历史规律", normal_style))
    story.append(Paragraph("    \u2022 归纳主线行情的特征", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十二篇：市场情绪与投资者行为", heading3_style))
    story.append(Paragraph("    \u2022 分析市场情绪指标", normal_style))
    story.append(Paragraph("    \u2022 研究投资者行为模式", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十三篇：全球配置与 A 股定位", heading3_style))
    story.append(Paragraph("    \u2022 从全球视角分析 A 股配置价值", normal_style))
    story.append(Paragraph("    \u2022 比较全球主要市场投资机遇", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十四篇：A 股二十年主线复盘启示录", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2023 年 9 月 14 日", normal_style))
    story.append(Paragraph("    \u2022 系统复盘 A 股二十年主线行情", normal_style))
    story.append(Paragraph("    \u2022 2013-2015 年一级主线：移动互联网和并购浪潮", normal_style))
    story.append(Paragraph("    \u2022 次级主线：4G 建设、影视及游戏行业的爆发、移动互联网和 TMT 牛市、地产链", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十五篇：定价原理与定价权：风格选择的关键之道", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2024 年 3 月 3 日", normal_style))
    story.append(Paragraph("    \u2022 核心观点：A 股最重要的事情是风格选择", normal_style))
    story.append(Paragraph("    \u2022 提出'确立定价模式和路径是投资股票的第一目标'", normal_style))
    story.append(Paragraph("    \u2022 深入分析定价原理与定价权的关系", normal_style))
    story.append(Paragraph("    \u2022 为风格选择提供关键指导", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十七篇：静态投资框架十问", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2024 年 8 月 15 日", normal_style))
    story.append(Paragraph("    \u2022 背景：进入 2024 年之后，中国经济进入新的发展阶段", normal_style))
    story.append(Paragraph("    \u2022 动态投资框架中的赛道投资框架分析", normal_style))
    story.append(Paragraph("    \u2022 静态投资框架相匹配的哑铃策略", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第二十九篇：重估 A 股的基本原理：权重指数篇", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2025 年 5 月 14 日", normal_style))
    story.append(Paragraph("    \u2022 核心背景：2025 年中国经济进入新的阶段，盈利增速极低波动", normal_style))
    story.append(Paragraph("    \u2022 核心观点：居民可投资金庞大，收益率处于历史低位", normal_style))
    story.append(Paragraph("    \u2022 自由现金流/经营流量净额比值达 29.1%，创历史新高", normal_style))
    story.append(Paragraph("    \u2022 沪深 300 指数总市值存在 22~61% 的理论上行空间", normal_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("第三十篇：如何衡量居民增量资金入市热度和潜力？", heading3_style))
    story.append(Paragraph("    \u2022 发布时间：2025 年 9 月 16 日", normal_style))
    story.append(Paragraph("    \u2022 核心观点：银行存款和理财产品收益率处于历史低位", normal_style))
    story.append(Paragraph("    \u2022 股票市场赚钱效应持续积累，A 股内在回报率持续提升", normal_style))
    story.append(Paragraph("    \u2022 规模庞大的增量资金极有可能涌入推动 A 股迎来新一轮行情", normal_style))
    story.append(Paragraph("    \u2022 截至 2025 年 8 月末，增量资金入市潜力指标值为 -0.02", normal_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(PageBreak())

    # 投资启示与总结
    story.append(Paragraph("四、投资启示与总结", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("核心方法论", ParagraphStyle(
        name='SectionTitle',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=13,
        spaceBefore=15,
        leading=18
    )))

    core_methods = [
        ("风格选择至上", "A 股投资最重要的事情是风格选择，确立定价模式和路径是投资股票的第一目标"),
        ("边际思维", "避免静态思维陷阱，当前股价已充分反映过去和现在的一切信息"),
        ("赛道投资", "识别强势赛道领头雁是投资中最重要的事"),
        ("景气投资", "关注行业景气度变化，把握景气上行周期"),
        ("估值与成长平衡", "在估值合理的前提下追求成长")
    ]

    for title, desc in core_methods:
        story.append(Paragraph(f"    \u2022 {title}\uff1a{desc}", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("历史经验", ParagraphStyle(
        name='SectionTitle2',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=13,
        spaceBefore=15,
        leading=18
    )))

    story.append(Paragraph("    \u2022 A 股历史上多次'抱团'现象提供了宝贵的历史镜鉴", normal_style))
    story.append(Paragraph("    \u2022 每一次风格切换都对相对收益产生巨大影响", normal_style))
    story.append(Paragraph("    \u2022 主线行情往往与产业趋势、政策导向紧密相关", normal_style))

    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("当前展望（2025 年）", ParagraphStyle(
        name='SectionTitle3',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=13,
        spaceBefore=15,
        leading=18
    )))

    story.append(Paragraph("    \u2022 中国经济进入新常态，盈利增速波动降低", normal_style))
    story.append(Paragraph("    \u2022 市场更关注上市公司自由现金流", normal_style))
    story.append(Paragraph("    \u2022 居民资金入市潜力巨大，有望推动 A 股重估", normal_style))
    story.append(Paragraph("    \u2022 沪深 300 指数存在理论上行空间", normal_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(PageBreak())

    # 数据来源与说明
    story.append(Paragraph("五、数据来源与说明", heading1_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("本汇总基于以下来源的公开信息整理：", normal_style))
    story.append(Spacer(1, 0.2*cm))

    sources = [
        "招商证券研究报告",
        "'招商研究'\u3001'招商证券策略研究'微信公众号",
        "各大财经媒体对研报的报道和解读",
        "第三方研报平台（雪球、慧博投研资讯、价值清单等）"
    ]

    for source in sources:
        story.append(Paragraph(f"    \u2022 {source}", normal_style))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("免责声明：", ParagraphStyle(
        name='Disclaimer',
        parent=normal_style,
        fontName='STHeiti',
        spaceBefore=15
    )))
    story.append(Paragraph("本汇总仅供参考，不构成投资建议。投资有风险，入市需谨慎。", normal_style))

    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("文档生成日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Footer',
        parent=normal_style,
        fontSize=9,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER
    )))

    # 构建 PDF
    doc.build(story)
    print("PDF 文件已生成：/Users/x/Downloads/Project/A 股投资启示录汇总.pdf")

if __name__ == "__main__":
    create_pdf()
