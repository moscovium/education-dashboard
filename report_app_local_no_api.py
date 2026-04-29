"""
E听说 成效报告系统（本地无 API Key 版）
基于上传 Excel 自动生成报告，不包含大模型对话修改功能。
"""
import streamlit as st
from datetime import datetime

from report_app_core import (
    parse_class_overview,
    parse_hw_details,
    parse_question_type,
    analyze_data,
    generate_report_text,
    make_charts,
    export_to_docx,
)

st.set_page_config(page_title="E听说成效报告系统", page_icon="📊", layout="wide")

APP_VERSION = "V1.1"

with st.sidebar:
    st.title("📋 使用说明")
    st.markdown("""
    **步骤：**
    1. 上传 `班级数据总览.xlsx`
    2. 上传 `作业明细.xlsx`
    3. 可选上传 `听说模拟班级总体情况-题型.xlsx`
    4. 系统自动分析并生成报告
    5. 导出为 Word

    **说明：**
    - 本版本**不需要 API Key**
    - 仅基于上传的数据自动生成报告
    - 不包含大模型对话改写功能
    """)
    st.divider()
    st.caption("纯本地/纯数据版")

st.title("E听说 成效报告系统")
st.caption(f"上传 Excel 后自动生成报告与图表（无 API Key 版）｜版本 {APP_VERSION}")

col1, col2, col3 = st.columns(3)
with col1:
    class_file = st.file_uploader("📁 上传「班级数据总览.xlsx」", type=["xlsx"], key="class_file")
with col2:
    hw_file = st.file_uploader("📁 上传「作业明细.xlsx」", type=["xlsx"], key="hw_file")
with col3:
    qt_file = st.file_uploader("📁 可选上传「题型统计.xlsx」", type=["xlsx"], key="qt_file")

generate_clicked = st.button("🚀 生成报告", type="primary", disabled=not (class_file and hw_file))

if class_file and hw_file and generate_clicked:
    with st.spinner("正在分析数据，请稍候..."):
        try:
            class_df = parse_class_overview(class_file)
            hw_df = parse_hw_details(hw_file)
            qt_df = parse_question_type(qt_file) if qt_file else None
            data = analyze_data(class_df, hw_df, qt_df)
            report_text = generate_report_text(data)
            charts = make_charts(data)
            st.session_state['data'] = data
            st.session_state['report'] = report_text
            st.session_state['charts'] = charts
            st.success(f"✅ 分析完成！学校：{data['school_name']}，班级：{data['classes']}个，学生：{data['total_students']}人")
        except Exception as e:
            st.error(f"❌ 数据解析出错：{e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

if 'report' in st.session_state:
    data = st.session_state['data']
    charts = st.session_state['charts']
    report_text = st.session_state['report']

    tab1, tab2, tab3 = st.tabs(["📄 成效报告", "📈 图表分析", "📥 导出Word"])

    with tab1:
        st.markdown("### 📄 成效报告")
        st.divider()
        st.markdown(report_text)

    with tab2:
        st.markdown("### 📈 数据可视化")
        st.divider()
        chart_map = [
            ('monthly_line', '📊 月度作业总量趋势（折线图）'),
            ('grade_monthly_line', '📈 各年级月度作业量趋势'),
            ('category_pie', '🥧 作业类型占比'),
            ('cat_stacked', '📊 各月各类作业量堆叠图'),
            ('mock_score', '📉 听说模拟得分率趋势'),
            ('grade_score', '📈 各年级听说模拟得分率趋势'),
            ('top_class_trend', '🎯 标杆班级月度分析'),
        ]
        shown = 0
        for key, title in chart_map:
            if key in charts:
                st.markdown(f"#### {title}")
                st.plotly_chart(charts[key], use_container_width=True)
                st.divider()
                shown += 1
        if shown == 0:
            st.info("当前数据未生成可展示图表。")

    with tab3:
        st.markdown("### 📥 导出为公文格式 Word")
        st.divider()
        if st.button("📄 生成Word文档", type="primary"):
            with st.spinner("正在生成Word文档..."):
                buf, err = export_to_docx(report_text, charts)
                if err:
                    st.error(err)
                else:
                    school = data.get('school_name', '学校')
                    fname = f"{school}成效报告_{datetime.now().strftime('%Y%m%d')}.docx"
                    st.download_button(
                        label=f"⬇️ 下载 {fname}",
                        data=buf.getvalue(),
                        file_name=fname,
                        mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    st.success("✅ Word文档已生成！")
else:
    st.info("👆 请先上传至少两个 Excel 文件开始生成报告")
    st.markdown("""
    **本版本特点：**
    - 不需要 OpenAI / DeepSeek / 其他 API Key
    - 完全基于上传的数据自动生成报告
    - 支持图表展示与 Word 导出
    """)
