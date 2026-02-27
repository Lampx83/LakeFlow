# frontend/streamlit/pages/sqlite_viewer.py
"""
SQLite Database Viewer — xem catalog & ingest log (chế độ chỉ đọc).
Truy cập nhanh từ sidebar.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import streamlit as st

from config.settings import DATA_ROOT
from state.session import require_login
from utils.sqlite_viewer import (
    connect_readonly,
    list_tables,
    get_table_schema,
    preview_table,
)


def _sqlite_copy_to_local(db_path: Path) -> Path:
    """
    Copy SQLite file từ NAS sang temp local — tránh disk I/O error trên NFS.
    """
    db_path = Path(db_path).resolve()
    try:
        local_temp_dir = Path(tempfile.gettempdir())
    except Exception:
        local_temp_dir = Path(".").resolve()
    fd, temp_path = tempfile.mkstemp(suffix=".db", dir=local_temp_dir)
    os.close(fd)
    temp_path = Path(temp_path)
    last_err = None
    for attempt in range(3):
        try:
            shutil.copy2(db_path, temp_path)
            if temp_path.stat().st_size != db_path.stat().st_size:
                raise OSError("Copy size mismatch")
            break
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
    else:
        temp_path.unlink(missing_ok=True)
        raise last_err
    return temp_path


def render():
    if not require_login():
        return

    st.header("🗄️ SQLite Database Viewer")
    st.caption(
        "Chế độ chỉ đọc – kiểm tra catalog & ingest log. "
        "DB trong 500_catalog được copy tạm ra ổ local để tránh lỗi I/O trên NAS."
    )

    catalog_path = DATA_ROOT / "500_catalog"
    if not catalog_path.exists():
        st.warning(f"Thư mục Catalog chưa tồn tại: {catalog_path}")
        return

    sqlite_files = [
        p for p in catalog_path.iterdir()
        if p.is_file() and p.suffix.lower() in {".sqlite", ".db"}
    ]

    if not sqlite_files:
        st.info("Không tìm thấy file SQLite (.sqlite / .db) trong 500_catalog.")
        return

    db_file = st.selectbox(
        "🗄️ Chọn database",
        sqlite_files,
        format_func=lambda p: p.name,
    )

    cache_key = "sqlite_viewer_local_copy"
    path_key = "sqlite_viewer_copy_path"
    db_resolved = str(db_file.resolve())
    cached_path = st.session_state.get(cache_key)
    need_copy = (
        cache_key not in st.session_state
        or st.session_state.get(path_key) != db_resolved
        or not (cached_path and isinstance(cached_path, Path) and cached_path.exists())
    )
    if need_copy:
        try:
            local_copy = _sqlite_copy_to_local(db_file)
            st.session_state[cache_key] = local_copy
            st.session_state[path_key] = db_resolved
        except Exception as exc:
            st.error(f"Không đọc được database (copy từ NAS): {exc}")
            return
    local_copy = st.session_state[cache_key]
    if not local_copy.exists():
        st.error("Bản copy tạm không còn tồn tại. Vui lòng chọn lại database.")
        if cache_key in st.session_state:
            del st.session_state[cache_key]
            del st.session_state[path_key]
        return

    try:
        conn = connect_readonly(local_copy)
    except Exception as exc:
        st.error(f"Không mở được database: {exc}")
        return

    try:
        tables = list_tables(conn)
    except Exception as exc:
        st.error(f"Lỗi đọc metadata database: {exc}")
        return

    if not tables:
        st.warning("Database không có bảng nào.")
        return

    table = st.selectbox("📋 Chọn bảng", tables)

    st.markdown("### 🧱 Schema")
    schema_df = get_table_schema(conn, table)
    st.dataframe(schema_df, use_container_width=True)

    st.markdown("### 👁️ Preview dữ liệu")
    limit = st.slider(
        "Số dòng hiển thị",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
    )

    try:
        data_df = preview_table(conn, table, limit)
        st.dataframe(data_df, use_container_width=True)
    except Exception as exc:
        st.error(f"Lỗi đọc dữ liệu bảng: {exc}")
