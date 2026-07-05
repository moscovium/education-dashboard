# -*- coding: utf-8 -*-
"""
单校图文版 本地样例：银川市第十六中学（班级总览 + 作业明细 + 听说模拟题型）。
走 graphic_report.analyze_graphic_school / build_school_graphic_html（未上线，验证用）。
"""
import subprocess

import report_app_core as C
import graphic_report as G

BASE = "/Users/x/Downloads/银川市第十六中学_"
OUT = "/Users/x/Downloads/银川市第十六中学_图文版_单校样例"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    cls = C.parse_class_overview(open(BASE + "班级数据总览.xlsx", "rb"))
    det = C.parse_hw_details(open(BASE + "作业明细.xlsx", "rb"))
    qt = C.parse_question_type(open(BASE + "听说模拟题型.xlsx", "rb"))
    S = G.analyze_graphic_school(cls, det, qt)
    sc = S["school"]
    print(f"{sc['name']}: {sc['classes']}班 {sc['students']}人 布置{sc['assigns']} 周期{sc['weeks']}周 "
          f"周维度={sc['weekly']} 套题可比={len(S.get('papers', []))} 阶段成效={'有' if S.get('stage') else '无'}")
    html = G.build_school_graphic_html(S)
    with open(OUT + ".html", "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={OUT}.pdf", f"file://{OUT}.html"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("已生成：", OUT + ".pdf")


if __name__ == "__main__":
    main()
