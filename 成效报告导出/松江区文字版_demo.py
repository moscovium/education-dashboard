# -*- coding: utf-8 -*-
"""
测试：仅凭「作业明细（作业数据）」能否生成 区级·文字版 报告？
================================================================
线上文字版流程 analyze_district_data → generate_district_report_text → export_to_docx
依赖「班级数据总览」(总学生数 / 布置作业次数 / 作业完成率 / 作业得分率 / 自主练习 等)。
作业明细本身不含这些班级级聚合列，但可由明细派生出等价口径的「班级数据总览」夹具：
  布置作业次数 = 班级 distinct 作业ID 数
  作业完成率   = 100%完成学生占比 均值
  作业得分率   = 作业得分率 均值
  总学生数     = 作答学生总数 最大值
  自主练习/词汇练习 = 作业明细无此数据，置 0（仅作业明细时的固有缺口）

据此用「现有文字版模版」生成上海市松江区区级文字版报告。
"""
import pandas as pd

import report_app_core as C

SRC = "/Users/x/Downloads/松江区_作业明细.xlsx"
OUT = "/Users/x/Downloads/松江区_文字版_区级样例.docx"


def build_fixture_class_df(det):
    """从作业明细聚合出「班级数据总览」口径夹具（一班一行）。

    班级单元 = (学校名称, 班级id)：班级id 非全局唯一（存在跨校复用），
    且同一班级在明细中可能因多教师 / 多年级拆成多行，若按全部维度分组会
    重复累计学生数与布置次数，故仅按 (学校, 班级id) 聚合，描述列取首个。
    """
    det = det.copy()
    for c in ("100%完成学生占比", "作业得分率", "作答学生总数", "单次作业平均耗时/min"):
        if c in det.columns:
            det[c] = pd.to_numeric(det[c], errors="coerce")
    desc = [c for c in ["省份", "城市", "区县", "学校ID", "学段", "年级",
                        "班级名称", "教师姓名"] if c in det.columns]
    rows = []
    for (school, cid), grp in det.groupby(["学校名称", "班级id"]):
        d = {"学校名称": school, "班级id": cid}
        for c in desc:
            nn = grp[c].dropna()
            d[c] = nn.iloc[0] if len(nn) else ""
        assigns = int(grp["作业ID"].nunique())
        d.update({
            "总学生数": int(grp["作答学生总数"].max() or 0),
            "布置作业次数": assigns,
            "布置作业份数": assigns,  # 作业明细无“份数”，以次数占位
            "作业完成率": float(grp["100%完成学生占比"].mean()),   # 0–1 分数，analyze_data ×100
            "作业得分率": float(grp["作业得分率"].mean()),
            "作答平均耗时/min": float(grp["单次作业平均耗时/min"].mean() or 0),
            "自主练习次数": 0,      # 作业明细缺口
            "词汇自主练习次数": 0,  # 作业明细缺口
            "转化率": 0,
        })
        rows.append(d)
    return pd.DataFrame(rows)


def main():
    det = pd.read_excel(SRC, sheet_name="E听说作业明细")
    # 作业明细中 作业得分率/耗时 等含 '-'（无作答/未批改），统一 coerce 为数值，
    # 否则 analyze_data 对 mock 子集求均值时会因混合类型报错。
    for c in ("作业得分率", "100%完成学生占比", "作答学生总数", "单次作业平均耗时/min"):
        if c in det.columns:
            det[c] = pd.to_numeric(det[c], errors="coerce")
    print(f"作业明细：{len(det):,} 行 / {det['学校名称'].nunique()} 校 / 区县={det['区县'].dropna().iloc[0]}")
    class_df = build_fixture_class_df(det)
    print(f"派生班级总览夹具：{len(class_df)} 班")

    data = C.analyze_district_data(class_df, det, None)
    md = C.generate_district_report_text(data)

    # 现有模版：随文字版生成图表并嵌入 Word（与线上一致）
    charts = None
    try:
        charts = C.make_district_charts(data)
    except Exception as e:
        print("图表生成跳过：", e)

    buf, err = C.export_to_docx(md, charts, data)
    if err:
        print("导出失败：", err)
        return
    with open(OUT, "wb") as f:
        f.write(buf.getvalue())
    with open(OUT.replace(".docx", ".md"), "w", encoding="utf-8") as f:
        f.write(md)
    print("已生成：", OUT)
    print("Markdown：", OUT.replace(".docx", ".md"))


if __name__ == "__main__":
    main()
