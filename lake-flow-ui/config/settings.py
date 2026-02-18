import os
import socket
from pathlib import Path

def _resolve_api_base() -> str:
    base = os.getenv("API_BASE_URL", "http://localhost:8011").strip()
    # Tên service cũ (eduai-backend) không còn — chuẩn hóa sang lakeflow-backend khi chạy Docker
    if base and "eduai-backend" in base:
        base = base.replace("eduai-backend", "lakeflow-backend")
    # Khi chạy dev trên host, "lakeflow-backend" không resolve → dùng localhost
    if base and "lakeflow-backend" in base:
        try:
            socket.gethostbyname("lakeflow-backend")
        except socket.gaierror:
            base = "http://localhost:8011"
    return base or "http://localhost:8011"

API_BASE = _resolve_api_base()
LAKEFLOW_MODE = os.getenv("LAKEFLOW_MODE", "DEV")

# Qdrant Service: mặc định khi không chọn (dev = localhost, docker = lakeflow-qdrant)
QDRANT_DEFAULT_DEV = "http://localhost:6333"
QDRANT_DEFAULT_DOCKER = "http://lakeflow-qdrant:6333"


def _parse_qdrant_services_env() -> list[tuple[str, str]]:
    """
    Đọc Qdrant services bổ sung từ env QDRANT_SERVICES.
    Format: URL hoặc "Nhãn|URL", nhiều service cách nhau bằng dấu phẩy.
    VD: QDRANT_SERVICES="http://qdrant-remote:6333, Production|https://qdrant.prod.example.com:6333"
    """
    raw = os.getenv("QDRANT_SERVICES", "").strip()
    if not raw:
        return []
    out = []
    seen_urls = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "|" in part:
            label, url = part.split("|", 1)
            label, url = label.strip(), url.strip()
        else:
            label = part
            url = part
        if not url:
            continue
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        if url in seen_urls:
            continue
        seen_urls.add(url)
        out.append((label, url))
    return out


def normalize_qdrant_url(url: str | None) -> str | None:
    """
    Chuẩn hóa URL Qdrant nhập tay: bỏ khoảng trắng thừa, thêm http:// nếu chưa có scheme.
    Trả về None nếu url rỗng.
    """
    if not url or not url.strip():
        return None
    u = url.strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        u = f"http://{u}"
    return u


def qdrant_service_options():
    """
    Danh sách (label, value) cho dropdown Qdrant Service.
    value=None = mặc định (backend env). Gồm mặc định + localhost + lakeflow-qdrant + các service khai báo thêm qua QDRANT_SERVICES.
    """
    default_label = (
        f"Mặc định (localhost:6333)"
        if LAKEFLOW_MODE == "DEV"
        else "Mặc định (lakeflow-qdrant:6333)"
    )
    base = [
        (default_label, None),
        ("http://localhost:6333", "http://localhost:6333"),
        ("http://lakeflow-qdrant:6333", "http://lakeflow-qdrant:6333"),
    ]
    extra = _parse_qdrant_services_env()
    return base + extra

# =========================
# DATA ROOT (CRITICAL)
# =========================
DATA_ROOT = Path(
    os.getenv(
        "LAKEFLOW_DATA_BASE_PATH",
        "/data",   # default cho Docker
    )
).expanduser().resolve()

# Mô tả mount (hiển thị trong System Settings khi chạy Docker)
LAKEFLOW_MOUNT_DESCRIPTION = os.getenv("LAKEFLOW_MOUNT_DESCRIPTION", "").strip()


def is_running_in_docker() -> bool:
    """Kiểm tra có đang chạy trong container Docker hay không."""
    return Path("/.dockerenv").exists()
