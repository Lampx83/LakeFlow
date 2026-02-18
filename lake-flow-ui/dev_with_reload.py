#!/usr/bin/env python3
"""
Run Streamlit and auto-restart when .py files change in lake-flow-ui.
Usage (from project root):
  cd /path/to/LakeFlow
  python lake-flow-ui/dev_with_reload.py

Or from lake-flow-ui:
  python dev_with_reload.py
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Directory containing the app (lake-flow-ui)
SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_DIR = SCRIPT_DIR
# File extensions to watch
WATCH_EXT = (".py", ".toml")


def get_mtimes():
    """Return dict path -> mtime for all .py, .toml files in WATCH_DIR."""
    mtimes = {}
    for root, _, files in os.walk(WATCH_DIR):
        # Skip __pycache__ and .git
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
    # Load .env from project root if present
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
