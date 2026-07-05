# E听说成效报告导出

该项目已接入主站：

- <https://0xsense.org/report>

当前版本不再依赖 Streamlit 独立服务。页面由 `/Users/x/Downloads/Project/dashboard` 的 Node 服务直接提供，报告生成通过主站接口 `/api/report/generate` 调用本目录的 `report_api.py` 和 `report_app_core.py`。

## 使用方式

1. 打开 <https://0xsense.org/report>
2. 上传 `班级数据总览.xlsx`
3. 上传 `作业明细.xlsx`
4. 可选上传 `听说模拟班级总体情况-题型.xlsx`
5. 点击“生成报告”
6. 页面展示报告正文、图表，并可下载 Word

## 主站启动

```bash
cd /Users/x/Downloads/Project/dashboard
PORT=8090 node server.js
```

## 核心文件

- `report_api.py`：主站后端调用入口
- `report_app_core.py`：Excel 解析、分析、图表和 Word 导出核心逻辑
- `report_app_local_no_api.py`：历史 Streamlit 页面，当前线上入口不再使用
