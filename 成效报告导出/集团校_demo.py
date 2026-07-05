# -*- coding: utf-8 -*-
"""
集团校（多校区）成效报告「图文版」样例生成器 —— 内容设计验证用
====================================================================
场景：集团校以「多条学校名称 + 校区后缀」形式出现在同一份班级宽表里
（如 滨州实验学校（北校区）/ 滨州实验学校西校区 / 滨州实验学校（南校区）），
报告介于「单校」与「区级」之间：顶层取各校区合计，核心层做「校区横向对比」，
下钻保留班级 / 年级 / 教师粒度。措辞从「学校 / 全区」改为「校区 / 集团」。

复用 graphic_report 的 Spectrum 视觉语言（CSS + 组件），只替换统计单元与文案。
渲染：HTML → Google Chrome headless --print-to-pdf。
"""
import subprocess

import pandas as pd

import graphic_report as G

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = "/Users/x/Downloads"

# 样例数据：含全 3 校区的两份 87 班宽表（单周用量稀疏，聚合两周使各校区有足够活跃班级）
FILES = [
    ("/Users/x/Downloads/0316-0322.xlsx", "03/16–03/22"),
    ("/Users/x/Downloads/20260608-20260614_作业数据.xlsx", "06/08–06/14"),
]
GROUP_KW = "滨州实验学校"
GROUP_NAME = "滨州实验学校"
PERIOD_TEXT = "03/16–03/22、06/08–06/14（两个抽样周）"


def num(s):
    return pd.to_numeric(s, errors="coerce")


def load_group():
    parts = []
    for f, _ in FILES:
        d = pd.read_excel(f)
        parts.append(d[d["学校名称"].astype(str).str.contains(GROUP_KW)])
    df = pd.concat(parts, ignore_index=True)
    for c in ["布置作业次数", "作业完成率", "作业得分率", "总学生数",
              "付费学生数", "转化率", "自主练习次数", "作答平均耗时/min"]:
        if c in df.columns:
            df[c] = num(df[c])
    # 同班跨周合并：布置求和，完成率/得分率/耗时取有值均值，学生 / 付费取 max
    agg = df.groupby(["学校名称", "班级id"]).agg(
        年级=("年级", "first"), 教师姓名=("教师姓名", "first"),
        总学生数=("总学生数", "max"), 付费学生数=("付费学生数", "max"),
        布置作业次数=("布置作业次数", "sum"),
        作业完成率=("作业完成率", "mean"), 作业得分率=("作业得分率", "mean"),
        作答耗时=("作答平均耗时/min", "mean"), 自主练习次数=("自主练习次数", "sum"),
    ).reset_index()
    return agg


def short_name(full):
    s = str(full).replace(GROUP_NAME, "").strip("（）() ")
    return s or "本部"


