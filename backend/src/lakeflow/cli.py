#!/usr/bin/env python3
"""
LakeFlow CLI — scaffold a new LakeFlow project (like create-react-app).
Usage: lakeflow init [folder-name]
"""

import os
import sys
import shutil
import zipfile
import tempfile
import urllib.request
from pathlib import Path

GITHUB_REPO = "Lampx83/LakeFlow"
GITHUB_BRANCH = "main"
ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"


def ask(question: str, default: str = "y") -> bool:
    """Ask yes/no, default yes."""
    d = default.lower()
    suffix = "[Y/n]" if d == "y" else "[y/N]"
    try:
        ans = input(f"  {question} {suffix} ").strip().lower() or d
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return d == "y"


def ask_folder(prompt: str, default: str = "lakeflow-app") -> str | None:
    """Ask for folder name."""
    try:
        ans = input(f"  {prompt} [{default}] ").strip() or default
        return ans if ans else None
    except (EOFError, KeyboardInterrupt):
        return None


def download_and_extract(target_dir: Path) -> bool:
    """Download LakeFlow from GitHub and extract to target_dir."""
    tmp_dir = Path(tempfile.mkdtemp(prefix=".lakeflow-init-"))
    zip_path = tmp_dir / "repo.zip"
    try:
        print(f"  Downloading LakeFlow from GitHub ({GITHUB_REPO})...")
        urllib.request.urlretrieve(ZIP_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            # GitHub zip has one top-level dir: LakeFlow-main/
            names = zf.namelist()
            if not names:
                print("  Error: Empty archive.")
                return False
            top = names[0].split("/")[0]  # e.g. LakeFlow-main
            zf.extractall(tmp_dir)
        extracted = tmp_dir / top
        if not extracted.exists():
            print(f"  Error: Expected {top} in archive.")
            return False
        # Move contents to target_dir (target_dir already exists and is empty)
        for item in extracted.iterdir():
            shutil.move(str(item), str(target_dir / item.name))
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def run_docker(target_dir: Path) -> None:
    """Run docker compose up -d."""
    import subprocess

    os.chdir(target_dir)
    try:
        subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
        print("  Docker Compose started. Backend: http://localhost:8011 | Streamlit: http://localhost:8012")
    except subprocess.CalledProcessError as e:
        print(f"  Docker failed: {e}")
    except FileNotFoundError:
        print("  Docker not found. Run manually: docker compose up -d")


def main() -> None:
    print("\n  LakeFlow — Data Lake pipelines for RAG & AI\n")

    project_name = sys.argv[1] if len(sys.argv) > 1 else None
    if not project_name or not project_name.strip():
        project_name = ask_folder("Project folder name?", "lakeflow-app")
        if not project_name:
            print("  Aborted.")
            sys.exit(1)

    target_dir = Path.cwd() / project_name
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"  Error: {project_name} already exists and is not empty.")
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)

    if not download_and_extract(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
        sys.exit(1)

    # Remove website folder from scaffold (optional — users get backend+frontend+docker)
    website_dir = target_dir / "website"
    if website_dir.exists():
        shutil.rmtree(website_dir)

    print(f"  Created {project_name}.")

    if ask("Run Docker Compose now?"):
        run_docker(target_dir)
    else:
        print(f"  To start later: cd {project_name} && docker compose up -d")

    print("")


if __name__ == "__main__":
    main()
