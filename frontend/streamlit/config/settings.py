import os
import socket
from pathlib import Path

def _resolve_api_base() -> str:
    base = os.getenv("API_BASE_URL", "http://localhost:8011")
    # Khi chạy dev trên host, "eduai-backend" không resolve → dùng localhost
    if "eduai-backend" in base:
        try:
            socket.gethostbyname("eduai-backend")
        except socket.gaierror:
            base = "http://localhost:8011"
    return base

API_BASE = _resolve_api_base()
EDUAI_MODE = os.getenv("EDUAI_MODE", "DEV")

# Qdrant Service: mặc định khi không chọn (dev = localhost, docker = eduai-qdrant)
QDRANT_DEFAULT_DEV = "http://localhost:6333"
QDRANT_DEFAULT_DOCKER = "http://eduai-qdrant:6333"


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
    value=None = mặc định (backend env). Gồm mặc định + localhost + eduai-qdrant + các service khai báo thêm qua QDRANT_SERVICES.
    """
    default_label = (
        f"Mặc định (localhost:6333)"
        if EDUAI_MODE == "DEV"
        else "Mặc định (eduai-qdrant:6333)"
    )
    base = [
        (default_label, None),
        ("http://localhost:6333", "http://localhost:6333"),
        ("http://eduai-qdrant:6333", "http://eduai-qdrant:6333"),
    ]
    extra = _parse_qdrant_services_env()
    return base + extra

# =========================
# DATA ROOT (CRITICAL)
# =========================
DATA_ROOT = Path(
    os.getenv(
        "EDUAI_DATA_BASE_PATH",
        "/data",   # default cho Docker
    )
).expanduser().resolve()
