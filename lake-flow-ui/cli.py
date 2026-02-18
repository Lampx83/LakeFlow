"""Entry point: lakeflow-ui — runs the Streamlit control UI."""
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.port=8012",
            "--server.address=0.0.0.0",
        ]
        + sys.argv[1:],
        check=True,
    )


if __name__ == "__main__":
    main()
