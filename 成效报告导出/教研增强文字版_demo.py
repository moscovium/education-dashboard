# -*- coding: utf-8 -*-
"""
教研增强版·区级文字版 本地验证薄壳
====================================
教研增强逻辑已于 v2.7 正式合入 report_app_core（analyze_district_data /
generate_district_report_text / make_district_charts），本脚本仅负责：
读滨城区测试数据 → 走与线上一致的核心路径 → 出 Word，供本地回归。

v2.7 增量（客户反馈定稿）：概况表增 平均作答率/单次耗时（仅列指标不加解释）、
3.2 班级四象限（教师画像顺延 3.3）、作业负担句（>20min 学校标注）、
薄弱题型→课堂动作表（样本数≥100）、总结改“谁—何时—做什么—怎么验收”；
仅 1 个年级时省略年级分布语句与图2；图3 为全部学校总列表。
"""
import pandas as pd

import report_app_core as C
from 松江区文字版_demo import build_fixture_class_df

DETAIL = "/Users/x/Downloads/滨城区七年级_作业明细.xlsx"
QTYPE = "/Users/x/Downloads/滨城区七年级_听说模拟套题.xlsx"
OUT = "/Users/x/Downloads/滨城区_文字版_教研增强样例.docx"


def main():
    det = C.parse_hw_details(open(DETAIL, "rb"))
    qt = C.parse_question_type(open(QTYPE, "rb"))
    class_df = build_fixture_class_df(det)
    print(f"明细 {len(det):,} 行 / {det['学校名称'].nunique()} 校 / 班级夹具 {len(class_df)} 班")

    data = C.analyze_district_data(class_df, det, qt)
    md = C.generate_district_report_text(data)
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


if __name__ == "__main__":
    main()
