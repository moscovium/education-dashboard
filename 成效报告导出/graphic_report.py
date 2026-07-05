# -*- coding: utf-8 -*-
"""
区级成效报告「图文版」生成器（线上 + demo 共用单一源）
=========================================================
按 Adobe React Spectrum 设计语言（中性灰基底 + 单一蓝色强调 + 克制描边阴影），
偏汇报风格。面向「班级数据总览 + 作业明细」两张基础表，题型 / 联考为可选增强。

入口：
  analyze_graphic(class_df, hw_df, qt_df=None, exam_stages=None) -> dict
  build_graphic_html(D) -> str   # 自包含 HTML（含 <style>），交由浏览器渲染 / 打印 PDF

综合指标：班均周布置频次 = Σ布置作业次数 ÷ 班级数 ÷ 窗口周数，
窗口 = 各校首次布置作业日 → 全区最后一次布置作业日（统一截止）。
"""
import base64
import html
import math
import re
from datetime import datetime

import pandas as pd

try:
    import report_app_core as C  # 复用：联考解析 / 题型 / 模糊匹配
except Exception:  # pragma: no cover
    C = None

REGION_DEFAULT = "本区域"
SCHOOL_PAT = re.compile(r"(中学|学校|学园|小学|中心|附中|分校|实验)")
EXAM_QTYPES = (C.EXAM_QTYPES if C else
               ['听句子选答案', '听对话选答案', '听短文选答案', '短文朗读', '情景对话', '情景表达'])


def esc(x):
    return html.escape(str(x))


def fp(v):
    """百分比显示兜底：None → —，避免 nan% 上报告。"""
    return f"{v}%" if v is not None else "—"


def is_school(name):
    return bool(SCHOOL_PAT.search(str(name)))


def _quals(region, city="", province=""):
    qs = set()
    for v in (province, city, region):
        v = str(v or "").strip()
        if v:
            qs.add(v)
            qs.add(v.rstrip("省市区县"))
    qs.discard("")
    return sorted(qs, key=len, reverse=True)


def _short(name, quals):
    s = str(name)
    for q in quals:
        s = s.replace(q, "")
    return s.replace("街道办事处", "").replace("中心学校", "中心").strip() or str(name)


# ════════════════════════════════════════════════════════════════════════
# 取数
# ════════════════════════════════════════════════════════════════════════
def analyze_graphic(class_df, hw_df, qt_df=None, exam_stages=None):
    # 全部以「作业明细」为准：该表稳定且必含 班级id / 作业ID / 日期 / 完成率 / 得分率，
    # 「班级数据总览」格式多变，仅在含 总学生数 时用作学生数补充，避免列名缺失报错。
    hw = hw_df.copy()

    def num(s):
        return pd.to_numeric(s, errors="coerce")

    def first_val(df, col):
        if df is not None and col in df.columns:
            vals = [str(v).strip() for v in df[col].dropna() if str(v).strip()]
            if vals:
                return vals[0]
        return ""

    region_name = first_val(hw, "区县") or first_val(hw, "城市") or REGION_DEFAULT
    city = first_val(hw, "城市")
    province = first_val(hw, "省份")
    quals = _quals(region_name, city, province)

    hw["d"] = pd.to_datetime(hw["作业开始日期"], errors="coerce")
    for c in ("作业得分率", "100%完成学生占比", "单次作业平均耗时/min", "作答学生总数"):
        if c in hw.columns:
            hw[c] = pd.to_numeric(hw[c], errors="coerce")
    hw["大类"] = hw["作业路径"].astype(str).str.split("-").str[0]
    hw["小类"] = hw["作业路径"].astype(str).str.split("-").str[1].fillna("其他")
    hw = hw[hw["学校名称"].map(is_school)].copy()

    # 可选：从班级数据总览取真实学生数 + 全量名册（含未布置班级，用于激活率）
    roster = {}
    total_schools = total_classes = None
    if class_df is not None and "学校名称" in class_df.columns:
        cc = class_df[class_df["学校名称"].map(is_school)]
        if not cc.empty:
            total_schools = int(cc["学校名称"].nunique())
            if "班级id" in cc.columns:
                total_classes = int(cc["班级id"].nunique())
            if "总学生数" in cc.columns:
                roster = cc.groupby("学校名称")["总学生数"].apply(
                    lambda g: int(num(g).fillna(0).sum())).to_dict()

    gstart, gend = hw["d"].min(), hw["d"].max()
    region_weeks = max(1.0, (gend - gstart).days / 7)
    span_days = int((gend - gstart).days) + 1
    # 短周期（窗口 < 5 周）：周频次因窗口过短、各校启动错位而失真，
    # 改用「班均布置次数」(窗口内每班累计布置次数) 作为综合指标，更稳健直观。
    short = region_weeks < 5

    schools = []
    for name, grp in hw.groupby("学校名称"):
        classes = int(grp["班级id"].nunique())
        assigns = int(grp["作业ID"].nunique())
        first = grp["d"].min()
        weeks = max(1.0, (gend - first).days / 7)
        per_class = round(assigns / classes, 1) if classes else 0
        week_freq = round(assigns / classes / weeks, 2) if classes else 0
        hw_students = int(grp.groupby("班级id")["作答学生总数"].max().fillna(0).sum())
        schools.append({
            "name": str(name), "short": _short(name, quals),
            "classes": classes,
            "students": int(roster.get(name, hw_students)),
            "assigns": assigns,
            "first": first, "weeks": round(weeks, 1),
            "active_days": int((gend - first).days) + 1,
            "week_freq": week_freq, "per_class": per_class,
            "metric": per_class if short else week_freq,
            # 全部记录得分率/完成率缺失（如'-'）时置 None，渲染为"—"，避免 nan% 上报告
            "completion": round(float(comp_m * 100), 1) if pd.notna(comp_m := grp["100%完成学生占比"].mean()) else None,
            "score": round(float(score_m * 100), 1) if pd.notna(score_m := grp["作业得分率"].mean()) else None,
            "minutes": round(float(mins_m), 1) if pd.notna(mins_m := grp["单次作业平均耗时/min"].mean()) else None,
        })
    schools.sort(key=lambda s: s["metric"], reverse=True)

    region_assigns = int(hw["作业ID"].nunique())
    region_classes = int(hw["班级id"].nunique())
    region = {
        "name": region_name,
        "schools": len(schools),
        "classes": region_classes,
        "students": sum(s["students"] for s in schools),
        "assigns": region_assigns,
        "completion": round(float(hw["100%完成学生占比"].mean() * 100), 1),
        "score": round(float(hw["作业得分率"].mean() * 100), 1),
        "minutes": (round(float(m_), 1) if "单次作业平均耗时/min" in hw and pd.notna(m_ := hw["单次作业平均耗时/min"].mean()) else 0),
        "gstart": gstart, "gend": gend, "weeks": round(region_weeks, 1), "span_days": span_days,
        "week_freq": round(region_assigns / region_classes / region_weeks, 2) if region_classes else 0,
        "per_class": round(region_assigns / region_classes, 1) if region_classes else 0,
        "total_schools": total_schools, "total_classes": total_classes,
        "short": short, "quals": quals,
    }
    region["metric"] = region["per_class"] if short else region["week_freq"]
    region["metric_label"] = "班均布置次数" if short else "班均周布置频次"
    region["metric_unit"] = " 次/班" if short else " 次/班·周"
    region["metric_caliber"] = (
        "综合指标口径＝窗口内班均布置次数：统计周期内 布置次数 ÷ 班级数（次/班），适用于 2～4 周短周期。"
        if short else
        "综合指标口径＝窗口内平均每周布置次数：以各校首次布置作业为起点、全区最后一次布置作业为统一截止日，"
        "计 布置次数 ÷ 班级数 ÷ 窗口周数（次/班·周）。")

    # 趋势：短周期按「每日」呈现，长周期按「月度」
    if short:
        ser = hw.groupby(hw["d"].dt.strftime("%m/%d"))["作业ID"].nunique().sort_index()
        trend = [(k, int(v)) for k, v in ser.items() if k]
        trend_title, trend_desc = "每日作业量趋势", "按作业开始日期统计去重作业数，观察短周期内的布置节奏。"
    else:
        ser = hw.groupby(hw["d"].dt.to_period("M").astype(str))["作业ID"].nunique().sort_index()
        trend = [(m[2:].replace("-", "/"), int(v)) for m, v in ser.items() if m != "NaT"]
        trend_title, trend_desc = "月度作业量趋势", "按作业开始月份统计去重作业数，观察全区推进节奏。"

    cat = hw.groupby("大类")["作业ID"].nunique().sort_values(ascending=False)
    ctotal = int(cat.sum()) or 1
    categories = [(str(k), int(v), round(v / ctotal * 100, 1)) for k, v in cat.items()]

    sub = hw.groupby(["大类", "小类"]).agg(
        n=("作业ID", "nunique"), score=("作业得分率", "mean"), mins=("单次作业平均耗时/min", "mean")
    ).reset_index().sort_values("n", ascending=False).head(8)
    subitems = [(r["大类"], r["小类"], int(r["n"]),
                 round(r["score"] * 100, 1) if pd.notna(r["score"]) else "—",
                 round(r["mins"], 1) if pd.notna(r["mins"]) else "—")
                for _, r in sub.iterrows()]

    teachers = []
    if "教师姓名" in hw.columns:
        tch = hw.groupby("教师姓名").agg(
            school=("学校名称", "first"), classes=("班级id", "nunique"),
            assigns=("作业ID", "nunique"), completion=("100%完成学生占比", "mean"),
            score=("作业得分率", "mean"), first=("d", "min"),
        ).reset_index().sort_values("assigns", ascending=False).head(8)
        for _, r in tch.iterrows():
            wk = max(1.0, (gend - r["first"]).days / 7)
            teachers.append({
                "name": r["教师姓名"], "school": _short(r["school"], quals), "classes": int(r["classes"]),
                "assigns": int(r["assigns"]), "week_freq": round(r["assigns"] / r["classes"] / wk, 2),
                "completion": round(r["completion"] * 100, 1), "score": round(r["score"] * 100, 1),
            })

    D = {"region": region, "schools": schools,
         "trend": trend, "trend_title": trend_title, "trend_desc": trend_desc,
         "categories": categories, "subitems": subitems, "teachers": teachers}

    # ── 阶段成效（听说模拟）：由作业明细「模拟-」路径记录派生，题型表非必传时亦可呈现 ──
    mock = hw[hw["大类"] == "模拟"]
    if int(mock["作业ID"].nunique()) >= 10:
        mser = mock.groupby(mock["d"].dt.to_period("M").astype(str))["作业得分率"].mean().dropna().sort_index()
        mtrend = [(m[2:].replace("-", "/"), round(float(v) * 100, 1)) for m, v in mser.items() if m != "NaT"]
        improve = (round(max(v for _, v in mtrend) - min(v for _, v in mtrend), 1)
                   if len(mtrend) >= 2 else None)

        def _imp(gg):
            ser = gg.groupby(gg["d"].dt.to_period("M"))["作业得分率"].mean().dropna()
            return round(float(ser.max() - ser.min()) * 100, 1) if len(ser) >= 2 else 0.0

        def _sc(gg):
            m = gg["作业得分率"].mean()
            return round(float(m) * 100, 1) if pd.notna(m) else None

        grades = [{"grade": str(g), "n": int(gg["作业ID"].nunique()), "score": _sc(gg), "improve": _imp(gg)}
                  for g, gg in mock.groupby("年级")]
        if C:
            grades.sort(key=lambda r: C._grade_sort_key(r["grade"]))
        cases = [{"school": _short(s, quals), "grade": str(g), "n": int(gg["作业ID"].nunique()),
                  "score": _sc(gg), "improve": _imp(gg)}
                 for (s, g), gg in mock.groupby(["学校名称", "年级"])]
        cases.sort(key=lambda r: (-r["n"], -(r["improve"] or 0)))

        top_cls = None
        cstat = mock.groupby(["学校名称", "班级id"]).agg(
            名称=("班级名称", "first"), 年级=("年级", "first"), n=("作业ID", "nunique")).reset_index()
        if len(cstat):
            b = cstat.sort_values("n", ascending=False).iloc[0]
            gg = mock[(mock["学校名称"] == b["学校名称"]) & (mock["班级id"] == b["班级id"])]
            ser = gg.groupby(gg["d"].dt.to_period("M"))["作业得分率"].mean().dropna()
            if len(ser) >= 2:
                cn, gname = str(b["名称"]), str(b["年级"])
                label = f"{cn}班" if cn.startswith(gname[:1]) and len(cn) > 1 else f"{gname}{cn}班"
                top_cls = {"school": _short(b["学校名称"], quals), "cls": label, "n": int(b["n"]),
                           "first": round(float(ser.iloc[0]) * 100, 1),
                           "last": round(float(ser.iloc[-1]) * 100, 1),
                           "peak": round(float(ser.max()) * 100, 1)}
        D["mock"] = {"n": int(mock["作业ID"].nunique()), "schools": int(mock["学校名称"].nunique()),
                     "classes": int(mock["班级id"].nunique()), "score": _sc(mock),
                     "improve": improve, "trend": mtrend,
                     "grades": grades, "cases": cases[:5], "top_class": top_cls}

    qt_means = {}
    if qt_df is not None and not qt_df.empty and "题型名称" in qt_df.columns:
        m = qt_df.groupby("题型名称")["得分率"].agg(["mean", "size"])
        opt = qt_df.groupby("题型名称")["优秀率"].mean()
        low = qt_df.groupby("题型名称")["低分率"].mean()
        qt_means = {k: round(v["mean"] * 100, 1) for k, v in m.iterrows()}
        rows = [(k, round(v["mean"] * 100, 1), round(opt[k] * 100, 1), round(low[k] * 100, 1), int(v["size"]))
                for k, v in m.iterrows()]
        rows.sort(key=lambda r: r[1], reverse=True)
        D["qt"] = {"rows": rows, "records": int(len(qt_df)), "types": int(qt_df["题型名称"].nunique())}

    if exam_stages and C:
        latest = exam_stages[-1]
        ex_names = list(latest["schools"].keys())
        pnames = [s["name"] for s in schools]
        matched, only_p, only_e = C._fuzzy_match_schools(pnames, ex_names, quals)
        link = []
        for p, ex in matched.items():
            sd = next(x for x in schools if x["name"] == p)
            avg = latest["schools"][ex].get("平均分")
            if avg is None or sd["score"] is None:
                continue
            link.append({"school": p, "exam": ex, "short": _short(ex, quals),
                         "prac": sd["score"], "week_freq": sd["week_freq"], "avg": avg})
        link.sort(key=lambda r: r["avg"], reverse=True)

        def corr(xs, ys):
            n = len(xs)
            if n < 3:
                return 0.0
            mx, my = sum(xs) / n, sum(ys) / n
            cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((y - my) ** 2 for y in ys))
            return round(cov / (sx * sy), 3) if sx * sy else 0.0

        qt_cmp = []
        for q in EXAM_QTYPES:
            pv = qt_means.get(q)
            ev = C._safe_float(latest["qtype"].get(q, {}).get("得分率"))
            if pv is not None or ev is not None:
                qt_cmp.append({"q": q, "prac": pv, "exam": ev})
        D["exam"] = {
            "label": latest["label"], "full_mark": latest.get("full_mark", 30),
            "overall": latest.get("overall", {}), "score_rate": latest.get("score_rate"),
            "school_count": len(latest["schools"]), "schools": latest["schools"],
            "link": link, "r_score": corr([r["prac"] for r in link], [r["avg"] for r in link]),
            "r_freq": corr([r["week_freq"] for r in link], [r["avg"] for r in link]),
            "only_exam": only_e, "qt_cmp": qt_cmp,
        }
    return D


