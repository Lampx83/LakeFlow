import os
from pathlib import Path
import requests
import streamlit as st

from config.settings import (
    API_BASE,
    LAKEFLOW_MODE,
    DATA_ROOT,
    QDRANT_DEFAULT_DEV,
    QDRANT_DEFAULT_DOCKER,
    is_running_in_docker,
    LAKEFLOW_MOUNT_DESCRIPTION,
)
from state.session import require_login


# ======================================================
# CONFIG
# ======================================================

REQUIRED_ZONES = [
    "000_inbox",
    "100_raw",
    "200_staging",
    "300_processed",
    "400_embeddings",
    "500_catalog",
]

# Chỉ dùng cho PROD
PROD_DATA_PATHS = {
    "Giáo dục – Đào tạo": "/data/education",
    "Nghiên cứu": "/data/research",
    "Thử nghiệm": "/data/test",
}


# ======================================================
# API CLIENT
# ======================================================

def api_get_data_path(token: str) -> str | None:
    resp = requests.get(
        f"{API_BASE}/system/data-path",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("data_base_path")


def api_set_data_path(path: str, token: str) -> None:
    resp = requests.post(
        f"{API_BASE}/system/data-path",
        json={"path": path},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()


# ======================================================
# LOCAL VALIDATION
# ======================================================

def validate_local_path(path: str) -> tuple[bool, str]:
    try:
        p = Path(path).expanduser().resolve()
    except Exception as exc:
        return False, f"Path không hợp lệ: {exc}"

    if not p.exists():
        return False, "Path không tồn tại"

    if not p.is_dir():
        return False, "Path không phải thư mục"

    missing = [z for z in REQUIRED_ZONES if not (p / z).exists()]
    if missing:
        return False, f"Thiếu các thư mục bắt buộc: {', '.join(missing)}"

    return True, ""


# ======================================================
# UI
# ======================================================

def render():
    if not require_login():
        return

    st.header("⚙️ System Settings")
    st.caption("Cấu hình hệ thống – Data Lake & Runtime")

    token = st.session_state.token

    # --------------------------------------------------
    # QDRANT CONFIG (thông tin)
    # --------------------------------------------------
    st.subheader("🔗 Qdrant")
    default_qdrant = QDRANT_DEFAULT_DOCKER if is_running_in_docker() else QDRANT_DEFAULT_DEV
    st.info(
        f"**Mặc định truy cập:** `{default_qdrant}`\n\n"
        "Người dùng có thể chọn Qdrant khác tại từng trang: **Semantic Search**, **Qdrant Inspector** "
        "(dropdown « Qdrant Service » hoặc nhập URL tùy chỉnh)."
    )

    st.divider()

    # --------------------------------------------------
    # CURRENT DATA PATH + DOCKER MOUNT
    # --------------------------------------------------
    st.subheader("📂 Data Lake hiện tại")
    try:
        current_path = api_get_data_path(token)
    except Exception as exc:
        st.error(f"Không lấy được data path hiện tại: {exc}")
        return

    if current_path:
        st.code(current_path)
        if is_running_in_docker():
            mount_note = (
                LAKEFLOW_MOUNT_DESCRIPTION
                if LAKEFLOW_MOUNT_DESCRIPTION
                else "Khi chạy Docker: path này là mount point trong container (thường /data). "
                "Volume tương ứng được cấu hình trong docker-compose (bind mount từ host hoặc volume)."
            )
            st.caption(f"📌 {mount_note}")
    else:
        st.warning("Chưa cấu hình Data Lake path")

    st.divider()

    # --------------------------------------------------
    # CONFIGURE DATA PATH
    # --------------------------------------------------
    st.subheader("🔧 Cấu hình Data Lake Path")

    selected_path: str | None = None

    # ---------- DEV MODE ----------
    if LAKEFLOW_MODE == "DEV":
        st.info("DEV mode: cho phép nhập Data Lake path bất kỳ")

        _default_path = (current_path or str(DATA_ROOT)).strip() or ""
        _key = "system_settings_data_path"
        if _key not in st.session_state:
            st.session_state[_key] = _default_path
        selected_path = st.text_input(
            "Nhập Data Lake root path",
            key=_key,
            placeholder="/Users/mac/Library/CloudStorage/...",
        )

    # ---------- PROD MODE ----------
    else:
        st.warning("PROD mode: chỉ admin được phép, chỉ chọn từ danh sách")

        label = st.selectbox(
            "Chọn Data Lake",
            list(PROD_DATA_PATHS.keys()),
        )
        selected_path = PROD_DATA_PATHS[label]

        st.code(selected_path)

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------
    if selected_path:
        is_valid, error = validate_local_path(selected_path)

        if is_valid:
            st.success("✔️ Cấu trúc Data Lake hợp lệ")
        else:
            st.error(f"❌ {error}")

    # --------------------------------------------------
    # APPLY
    # --------------------------------------------------
    if st.button("💾 Apply Configuration", use_container_width=True):
        if not selected_path:
            st.warning("Chưa chọn Data Lake path")
            return

        ok, error = validate_local_path(selected_path)
        if not ok:
            st.error(f"Không thể áp dụng: {error}")
            return

        try:
            api_set_data_path(selected_path, token)
            st.success("✅ Đã cập nhật Data Lake path")
            st.rerun()
        except requests.HTTPError as exc:
            st.error(f"Lỗi từ backend: {exc.response.text}")
        except Exception as exc:
            st.error(f"Lỗi không xác định: {exc}")
