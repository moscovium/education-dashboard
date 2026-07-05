# -*- coding: utf-8 -*-
"""
集团校（多校区）成效报告「文字版（公文 Word）」样例生成器 —— 内容设计验证用
==============================================================================
对齐线上区级文字版的公文体例（report_app_core.export_to_docx：方正小标宋简体标题 /
黑体一级标题 / 楷体_GB2312 二级标题 / 仿宋_GB2312 正文），但统计单元从「学校 / 全区」
换为「校区 / 集团」。数据为「数据宽表--班级」（无作业路径 / 题型 / 月度明细），故
省略训练内容结构、题型表现、月度趋势等栏目，改以校区对比 + 付费转化为核心。

复用 集团校_demo 的取数与校区/教师分析；输出 .docx 到 ~/Downloads。
"""
from datetime import datetime

import pandas as pd

import 集团校_demo as GD
import report_app_core as C

OUT = "/Users/x/Downloads/滨州实验学校_文字版_集团校区样例.docx"
GRADE_ORDER = ["七年级", "八年级", "九年级", "高一", "高二", "高三"]


def grade_stats(agg):
    rows = []
    for grade, g in agg.groupby("年级"):
        act = g[g["布置作业次数"] > 0]
        rows.append({
            "年级": str(grade), "班级数": int(len(g)),
            "学生数": int(g["总学生数"].fillna(0).sum()),
            "布置次数": int(g["布置作业次数"].fillna(0).sum()),
            "活跃班级": int(len(act)),
            "完成率": round(act["作业完成率"].mean() * 100, 1) if len(act) and act["作业完成率"].notna().any() else None,
            "得分率": round(act["作业得分率"].mean() * 100, 1) if len(act) and act["作业得分率"].notna().any() else None,
            "自主练习": int(g["自主练习次数"].fillna(0).sum()),
        })
    rows.sort(key=lambda r: GRADE_ORDER.index(r["年级"]) if r["年级"] in GRADE_ORDER else 99)
    return rows


def pct(v):
    return f"{v}%" if v is not None else "—"


