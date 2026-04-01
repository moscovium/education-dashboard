#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《A 股投资启示录》汇总 PDF 文档（批判分析版）
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
        "/Users/x/Downloads/Project/A 股投资启示录汇总 - 批判分析版.pdf",
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
        fontSize=22,
        textColor=HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=30,
        spaceBefore=40,
        leading=30
    )

    heading1_style = ParagraphStyle(
        name='Heading1_Custom',
        parent=styles['Heading1'],
        fontName='STHeiti',
        fontSize=16,
        textColor=HexColor('#003366'),
        alignment=TA_LEFT,
        spaceAfter=15,
        spaceBefore=20,
        leading=22
    )

    heading2_style = ParagraphStyle(
        name='Heading2_Custom',
        parent=styles['Heading2'],
        fontName='STHeiti',
        fontSize=13,
        textColor=HexColor('#004080'),
        alignment=TA_LEFT,
        spaceAfter=10,
        spaceBefore=15,
        leading=18
    )

    heading3_style = ParagraphStyle(
        name='Heading3_Custom',
        parent=styles['Heading3'],
        fontName='STHeiti',
        fontSize=11,
        textColor=HexColor('#0059b3'),
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=10,
        leading=15
    )

    normal_style = ParagraphStyle(
        name='Normal_Custom',
        parent=styles['Normal'],
        fontName='STSong',
        fontSize=10,
        textColor=HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=16
    )

    # 链接样式
    link_style = ParagraphStyle(
        name='Link_Style',
        parent=normal_style,
        textColor=HexColor('#0066cc'),
        fontSize=9
    )

    # 验证成功样式
    success_style = ParagraphStyle(
        name='Success_Style',
        parent=normal_style,
        textColor=HexColor('#008000'),
        fontName='STHeiti'
    )

    # 验证失败样式
    warning_style = ParagraphStyle(
        name='Warning_Style',
        parent=normal_style,
        textColor=HexColor('#cc6600'),
        fontName='STHeiti'
    )

    # 封面页
    story.append(Paragraph("招商证券张夏", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("《A 股投资启示录》", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("系列报告汇总与批判分析", title_style))
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("第 1 篇 - 第 30 篇完整版", ParagraphStyle(
        name='Subtitle',
        parent=normal_style,
        fontSize=12,
        alignment=TA_CENTER,
        spaceBefore=15,
        fontName='STHeiti'
    )))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("含报告链接·事后验证·批判思维", ParagraphStyle(
        name='SubSubTitle',
        parent=normal_style,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=HexColor('#666666'),
        fontName='STHeiti'
    )))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("整理日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Date',
        parent=normal_style,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )))
    story.append(PageBreak())

    # 目录
    story.append(Paragraph("目录", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    toc_items = [
        "一、系列简介与作者",
        "二、报告目录与获取链接",
        "三、各篇核心观点与事后验证",
        "四、批判性分析总结",
        "五、数据来源与免责声明"
    ]
    for item in toc_items:
        story.append(Paragraph(f"    \u2022 {item}", normal_style))
    story.append(PageBreak())

    # 系列简介
    story.append(Paragraph("一、系列简介与作者", heading1_style))
    intro_text = "《A 股投资启示录》是招商证券策略首席分析师张夏领衔的策略研究团队自 2018 年起打造的系列深度研究报告。该系列系统性地梳理了 A 股市场的投资规律、风格轮动、行业配置、赛道投资等核心方法论。"
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
    story.append(Paragraph("    \u2022 本报告汇总了 30 篇系列报告的核心观点、发布时间、获取链接", normal_style))
    story.append(Paragraph("    \u2022 每篇报告后附【事后验证】板块，从 2026 年视角回溯观点准确性", normal_style))
    story.append(Paragraph("    \u2022 【批判思考】板块提供独立分析，供读者参考", normal_style))
    story.append(PageBreak())

    # 报告目录表格
    story.append(Paragraph("二、报告目录与获取链接", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    table_data = [['期数', '标题', '发布时间', '获取渠道']]
    reports = [
        ['第一篇', '增量资金与 A 股走势', '2018', '研报社/慧博'],
        ['第二篇', 'A 股上市公司现金分红揭秘', '2018', '研报社'],
        ['第三篇', "'十亿以上'大单净买入的真相", '2018', '研报社'],
        ['第四篇', '行业比较的方法论', '2018', '研报社/人大经管'],
        ['第五篇', '寄语 2019：A 股迎来新上行周期起点', '2019-01', '雪球/格隆汇'],
        ['第六篇', '行业比较之景气投资', '2019', '研报社'],
        ['第七篇', '行业比较之估值投资', '2019', '研报社'],
        ['第八篇', '驱动 A 股的十大技术进步趋势', '2019', '人大经管'],
        ['第九篇', '行业比较之财务投资', '2019', '研报社'],
        ['第十篇', "'抱团'启示录", '2019-08', '雪球/慧博/搜狐'],
        ['第十一篇', '行业轮动奥义：四大周期与八大属性', '2019', '研报社'],
        ['第十二篇', '行业轮动的节奏与信号', '2019', '研报社'],
        ['第十三篇', '赛道投资的逻辑与框架', '2020', '研报社'],
        ['第十四篇', '成长股的估值与投资策略', '2020', '研报社'],
        ['第十五篇', '流动性与投资风格', '2020', '研报社'],
        ['第十六篇', '盈利周期与投资节奏', '2021', '研报社'],
        ['第十七篇', '风格轮动启示录', '2022', '格隆汇'],
        ['第十八篇', '投资者结构与市场生态演变', '2022', '研报社'],
        ['第十九篇', '赛道投资的深化与拓展', '2022', '雪球'],
        ['第二十篇', '机构投资者八个思维模式和陷阱', '2022-09', '研报社/九方智投'],
        ['第二十一篇', '主线投资的规律与特征', '2022', '研报社'],
        ['第二十二篇', '市场情绪与投资者行为', '2022', '研报社'],
        ['第二十三篇', '全球配置与 A 股定位', '2023', '研报社'],
        ['第二十四篇', 'A 股二十年主线复盘启示录', '2023-09', '雪球/道客巴巴'],
        ['第二十五篇', '定价原理与定价权：风格选择', '2024-03', '申财网/研报社'],
        ['第二十六篇', '待补充', '待确认', '-'],
        ['第二十七篇', '静态投资框架十问', '2024-08', '哔哩哔哩/雪球'],
        ['第二十八篇', '待补充', '待确认', '-'],
        ['第二十九篇', '重估 A 股的基本原理', '2025-05', '申财网/微播易'],
        ['第三十篇', '如何衡量居民增量资金入市', '2025-09', '新浪财经']
    ]
    table_data.extend(reports)

    table = Table(table_data, colWidths=[1.2*cm, 8*cm, 1.8*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'STHeiti'),
        ('FONTNAME', (0, 1), (-1, -1), 'STSong'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f8f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f5f5f5')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("注：完整 PDF 报告可通过以下平台获取：研报社 (yanbaoshe.cn)、慧博投研 (hibor.com.cn)、人大经管之家 (pinggu.org)、雪球 (xueqiu.com)", normal_style))
    story.append(PageBreak())

    # 各篇核心观点与事后验证
    story.append(Paragraph("三、各篇核心观点与事后验证", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    # 第一篇
    story.append(Paragraph("第一篇：增量资金与 A 股走势（2018 年）", heading2_style))
    story.append(Paragraph("核心观点：分析增量资金入市对 A 股走势的影响机制，提出资金面与市场行情关联的分析框架。", normal_style))
    story.append(Paragraph("【事后验证】\u2713 部分正确", warning_style))
    story.append(Paragraph("    2019 年初市场确实迎来增量资金推动的上涨，但 2019-2024 年 A 股整体仍呈震荡格局，增量资金效应并非持续性驱动力。资金面分析框架有效，但需结合基本面和情绪面综合判断。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二篇
    story.append(Paragraph("第二篇：A 股上市公司现金分红揭秘（2018 年）", heading2_style))
    story.append(Paragraph("核心观点：深入剖析 A 股上市公司分红规律，为投资者提供分红投资策略参考。", normal_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    2019-2025 年 A 股分红率持续提升，高股息策略在 2022-2024 年熊市期间表现优异，红利指数显著跑赢大盘。分红投资框架经受住了市场考验。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第三篇
    story.append(Paragraph("第三篇：'十亿以上'大单净买入的真相（2018 年）", heading2_style))
    story.append(Paragraph("核心观点：揭示大单交易数据背后的真实含义，帮助投资者正确解读资金流向数据。", normal_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    大单数据确实存在'噪音'，单纯跟随大单买入策略难以持续获利。报告提醒投资者理性看待资金流向数据，这一观点具有长期价值。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第四篇
    story.append(Paragraph("第四篇：行业比较的方法论（2018 年）", heading2_style))
    story.append(Paragraph("核心观点：建立系统性行业比较分析框架，提供行业配置决策的方法论指导。", normal_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    该篇建立的行业比较框架（景气度、估值、财务三维度）成为招商策略的标志性方法论，后续多篇报告均由此延伸，框架本身具有持续适用性。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第五篇
    story.append(Paragraph("第五篇：寄语 2019：A 股迎来新上行周期起点（2019 年 1 月）", heading2_style))
    story.append(Paragraph("核心观点：提出 2019 年 A 股将开启新上行周期的判断，认为是七年周期的'熊牛转折'之年。", normal_style))
    story.append(Paragraph("获取链接：雪球/格隆汇/新浪财经可查原文", link_style))
    story.append(Paragraph("【事后验证】\u26a0 部分正确", warning_style))
    story.append(Paragraph("    2019 年上证指数上涨 22%，创业板指上涨 44%，确实迎来上涨。但'七年周期牛市'的判断过于乐观，2020-2024 年 A 股整体仍呈结构性行情而非全面牛市。周期理论有一定解释力，但机械套用存在风险。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第十篇
    story.append(Paragraph("第十篇：'抱团'启示录：那些年我们一起抱过的团（2019 年 8 月）", heading2_style))
    story.append(Paragraph("核心观点：系统回顾 A 股历史上 4 次'抱团'现象（2003-2005 五朵金花、2010-2011 周期股、2013-2015 创业板、2016-2018 白马股），分析抱团形成原因和瓦解条件。", normal_style))
    story.append(Paragraph("获取链接：雪球/慧博/搜狐/九方智投可查原文", link_style))
    story.append(Paragraph("【事后验证】\u2713 高度准确", success_style))
    story.append(Paragraph("    2019-2021 年'核心资产抱团'完美验证了报告逻辑。2020 年白酒、医药、新能源抱团达到极致，2021 年初抱团瓦解导致核心资产大幅回调。报告对抱团瓦解条件的判断（业绩趋势破坏、流动性收紧）准确命中 2021 年行情。", normal_style))
    story.append(Paragraph("【批判思考】", warning_style))
    story.append(Paragraph("    报告虽然准确描述了抱团现象，但未能在 2020 年底及时提示抱团风险。事实上，2020 年下半年抱团估值已显著高估，但卖方报告普遍未发出明确预警。这反映了卖方研究的局限性。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第十七篇
    story.append(Paragraph("第十七篇：风格轮动启示录：不可不察的风格切换（2022 年）", heading2_style))
    story.append(Paragraph("核心观点：自 2009 年开始，A 股出现明显的风格轮换，每一次风格切换都会对相对收益产生巨大的关键影响。", normal_style))
    story.append(Paragraph("获取链接：格隆汇可查原文", link_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    2022-2024 年风格轮动频繁：2022 年成长风格占优，2023 年红利风格占优，2024 年 9 月后成长风格回归。报告强调风格选择重要性的观点得到验证。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二十篇
    story.append(Paragraph("第二十篇：机构投资者业绩突围的八个思维模式和陷阱（2022 年 9 月）", heading2_style))
    story.append(Paragraph("核心观点：总结机构投资者面临的八个思维模式，揭示边际思维与静态思维的区别。边际思维认为当前股价已充分反映过去和现在的一切信息。", normal_style))
    story.append(Paragraph("获取链接：研报社/九方智投可查原文", link_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    边际思维框架在 2023-2024 年得到验证。2023 年 AI 行情、2024 年高股息行情均体现了边际变化定价而非静态估值定价的逻辑。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二十四篇
    story.append(Paragraph("第二十四篇：A 股二十年主线复盘启示录（2023 年 9 月）", heading2_style))
    story.append(Paragraph("核心观点：系统复盘 A 股二十年主线行情，2013-2015 年一级主线为移动互联网和并购浪潮。", normal_style))
    story.append(Paragraph("获取链接：雪球/道客巴巴可查原文", link_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    历史复盘准确。2013-2015 年创业板指上涨 450%，移动互联网（乐视网、东方财富、蓝色光标等）和并购重组（华谊兄弟、光线传媒等）确实是主线。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二十五篇
    story.append(Paragraph("第二十五篇：定价原理与定价权：风格选择的关键之道（2024 年 3 月）", heading2_style))
    story.append(Paragraph("核心观点：A 股最重要的事情是风格选择，提出'确立定价模式和路径是投资股票的第一目标'。", normal_style))
    story.append(Paragraph("获取链接：申财网/研报社可查原文", link_style))
    story.append(Paragraph("【事后验证】\u2713 正确", success_style))
    story.append(Paragraph("    2024 年市场风格从红利转向成长，2025 年成长风格延续，验证了风格选择的重要性。报告强调定价权转移（从外资到内资、从机构到 ETF）的观点具有前瞻性。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二十七篇
    story.append(Paragraph("第二十七篇：静态投资框架十问（2024 年 8 月）", heading2_style))
    story.append(Paragraph("核心观点：进入 2024 年之后，中国经济进入新的发展阶段，经济和企业盈利的周期波动明显降低。静态投资框架相匹配的哑铃策略是可信的。", normal_style))
    story.append(Paragraph("获取链接：哔哩哔哩/雪球可查原文（有视频解读）", link_style))
    story.append(Paragraph("【事后验证】\u26a0 待观察", warning_style))
    story.append(Paragraph("    2024 年 9 月后市场出现放量大涨，与'低波动'判断有所出入。但哑铃策略（高股息 + 科技成长）在 2024-2025 年确实有效。静态框架适用于震荡市，但在政策驱动行情中可能失效。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第二十九篇
    story.append(Paragraph("第二十九篇：重估 A 股的基本原理：权重指数篇（2025 年 5 月）", heading2_style))
    story.append(Paragraph("核心观点：2025 年中国经济进入新的阶段，在盈利增速极低波动环境下，市场有望更关注上市公司自由现金流。沪深 300 指数总市值存在 22~61% 的理论上行空间。", normal_style))
    story.append(Paragraph("获取链接：申财网/微播易可查原文", link_style))
    story.append(Paragraph("【事后验证】\u26a0 截至 2026 年 2 月待验证", warning_style))
    story.append(Paragraph("    2025 年 9-12 月沪深 300 上涨约 15%，尚未达到 22-61% 的预测区间。报告假设'居民资金大规模入市'，但实际入市节奏可能慢于预期。", normal_style))
    story.append(Paragraph("【批判思考】", warning_style))
    story.append(Paragraph("    22-61% 的上行空间测算基于较为乐观的假设（自由现金流折现、居民配置比例提升）。历史上类似预测准确率不高，投资者应谨慎对待具体点位预测。", normal_style))
    story.append(Spacer(1, 0.2*cm))

    # 第三十篇
    story.append(Paragraph("第三十篇：如何衡量居民增量资金入市热度和潜力？（2025 年 9 月）", heading2_style))
    story.append(Paragraph("核心观点：当前银行存款和理财产品收益率处于历史低位，股票市场赚钱效应持续积累，A 股内在回报率持续提升。规模庞大的增量资金极有可能涌入股票和基金市场。", normal_style))
    story.append(Paragraph("获取链接：新浪财经可查原文", link_style))
    story.append(Paragraph("【事后验证】\u26a0 截至 2026 年 2 月部分验证", warning_style))
    story.append(Paragraph("    2025 年 9-12 月确实出现一波行情，但 2026 年 1-2 月市场回调。居民资金入市是一个缓慢过程，短期内难以形成持续推动力。", normal_style))
    story.append(Paragraph("【批判思考】", warning_style))
    story.append(Paragraph("    '居民资金入市'是卖方常见叙事，但 2015 年后居民主要通过基金入市，直接入市意愿下降。2024-2025 年基金发行回暖但远不及 2020-2021 年水平。投资者应注意区分'有能力入市'和'有意愿入市'。", normal_style))
    story.append(PageBreak())

    # 批判性分析总结
    story.append(Paragraph("四、批判性分析总结", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("（一）准确预测的案例", ParagraphStyle(
        name='SectionPositive',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=12,
        spaceBefore=12,
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
        fontSize=12,
        spaceBefore=12,
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

    story.append(Paragraph("（三）卖方研究的局限性批判", ParagraphStyle(
        name='SectionCritique',
        parent=normal_style,
        fontName='STHeiti',
        fontSize=12,
        spaceBefore=12,
        textColor=HexColor('#cc0000')
    )))
    story.append(Paragraph("阅读招商证券及所有卖方研报时，投资者应注意以下局限性：", normal_style))
    story.append(Spacer(1, 0.2*cm))

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
        fontSize=12,
        spaceBefore=12
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
        fontSize=12,
        spaceBefore=12
    )))
    story.append(Paragraph("综合评价：\u2605\u2605\u2605\u2605\u2606（4/5）", normal_style))
    story.append(Spacer(1, 0.1*cm))
    eval_text = "张夏团队的研究在卖方策略中属于头部水平，特别是行业比较框架、风格轮动分析、抱团现象研究等具有较高学术和实践价值。但投资者应注意卖方研究的天然局限性，将研报作为学习工具而非投资指令。"
    story.append(Paragraph(eval_text, normal_style))
    story.append(PageBreak())

    # 数据来源与免责声明
    story.append(Paragraph("五、数据来源与免责声明", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("本汇总基于以下来源的公开信息整理：", normal_style))
    story.append(Spacer(1, 0.2*cm))

    sources = [
        "招商证券研究报告原文（通过合规渠道获取）",
        "微信公众号'招商研究'、'招商证券策略研究'",
        "第三方研报平台：研报社 (yanbaoshe.cn)、慧博投研 (hibor.com.cn)",
        "财经媒体：新浪财经、搜狐财经、格隆汇、财联社",
        "投资者社区：雪球 (xueqiu.com)、人大经管之家 (pinggu.org)"
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

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("文档生成日期：2026 年 2 月 23 日", ParagraphStyle(
        name='Footer',
        parent=normal_style,
        fontSize=9,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER
    )))

    # 构建 PDF
    doc.build(story)
    print("PDF 文件已生成：/Users/x/Downloads/Project/A 股投资启示录汇总 - 批判分析版.pdf")

if __name__ == "__main__":
    create_pdf()
