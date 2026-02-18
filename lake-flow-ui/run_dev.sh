#!/usr/bin/env bash
# Chạy Streamlit dev từ đúng thư mục để runOnSave và file watch hoạt động.
# Có thể gọi từ project root: ./frontend/streamlit/run_dev.sh
# Load .env: trước khi chạy có thể chạy: export $(grep -v '^#' ../../.env | xargs)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

exec streamlit run app.py --server.runOnSave true --server.fileWatcherType poll