def build_text(D, agg):
    g = D["group"]
    cs = D["campuses"]
    top = cs[0]
    dormant = [c for c in cs if c["active"] == 0]
    laggards = "、".join(c["short"] for c in dormant) or cs[-1]["short"]
    grades = grade_stats(agg)
    L = []

    L.append(f"# {GD.GROUP_NAME}英语AI听说训练集团校应用成效报告\n")
    L.append(f"**报告生成时间：{datetime.now().strftime('%Y年%m月%d日')}**\n")
    L.append(f"**模板版本：{C.REPORT_VERSION} 集团校模板**\n\n")

    # ── 一、应用概况 ───────────────────────────────────────
    L.append("## 一、应用概况\n")
    L.append(f"　　本报告基于{GD.GROUP_NAME}{GD.PERIOD_TEXT}期间各校区的班级数据总览，"
             f"以「校区」为统计单元，重点从集团整体应用、校区推进差异、教师使用画像、"
             f"年级训练表现等维度，对比各校区应用冷热、定位待启动校区，为集团统一教研与过程管理提供参考。\n\n")
    L.append("| 指标 | 数值 |\n|------|------|\n")
    L.append(f"| 覆盖校区 | {g['campuses']}个 |\n")
    L.append(f"| 覆盖班级 | {g['classes']}个（活跃{g['active']}个） |\n")
    L.append(f"| 覆盖学生 | {g['students']:,}人 |\n")
    L.append(f"| 累计布置 | {g['assigns']}次 |\n")
    L.append(f"| 活跃班级率 | {g['active_rate']}% |\n")
    L.append(f"| 班均布置次数 | {g['per_class']}次/班 |\n")
    L.append(f"| 平均完成率 | {g['completion']}% |\n")
    L.append(f"| 平均得分率 | {g['score']}% |\n")
    L.append(f"| 付费转化率 | {g['paid_rate']}% |\n\n")
    L.append(f"　　从集团整体看，统计周期内共覆盖{g['campuses']}个校区、{g['classes']}个班级和"
             f"{g['students']:,}名学生，累计布置作业{g['assigns']}次，活跃班级率仅{g['active_rate']}%，"
             f"应用整体处于推广阶段；校区之间冷热不均是本期最突出的特征，详见下节对比。\n\n")

    # ── 二、各校区应用对比（核心）─────────────────────────
    L.append("## 二、各校区应用对比\n")
    L.append("### 2.1 各校区应用画像\n")
    L.append("　　考虑各校区班级规模差异，以「班均布置次数」（校区累计布置次数÷班级数）观察校区应用推进深度，"
             "完成率、得分率作为结果表现参考，仅统计有布置记录的活跃班级。\n\n")
    L.append("| 校区 | 班级数 | 活跃班级 | 学生数 | 累计布置 | 班均布置次数 | 完成率 | 得分率 | 付费转化 |\n"
             "|------|------|------|------|------|------|------|------|------|\n")
    for c in cs:
        L.append(f"| {c['short']} | {c['classes']} | {c['active']} | {c['students']:,} | {c['assigns']} | "
                 f"{c['per_class']} | {pct(c['completion'])} | {pct(c['score'])} | {c['paid_rate']}% |\n")
    L.append("\n")
    dz = "、".join(f"{c['short']}（{c['classes']}个班）" for c in dormant)
    L.append(f"　　{top['short']}为集团应用主力，{top['active']}个班有布置、班均{top['per_class']}次，"
             f"明显领先其余校区，可作为集团内示范校区。"
             + (f"而{dz}本期整周零布置、尚未真正启动应用，与主力校区差距悬殊。\n\n"
                if dormant else
                f"{cs[-1]['short']}班均仅{cs[-1]['per_class']}次，相对靠后。\n\n"))

    L.append("### 2.2 校区冷热差异与跟进方向\n")
    L.append(f"　　集团内应用呈现明显的“一校独热、其余偏冷”格局：{top['short']}贡献了大部分布置量，"
             f"而{laggards}应用基本停滞。这一差异更多源于校区账号开通、教师培训与作业布置机制是否到位，"
             f"而非学生因素。建议集团层面对待启动校区做名单化跟进，设定首月布置量目标，"
             f"并将{top['short']}的布置节奏与督促做法在集团内复制推广。\n\n")

    # ── 三、教师使用画像 ───────────────────────────────────
    L.append("## 三、教师使用画像\n")
    if D["teachers"]:
        L.append("　　教师层面同样以布置次数与完成率形成应用画像，得分率作为结果表现展示。"
                 "下表为集团内活跃教师 TOP，并标注其所属校区，便于经验萃取与跨校区示范。\n\n")
        L.append("| 教师 | 所属校区 | 班级数 | 布置次数 | 完成率 | 得分率 |\n"
                 "|------|------|------|------|------|------|\n")
        for t in D["teachers"]:
            L.append(f"| {t['name']} | {t['campus']} | {t['classes']} | {t['assigns']} | "
                     f"{pct(t['completion'])} | {pct(t['score'])} |\n")
        L.append("\n")
        cc = {}
        for t in D["teachers"]:
            cc[t["campus"]] = cc.get(t["campus"], 0) + 1
        camps_ordered = "、".join(f"{k}（{v}人）" for k, v in sorted(cc.items(), key=lambda x: -x[1]))
        L.append(f"　　从活跃教师分布看，集团 TOP 教师主要集中在{camps_ordered}，"
                 f"骨干教师的布置经验尚未向其他校区充分扩散，是后续集团教研需要打通的重点。\n\n")

    # ── 四、年级使用画像 ───────────────────────────────────
    L.append("## 四、年级使用画像\n")
    if grades:
        L.append("| 年级 | 班级数 | 学生数 | 布置次数 | 完成率 | 得分率 | 自主练习次数 |\n"
                 "|------|------|------|------|------|------|------|\n")
        for r in grades:
            L.append(f"| {r['年级']} | {r['班级数']} | {r['学生数']:,} | {r['布置次数']} | "
                     f"{pct(r['完成率'])} | {pct(r['得分率'])} | {r['自主练习']} |\n")
        L.append("\n")
        active_grades = [r for r in grades if r["布置次数"] > 0]
        if active_grades:
            tg = max(active_grades, key=lambda r: r["布置次数"])
            L.append(f"　　从年级分布看，{tg['年级']}布置次数最高（{tg['布置次数']}次），"
                     f"年级间差异同样反映各校区推进节奏不均；建议结合集团统一教研计划，"
                     f"补齐布置偏少年级的训练安排。\n\n")

    # ── 五、总结与建议 ─────────────────────────────────────
    L.append("## 五、总结与建议\n")
    L.append(f"　　总体来看，{GD.GROUP_NAME}各校区应用差距显著，集团整体仍处于推广启动期，"
             f"{top['short']}已形成一定应用基础，而{laggards}尚未启动。后续建议："
             f"①提炼{top['short']}的布置与督促经验，在集团内统一推广；"
             f"②对{laggards}等待启动校区做名单化跟进，核查账号开通、教师培训与布置机制，设定阶段性布置量目标；"
             f"③由集团教研组统一规划各年级听说训练计划与高频资源，缩小校区间应用差距；"
             f"④以“数据观察—问题定位—专项跟进—阶段复盘”闭环，持续监测各校区应用进展，服务集团统一管理决策。\n\n")
    return "".join(L)


def main():
    agg = GD.load_group()
    D = GD.analyze(agg)
    md = build_text(D, agg)
    buf, err = C.export_to_docx(md)
    if err:
        print("导出失败：", err)
        return
    with open(OUT, "wb") as f:
        f.write(buf.getvalue())
    print("已生成：", OUT)
    # 同时落一份 markdown 便于审阅
    with open(OUT.replace(".docx", ".md"), "w", encoding="utf-8") as f:
        f.write(md)
    print("Markdown：", OUT.replace(".docx", ".md"))


if __name__ == "__main__":
    main()
