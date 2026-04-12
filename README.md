# E听说成效报告系统

一个基于上传 Excel 数据自动生成成效报告的 Streamlit 应用。

## 本地启动

在项目目录运行：

```bash
./start_report_app.sh
```

默认地址：

- <http://localhost:8506>

如果脚本不可执行，也可以直接运行：

```bash
python3 -m streamlit run report_app_local_no_api.py --server.port 8506 --server.headless true
```

## Hugging Face 访问

公开访问链接：

- <https://0xsense-ets-report.hf.space>

## API Key 说明

这个版本**不需要 API Key**。

- 不依赖 OpenAI
- 不依赖 DeepSeek
- 不依赖其他大模型服务
- 仅基于上传的 Excel 数据自动分析、生成图表、输出报告和导出 Word

## 主要入口文件

- 本地 / 线上无 API Key 入口： [report_app_local_no_api.py](file:///Users/x/Downloads/Project/report_app_local_no_api.py)
- 核心分析逻辑： [report_app_core.py](file:///Users/x/Downloads/Project/report_app_core.py)
- 本地启动脚本： [start_report_app.sh](file:///Users/x/Downloads/Project/start_report_app.sh)