# ════════════════════════════════════════════════════════════════════════
# 图标 / 组件
# ════════════════════════════════════════════════════════════════════════
ICONS = {
    "school": '<path d="M3 21h18M5 21V9l7-4 7 4v12M9 21v-5h6v5"/>',
    "class": '<rect x="4" y="4" width="16" height="16" rx="1.5"/><path d="M4 9h16M9 4v16"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3 3-5 6-5s6 2 6 5M16 6a3 3 0 0 1 0 6M22 20c0-2-1.5-3.5-3.5-4"/>',
    "doc": '<path d="M7 3h7l5 5v13H7zM14 3v5h5"/>',
    "check": '<path d="M4 12l5 5L20 6"/>',
    "score": '<path d="M4 19V5m4 14v-8m4 8V8m4 11v-6m4 6V4"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/>',
    "trend": '<path d="M4 16l5-5 4 3 7-8M15 6h5v5"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
    "star": '<path d="M12 3l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 18l-5.9 3 1.2-6.5L2.5 9.9 9.1 9z"/>',
    "alert": '<path d="M12 4l9 16H3zM12 10v4M12 17h.01"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5zM3 13l9 5 9-5M3 17l9 5 9-5"/>',
    "teacher": '<path d="M12 3l9 4-9 4-9-4zM7 9v5c0 1.5 2.5 3 5 3s5-1.5 5-3V9"/>',
    "speed": '<path d="M12 14l4-4M5 19a9 9 0 1 1 14 0"/>',
}


def icon(name, color="#1473e6", size=18, sw=1.9):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICONS.get(name, "")}</svg>')


def stat(ic, label, value, sub=""):
    return f"""<div class="stat"><div class="stat-h">{icon(ic,'#1473e6',16)}<span>{esc(label)}</span></div>
      <div class="stat-v">{esc(value)}</div><div class="stat-s">{esc(sub)}</div></div>"""


def sec_title(ic, title, desc=""):
    d = f'<div class="sec-desc">{esc(desc)}</div>' if desc else ""
    return (f'<div class="sec-head"><span class="sec-rail"></span>{icon(ic,"#1473e6",18)}'
            f'<span class="sec-t">{esc(title)}</span></div>{d}')


def bar_row(label, value, vmax, suffix="", color="#1473e6"):
    pct = max(2, min(100, value / vmax * 100)) if vmax else 0
    return (f'<div class="brow"><div class="blabel">{esc(label)}</div>'
            f'<div class="btrack"><div class="bfill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<div class="bval">{esc(value)}{esc(suffix)}</div></div>')


def conclusion(n, title, body):
    return (f'<div class="cc"><span class="cc-n">{n}</span><div>'
            f'<div class="cc-t">{esc(title)}</div><div class="cc-b">{esc(body)}</div></div></div>')


def mini(label, value):
    return f'<div class="ms"><div class="ms-l">{esc(label)}</div><div class="ms-v">{esc(value)}</div></div>'


def school_card(s, fmax, unit, short):
    pct = max(3, min(100, s["metric"] / fmax * 100)) if fmax else 0
    active = f"活跃 {s['active_days']} 天" if short else f"活跃 {s['weeks']:.0f} 周"
    return f"""<div class="ecard"><div class="ecard-h"><div class="ecard-name">{esc(s['short'])}</div>
        <div class="ecard-idx">{s['metric']}<span>{esc(unit.strip())}</span></div></div>
      <div class="ecard-track"><div class="ecard-fill" style="width:{pct:.0f}%"></div></div>
      <div class="ms-grid">{mini('班级', s['classes'])}{mini('学生', f"{s['students']:,}")}
        {mini('完成率', fp(s['completion']))}{mini('得分率', fp(s['score']))}</div>
      <div class="ecard-foot">{icon('calendar','#8c8c8c',13)} 启动 {s['first'].strftime('%m-%d')} · {active} · 布置 {s['assigns']} 次</div></div>"""


def school_rows_section(schools, fmax, munit, mlabel, short, caliber="", head_extra=""):
    """各校应用画像：紧凑行式列表，每校一行、每 18 所一页，大区（40+ 校）约 3 页。
    行内自带指标条形，兼具排名功能（原独立排名栏目已并入）；head_extra 放最好/待提升卡。"""
    CHUNK = 18

    def row(i, s):
        pct = max(3, min(100, s["metric"] / fmax * 100)) if fmax else 0
        active = f"活跃 {s['active_days']} 天" if short else f"活跃 {s['weeks']:.0f} 周"
        sub = f"{s['classes']} 班 · {s['students']:,} 人 · 启动 {s['first'].strftime('%m-%d')} · {active}"
        return (f'<div class="srow"><div class="sr-i">{i}</div>'
                f'<div><div class="sr-name">{esc(s["short"])}</div><div class="sr-sub">{esc(sub)}</div></div>'
                f'<div class="btrack sm"><div class="bfill" style="width:{pct:.0f}%;background:#1473e6"></div></div>'
                f'<div class="sr-v">{s["metric"]}<span>{esc(munit.strip())}</span></div>'
                f'<div class="sr-c">{fp(s["completion"])}</div><div class="sr-c">{fp(s["score"])}</div>'
                f'<div class="sr-c">{s["assigns"]:,}</div></div>')

    header = ('<div class="srow h"><div class="sr-i">#</div><div>学校</div>'
              f'<div>{esc(mlabel)}</div><div></div>'
              '<div class="sr-c">完成率</div><div class="sr-c">得分率</div><div class="sr-c">布置次数</div></div>')
    chunks = [schools[i:i + CHUNK] for i in range(0, len(schools), CHUNK)]
    out = []
    for ci, ch in enumerate(chunks):
        desc = (f'{caliber}共 {len(schools)} 所学校按{mlabel}降序排列，'
                f'行内依次为{mlabel}、完成率、得分率与累计布置次数。') if ci == 0 else ''
        title = sec_title('school', '各校应用画像' + ('' if ci == 0 else '（续）'), desc)
        extra = head_extra if ci == 0 else ''
        rows = header + ''.join(row(ci * CHUNK + j + 1, s) for j, s in enumerate(ch))
        out.append(f'<section class="block page">{title}{extra}<div class="slist">{rows}</div></section>')
    return ''.join(out)


