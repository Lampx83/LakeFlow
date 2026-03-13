import os
import socket
from pathlib import Path

def _resolve_api_base() -> str:
    base = os.getenv("API_BASE_URL", "http://localhost:8011").strip()
    # Old service name (eduai-backend) deprecated — normalize to lakeflow-backend when running Docker
    if base and "eduai-backend" in base:
        base = base.replace("eduai-backend", "lakeflow-backend")
    # When running dev on host, "lakeflow-backend" does not resolve → use localhost
    if base and "lakeflow-backend" in base:
        try:
            socket.gethostbyname("lakeflow-backend")
        except socket.gaierror:
            base = "http://localhost:8011"
    return base or "http://localhost:8011"

API_BASE = _resolve_api_base()
LAKEFLOW_MODE = os.getenv("LAKEFLOW_MODE", "DEV")

# Qdrant Service: default when not selected (dev = localhost, docker = lakeflow-qdrant)
QDRANT_DEFAULT_DEV = "http://localhost:6333"
QDRANT_DEFAULT_DOCKER = "http://lakeflow-qdrant:6333"


def _parse_qdrant_services_env() -> list[tuple[str, str]]:
    """
    Read additional Qdrant services from env QDRANT_SERVICES.
    Format: URL or "Label|URL", multiple services separated by comma.
    Example: QDRANT_SERVICES="http://qdrant-remote:6333, Production|https://qdrant.prod.example.com:6333"
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
    Normalize manually entered Qdrant URL: trim whitespace, add http:// if no scheme.
    Returns None if url is empty.
    """
    if not url or not url.strip():
        return None
    u = url.strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        u = f"http://{u}"
    return u


def qdrant_service_options():
    """
    List of (label, value) for Qdrant Service dropdown.
    value=None = default (backend env). Includes default + localhost + lakeflow-qdrant + services from QDRANT_SERVICES.
    """
    default_label = (
        "Default (localhost:6333)"
        if LAKEFLOW_MODE == "DEV"
        else "Default (lakeflow-qdrant:6333)"
    )
    base = [
        (default_label, None),
        ("http://localhost:6333", "http://localhost:6333"),
        ("http://lakeflow-qdrant:6333", "http://lakeflow-qdrant:6333"),
    ]
    extra = _parse_qdrant_services_env()
    return base + extra


DATA_ROOT = Path(
    os.getenv(
        "LAKE_ROOT",
        "/data",   # default for Docker
    )
).expanduser().resolve()

# Mount description (shown in System Settings when running Docker)
LAKEFLOW_MOUNT_DESCRIPTION = os.getenv("LAKEFLOW_MOUNT_DESCRIPTION", "").strip()


def is_running_in_docker() -> bool:
    """Check if running inside a Docker container."""
    return Path("/.dockerenv").exists()
