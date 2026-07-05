# -*- coding: utf-8 -*-
"""
图文版本地预览 DEMO（不改动线上代码）
======================================
仅负责：把滨城区测试数据读成 DataFrame → 调 graphic_report.build_graphic_html →
Google Chrome headless 打印成 PDF，产出两份样例：
  · 成效报告_图文版_两表_DEMO.pdf  （仅 班级数据总览 + 作业明细）
  · 成效报告_图文版_全表_DEMO.pdf  （+ 听说模拟题型 + 阶段性联考）

线上图文版逻辑全部在 graphic_report.py（与本 demo 共用），浏览器端打印即得 PDF。
"""
import subprocess
import warnings

import pandas as pd

import report_app_core as C
import graphic_report as G

warnings.filterwarnings("ignore")

DETAIL_XLSX = "/Users/x/Downloads/滨城区七年级_作业明细.xlsx"
QTYPE_XLSX = "/Users/x/Downloads/滨城区七年级_听说模拟套题.xlsx"
EXAM_DOCX = "/Users/x/Downloads/2026年1月滨州市滨城区七年级期末考试报告.docx"
OUT_DIR = "/Users/x/Downloads/Project/成效报告导出"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def build_fixture_class_df(det):
    """无真实多校班级总览时，从作业明细聚合出班级数据总览口径的夹具。"""
    g = det.groupby(['省份', '城市', '区县', '学校ID', '学校名称', '学段', '年级',
                     '班级id', '班级名称', '教师姓名'])
    rows = []
    for key, grp in g:
        rows.append({
            '省份': key[0], '城市': key[1], '区县': key[2], '学校名称': key[4], '学段': key[5],
            '年级': key[6], '班级id': key[7], '班级名称': key[8], '教师姓名': key[9],
            '总学生数': int(grp['作答学生总数'].max()),
            '布置作业次数': int(grp['作业ID'].nunique()),
            '作业完成率': float(grp['100%完成学生占比'].mean()),
            '作业得分率': float(grp['作业得分率'].mean()),
            '作答平均耗时/min': float(grp['单次作业平均耗时/min'].mean()),
        })
    return pd.DataFrame(rows)


def render(html_str, name):
    html_path = f"{OUT_DIR}/{name}.html"
    pdf_path = f"{OUT_DIR}/{name}.pdf"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("已生成：", pdf_path)


def main():
    det = pd.read_excel(DETAIL_XLSX)
    class_df = build_fixture_class_df(det)
    hw_df = C.parse_hw_details(DETAIL_XLSX)
    qt_df = C.parse_question_type(QTYPE_XLSX)
    exam_stages = C.parse_exam_reports([EXAM_DOCX])

    # 样例一：两表
    D1 = G.analyze_graphic(class_df, hw_df)
    render(G.build_graphic_html(D1), "成效报告_图文版_两表_DEMO")
    # 样例二：全表
    D2 = G.analyze_graphic(class_df, hw_df, qt_df=qt_df, exam_stages=exam_stages)
    render(G.build_graphic_html(D2), "成效报告_图文版_全表_DEMO")


if __name__ == "__main__":
    main()