def col_chart(trend):
    if not trend:
        return ""
    vmax = max(v for _, v in trend) or 1
    cols = "".join(f"""<div class="col"><div class="col-v">{v}</div>
        <div class="col-bar" style="height:{max(4, v/vmax*100):.0f}%"></div>
        <div class="col-l">{esc(lbl)}</div></div>""" for lbl, v in trend)
    return f'<div class="colchart">{cols}</div>'


def pct_card(cat, n, pct):
    return (f'<div class="pcard"><div class="pcard-h"><span>{esc(cat)}</span><b>{pct}%</b></div>'
            f'<div class="btrack"><div class="bfill" style="width:{max(3,min(100,pct)):.0f}%;background:#1473e6"></div></div>'
            f'<div class="pcard-s">{n:,} 次作业</div></div>')


def table(headers, rows, aligns=None):
    aligns = aligns or ["left"] * len(headers)
    th = "".join(f'<th style="text-align:{a}">{esc(h)}</th>' for h, a in zip(headers, aligns))
    tr = "".join("<tr>" + "".join(f'<td style="text-align:{a}">{esc(c)}</td>' for c, a in zip(r, aligns)) + "</tr>"
                 for r in rows)
    return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def suggestion(ic, title, body):
    return (f'<div class="scard"><div class="scard-t">{icon(ic,"#1473e6",16)} {esc(title)}</div>'
            f'<div class="scard-b">{esc(body)}</div></div>')


def paired_qt(qt_cmp):
    out = []
    for c in qt_cmp:
        prac, ex = c["prac"] or 0, c["exam"] or 0
        out.append(f"""<div class="qtrow"><div class="qt-name">{esc(c['q'])}</div><div class="qt-bars">
          <div class="qt-line"><span class="qt-tag">练习</span><span class="btrack sm"><span class="bfill" style="width:{prac:.0f}%;background:#1473e6"></span></span><span class="qt-v">{prac:.0f}%</span></div>
          <div class="qt-line"><span class="qt-tag">联考</span><span class="btrack sm"><span class="bfill" style="width:{ex:.0f}%;background:#0d66d0;opacity:.55"></span></span><span class="qt-v">{ex:.0f}%</span></div>
        </div></div>""")
    return "".join(out)


def qt_section(qt):
    rows = qt["rows"]
    bars = "".join(bar_row(q, rate, 100, "%") for q, rate, _o, _l, _n in rows)
    tbl = table(["题型", "得分率", "优秀率", "低分率", "样本数"],
                [(q, f"{rate}%", f"{o}%", f"{l}%", f"{n:,}") for q, rate, o, l, n in rows],
                ["left", "right", "right", "right", "right"])
    weak = min(rows, key=lambda r: r[1])
    return f"""<section class="block page">{sec_title('layers','听说模拟题型表现',f"基于听说模拟题型数据（{qt['records']:,} 条记录、{qt['types']} 类题型），观察各题型得分率与两极分化。")}
  <div class="grid2"><div class="card"><div class="card-h">各题型得分率</div><div class="barlist">{bars}</div></div>
    <div class="card tbl-card"><div class="card-h">题型明细（含优秀率 / 低分率）</div>{tbl}</div></div>
  <div class="note">{icon('alert','#e34850',14)} 相对薄弱题型为「{esc(weak[0])}」（得分率 {weak[1]}%、低分率 {weak[3]}%），建议作为专项训练优先对象。</div></section>"""


def mock_section(mk):
    """阶段成效与典型样本（听说模拟）：区域月度得分率、各年级成效、典型学校年级/班级。"""
    ratio_stat = stat("trend", "月度提分幅度",
                      f"{mk['improve']} 个百分点" if mk["improve"] is not None else "—",
                      "月度平均得分率峰谷差")
    kpis = "".join([
        stat("doc", "听说模拟布置", f"{mk['n']:,} 次", f"覆盖 {mk['schools']} 所学校 · {mk['classes']} 个班级"),
        stat("score", "模拟平均得分率", fp(mk["score"]), "题型口径与联考一致"),
        ratio_stat,
    ])
    cols_html = ""
    if len(mk["trend"]) >= 2:
        vmax = max(v for _, v in mk["trend"])
        base = max(0.0, min(v for _, v in mk["trend"]) - 8)
        cols = "".join(
            f'<div class="col"><div class="col-v">{v}%</div>'
            f'<div class="col-bar" style="height:{max(6, (v - base) / max(vmax - base, 1) * 100):.0f}%"></div>'
            f'<div class="col-l">{esc(l)}</div></div>' for l, v in mk["trend"])
        cols_html = (f'<div class="card" style="margin-top:12px"><div class="card-h">听说模拟月度平均得分率</div>'
                     f'<div class="colchart">{cols}</div></div>')
    gr_tbl = ""
    if len(mk["grades"]) > 1:
        gr_tbl = ('<div class="card tbl-card"><div class="card-h">各年级听说模拟成效</div>'
                  + table(["年级", "模拟次数", "平均得分率", "提分幅度"],
                          [(g["grade"], f"{g['n']:,}", fp(g["score"]), f"{g['improve']} 个百分点")
                           for g in mk["grades"]],
                          ["left", "right", "right", "right"]) + "</div>")
    case_tbl = ""
    if mk["cases"]:
        case_tbl = ('<div class="card tbl-card"><div class="card-h">典型学校年级样本（按模拟次数）</div>'
                    + table(["学校", "年级", "模拟次数", "平均得分率", "提分幅度"],
                            [(c["school"], c["grade"], f"{c['n']:,}", fp(c["score"]), f"{c['improve']} 个百分点")
                             for c in mk["cases"]],
                            ["left", "left", "right", "right", "right"]) + "</div>")
    body = (f'<div class="grid2">{gr_tbl}{case_tbl}</div>' if gr_tbl and case_tbl
            else (f'<div style="margin-top:12px">{gr_tbl or case_tbl}</div>' if (gr_tbl or case_tbl) else ""))
    tc = mk.get("top_class")
    tc_note = ""
    if tc:
        word = "呈稳步提升态势" if tc["last"] > tc["first"] else "整体保持稳定"
        tc_note = (f'<div class="note">{icon("star", "#2d9d78", 14)} 典型班级：{esc(tc["school"])}{esc(tc["cls"])} —— '
                   f'累计听说模拟 {tc["n"]} 次，月度平均得分率由 {tc["first"]}% 至 {tc["last"]}%'
                   f'（峰值 {tc["peak"]}%），{word}。</div>')
    return f"""<section class="block page">{sec_title('target', '阶段成效与典型样本（听说模拟）',
        '以听说模拟作业（题型口径与联考一致）观察区域阶段成效：月度得分率变化、各年级表现与典型学校年级、班级样本。')}
  <div class="stat-grid">{kpis}</div>
  {cols_html}
  {body}
  {tc_note}</section>"""


def exam_section(ex, quals):
    ov, fm = ex["overall"], ex["full_mark"]
    avg = ov.get("平均分")
    only_e = set(ex["only_exam"])
    link = ex["link"]
    kpis = "".join([
        stat("target", "联考满分", f"{fm:.0f}", esc(ex["label"])),
        stat("school", "参考学校", ex["school_count"], "区域统一联考"),
        stat("users", "实考人数", f"{ov.get('实考人数', 0):,}", f"报名 {ov.get('学生人数', 0):,}"),
        stat("trend", "全区平均分", avg if avg is not None else "—", f"得分率 {ex['score_rate']}%" if ex['score_rate'] else ""),
    ])
    rows = sorted([(n, v.get("平均分")) for n, v in ex["schools"].items() if v.get("平均分") is not None],
                  key=lambda x: x[1], reverse=True)
    bars = []
    for n, v in rows:
        if n in only_e:
            color, tag = "#cacaca", "（无平台练习）"
        elif avg is not None and v >= avg:
            color, tag = "#2d9d78", ""
        else:
            color, tag = "#e34850", ""
        bars.append(bar_row(_short(n, quals) + tag, v, fm, "", color))
    bench = "".join(f"""<div class="bench"><div class="bench-tag">{icon('star','#2d9d78',14)} 正向标杆 {i+1}</div>
        <div class="bench-name">{esc(b['short'])}</div>
        <div class="bench-sub">练习得分率 {b['prac']:.0f}% · 联考 {b['avg']} 分</div></div>""" for i, b in enumerate(link[:3]))
    only_txt = "、".join(_short(s, quals) for s in ex["only_exam"]) or "无"
    low = sorted([r for r in link if avg is not None and r["avg"] < avg], key=lambda r: r["week_freq"])[:3]
    low_txt = "、".join(f"{r['short']}（周频次{r['week_freq']}）" for r in low) or "无"
    wq = min([c for c in ex["qt_cmp"] if c["exam"] is not None], key=lambda c: c["exam"], default=None)
    weak_name = wq["q"] if wq else ""
    return f"""<section class="block page">{sec_title('target','阶段性联考成绩对比',f"将日常听说训练（过程）与区域统一联考（{esc(ex['label'])}）对照，观察训练成效在联考中的体现。")}
  <div class="stat-grid g4">{kpis}</div>
  <div class="card" style="margin-top:14px"><div class="card-h">各校联考平均分（绿＝高于全区均线 {avg}，红＝低于，灰＝无平台练习）</div><div class="barlist">{''.join(bars)}</div></div>
  <div class="grid2"><div class="card hl"><div class="rcallout"><div class="rbig">r = {ex['r_score']}</div>
        <div class="rlabel">练习得分率 × 联考平均分<br>呈显著正相关</div></div><div class="bench-list">{bench}</div></div>
    <div class="card"><div class="card-h">各题型「练—考」得分率对照</div><div class="qtlist">{paired_qt(ex['qt_cmp'])}</div></div></div>
  <div class="grid2">{suggestion('alert','无平台练习的参考校',f"{only_txt} 参加联考但平台无日常练习数据，联考多居全区偏后，建议优先纳入常态化听说训练。")}
    {suggestion('speed','低频校与共性弱项',f"联考低于均线且布置频次偏低：{low_txt}；频次相关性（r={ex['r_freq']}）弱于练习质量，重在练扎实；共性弱项「{weak_name}」宜专项突破。")}</div></section>"""


