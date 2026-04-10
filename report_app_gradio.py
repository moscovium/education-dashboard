"""
E听说 成效报告对话系统 v2.0 - Gradio 版本
迁移自 report_app.py（Streamlit）
"""

import gradio as gr
import openai
import sys
import os

# 导入共享核心逻辑
from report_app_core import (
    parse_class_overview,
    parse_hw_details,
    analyze_data,
    generate_report_text,
    make_charts,
)

# ─────────────────────────────────────────────
# Gradio 界面
# ─────────────────────────────────────────────

PROVIDERS = {
    " Minimax（海螺AI）": {
        "base_url": "https://api.minimax.chat/v",
        "model": "MiniMax-Text-01",
        "key_hint": "Bearer Token（maa-...）",
    },
    " DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "key_hint": "API Key（sk-...）",
    },
    " 硅基流动（SiliconFlow）": {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3",
        "key_hint": "API Key（sk-...）",
    },
    " Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "mixtral-8x7b-32768",
        "key_hint": "API Key（gsk_...）",
    },
}


def process_files(class_file, hw_file, provider_name, api_key):
    """处理上传的文件，返回分析结果"""
    if class_file is None or hw_file is None:
        return None, None, None, "⚠️ 请同时上传两个Excel文件：班级数据总览 和 作业明细"

    try:
        class_df = parse_class_overview(class_file)
        hw_df = parse_hw_details(hw_file)
        data = analyze_data(class_df, hw_df)
        report_text = generate_report_text(data)
        charts = make_charts(data)

        # 生成图表HTML
        chart_htmls = {}
        for key, fig in charts.items():
            chart_htmls[key] = fig.to_html(full_html=False, include_plotlyjs='cdn')

        school = data.get('school_name', '未知学校')
        summary = f"✅ 分析完成！\n\n学校：{school}\n班级：{data['classes']}个\n学生：{data['total_students']}人\n作业总数：{data['total_hw']}次\n作业完成率：{data['completion_rate']}%\n平均得分率：{data['score_rate_avg']}%"

        return report_text, chart_htmls, data, summary
    except Exception as e:
        import traceback
        return None, None, None, f"❌ 数据解析出错：{e}\n\n{traceback.format_exc()}"


