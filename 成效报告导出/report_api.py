import base64
import json
import sys
from pathlib import Path

from plotly.utils import PlotlyJSONEncoder

from report_app_core import (
    REPORT_VERSION,
    analyze_data,
    analyze_district_data,
    attach_exam_analysis,
    export_to_docx,
    generate_district_report_text,
    generate_report_text,
    make_charts,
    make_district_charts,
    parse_class_overview,
    parse_exam_reports,
    parse_hw_details,
    parse_question_type,
)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("missing input json path")

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    class_path = payload["classFile"]
    homework_path = payload["homeworkFile"]
    question_path = payload.get("questionFile")
    exam_paths = payload.get("examFiles") or []
    report_type = payload.get("reportType", "school")
    report_format = payload.get("format", "text")

    class_df = parse_class_overview(class_path)
    homework_df = parse_hw_details(homework_path)
    question_df = parse_question_type(question_path) if question_path else None

    # 图文版（区级 / 校级，浏览器端渲染 / 打印 PDF）
    if report_format == "graphic":
        import graphic_report as G
        if report_type == "school":
            sd = G.analyze_graphic_school(class_df, homework_df, question_df)
            school = sd.get("school", {})
            result = {
                "ok": True,
                "version": REPORT_VERSION,
                "format": "graphic",
                "summary": {
                    "report_scope": "school",
                    "region_name": school.get("name", ""),
                    "schools": 1,
                    "classes": school.get("classes", 0),
                    "total_students": school.get("students", 0),
                    "total_hw": school.get("assigns", 0),
                },
                "graphicHtml": G.build_school_graphic_html(sd),
            }
        else:
            exam_stages = parse_exam_reports(exam_paths) if exam_paths else None
            gd = G.analyze_graphic(class_df, homework_df, question_df, exam_stages)
            region = gd.get("region", {})
            result = {
                "ok": True,
                "version": REPORT_VERSION,
                "format": "graphic",
                "summary": {
                    "report_scope": "district",
                    "region_name": region.get("name", ""),
                    "schools": region.get("schools", 0),
                    "classes": region.get("classes", 0),
                    "total_students": region.get("students", 0),
                    "total_hw": region.get("assigns", 0),
                },
                "graphicHtml": G.build_graphic_html(gd),
            }
        print(json.dumps(result, ensure_ascii=False))
        return

    if report_type == "district":
        data = analyze_district_data(class_df, homework_df, question_df)
        # 阶段性联考（可选）：仅区级支持，按文档时间排序后做“练—考”关联
        if exam_paths:
            exam_stages = parse_exam_reports(exam_paths)
            attach_exam_analysis(data, exam_stages)
        report_text = generate_district_report_text(data)
        charts = make_district_charts(data)
    else:
        data = analyze_data(class_df, homework_df, question_df)
        report_text = generate_report_text(data)
        charts = make_charts(data)
    docx_buf, docx_error = export_to_docx(report_text, charts, data)

    chart_titles = {
        "monthly_line": "月度作业总量趋势",
        "grade_monthly_line": "各年级月度作业量趋势",
        "cat_stacked": "各月各类作业量堆叠图",
        "cat_grade_pct": "各年级各栏目训练占比",
        "grade_score": "各年级听说模拟得分率趋势",
        "top_class_trend": "标杆班级月度分析",
        "district_school_active": "班均有效布置指数Top学校",
        "district_school_category_pct": "各校各栏目训练结构",
        "district_case_grade": "典型学校年级听说模拟次数与提分率",
        "district_qt_grade": "各年级各题型平均得分率展示",
        "exam_trend": "全区联考整体均分阶段趋势",
        "exam_school": "各校联考平均分对比",
        "exam_qt": "各题型“日常练习 vs 联考”得分率对照",
        "exam_scatter": "日常练习得分率与联考平均分关联",
    }
    chart_html = []
    for key, fig in charts.items():
        chart_html.append({
            "key": key,
            "title": chart_titles.get(key, key),
            "figure": json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)),
        })

    safe_data = {}
    for key in ["school_name", "region_name", "report_scope", "province", "city", "stage_name", "stages", "classes", "schools", "total_students", "total_hw", "assign_count", "completion_rate", "score_rate_avg", "month_range"]:
        if key in data:
            safe_data[key] = data[key]

    result = {
        "ok": True,
        "version": REPORT_VERSION,
        "format": "text",
        "summary": safe_data,
        "report": report_text,
        "charts": chart_html,
        "docxError": docx_error,
        "docxBase64": base64.b64encode(docx_buf.getvalue()).decode("ascii") if docx_buf and not docx_error else "",
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