# ════════════════════════════════════════════════════════════════════════
# 单校版：取数 + 组件
# ════════════════════════════════════════════════════════════════════════
def _cls_disp(grade, name):
    """班级显示名：年级+班级名称+班（班级名称已含年级首字则不重复）。"""
    cn, g = str(name), str(grade)
    return f"{cn}班" if cn.startswith(g[:1]) and len(cn) > 1 else f"{g}{cn}班"


def analyze_graphic_school(class_df, hw_df, qt_df=None):
    """单校图文版取数：统计单元=班级。周期不足 3 个月（首次→最后一次布置）趋势按自然周。"""
    hw = hw_df.copy()
    for c in ("作业得分率", "100%完成学生占比", "作答学生占比", "作答学生总数", "单次作业平均耗时/min"):
        if c in hw.columns:
            hw[c] = pd.to_numeric(hw[c], errors="coerce")
    hw["d"] = pd.to_datetime(hw["作业开始日期"], errors="coerce")
    hw["大类"] = hw["作业路径"].astype(str).str.split("-").str[0]
    hw["小类"] = hw["作业路径"].astype(str).str.split("-").str[1].fillna("其他")

    school_name = str(hw["学校名称"].dropna().iloc[0]) if "学校名称" in hw.columns and hw["学校名称"].notna().any() else "本校"
    gstart, gend = hw["d"].min(), hw["d"].max()
    span_days = int((gend - gstart).days) + 1
    weeks = max(1.0, (gend - gstart).days / 7)
    weekly = span_days < 90  # 周期不足 3 个月 → 自然周维度
    hw["_p"] = ((hw["d"] - pd.to_timedelta(hw["d"].dt.weekday, unit="D")).dt.strftime("%m/%d")
                if weekly else hw["d"].dt.to_period("M").astype(str).str[2:].str.replace("-", "/"))

    # 名册（班级数据总览）：学生数 / 自主练习 / 词汇练习 / 教师
    roster = {}
    if class_df is not None and "班级id" in class_df.columns:
        for _, r in class_df.iterrows():
            roster[r["班级id"]] = {
                "students": int(pd.to_numeric(pd.Series([r.get("总学生数")]), errors="coerce").fillna(0).iloc[0]),
                "self_prac": int(pd.to_numeric(pd.Series([r.get("自主练习次数")]), errors="coerce").fillna(0).iloc[0]),
                "vocab": int(pd.to_numeric(pd.Series([r.get("词汇自主练习次数")]), errors="coerce").fillna(0).iloc[0]),
            }
    short = weeks < 5

    classes = []
    for cid, grp in hw.groupby("班级id"):
        assigns = int(grp["作业ID"].nunique())
        first = grp["d"].min()
        cw = max(1.0, (gend - first).days / 7)
        info = roster.get(cid, {})
        hw_students = int(grp["作答学生总数"].max() or 0)
        classes.append({
            "id": cid, "label": _cls_disp(grp["年级"].iloc[0], grp["班级名称"].iloc[0]),
            "teacher": str(grp["教师姓名"].dropna().iloc[0]) if grp["教师姓名"].notna().any() else "—",
            "students": int(info.get("students") or hw_students),
            "assigns": assigns, "week_freq": round(assigns / cw, 2),
            "metric": assigns if short else round(assigns / cw, 2),
            "completion": round(float(cm * 100), 1) if pd.notna(cm := grp["100%完成学生占比"].mean()) else None,
            "score": round(float(sm * 100), 1) if pd.notna(sm := grp["作业得分率"].mean()) else None,
            "self_prac": int(info.get("self_prac") or 0), "vocab": int(info.get("vocab") or 0),
            "first": first, "active_days": int((gend - first).days) + 1, "weeks": round(cw, 1),
        })
    classes.sort(key=lambda c: c["metric"], reverse=True)

    total_assigns = int(hw["作业ID"].nunique())
    n_classes = len(classes)
    school = {
        "name": school_name, "classes": n_classes,
        "roster_classes": int(class_df["班级id"].nunique()) if class_df is not None and "班级id" in class_df.columns else n_classes,
        "students": sum(c["students"] for c in classes),
        "assigns": total_assigns,
        "per_class": round(total_assigns / n_classes, 1) if n_classes else 0,
        "completion": round(float(hw["100%完成学生占比"].mean() * 100), 1),
        "score": round(float(hw["作业得分率"].mean() * 100), 1),
        "minutes": (round(float(m_), 1) if pd.notna(m_ := hw["单次作业平均耗时/min"].mean()) else 0),
        "self_prac": sum(c["self_prac"] for c in classes), "vocab": sum(c["vocab"] for c in classes),
        "gstart": gstart, "gend": gend, "weeks": round(weeks, 1), "span_days": span_days,
        "weekly": weekly, "short": short,
        "metric_label": "布置次数" if short else "周布置频次",
        "metric_unit": " 次" if short else " 次/周",
    }

    ser = hw.groupby("_p")["作业ID"].nunique().sort_index()
    trend = [(k, int(v)) for k, v in ser.items() if k]
    trend_title = "周度作业量趋势" if weekly else "月度作业量趋势"
    trend_desc = ("统计周期不足 3 个月，按自然周（周一起始）统计去重作业数，观察短周期布置节奏。"
                  if weekly else "按作业开始月份统计去重作业数，观察推进节奏。")

    cat = hw.groupby("大类")["作业ID"].nunique().sort_values(ascending=False)
    ctotal = int(cat.sum()) or 1
    categories = [(str(k), int(v), round(v / ctotal * 100, 1)) for k, v in cat.items()]
    sub = hw.groupby(["大类", "小类"]).agg(
        n=("作业ID", "nunique"), score=("作业得分率", "mean"), mins=("单次作业平均耗时/min", "mean")
    ).reset_index().sort_values("n", ascending=False).head(8)
    subitems = [(r["大类"], r["小类"], int(r["n"]),
                 round(r["score"] * 100, 1) if pd.notna(r["score"]) else "—",
                 round(r["mins"], 1) if pd.notna(r["mins"]) else "—")
                for _, r in sub.iterrows()]

    S = {"school": school, "classes": classes, "trend": trend,
         "trend_title": trend_title, "trend_desc": trend_desc,
         "categories": categories, "subitems": subitems}

    # ── 听说模拟作业横向对比：同一套题（作业名称）≥2 个班有有效得分才可比 ──
    mock = hw[hw["大类"] == "模拟"].copy()
    mock_ok = mock[mock["作业得分率"] > 0]  # 0 分记录多为刚布置未作答，剔除
    papers = []
    for name, g in mock_ok.groupby("作业名称"):
        rows = [( _cls_disp(r["年级"], r["班级名称"]), round(float(r["作业得分率"]) * 100, 1))
                for _, r in g.groupby("班级id").agg(
                    年级=("年级", "first"), 班级名称=("班级名称", "first"),
                    作业得分率=("作业得分率", "mean")).reset_index().iterrows()]
        if len(rows) >= 2:
            rows.sort(key=lambda r: -r[1])
            papers.append({"name": str(name).strip(), "rows": rows,
                           "date": g["d"].max(), "spread": round(rows[0][1] - rows[-1][1], 1)})
    papers.sort(key=lambda p: (-len(p["rows"]), -p["date"].toordinal()))
    S["papers"] = papers[:6]

    # ── 同套题正向归因洞察：领先班级好在哪（频次/结构/题型），其他班的提升杠杆是什么 ──
    # 面向客户的措辞原则：只做"领先做法归因 + 建议方向"，不做负面评判。
    if papers:
        # 各班：模拟得分率 / 布置次数 / 大类结构
        attr = {}
        for cid, g in hw.groupby("班级id"):
            lbl = _cls_disp(g["年级"].iloc[0], g["班级名称"].iloc[0])
            okg = g[(g["大类"] == "模拟") & (g["作业得分率"] > 0)]
            cats = g.groupby("大类")["作业ID"].nunique().sort_values(ascending=False)
            attr[lbl] = {
                "mock": round(float(okg["作业得分率"].mean()) * 100, 1) if len(okg) else None,
                "assigns": int(g["作业ID"].nunique()),
                "cats": {str(k): int(v) for k, v in cats.items()},
            }
        scored = {k: v for k, v in attr.items() if v["mock"] is not None}
        if len(scored) >= 2:
            avg_assigns = sum(v["assigns"] for v in attr.values()) / max(len(attr), 1)
            school_mock = sum(v["mock"] for v in scored.values()) / len(scored)
            bench_lbl = max(scored, key=lambda k: scored[k]["mock"])
            bench = scored[bench_lbl]

            # 题型维度（可选）：各班 vs 全校均值，以及前/后半段趋势（用于"专项建议"）
            qt_adv, weak_map = [], {}
            if qt_df is not None and not qt_df.empty and {"题型名称", "班级", "得分率"}.issubset(qt_df.columns):
                q = qt_df.copy()
                q["_cls"] = q.apply(lambda r: _cls_disp(r.get("年级", ""), r.get("班级", "")), axis=1)
                q["得分率"] = pd.to_numeric(q["得分率"], errors="coerce")
                t_avg = q.groupby("题型名称")["得分率"].mean() * 100
                if "作业" in q.columns:
                    dmap = hw.drop_duplicates("作业名称").set_index("作业名称")["d"]
                    q["_d"] = pd.to_datetime(q["作业"].map(dmap), errors="coerce")
                mid = q["_d"].dropna().median() if "_d" in q.columns and q["_d"].notna().any() else None
                for lbl in scored:
                    sub = q[q["_cls"] == lbl]
                    if sub.empty:
                        continue
                    gaps = (sub.groupby("题型名称")["得分率"].mean() * 100 - t_avg).dropna()
                    if lbl == bench_lbl:
                        qt_adv = [(t, round(v, 1)) for t, v in
                                  gaps.sort_values(ascending=False).head(2).items() if v >= 3]
                    elif mid is not None:
                        weak = []
                        for t, gap in gaps.sort_values().items():
                            if gap >= -3:
                                break
                            gg = sub[sub["题型名称"] == t]
                            a = gg[gg["_d"] <= mid]["得分率"].mean()
                            b = gg[gg["_d"] > mid]["得分率"].mean()
                            if pd.notna(a) and pd.notna(b) and b <= a + 0.01:  # 尚未看到提升
                                weak.append(t)
                            if len(weak) >= 2:
                                break
                        if weak:
                            weak_map[lbl] = weak
            ALL_CATS = ("同步", "模拟", "专项")
            # 其他班级的建议方向（只给杠杆，不作评判）
            levers = []
            for lbl, v in scored.items():
                if lbl == bench_lbl or v["mock"] >= school_mock:
                    continue
                sug = []
                if v["assigns"] < avg_assigns * 0.85:
                    sug.append(f"提高训练频次（当前 {v['assigns']} 次，班均 {avg_assigns:.0f} 次）")
                missing = [c for c in ALL_CATS if c not in v["cats"]]
                if missing:
                    sug.append(f"补充「{'、'.join(missing)}」类作业，结构更均衡")
                for t in weak_map.get(lbl, []):
                    sug.append(f"「{t}」专项练习")
                if sug:
                    levers.append({"label": lbl, "mock": v["mock"],
                                   "assigns": v["assigns"], "ncats": len(v["cats"]), "sug": sug})
            levers.sort(key=lambda r: r["mock"])

            # 全校规律：结构均衡（三类）且频次较高的班级是否整体领先
            full3 = sorted(((k, v) for k, v in scored.items()
                            if len(v["cats"]) >= 3 and k != bench_lbl),
                           key=lambda kv: -kv[1]["mock"])[:2]
            S["paper_insight"] = {
                "bench": {"label": bench_lbl, "mock": bench["mock"], "assigns": bench["assigns"],
                          "avg_assigns": round(avg_assigns, 1),
                          "cats": [c for c in ALL_CATS if c in bench["cats"]] +
                                  [c for c in bench["cats"] if c not in ALL_CATS],
                          "qt_adv": qt_adv},
                "pattern": [{"label": k, "assigns": v["assigns"], "ncats": len(v["cats"]),
                             "mock": v["mock"]} for k, v in full3],
                "levers": levers,
            }

    # ── 阶段成效（班级维度）：模拟得分首末周期对比，星级班级出组合图 ──
    stages = []
    for cid, g in mock.groupby("班级id"):
        ok = g[g["作业得分率"] > 0]
        ser = ok.groupby("_p")["作业得分率"].mean().sort_index()
        if len(ser) < 2:
            continue
        info = next((c for c in classes if c["id"] == cid), None)
        stages.append({
            "id": cid, "label": _cls_disp(g["年级"].iloc[0], g["班级名称"].iloc[0]),
            "n": int(g["作业ID"].nunique()),
            "first": round(float(ser.iloc[0]) * 100, 1), "last": round(float(ser.iloc[-1]) * 100, 1),
            "peak": round(float(ser.max()) * 100, 1),
            "growth": round(float(ser.iloc[-1] - ser.iloc[0]) * 100, 1),
            "self_prac": info["self_prac"] if info else 0,
            "assigns": info["assigns"] if info else 0,
        })
    stages.sort(key=lambda s: -s["growth"])
    growers = [s for s in stages if s["growth"] > 0]
    star = growers[0] if growers else None
    combo = None
    if star:
        # 柱＝该班全部作业布置次数（按周期），折线＝听说模拟平均得分率
        all_g = hw[hw["班级id"] == star["id"]]
        ok = mock[(mock["班级id"] == star["id"]) & (mock["作业得分率"] > 0)]
        n_ser = all_g.groupby("_p")["作业ID"].nunique().sort_index()
        s_ser = ok.groupby("_p")["作业得分率"].mean()
        combo = [(p, int(n), round(float(s_ser[p]) * 100, 1) if p in s_ser.index else None)
                 for p, n in n_ser.items()]
    S["stage"] = {"star": star, "combo": combo, "growers": growers[1:6],
                  "period_word": "周" if weekly else "月"} if star else None

    # ── 题型（口径与区级一致）──
    if qt_df is not None and not qt_df.empty and "题型名称" in qt_df.columns:
        m = qt_df.groupby("题型名称")["得分率"].agg(["mean", "size"])
        opt = qt_df.groupby("题型名称")["优秀率"].mean()
        low = qt_df.groupby("题型名称")["低分率"].mean()
        rows = [(k, round(v["mean"] * 100, 1), round(opt[k] * 100, 1), round(low[k] * 100, 1), int(v["size"]))
                for k, v in m.iterrows()]
        rows.sort(key=lambda r: r[1], reverse=True)
        S["qt"] = {"rows": rows, "records": int(len(qt_df)), "types": int(qt_df["题型名称"].nunique())}

    teachers = []
    if "教师姓名" in hw.columns:
        tch = hw.groupby("教师姓名").agg(
            classes=("班级id", "nunique"), assigns=("作业ID", "nunique"),
            completion=("100%完成学生占比", "mean"), score=("作业得分率", "mean"),
        ).reset_index().sort_values("assigns", ascending=False).head(8)
        for _, r in tch.iterrows():
            teachers.append({
                "name": r["教师姓名"], "classes": int(r["classes"]), "assigns": int(r["assigns"]),
                "completion": round(r["completion"] * 100, 1) if pd.notna(r["completion"]) else None,
                "score": round(r["score"] * 100, 1) if pd.notna(r["score"]) else None,
            })
    S["teachers"] = teachers
    return S


