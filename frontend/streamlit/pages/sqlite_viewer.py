# frontend/streamlit/pages/sqlite_viewer.py
"""
SQLite Database Viewer — view catalog & ingest log (read-only).
Quick access from sidebar.
"""

from pathlib import Path

import streamlit as st

from config.settings import DATA_ROOT
from state.session import require_login
from utils.sqlite_viewer import (
    connect_readonly,
    copy_db_to_temp,
    list_tables,
    get_table_schema,
    preview_table,
)


def render():
    if not require_login():
        return

    st.header("🗄️ SQLite Database Viewer")
    st.caption(
        "Read-only mode – inspect catalog & ingest log. "
        "DB in 500_catalog is copied to local temp to avoid I/O errors on NAS."
    )

    catalog_path = DATA_ROOT / "500_catalog"
    if not catalog_path.exists():
        st.warning(f"Catalog directory does not exist: {catalog_path}")
        return

    sqlite_files = [
        p for p in catalog_path.iterdir()
        if p.is_file() and p.suffix.lower() in {".sqlite", ".db"}
    ]

    if not sqlite_files:
        st.info("No SQLite file (.sqlite / .db) found in 500_catalog.")
        return

    db_file = st.selectbox(
        "🗄️ Select database",
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
            local_copy = copy_db_to_temp(db_file)
            st.session_state[cache_key] = local_copy
            st.session_state[path_key] = db_resolved
        except Exception as exc:
            st.error(f"Cannot read database (copy from NAS): {exc}")
            return
    local_copy = st.session_state[cache_key]
    if not local_copy.exists():
        st.error("Temporary copy no longer exists. Please select database again.")
        if cache_key in st.session_state:
            del st.session_state[cache_key]
            del st.session_state[path_key]
        return

    try:
        conn = connect_readonly(local_copy)
    except Exception as exc:
        st.error(f"Cannot open database: {exc}")
        return

    try:
        tables = list_tables(conn)
    except Exception as exc:
        st.error(f"Error reading database metadata: {exc}")
        return

    if not tables:
        st.warning("Database has no tables.")
        return

    table = st.selectbox("📋 Select table", tables)

    st.markdown("### 🧱 Schema")
    schema_df = get_table_schema(conn, table)
    st.dataframe(schema_df, use_container_width=True)

    st.markdown("### 👁️ Data preview")
    limit = st.slider(
        "Rows to display",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
    )

    try:
        data_df = preview_table(conn, table, limit)
        st.dataframe(data_df, use_container_width=True)
    except Exception as exc:
        st.error(f"Error reading table data: {exc}")
