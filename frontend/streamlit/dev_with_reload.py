#!/usr/bin/env python3
"""
Chạy Streamlit và tự restart khi có thay đổi file .py trong frontend/streamlit.
Cách dùng (từ project root):
  cd /path/to/EDUAI
  python frontend/streamlit/dev_with_reload.py

Hoặc từ frontend/streamlit:
  python dev_with_reload.py
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Thư mục chứa app (frontend/streamlit)
SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_DIR = SCRIPT_DIR
# Đuôi file cần watch
WATCH_EXT = (".py", ".toml")


def get_mtimes():
    """Lấy dict path -> mtime cho mọi file .py, .toml trong WATCH_DIR."""
    mtimes = {}
    for root, _, files in os.walk(WATCH_DIR):
        # Bỏ __pycache__ và .git
        if "__pycache__" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith(WATCH_EXT):
                p = Path(root) / f
                try:
                    mtimes[str(p)] = p.stat().st_mtime
                except OSError:
                    pass
    return mtimes


def main():
    os.chdir(SCRIPT_DIR)
    env = os.environ.copy()
    # Đảm bảo .env từ project root được load nếu có
    root_env = SCRIPT_DIR / ".." / ".." / ".env"
    if root_env.resolve().exists():
        try:
            with open(root_env) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        env[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass

    prev_mtimes = get_mtimes()
    proc = None

    while True:
        if proc is None:
            print("[dev_with_reload] Starting streamlit...", flush=True)
            proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "app.py", "--server.runOnSave", "true", "--server.fileWatcherType", "poll"],
                cwd=str(SCRIPT_DIR),
                env=env,
            )
            time.sleep(1)
            prev_mtimes = get_mtimes()
            continue

        ret = proc.poll()
        if ret is not None:
            print(f"[dev_with_reload] Streamlit exited with code {ret}. Restarting...", flush=True)
            proc = None
            continue

        cur_mtimes = get_mtimes()
        if cur_mtimes != prev_mtimes:
            for p in cur_mtimes:
                if cur_mtimes.get(p) != prev_mtimes.get(p):
                    print(f"[dev_with_reload] Detected change: {p}. Restarting streamlit...", flush=True)
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    proc = None
                    break
        prev_mtimes = cur_mtimes
        time.sleep(0.5)


if __name__ == "__main__":
    main()