def combo_svg(points, w=660, h=210):
    """组合图：柱=每周期听说模拟布置次数，折线=模拟平均得分率（%）。纯内联 SVG。"""
    if not points:
        return ""
    pl, pr, pt, pb = 30, 30, 18, 30
    iw, ih = w - pl - pr, h - pt - pb
    n = len(points)
    slot = iw / n
    nmax = max(p[1] for p in points) or 1
    scores = [p[2] for p in points if p[2] is not None]
    smin, smax = (min(scores), max(scores)) if scores else (0, 100)
    slo, shi = max(0, smin - 8), min(100, smax + 8)

    def sy(v):
        return pt + ih - (v - slo) / max(shi - slo, 1) * ih

    bars, labels, pts, dots = [], [], [], []
    for i, (lbl, cnt, sc) in enumerate(points):
        cx = pl + slot * i + slot / 2
        bw = min(34, slot * 0.42)
        bh = max(3, cnt / nmax * (ih * 0.9))
        bars.append(f'<rect x="{cx - bw / 2:.1f}" y="{pt + ih - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="#1473e6" opacity=".8"/>')
        bars.append(f'<text x="{cx:.1f}" y="{pt + ih - bh - 4:.1f}" text-anchor="middle" font-size="10" fill="#4b4b4b">{cnt}</text>')
        labels.append(f'<text x="{cx:.1f}" y="{h - 10:.1f}" text-anchor="middle" font-size="10" fill="#8c8c8c">{esc(lbl)}</text>')
        if sc is not None:
            pts.append(f"{cx:.1f},{sy(sc):.1f}")
            dots.append(f'<circle cx="{cx:.1f}" cy="{sy(sc):.1f}" r="3.2" fill="#2d9d78"/>'
                        f'<text x="{cx:.1f}" y="{sy(sc) - 7:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#2d9d78">{sc}%</text>')
    line = f'<polyline points="{" ".join(pts)}" fill="none" stroke="#2d9d78" stroke-width="2"/>' if len(pts) >= 2 else ""
    legend = (f'<rect x="{pl}" y="2" width="10" height="10" rx="2" fill="#1473e6" opacity=".8"/>'
              f'<text x="{pl + 14}" y="11" font-size="10" fill="#4b4b4b">作业布置次数</text>'
              f'<circle cx="{pl + 104}" cy="7" r="4" fill="#2d9d78"/>'
              f'<text x="{pl + 112}" y="11" font-size="10" fill="#4b4b4b">模拟平均得分率</text>')
    svg = (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
           f'font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,sans-serif" '
           f'xmlns="http://www.w3.org/2000/svg">'
           f'{legend}{"".join(bars)}{line}{"".join(dots)}{"".join(labels)}</svg>')
    # 以 base64 <img> 内嵌：html2pdf(html2canvas) 对带 viewBox 的内联 SVG 缩放失真，
    # 图片形式则按位图正确光栅化；Chrome 打印路径同样兼容。
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<img src="data:image/svg+xml;base64,{b64}" alt="组合图" '
            f'style="width:100%;height:auto;display:block" width="{w}" height="{h}"/>')


def class_rows_section(classes, fmax, munit, mlabel, short):
    """各班应用画像：紧凑行式列表（含自主练习列），每 18 班一页。"""
    CHUNK = 18

    def row(i, c):
        pct = max(3, min(100, c["metric"] / fmax * 100)) if fmax else 0
        active = f"活跃 {c['active_days']} 天" if short else f"活跃 {c['weeks']:.0f} 周"
        sub = f"{c['students']} 人 · {c['teacher']} · 启动 {c['first'].strftime('%m-%d')} · {active}"
        return (f'<div class="srow c8"><div class="sr-i">{i}</div>'
                f'<div><div class="sr-name">{esc(c["label"])}</div><div class="sr-sub">{esc(sub)}</div></div>'
                f'<div class="btrack sm"><div class="bfill" style="width:{pct:.0f}%;background:#1473e6"></div></div>'
                f'<div class="sr-v">{c["metric"]}<span>{esc(munit.strip())}</span></div>'
                f'<div class="sr-c">{fp(c["completion"])}</div><div class="sr-c">{fp(c["score"])}</div>'
                f'<div class="sr-c">{c["self_prac"]:,}</div><div class="sr-c">{c["assigns"]:,}</div></div>')

    header = ('<div class="srow c8 h"><div class="sr-i">#</div><div>班级</div>'
              f'<div>{esc(mlabel)}</div><div></div>'
              '<div class="sr-c">完成率</div><div class="sr-c">得分率</div>'
              '<div class="sr-c">自主练习</div><div class="sr-c">布置次数</div></div>')
    chunks = [classes[i:i + CHUNK] for i in range(0, len(classes), CHUNK)]
    out = []
    for ci, ch in enumerate(chunks):
        desc = (f'共 {len(classes)} 个班级按{mlabel}降序排列；自主练习次数来自班级数据总览，'
                '反映学生课后自驱训练量。') if ci == 0 else ''
        title = sec_title('class', '各班应用画像' + ('' if ci == 0 else '（续）'), desc)
        rows = header + ''.join(row(ci * CHUNK + j + 1, c) for j, c in enumerate(ch))
        out.append(f'<section class="block page">{title}<div class="slist">{rows}</div></section>')
    return ''.join(out)


