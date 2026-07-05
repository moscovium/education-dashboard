# -*- coding: utf-8 -*-
"""
松江区 图文版 本地样例（走线上同一源 graphic_report，不改逻辑）
仅有作业明细 → 班级总览夹具由明细派生（口径与线上文字版测试一致）。
"""
import subprocess

import report_app_core as C
import graphic_report as G
from 松江区文字版_demo import build_fixture_class_df

SRC = "/Users/x/Downloads/松江区_作业明细.xlsx"
OUT = "/Users/x/Downloads/松江区_图文版_区级样例"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    det = C.parse_hw_details(open(SRC, "rb"))
    class_df = build_fixture_class_df(det)
    print(f"明细 {len(det):,} 行 / {det['学校名称'].nunique()} 校 / 夹具 {len(class_df)} 班")
    D = G.analyze_graphic(class_df, det)
    r = D["region"]
    print(f"区域={r['name']} 学校={r['schools']} 班级={r['classes']} 周={r['weeks']} 短周期={r['short']}")
    html = G.build_graphic_html(D)
    with open(OUT + ".html", "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={OUT}.pdf", f"file://{OUT}.html"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("已生成：", OUT + ".pdf")


if __name__ == "__main__":
    main()