def analyze(agg):
    campuses = []
    for name, g in agg.groupby("学校名称"):
        act = g[g["布置作业次数"] > 0]
        classes = int(len(g))
        students = int(g["总学生数"].fillna(0).sum())
        paid = int(g["付费学生数"].fillna(0).sum())
        assigns = int(g["布置作业次数"].fillna(0).sum())
        comp = round(act["作业完成率"].mean() * 100, 1) if len(act) and act["作业完成率"].notna().any() else None
        score = round(act["作业得分率"].mean() * 100, 1) if len(act) and act["作业得分率"].notna().any() else None
        grades = sorted(g.loc[g["布置作业次数"] > 0, "年级"].dropna().unique().tolist())
        campuses.append({
            "name": str(name), "short": short_name(name),
            "classes": classes, "active": int(len(act)),
            "students": students, "paid": paid,
            "paid_rate": round(paid / students * 100, 1) if students else 0,
            "teachers": int(g["教师姓名"].nunique()),
            "assigns": assigns,
            "per_class": round(assigns / classes, 2) if classes else 0,
            "completion": comp, "score": score,
            "active_grades": grades,
            "self_prac": int(g["自主练习次数"].fillna(0).sum()),
        })
    campuses.sort(key=lambda c: c["per_class"], reverse=True)

    tot_classes = sum(c["classes"] for c in campuses)
    tot_active = sum(c["active"] for c in campuses)
    tot_students = sum(c["students"] for c in campuses)
    tot_paid = sum(c["paid"] for c in campuses)
    tot_assigns = sum(c["assigns"] for c in campuses)
    act_df = agg[agg["布置作业次数"] > 0]
    grp = {
        "campuses": len(campuses), "classes": tot_classes, "active": tot_active,
        "students": tot_students, "paid": tot_paid, "assigns": tot_assigns,
        "per_class": round(tot_assigns / tot_classes, 2) if tot_classes else 0,
        "active_rate": round(tot_active / tot_classes * 100, 1) if tot_classes else 0,
        "paid_rate": round(tot_paid / tot_students * 100, 1) if tot_students else 0,
        "completion": round(act_df["作业完成率"].mean() * 100, 1) if len(act_df) else 0,
        "score": round(act_df["作业得分率"].mean() * 100, 1) if len(act_df) else 0,
    }

    # 教师下钻：有布置的教师按布置次数排序
    tagg = agg[agg["布置作业次数"] > 0].groupby("教师姓名").agg(
        campus=("学校名称", "first"), classes=("班级id", "nunique"),
        assigns=("布置作业次数", "sum"), comp=("作业完成率", "mean"), score=("作业得分率", "mean"),
    ).reset_index().sort_values("assigns", ascending=False).head(8)
    teachers = [{
        "name": r["教师姓名"], "campus": short_name(r["campus"]),
        "classes": int(r["classes"]), "assigns": int(r["assigns"]),
        "completion": round(r["comp"] * 100, 1) if pd.notna(r["comp"]) else None,
        "score": round(r["score"] * 100, 1) if pd.notna(r["score"]) else None,
    } for _, r in tagg.iterrows()]

    return {"group": grp, "campuses": campuses, "teachers": teachers}


# ── 自定义组件（校区卡）─────────────────────────────────────────────
def campus_card(c, fmax):
    pct = max(3, min(100, c["per_class"] / fmax * 100)) if fmax else 0
    dormant = c["active"] == 0
    comp = f'{c["completion"]}%' if c["completion"] is not None else "—"
    score = f'{c["score"]}%' if c["score"] is not None else "—"
    foot = (f'{G.icon("alert", "#e34850", 13)} 整组 {c["classes"]} 个班本期零布置，建议优先启动'
            if dormant else
            f'{G.icon("teacher", "#8c8c8c", 13)} 教师 {c["teachers"]} 人 · 活跃年级 {"、".join(c["active_grades"]) or "—"} · 付费转化 {c["paid_rate"]}%')
    idx = "0" if dormant else c["per_class"]
    return f"""<div class="ecard">
      <div class="ecard-h"><div class="ecard-name">{G.esc(c['short'])}</div>
        <div class="ecard-idx">{idx}<span>次/班</span></div></div>
      <div class="ecard-track"><div class="ecard-fill" style="width:{pct:.0f}%"></div></div>
      <div class="ms-grid">{G.mini('班级', c['classes'])}{G.mini('活跃班级', c['active'])}
        {G.mini('完成率', comp)}{G.mini('得分率', score)}</div>
      <div class="ecard-foot">{foot}</div></div>"""