def paper_compare_section(papers, insight=None):
    """听说模拟作业横向对比：同一套题下各班得分率对比 + 标准化洞察结论。"""
    cards = []
    for p in papers:
        vmax = max(v for _, v in p["rows"]) or 1
        bars = "".join(
            bar_row(lbl, v, 100, "%", "#2d9d78" if v == vmax else "#1473e6")
            for lbl, v in p["rows"])
        cards.append(f'<div class="card"><div class="card-h">{esc(p["name"])}'
                     f'<span class="ph-sub">{len(p["rows"])} 个班可比 · 班间差 {p["spread"]} 个百分点</span></div>'
                     f'<div class="barlist">{bars}</div></div>')
    html_cards = f'<div class="grid2">{"".join(cards)}</div>'
    if not insight:
        return html_cards

    items = []
    b = insight["bench"]
    adv = ("，「" + "」「".join(t for t, _ in b["qt_adv"]) + "」等题型高出全校均值 "
           + "、".join(f"{v}" for _, v in b["qt_adv"]) + " 个百分点"
           if b.get("qt_adv") else "")
    items.append(("领先做法", f"{b['label']} 听说模拟平均得分率 {b['mock']}% 领先，其做法可供借鉴："
                  f"累计布置 {b['assigns']} 次（班均 {b['avg_assigns']} 次）、"
                  f"作业结构覆盖{'、'.join(b['cats'])} {len(b['cats'])} 类{adv}。"))
    if insight.get("pattern"):
        pat = "、".join(f"{p['label']}（{p['assigns']} 次 / {p['ncats']} 类 → {p['mock']}%）"
                        for p in insight["pattern"])
        items.append(("频次与结构", f"从全校规律看，布置频次较高、同步/模拟/专项结构均衡的班级模拟得分率整体更高"
                      f"（{pat}）；训练频次与作业结构是每个班都能直接使用的两个提升杠杆。"))
    cc = "".join(conclusion(i + 1, t, bd) for i, (t, bd) in enumerate(items))

    lever_html = ""
    if insight.get("levers"):
        rows = [(r["label"], f"{r['mock']}%", f"{r['assigns']} 次 / {r['ncats']} 类",
                 "；".join(r["sug"])) for r in insight["levers"]]
        lever_html = ('<div class="card tbl-card" style="margin-top:12px">'
                      '<div class="card-h">各班建议方向（对照领先班做法，供教学安排参考）</div>'
                      + table(["班级", "模拟得分率", "当前频次 / 结构", "建议方向"], rows,
                              ["left", "right", "left", "left"]) + "</div>")
    return f'{html_cards}<div class="cc-list" style="margin-top:12px">{cc}</div>{lever_html}'


def stage_section_school(st, school):
    """阶段成效与典型班级：星级班级组合图 + 其余增长班级方块（含自主练习参考）。"""
    star = st["star"]
    pw = st["period_word"]
    star_card = (
        f'<div class="card hl" style="margin-top:12px"><div class="card-h">'
        f'{icon("star", "#2d9d78", 15)} 进步最大班级：{esc(star["label"])}　'
        f'首{pw} {star["first"]}% → 末{pw} {star["last"]}%（+{star["growth"]} 个百分点）'
        f'<span class="ph-sub">累计模拟 {star["n"]} 次 · 自主练习 {star["self_prac"]} 次</span></div>'
        f'{combo_svg(st["combo"])}</div>')
    blocks = "".join(
        f'<div class="gblock"><div class="gb-name">{esc(g["label"])}</div>'
        f'<div class="gb-v">+{g["growth"]}<span> 个百分点</span></div>'
        f'<div class="gb-sub">{g["first"]}% → {g["last"]}%（峰值 {g["peak"]}%）</div>'
        f'<div class="gb-sub">模拟 {g["n"]} 次 · 自主练习 {g["self_prac"]:,} 次</div></div>'
        for g in st["growers"])
    blocks_html = (f'<div class="gblock-grid">{blocks}</div>' if blocks else "")
    return f"""<section class="block page">{sec_title('trend', '阶段成效与典型班级',
        f'以班级为单元、按自然{pw}对比听说模拟得分率首末变化（剔除刚布置未作答的 0 分记录）；'
        '进步最大的班级以组合图呈现布置节奏与得分率走势，其余增长班级以方块呈现，并附自主练习次数作参考。')}
  {star_card}
  {blocks_html}</section>"""


# ════════════════════════════════════════════════════════════════════════
# 组装 HTML
# ════════════════════════════════════════════════════════════════════════
def build_graphic_html(D):
    r = D["region"]
    region_name = r["name"]
    schools = D["schools"]
    quals = r["quals"]
    short = r.get("short")
    mlabel, munit = r["metric_label"], r["metric_unit"]
    fmax = max((s["metric"] for s in schools), default=1)
    top = schools[0] if schools else None
    low = schools[-1] if schools else None
    first_s = r["gstart"].strftime("%Y年%m月%d日")
    last_s = r["gend"].strftime("%Y年%m月%d日")
    top_cat = D["categories"][0] if D["categories"] else ("—", 0, 0)
    exam = D.get("exam")

    kpi_list = [
        stat("school", "覆盖学校", r["schools"], "有布置记录的学校"),
        stat("class", "覆盖班级", f"{r['classes']:,}", "有布置记录的班级"),
        stat("users", "覆盖学生", f"{r['students']:,}", "学生数"),
        stat("doc", "作业布置", f"{r['assigns']:,}", "累计布置次数"),
        stat("check", "平均完成率", f"{r['completion']}%", "100% 完成占比"),
        stat("score", "平均得分率", f"{r['score']}%", "日常作业"),
    ]
    # 激活率：当名册（班级数据总览）含未布置学校/班级时呈现，反映覆盖与激活差距
    ts, tc = r.get("total_schools"), r.get("total_classes")
    extras = []
    school_act = round(r["schools"] / ts * 100, 1) if ts and ts > r["schools"] else None
    class_act = round(r["classes"] / tc * 100, 1) if tc and tc > r["classes"] else None
    if school_act is not None:
        extras.append(stat("school", "学校激活率", f"{school_act}%", f"{ts} 所中 {r['schools']} 所有布置"))
    if class_act is not None:
        extras.append(stat("class", "班级激活率", f"{class_act}%", f"{tc} 班中 {r['classes']} 班有布置"))
    if len(extras) == 1:  # 凑足 2 个以保持 4×2 整齐
        extras.append(stat("clock", "平均单次耗时", f"{r['minutes']} min", "作答平均时长"))
    kpi_list += extras
    kpi_cols = 4 if len(kpi_list) == 8 else 3
    kpis = "".join(kpi_list)

    ccs = [
        ("应用覆盖", f"统计周期 {first_s} 至 {last_s}（约 {r['weeks']:.0f} 周），共有 {r['schools']} 所学校、"
                     f"{r['classes']} 个班级、{r['students']:,} 名学生产生布置记录，累计布置作业 {r['assigns']:,} 次"
                     + (f"；区内 {ts} 所学校中 {r['schools']} 所已激活（{school_act}%），仍有提升空间。" if school_act is not None else "。")),
        ("应用节奏", f"全区{mlabel} {r['metric']}{munit}；{top['short']} 投入最高（{top['metric']}{munit}），"
                     "可沉淀其布置与督促经验。"),
        ("待提升", f"{low['short']} {mlabel}偏低（{low['metric']}{munit}），"
                   "建议核查账号启用、教师培训与作业布置机制。"),
        ("完成质量", f"全区作业完成率 {r['completion']}%、得分率 {r['score']}%；"
                     f"高频资源为「{top_cat[0]}」（{top_cat[1]:,} 次，占 {top_cat[2]}%）。"),
    ]
    mk = D.get("mock")
    if mk and mk.get("improve") is not None and mk.get("cases"):
        c0 = mk["cases"][0]
        ccs.append(("阶段成效", f"听说模拟累计布置 {mk['n']:,} 次、平均得分率 {mk['score']}%，"
                                f"月度均值峰谷差 {mk['improve']} 个百分点；{c0['school']}{c0['grade']}等样本"
                                "以高频模拟带动成绩提升，可作为阶段成效观察样本。"))
    if exam and exam.get("link"):
        b0 = exam["link"][0]
        ccs.append(("联考印证", f"练习得分率与联考平均分正相关（r = {exam['r_score']}）；{b0['short']} 等以练促考、"
                                "联考居前，日常训练成效在联考中得到验证。"))
    cc_html = "".join(conclusion(i + 1, t, b) for i, (t, b) in enumerate(ccs))

    hcards_html = f"""<div class="grid2" style="margin:0 0 12px">
    <div class="hcard good"><div class="hcard-tag">{icon('star','#2d9d78',15)} 应用投入最高</div>
      <div class="hcard-name">{esc(top['short'])}</div>
      <div class="hcard-sub">{top['metric']}{munit} · 完成率 {fp(top['completion'])} · 得分率 {fp(top['score'])}</div></div>
    <div class="hcard warn"><div class="hcard-tag">{icon('alert','#e34850',15)} 应用投入待提升</div>
      <div class="hcard-name">{esc(low['short'])}</div>
      <div class="hcard-sub">{low['metric']}{munit} · 完成率 {fp(low['completion'])} · 得分率 {fp(low['score'])}</div></div>
  </div>"""
    schools_html = school_rows_section(schools, fmax, munit, mlabel, short,
                                       caliber=r['metric_caliber'], head_extra=hcards_html)
    cat_html = "".join(pct_card(c, n, p) for c, n, p in D["categories"])
    sub_tbl = table(["资源大类", "试题类型", "布置次数", "得分率", "单次耗时/min"],
                    [(c, sc, f"{n:,}", f"{score}%", f"{mins}") for c, sc, n, score, mins in D["subitems"]],
                    ["left", "left", "right", "right", "right"])
    tch_tbl = table(["教师", "学校", "班级", "布置次数", "周频次", "完成率", "得分率"],
                    [(t["name"], t["school"], t["classes"], t["assigns"], f"{t['week_freq']}",
                      f"{t['completion']}%", f"{t['score']}%") for t in D["teachers"]],
                    ["left", "left", "right", "right", "right", "right", "right"])

    qt_html = qt_section(D["qt"]) if D.get("qt") else ""
    mock_html = mock_section(D["mock"]) if D.get("mock") else ""
    exam_html = exam_section(exam, quals) if exam else ""
    exam_sug = (suggestion("trend", "以练促考闭环",
                           "建立“练—测—评—改”闭环：用联考结果反推日常训练重点，对得分率偏低的题型做专项突破。")
                if exam else
                suggestion("speed", "关注作答质量",
                           f"全区完成率 {r['completion']}%、得分率 {r['score']}%，可针对得分率偏低的资源类型做专项讲评。"))
    srcs = ["班级数据总览", "作业明细"]
    if D.get("qt"):
        srcs.append("听说模拟题型")
    if exam:
        srcs.append(esc(exam["label"]) + " 联考报告")
    data_src = f"{region_name} " + "、".join(srcs)
    now = datetime.now().strftime("%Y年%m月%d日")

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{CSS}</style></head><body>

<header class="cover">
  <h1>{esc(region_name)} E听说应用成效报告</h1>
  <p class="cover-sub">基于{esc(region_name)}自 {first_s} - {last_s} 应用，从使用数据分析区域整体应用情况以及下阶段建议。</p>
  <div class="chips">
    <span class="chip">{icon('calendar','#4b4b4b',14)} {first_s} – {last_s}</span>
    <span class="chip">{icon('clock','#4b4b4b',14)} 约 {r['weeks']:.0f} 周</span>
  </div>
