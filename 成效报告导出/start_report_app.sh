#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
成效报告导出已接入 0xsense.org/report，不再需要单独启动 Streamlit。

请确保主站服务正在运行：
  cd /Users/x/Downloads/Project/dashboard
  PORT=8090 node server.js

访问地址：
  https://0xsense.org/report
MSG