def build_html(D):
    g = D["group"]
    cs = D["campuses"]
    fmax = max((c["per_class"] for c in cs), default=1)
    top = cs[0]
    dormant = [c for c in cs if c["active"] == 0]
    low = dormant[0] if dormant else cs[-1]
    now = pd.Timestamp.now().strftime("%Y年%m月%d日")

    kpis = "".join([
        G.stat("layers", "校区数", g["campuses"], "纳入集团对比"),
        G.stat("class", "覆盖班级", f"{g['classes']:,}", f"活跃 {g['active']} 班"),
        G.stat("users", "覆盖学生", f"{g['students']:,}", f"付费转化 {g['paid_rate']}%"),
        G.stat("doc", "累计布置", f"{g['assigns']:,}", "各校区布置次数合计"),
        G.stat("trend", "班均布置次数", g["per_class"], "集团整体（次/班）"),
        G.stat("check", "活跃班级率", f"{g['active_rate']}%", f"{g['active']}/{g['classes']} 班有布置"),
        G.stat("score", "平均完成率", f"{g['completion']}%", "活跃班级 100% 完成占比"),
        G.stat("target", "平均得分率", f"{g['score']}%", "活跃班级日常作业"),
    ])

    # 核心结论（校区维度）
    act_camps = [c for c in cs if c["active"] > 0]
    laggards = "、".join(c["short"] for c in dormant) or "无"
    ccs = [
        ("集团覆盖", f"{GROUP_NAME}共 {g['campuses']} 个校区、{g['classes']} 个班级、{g['students']:,} 名学生纳入对比；"
                     f"本期累计布置作业 {g['assigns']} 次，活跃班级 {g['active']} 个（活跃班级率 {g['active_rate']}%）。"),
        ("校区分化", f"{top['short']}为应用主力（班均 {top['per_class']} 次、{top['active']} 个班活跃），"
                     f"明显领先其余校区，可作为集团内示范。"),
        ("待启动校区", f"{laggards} 本期布置极少甚至为零，集团内应用冷热不均，"
                       "是下阶段重点跟进对象。" if dormant else
                       f"各校区均有布置，但 {cs[-1]['short']} 班均仅 {cs[-1]['per_class']} 次，相对靠后。"),
        ("作答质量", f"活跃班级平均完成率 {g['completion']}%、得分率 {g['score']}%；"
                     "应用主力校区在保证布置量的同时需关注完成率，避免“布置多、完成少”。"),
    ]
    cc_html = "".join(G.conclusion(i + 1, t, b) for i, (t, b) in enumerate(ccs))

    rank_html = "".join(
        G.bar_row(c["short"], c["per_class"], fmax, " 次/班",
                  "#2d9d78" if c is top else ("#cacaca" if c["active"] == 0 else "#1473e6"))
        for c in cs)
    cards = "".join(campus_card(c, fmax) for c in cs)

    # 校区 × 关键指标对照表
    cmp_tbl = G.table(
        ["校区", "班级", "活跃班级", "教师", "累计布置", "班均次数", "完成率", "得分率", "付费转化"],
        [(c["short"], c["classes"], c["active"], c["teachers"], c["assigns"], c["per_class"],
          f'{c["completion"]}%' if c["completion"] is not None else "—",
          f'{c["score"]}%' if c["score"] is not None else "—", f'{c["paid_rate"]}%') for c in cs],
        ["left", "right", "right", "right", "right", "right", "right", "right", "right"])

    tch_rows = [(t["name"], t["campus"], t["classes"], t["assigns"],
                 f'{t["completion"]}%' if t["completion"] is not None else "—",
                 f'{t["score"]}%' if t["score"] is not None else "—") for t in D["teachers"]]
    tch_tbl = G.table(["教师", "所属校区", "班级", "布置次数", "完成率", "得分率"], tch_rows,
                      ["left", "left", "right", "right", "right", "right"])

    suggestions = "".join([
        G.suggestion("star", "沉淀并复制应用主力经验",
                     f"组织 {top['short']}的骨干教师在集团教研中分享布置节奏与学生督促做法，形成可复制的标准动作。"),
        G.suggestion("alert", "名单化启动待跟进校区",
                     f"针对 {laggards} 等冷启动校区，逐校核查账号开通、教师培训与作业布置机制，设定首月布置量目标。"),
        G.suggestion("layers", "集团统一教研与资源",
                     "由集团教研组统一规划各年级听说训练计划与高频资源，缩小校区间应用差距，避免各校区各自为战。"),
        G.suggestion("speed", "关注作答质量闭环",
                     f"活跃班级完成率 {g['completion']}%，建议对完成率偏低的班级跟进督促机制，把“布置”转化为“完成”。"),
    ])

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{G.CSS}
.ecard-grid{{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
</style></head><body>

<header class="cover">
  <h1>{G.esc(GROUP_NAME)} E听说应用成效报告</h1>
  <p class="cover-sub">集团多校区版 · 基于 {G.esc(GROUP_NAME)} 北校区 / 西校区 / 南校区
    {PERIOD_TEXT} 应用数据，横向对比各校区应用情况，定位冷热不均并提出下阶段建议。</p>
  <div class="chips">
    <span class="chip">{G.icon('calendar','#4b4b4b',14)} {PERIOD_TEXT}</span>
    <span class="chip">{G.icon('layers','#4b4b4b',14)} {g['campuses']} 个校区</span>
    <span class="chip">{G.icon('class','#4b4b4b',14)} {g['classes']} 个班级</span>
  </div>
</header>

<section class="band"><div class="stat-grid g4">{kpis}</div></section>

<section class="block">{G.sec_title('star','本期核心结论')}<div class="cc-list">{cc_html}</div></section>

<section class="block page">{G.sec_title('trend','各校区班均布置次数对比','统计单元为校区：班均布置次数 = 校区累计布置次数 ÷ 班级数（次/班），适用于短周期对比。绿＝应用主力，灰＝本期零布置。')}
  <div class="card"><div class="barlist">{rank_html}</div></div>
  <div class="grid2">
    <div class="hcard good"><div class="hcard-tag">{G.icon('star','#2d9d78',15)} 应用主力校区</div>
      <div class="hcard-name">{G.esc(top['short'])}</div>
      <div class="hcard-sub">班均 {top['per_class']} 次 · {top['active']} 班活跃 · 完成率 {top['completion']}% · 得分率 {top['score']}%</div></div>
    <div class="hcard warn"><div class="hcard-tag">{G.icon('alert','#e34850',15)} 待启动校区</div>
      <div class="hcard-name">{G.esc(low['short'])}</div>
      <div class="hcard-sub">{low['classes']} 个班 · 活跃 {low['active']} 班 · 本期布置 {low['assigns']} 次</div></div>
  </div></section>

<section class="block page">{G.sec_title('school','各校区应用画像','每个校区一张卡片：班均布置次数、活跃班级、完成率、得分率与教师 / 年级覆盖一览。')}
  <div class="ecard-grid">{cards}</div>
  <div class="card tbl-card" style="margin-top:14px"><div class="card-h">校区关键指标对照</div>{cmp_tbl}</div></section>

<section class="block page">{G.sec_title('teacher','教师应用下钻（集团 TOP）','跨校区按布置次数排序，定位集团内活跃教师及其所属校区，便于经验萃取与示范。')}
  <div class="card tbl-card">{tch_tbl}</div></section>

<section class="block">{G.sec_title('target','下一步工作建议')}
  <div class="grid2">{suggestions}</div>
  <div class="footer">数据来源：{G.esc(GROUP_NAME)} 班级数据总览（{PERIOD_TEXT}）　|　统计单元：校区　|　综合指标：班均布置次数（窗口内每班累计）　|　报告生成：{now}</div></section>

</body></html>"""


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
    agg = load_group()
    D = analyze(agg)
    g = D["group"]
    print(f"集团 {GROUP_NAME}: {g['campuses']} 校区 / {g['classes']} 班 / 活跃 {g['active']} 班 / 布置 {g['assigns']} 次")
    for c in D["campuses"]:
        print(f"  - {c['short']}: {c['classes']}班 活跃{c['active']} 班均{c['per_class']} "
              f"完成{c['completion']} 得分{c['score']}")
    render(build_html(D), "滨州实验学校_图文版_集团校区样例")


if __name__ == "__main__":
    main()
