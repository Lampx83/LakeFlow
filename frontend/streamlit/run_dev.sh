#!/usr/bin/env bash
# Run Streamlit dev from correct directory so runOnSave and file watch work.
# Can call from project root: ./frontend/streamlit/run_dev.sh
# Load .env: before running you can run: export $(grep -v '^#' ../../.env | xargs)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

exec streamlit run app.py --server.runOnSave true --server.fileWatcherType poll
