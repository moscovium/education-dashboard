#!/usr/bin/env bash
set -euo pipefail
cd /Users/x/Downloads/Project
python3 -m streamlit run report_app_local_no_api.py --server.port 8506 --server.headless true
