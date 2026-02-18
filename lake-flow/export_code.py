import os

# ================== CẤU HÌNH ==================
PROJECT_ROOT = "."                 # Thư mục gốc dự án
OUTPUT_FILE = "project_code.txt"  # File xuất code

# Thư mục không duyệt
EXCLUDE_DIRS = {
    ".git", "__pycache__", "venv", ".venv",
    "env", "node_modules", ".idea", ".vscode",
}

# File Python không export
EXCLUDE_FILES = {
    "__init__.py", "export_code.py",
}

# File đặc biệt cần export (không phải .py)
EXTRA_FILES = {
    "requirements.txt",
    "docker-compose.yml",
    "Dockerfile",
    "env.example",
    "pyproject.toml"
}
# =============================================


def should_skip_dir(dir_name: str) -> bool:
    return dir_name in EXCLUDE_DIRS


def should_export_file(file_name: str) -> bool:
    # Export file .py (trừ file bị loại)
    if file_name.endswith(".py"):
        return file_name not in EXCLUDE_FILES

    # Export file đặc biệt
    if file_name in EXTRA_FILES:
        return True

    return False


def export_project_code():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Loại bỏ các thư mục không cần duyệt
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]

            for file in files:
                if not should_export_file(file):
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)

                out.write("\n" + "=" * 80 + "\n")
                out.write(f"# FILE: {rel_path}\n")
                out.write("=" * 80 + "\n\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"# ERROR reading file: {e}\n")

    print(f"✅ Đã xuất toàn bộ code ra file: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_project_code()