def chat_adjustments(message, history, provider_name, api_key, current_report):
    """处理对话调整请求"""
    if not api_key or not message:
        return current_report, history

    provider = PROVIDERS.get(provider_name, PROVIDERS[" Minimax（海螺AI）"])

    prompt = f"""你是一个专业的教育数据分析报告编辑助手。请根据用户指示修改报告。

**原始报告：**
---
{current_report}

**用户指示：**
{message}

请直接输出修改后的完整报告（Markdown格式），保持原有结构，只修改指定内容。"""

    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=provider.get("base_url") if provider.get("base_url") else None,
        )
        response = client.chat.completions.create(
            model=provider.get("model", "deepseek-chat"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3,
        )
        revised = response.choices[0].message.content
        # 去掉可能的markdown代码块包裹
        if revised.startswith('```'):
            lines_r = revised.split('\n')
            revised = '\n'.join(lines_r[1:-1] if lines_r[-1] == '```' else lines_r[1:])

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": revised})
        return revised, history
    except Exception as e:
        error_msg = f"❌ 大模型调用失败：{e}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return current_report, history


def render_charts(chart_htmls):
    """渲染图表"""
    if not chart_htmls:
        return "📊 暂无图表数据"

    html_parts = []
    chart_titles = {
        'monthly_line': '📊 图1 月度作业布置总量趋势',
        'grade_monthly_line': '📈 图2 各年级月度作业量趋势',
        'cat_stacked': '📊 图3 月度作业大类分布堆叠图',
        'cat_pie': '🥧 图4 作业类型占比分布',
        'mock_score': '📉 图5 听说模拟类月均得分率趋势',
        'grade_score': '📈 图6 各年级听说模拟得分率趋势',
        'top_class_trend': '🎯 图7 标杆班级月度分析',
    }
    for key, html in chart_htmls.items():
        title = chart_titles.get(key, key)
        html_parts.append(f"<h4>{title}</h4>")
        html_parts.append(html)
        html_parts.append("<hr/>")
    return "\n".join(html_parts)


# ─────────────────────────────────────────────
# 构建 Gradio Blocks 界面
# ─────────────────────────────────────────────

with gr.Blocks(title="E听说成效报告系统", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📊 E听说 成效报告对话系统 v2.0")
    gr.Markdown("上传Excel文件，自动生成分析报告。支持对话式调整报告内容。")

    # 状态存储
    report_state = gr.State("")
    data_state = gr.State({})
    charts_state = gr.State({})
    history_state = gr.State([])

    with gr.Tabs():
        # ── Tab 1: 文件上传 & 报告生成 ──
        with gr.TabItem("📁 上传 & 生成报告"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 使用说明")
                    gr.Markdown("""
                    **步骤：**
                    1. 上传 `班级数据总览.xlsx`
                    2. 上传 `作业明细.xlsx`
                    3. 点击「开始分析」生成报告
                    4. 切换到「报告预览」查看结果
                    5. 在「对话调整」标签页与大模型对话修改报告

                    **文件要求：**
                    - 班级数据总览：含班级id、总学生数、布置作业次数、作业完成率等
                    - 作业明细：含作业路径、得分率、开始日期等
                    """)
                    with gr.Accordion("🔑 大模型API配置（可选）", open=False):
                        provider_dropdown = gr.Dropdown(
                            choices=list(PROVIDERS.keys()),
                            value=" Minimax（海螺AI）",
                            label="模型服务商"
                        )
                        api_key_input = gr.Textbox(
                            label="API Key",
                            placeholder="输入你的API Key...",
                            type="password"
                        )

                with gr.Column(scale=2):
                    class_file = gr.File(
                        label="📁 上传「班级数据总览.xlsx」",
                        file_types=[".xlsx"],
                        file_count=1
                    )
                    hw_file = gr.File(
                        label="📁 上传「作业明细.xlsx」",
                        file_types=[".xlsx"],
                        file_count=1
                    )
                    analyze_btn = gr.Button("🔍 开始分析", variant="primary")

                    status_output = gr.Textbox(label="状态", lines=3, interactive=False)

                    analyze_btn.click(
                        fn=process_files,
                        inputs=[class_file, hw_file, provider_dropdown, api_key_input],
                        outputs=[report_state, charts_state, data_state, status_output]
                    )

        # ── Tab 2: 报告预览 ──
        with gr.TabItem("📄 成效报告"):
            gr.Markdown("### 📄 成效报告（初稿）")
            report_display = gr.Markdown("", elem_id="report-content")
            # 用js监听report_state变化并更新显示
            demo.load(
                fn=None,
                inputs=[report_state],
                outputs=[],
                js="""
                function(state) {
                    if(state && document.getElementById('report-content')) {
                        document.getElementById('report-content').innerHTML = marked.parse(state || '');
                    }
                    return [];
                }
                """
            )
            # 手动刷新按钮
            refresh_btn = gr.Button("🔄 刷新报告显示")
            refresh_btn.click(
                fn=lambda x: x,
                inputs=[report_state],
                outputs=[report_display]
            )

        # ── Tab 3: 图表分析 ──
        with gr.TabItem("📈 数据可视化"):
            gr.Markdown("### 📈 数据可视化")
            charts_display = gr.HTML("", elem_id="charts-content")
            demo.load(
                fn=None,
                inputs=[charts_state],
                outputs=[],
                js="""
                function(charts) {
                    if(!charts) return [];
                    let html = '';
                    const titles = {
                        'monthly_line': '📊 图1 月度作业布置总量趋势',
                        'grade_monthly_line': '📈 图2 各年级月度作业量趋势',
                        'cat_stacked': '📊 图3 月度作业大类分布堆叠图',
                        'cat_pie': '🥧 图4 作业类型占比分布',
                        'mock_score': '📉 图5 听说模拟类月均得分率趋势',
                        'grade_score': '📈 图6 各年级听说模拟得分率趋势',
                        'top_class_trend': '🎯 图7 标杆班级月度分析',
                    };
                    for(const [key, figHtml] of Object.entries(charts)) {
                        html += '<h4>' + (titles[key] || key) + '</h4>';
                        html += figHtml;
                        html += '<hr/>';
                    }
                    if(document.getElementById('charts-content')) {
                        document.getElementById('charts-content').innerHTML = html;
                        // 重新导入plotly
                        if(typeof Plotly === 'undefined') {
                            let script = document.createElement('script');
                            script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
                            document.head.appendChild(script);
                        }
                    }
                    return [];
                }
                """
            )
            refresh_charts_btn = gr.Button("🔄 刷新图表")
            refresh_charts_btn.click(
                fn=render_charts,
                inputs=[charts_state],
                outputs=[charts_display]
            )

        # ── Tab 4: 对话调整 ──
        with gr.TabItem("💬 对话调整"):
            gr.Markdown("### 💬 对话调整报告")
            gr.Markdown("""
            **支持的操作：**
            - 修改/补充结论（如"将七年级建议改为..."）
            - 调整数据口径或重新计算
            - 补充某班级详细分析
            - 改变建议优先级
            - 用更正式的公文语气重写某章节
            """)
            gr.Markdown("*请先在「上传 & 生成报告」标签页完成分析，再到这里对话调整。*")

            chatbot = gr.Chatbot(label="对话历史", height=400)
            msg_input = gr.Textbox(
                label="输入你的调整要求",
                placeholder="例如：将亮点二的描述改为更正式的语气...",
                lines=2
            )
            with gr.Row():
                send_btn = gr.Button("🚀 发送", variant="primary")
                clear_btn = gr.Button("🗑️ 清空对话")

            api_key_for_chat = gr.Textbox(label="API Key（用于大模型对话）", type="password", visible=False)
            provider_for_chat = gr.Dropdown(choices=list(PROVIDERS.keys()), value=" Minimax（海螺AI）", label="服务商", visible=False)

            def send_message(msg, hist, provider, key, report):
                if not report:
                    return report, hist + [{"role": "assistant", "content": "⚠️ 请先完成报告生成（上传文件并分析）"}]
                revised, new_hist = chat_adjustments(msg, hist, provider, key, report)
                return revised, new_hist

            send_btn.click(
                fn=send_message,
                inputs=[msg_input, chatbot, provider_for_chat, api_key_for_chat, report_state],
                outputs=[report_state, chatbot]
            )
            msg_input.submit(
                fn=send_message,
                inputs=[msg_input, chatbot, provider_for_chat, api_key_for_chat, report_state],
                outputs=[report_state, chatbot]
            )
            clear_btn.click(
                fn=lambda: (gr.Chatbot.clear()),
                outputs=[chatbot]
            )

# 启动
if __name__ == "__main__":
    demo.launch()