</header>

<section class="band"><div class="stat-grid" style="grid-template-columns:repeat({kpi_cols},1fr)">{kpis}</div></section>

<section class="block">{sec_title('star','本期核心结论')}<div class="cc-list">{cc_html}</div></section>

{schools_html}

<section class="block page">{sec_title('trend', D['trend_title'], D['trend_desc'])}
  <div class="card">{col_chart(D['trend'])}</div>
  {sec_title('layers','训练内容与资源结构','从“资源大类”观察教师最常布置的内容，便于安排教研指导与资源推广。')}
  <div class="pcard-grid">{cat_html}</div>
  <div class="card tbl-card"><div class="card-h">高频资源 Top（按布置次数）</div>{sub_tbl}</div></section>

{mock_html}

<section class="block page">{sec_title('teacher','教师应用画像','按累计布置次数排序，展示活跃教师的布置节奏与完成质量。')}
  <div class="card tbl-card">{tch_tbl}</div></section>

{qt_html}
{exam_html}

<section class="block">{sec_title('target','下一步工作建议')}
  <div class="grid2">
    {suggestion('star','推广示范经验',f"优先组织 {top['short']} 等{mlabel}高、完成率好的学校分享作业布置与学生督促经验。")}
    {suggestion('alert','跟进待提升学校',f"对 {low['short']} 等{mlabel}偏低的学校开展名单化跟进，核查账号启用、教师培训与作业布置机制。")}
    {suggestion('layers','围绕高频资源做教研',f"「{top_cat[0]}」类资源占比最高（{top_cat[2]}%），可围绕高频栏目形成一套标准化作业建议。")}
    {exam_sug}
  </div>
  <div class="footer">数据来源：{data_src}　|　统计口径：{mlabel}{('（窗口内每班累计）' if short else '（启动日→全区截止日）')}　|　报告生成：{now}</div></section>

</body></html>"""


def build_school_graphic_html(S):
    """单校图文版：KPI → 核心结论 → 各班画像 → 周/月趋势+资源结构 → 套题横向对比 →
    阶段成效与典型班级 → 题型表现 → 教师画像 → 建议。"""
    sc = S["school"]
    classes = S["classes"]
    short = sc["short"]
    mlabel, munit = sc["metric_label"], sc["metric_unit"]
    fmax = max((c["metric"] for c in classes), default=1)
    top, low = classes[0], classes[-1]
    first_s = sc["gstart"].strftime("%Y年%m月%d日")
    last_s = sc["gend"].strftime("%Y年%m月%d日")
    top_cat = S["categories"][0] if S["categories"] else ("—", 0, 0)
    st = S.get("stage")
    now = datetime.now().strftime("%Y年%m月%d日")

    kpis = "".join([
        stat("class", "覆盖班级", sc["classes"], f"名册 {sc['roster_classes']} 班"),
        stat("users", "覆盖学生", f"{sc['students']:,}", "班级数据总览"),
        stat("doc", "作业布置", f"{sc['assigns']:,}", f"班均 {sc['per_class']} 次"),
        stat("check", "平均完成率", f"{sc['completion']}%", "100% 完成占比"),
        stat("score", "平均得分率", f"{sc['score']}%", "日常作业"),
        stat("speed", "自主练习", f"{sc['self_prac']:,}", f"另有词汇练习 {sc['vocab']:,} 次"),
        stat("clock", "平均单次耗时", f"{sc['minutes']} min", "作答平均时长"),
        stat("calendar", "统计周期", f"{sc['weeks']:.0f} 周", f"{sc['gstart'].strftime('%m-%d')} 至 {sc['gend'].strftime('%m-%d')}"),
    ])

    sp_top = max(classes, key=lambda c: c["self_prac"])
    sp_low = min(classes, key=lambda c: c["self_prac"])
    ccs = [
        ("应用覆盖", f"统计周期 {first_s} 至 {last_s}（约 {sc['weeks']:.0f} 周），全校 {sc['classes']} 个班级、"
                     f"{sc['students']:,} 名学生产生布置记录，累计布置作业 {sc['assigns']:,} 次，班均 {sc['per_class']} 次。"),
        ("应用节奏", f"{top['label']} 投入最高（{top['metric']}{munit}），{low['label']} 相对靠后"
                     f"（{low['metric']}{munit}），班级间布置节奏存在差距。"),
        ("完成质量", f"全校作业完成率 {sc['completion']}%、得分率 {sc['score']}%；"
                     f"高频资源为「{top_cat[0]}」（{top_cat[1]:,} 次，占 {top_cat[2]}%）。"),
        ("自主训练", f"全校自主练习共 {sc['self_prac']:,} 次，班级间差异明显："
                     f"{sp_top['label']} {sp_top['self_prac']:,} 次、{sp_low['label']} 仅 {sp_low['self_prac']:,} 次，"
                     "可作为学习习惯引导的观察点。"),
    ]
    if st:
        star = st["star"]
        ccs.append(("阶段成效", f"以自然{st['period_word']}对比听说模拟得分率，{star['label']} 由 {star['first']}% "
                                f"提升至 {star['last']}%（+{star['growth']} 个百分点），另有 {len(st['growers'])} 个班级"
                                "呈上升趋势，日常训练成效逐步显现。"))
    cc_html = "".join(conclusion(i + 1, t, b) for i, (t, b) in enumerate(ccs))

    classes_html = class_rows_section(classes, fmax, munit, mlabel, short)
    cat_html = "".join(pct_card(c, n, p) for c, n, p in S["categories"])
    sub_tbl = table(["资源大类", "试题类型", "布置次数", "得分率", "单次耗时/min"],
                    [(c, s2, f"{n:,}", f"{score}%", f"{mins}") for c, s2, n, score, mins in S["subitems"]],
                    ["left", "left", "right", "right", "right"])
    papers_html = (f"""<section class="block page">{sec_title('layers', '听说模拟作业横向对比',
        '同一套题下各班平均得分率对比（绿＝该套题最高班），仅统计有有效作答的班级；'
        '并结合布置频次、作业结构与题型表现，自动提炼领先班级的做法与各班可参考的提升方向。')}
  {paper_compare_section(S['papers'], S.get('paper_insight'))}</section>""" if S.get("papers") else "")
    stage_html = stage_section_school(st, sc) if st else ""
    qt_html = qt_section(S["qt"]) if S.get("qt") else ""
    tch_tbl = table(["教师", "班级数", "布置次数", "完成率", "得分率"],
                    [(t["name"], t["classes"], t["assigns"], fp(t["completion"]), fp(t["score"]))
                     for t in S["teachers"]],
                    ["left", "right", "right", "right", "right"])

    sugs = [
        suggestion("star", "推广班内示范经验",
                   f"组织 {top['label']}（{top['metric']}{munit}）分享作业布置与督促做法，拉齐班级间应用节奏。"),
        suggestion("alert", "跟进低频班级",
                   f"对 {low['label']} 等布置偏低的班级，核查布置计划与课堂讲评安排，设定每周布置量下限。"),
        suggestion("speed", "引导自主练习",
                   f"自主练习班级差异大（{sp_top['self_prac']:,} vs {sp_low['self_prac']:,} 次），"
                   "可在班级内建立打卡与表扬机制，把课后自驱训练用起来。"),
    ]
    if st:
        sugs.append(suggestion("trend", "以模拟测练固化成效",
                               f"{st['star']['label']} 的“高频模拟＋讲评”节奏已见提分效果，"
                               "建议在其余班级复制，并结合薄弱题型做专项讲评。"))
    else:
        sugs.append(suggestion("layers", "丰富模拟测练",
                               "增加听说模拟套题的布置频次，形成“练—测—评”闭环，便于观察阶段成效。"))

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{CSS}</style></head><body>

<header class="cover">
  <h1>{esc(sc['name'])} E听说应用成效报告</h1>
  <p class="cover-sub">基于{esc(sc['name'])}自 {first_s} - {last_s} 应用，从班级维度分析应用情况、听说模拟成效以及下阶段建议。</p>
  <div class="chips">
    <span class="chip">{icon('calendar','#4b4b4b',14)} {first_s} – {last_s}</span>
    <span class="chip">{icon('clock','#4b4b4b',14)} 约 {sc['weeks']:.0f} 周</span>
    <span class="chip">{icon('class','#4b4b4b',14)} {sc['classes']} 个班级</span>
  </div>
</header>

<section class="band"><div class="stat-grid" style="grid-template-columns:repeat(4,1fr)">{kpis}</div></section>

<section class="block">{sec_title('star','本期核心结论')}<div class="cc-list">{cc_html}</div></section>

{classes_html}

<section class="block page">{sec_title('trend', S['trend_title'], S['trend_desc'])}
  <div class="card">{col_chart(S['trend'])}</div>
  {sec_title('layers','训练内容与资源结构','从“资源大类”观察最常布置的内容，便于安排教研与资源使用。')}
  <div class="pcard-grid">{cat_html}</div>
  <div class="card tbl-card"><div class="card-h">高频资源 Top（按布置次数）</div>{sub_tbl}</div></section>

{papers_html}
{stage_html}
{qt_html}

<section class="block page">{sec_title('teacher','教师应用画像','按累计布置次数排序，展示教师布置节奏与完成质量。')}
  <div class="card tbl-card">{tch_tbl}</div>
  {sec_title('target','下一步工作建议')}
  <div class="grid2">{''.join(sugs)}</div>
  <div class="footer">数据来源：{esc(sc['name'])} 班级数据总览、作业明细{('、听说模拟题型' if S.get('qt') else '')}　|
  统计单元：班级　|　趋势口径：{'自然周（周期不足 3 个月）' if sc['weekly'] else '月度'}　|　报告生成：{now}</div></section>

</body></html>"""


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root{
  --gray-50:#fafafa; --gray-75:#f5f5f5; --gray-100:#fff; --gray-200:#e6e6e6; --gray-300:#d5d5d5;
  --gray-400:#cacaca; --gray-500:#8c8c8c; --gray-700:#4b4b4b; --gray-800:#2c2c2c; --gray-900:#1f1f1f;
  --blue-500:#1473e6; --blue-600:#0d66d0; --blue-700:#095aba; --blue-bg:#e6f0fc;
  --green:#2d9d78; --green-bg:#eaf6f1; --red:#e34850; --red-bg:#fbeced; --radius:8px;
}
@page { size:A4; margin:13mm 12mm; }
body{ font-family:"adobe-clean",-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  color:var(--gray-900); background:var(--gray-100); font-size:12px; line-height:1.5;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; -webkit-font-smoothing:antialiased; }
.page{ break-before:page; page-break-before:always; }
.block{ margin-bottom:18px; }
.cover{ padding:6px 0 18px; border-bottom:1px solid var(--gray-200); margin-bottom:18px; }
.cover h1{ font-size:30px; font-weight:700; letter-spacing:-.02em; }
.cover-sub{ color:var(--gray-700); font-size:13px; max-width:86%; margin:12px 0 16px; line-height:1.6; }
.chips{ display:flex; gap:8px; flex-wrap:wrap; }
.chip{ display:inline-flex; align-items:center; gap:6px; padding:5px 11px; border-radius:999px;
  background:var(--gray-75); border:1px solid var(--gray-200); color:var(--gray-700); font-size:11.5px; font-weight:600; }
.sec-head{ display:flex; align-items:center; gap:8px; margin:2px 0; }
.sec-rail{ width:4px; height:18px; border-radius:2px; background:var(--blue-500); }
.sec-t{ font-size:15.5px; font-weight:700; letter-spacing:-.01em; }
.sec-desc{ font-size:11.5px; color:var(--gray-500); margin:4px 0 12px; line-height:1.55; max-width:96%; }
.band{ margin-bottom:18px; }
.stat-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.stat-grid.g4{ grid-template-columns:repeat(4,1fr); }
.stat{ border:1px solid var(--gray-200); border-radius:var(--radius); padding:13px; background:var(--gray-100); }
.stat-h{ display:flex; align-items:center; gap:6px; color:var(--gray-500); font-size:11px; font-weight:600; }
.stat-v{ font-size:23px; font-weight:800; color:var(--gray-900); margin-top:6px; letter-spacing:-.02em; }
.stat-s{ font-size:10.5px; color:var(--gray-500); margin-top:2px; }
.card{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius);
  padding:18px 20px; box-shadow:0 1px 4px rgba(0,0,0,.04); break-inside:avoid; }
.card-h{ font-size:13px; font-weight:700; margin-bottom:10px; color:var(--gray-800); }
.tbl-card{ padding:16px 18px; }
.cc-list{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.cc{ display:flex; gap:11px; background:var(--gray-50); border:1px solid var(--gray-200); border-radius:var(--radius); padding:13px 14px; break-inside:avoid; }
.cc-n{ flex:none; width:22px; height:22px; border-radius:6px; background:var(--blue-bg); color:var(--blue-700); font-weight:800; font-size:12px; display:flex; align-items:center; justify-content:center; }
.cc-t{ font-weight:700; font-size:12.5px; }
.cc-b{ font-size:11.5px; color:var(--gray-700); margin-top:3px; line-height:1.55; }
.barlist{ display:flex; flex-direction:column; gap:9px; }
.brow{ display:grid; grid-template-columns:124px 1fr 118px; align-items:center; gap:12px; }
.blabel{ font-size:12px; color:var(--gray-800); text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.btrack{ height:12px; background:var(--gray-200); border-radius:999px; overflow:hidden; }
.bfill{ height:100%; border-radius:999px; display:block; }
.bval{ font-size:12px; font-weight:700; color:var(--gray-800); }
.grid2{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
.hcard{ border-radius:var(--radius); padding:15px 17px; break-inside:avoid; border:1px solid var(--gray-200); }
.hcard.good{ background:var(--green-bg); border-color:#cde9de; }
.hcard.warn{ background:var(--red-bg); border-color:#f4d3d5; }
.hcard-tag{ font-size:11.5px; color:var(--gray-700); font-weight:600; display:flex; align-items:center; gap:6px; }
.hcard-name{ font-size:20px; font-weight:800; margin:6px 0 4px; letter-spacing:-.01em; }
.hcard-sub{ font-size:11.5px; color:var(--gray-700); }
.ecard-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.slist{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius); padding:2px 16px; box-shadow:0 1px 4px rgba(0,0,0,.04); }
.srow{ display:grid; grid-template-columns:22px minmax(0,1.5fr) minmax(100px,1fr) 68px 52px 52px 58px; gap:10px; align-items:center; padding:6px 0; border-bottom:1px solid var(--gray-75); break-inside:avoid; }
.srow:last-child{ border-bottom:none; }
.srow.h{ color:var(--gray-500); font-size:10.5px; font-weight:600; padding:8px 0 6px; border-bottom:1.5px solid var(--gray-300); }
.sr-i{ font-size:10.5px; color:var(--gray-500); font-weight:600; }
.sr-name{ font-size:12.5px; font-weight:700; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-sub{ font-size:10px; color:var(--gray-500); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-v{ font-size:13px; font-weight:800; color:var(--blue-600); white-space:nowrap; text-align:right; }
.sr-v span{ font-size:9.5px; color:var(--gray-500); font-weight:600; margin-left:2px; }
.sr-c{ font-size:11.5px; font-weight:600; color:var(--gray-800); text-align:right; }
.srow.c8{ grid-template-columns:22px minmax(0,1.35fr) minmax(80px,.9fr) 64px 50px 50px 56px 56px; }
/* 块级而非 float：html2canvas 对 float 换行场景会丢失后续兄弟元素的绘制 */
.ph-sub{ display:block; font-size:10.5px; color:var(--gray-500); font-weight:600; margin-top:2px; }
.gblock-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:11px; margin-top:12px; }
.gblock{ background:var(--green-bg); border:1px solid #cde9de; border-radius:var(--radius); padding:12px 14px; break-inside:avoid; }
.gb-name{ font-size:13px; font-weight:800; }
.gb-v{ font-size:20px; font-weight:800; color:var(--green); margin:3px 0 2px; }
.gb-v span{ font-size:10.5px; color:var(--gray-500); font-weight:600; }
.gb-sub{ font-size:10.5px; color:var(--gray-700); margin-top:2px; }
/* html2pdf 分页保护：legacy page-break-* 与 break-* 双写，避免组件被切片拦腰截断 */
.card,.stat,.cc,.hcard,.scard,.gblock,.pcard,.bench,.note,.srow,.brow,.qtrow,.ecard,.sec-head,.chips{ page-break-inside:avoid; }
.page{ break-before:page; page-break-before:always; }
.ecard{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius); padding:14px 15px; break-inside:avoid; }
.ecard-h{ display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
.ecard-name{ font-size:15px; font-weight:800; letter-spacing:-.01em; min-width:0; line-height:1.25; }
.ecard-idx{ font-size:19px; font-weight:800; color:var(--blue-600); flex:none; white-space:nowrap; }
.ecard-idx span{ font-size:10px; font-weight:600; color:var(--gray-500); margin-left:3px; }
.ecard-track{ height:6px; background:var(--gray-200); border-radius:999px; margin:9px 0 11px; overflow:hidden; }
.ecard-fill{ height:100%; background:var(--blue-500); border-radius:999px; }
.ms-grid{ display:grid; grid-template-columns:1fr 1fr; gap:7px; }
.ms{ background:var(--gray-50); border:1px solid var(--gray-200); border-radius:6px; padding:7px 9px; }
.ms-l{ font-size:10.5px; color:var(--gray-500); }
.ms-v{ font-size:14px; font-weight:800; margin-top:1px; }
.ecard-foot{ font-size:10.5px; color:var(--gray-500); margin-top:10px; display:flex; align-items:center; gap:5px; }
.colchart{ display:flex; align-items:flex-end; gap:14px; height:160px; padding:6px 4px 0; }
.col{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
.col-v{ font-size:11px; font-weight:700; color:var(--gray-700); margin-bottom:4px; }
.col-bar{ width:100%; max-width:54px; background:var(--blue-500); border-radius:6px 6px 0 0; }
.col-l{ font-size:10.5px; color:var(--gray-500); margin-top:6px; }
.pcard-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:11px; margin-bottom:14px; }
.pcard{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius); padding:13px 14px; break-inside:avoid; }
.pcard-h{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:8px; }
.pcard-h span{ font-size:13px; font-weight:700; }
.pcard-h b{ font-size:16px; color:var(--blue-600); }
.pcard-s{ font-size:10.5px; color:var(--gray-500); margin-top:7px; }
.tbl{ width:100%; border-collapse:collapse; }
.tbl th{ font-size:10.5px; color:var(--gray-500); font-weight:600; padding:7px 8px; border-bottom:1.5px solid var(--gray-300); }
.tbl td{ font-size:11.5px; padding:7px 8px; border-bottom:1px solid var(--gray-200); color:var(--gray-800); }
.tbl tbody tr:last-child td{ border-bottom:none; }
.scard{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius); padding:14px 16px; break-inside:avoid; }
.scard-t{ font-size:13px; font-weight:700; display:flex; align-items:center; gap:7px; }
.scard-b{ font-size:11.5px; color:var(--gray-700); margin-top:7px; line-height:1.55; }
.footer{ font-size:10.5px; color:var(--gray-500); margin-top:16px; padding-top:12px; border-top:1px solid var(--gray-200); text-align:center; }
.note{ font-size:11.5px; color:var(--gray-700); background:var(--gray-50); border:1px solid var(--gray-200); border-radius:var(--radius); padding:10px 13px; margin-top:12px; display:flex; align-items:center; gap:7px; }
.card.hl{ background:#f6f9ff; border-color:#d6e4fb; }
.rcallout{ display:flex; align-items:center; gap:14px; padding-bottom:13px; border-bottom:1px dashed #cdd9f0; margin-bottom:12px; }
.rbig{ font-size:34px; font-weight:800; color:var(--blue-600); letter-spacing:-.01em; }
.rlabel{ font-size:12px; color:var(--gray-700); line-height:1.5; }
.bench-list{ display:flex; flex-direction:column; gap:8px; }
.bench{ background:var(--gray-100); border:1px solid var(--gray-200); border-radius:var(--radius); padding:9px 12px; }
.bench-tag{ font-size:11px; color:var(--green); display:flex; align-items:center; gap:5px; font-weight:600; }
.bench-name{ font-size:14px; font-weight:800; margin-top:2px; }
.bench-sub{ font-size:11px; color:var(--gray-500); margin-top:1px; }
.qtlist{ display:flex; flex-direction:column; gap:9px; }
.qtrow{ display:grid; grid-template-columns:74px 1fr; gap:10px; align-items:center; }
.qt-name{ font-size:12px; font-weight:600; color:var(--gray-800); }
.qt-bars{ display:flex; flex-direction:column; gap:4px; }
.qt-line{ display:flex; align-items:center; gap:7px; }
.qt-tag{ font-size:10.5px; color:var(--gray-500); width:26px; }
.qt-v{ font-size:11px; font-weight:700; width:34px; color:var(--gray-800); }
.btrack.sm{ height:9px; flex:1; }
"""
