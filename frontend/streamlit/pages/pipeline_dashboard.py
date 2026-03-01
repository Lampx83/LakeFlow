# frontend/streamlit/pages/pipeline_dashboard.py
"""
Dashboard of processing status by Data Lake Pipeline.
Shows counts per zone and from catalog.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from config.settings import DATA_ROOT
from utils.sqlite_viewer import copy_db_to_temp
from state.session import require_login
from services.api_client import get_me, admin_list_users, admin_delete_user_messages

# Cache 60s to avoid reading NAS/DB repeatedly
CACHE_TTL = 60

ZONES = {
    "000_inbox": ("000_inbox", "Inbox", "Pending ingest"),
    "100_raw": ("100_raw", "Raw", "Ingested"),
    "200_staging": ("200_staging", "Staging", "Staged"),
    "300_processed": ("300_processed", "Processed", "Processed"),
    "400_embeddings": ("400_embeddings", "Embeddings", "Embedded"),
    "500_catalog": ("500_catalog", "Catalog", "Metadata"),
}


@st.cache_data(ttl=CACHE_TTL)
def _count_inbox_files() -> int:
    """Count files in 000_inbox (one domain level, count per domain)."""
    inbox = DATA_ROOT / "000_inbox"
    if not inbox.exists():
        return 0
    total = 0
    try:
        for d in inbox.iterdir():
            if d.name.startswith(".") or not d.is_dir():
                continue
            for _ in d.iterdir():
                total += 1
                if total > 50_000:  # limit to avoid hang
                    return total
    except (PermissionError, OSError):
        pass
    return total


def _read_catalog_count(table: str) -> int | None:
    """Read COUNT from catalog — copy DB to temp to avoid Errno 35 (resource deadlock)."""
    if table not in ("raw_objects", "ingest_log"):
        return None
    db = DATA_ROOT / "500_catalog" / "catalog.sqlite"
    if not db.exists():
        return None
    temp_path = None
    try:
        temp_path = copy_db_to_temp(db)
        conn = sqlite3.connect(str(temp_path), timeout=5)
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        n = cur.fetchone()[0]
        conn.close()
        return n
    except Exception:
        return None
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


@st.cache_data(ttl=CACHE_TTL)
def _count_raw_objects_catalog() -> int | None:
    """Count records in raw_objects (catalog)."""
    return _read_catalog_count("raw_objects")


@st.cache_data(ttl=CACHE_TTL)
def _count_ingest_log() -> int | None:
    """Count ingest_log records."""
    return _read_catalog_count("ingest_log")


@st.cache_data(ttl=CACHE_TTL)
def _count_zone_dirs(zone_key: str) -> int:
    """
    Count "items" in zone: for 100_raw = file count (domain/hash.ext);
    for 200/300/400 = subdirectory count (domain/hash).
    """
    path = DATA_ROOT / ZONES[zone_key][0]
    if not path.exists():
        return 0
    total = 0
    try:
        for domain in path.iterdir():
            if domain.name.startswith(".") or not domain.is_dir():
                continue
            for _ in domain.iterdir():
                total += 1
                if total > 100_000:
                    return total
    except (PermissionError, OSError):
        pass
    return total


@st.cache_data(ttl=CACHE_TTL)
def _count_raw_files() -> int:
    """Count files in 100_raw (domain/hash.ext)."""
    return _count_zone_dirs("100_raw")


def _get_pipeline_stats() -> dict:
    """Aggregate stats for dashboard."""
    inbox_count = _count_inbox_files()
    raw_catalog = _count_raw_objects_catalog()
    raw_files = _count_raw_files()
    staging_count = _count_zone_dirs("200_staging")
    processed_count = _count_zone_dirs("300_processed")
    embeddings_count = _count_zone_dirs("400_embeddings")
    ingest_log_count = _count_ingest_log()

    return {
        "000_inbox": {"count": inbox_count, "label": "Files pending ingest"},
        "100_raw": {
            "count": raw_files,
            "catalog": raw_catalog,
            "label": "File raw (catalog: " + (str(raw_catalog) if raw_catalog is not None else "—") + ")",
        },
        "200_staging": {"count": staging_count, "label": "Staging dirs"},
        "300_processed": {"count": processed_count, "label": "Processed dirs"},
        "400_embeddings": {"count": embeddings_count, "label": "Embeddings dirs"},
        "500_catalog": {
            "raw_objects": raw_catalog,
            "ingest_log": ingest_log_count,
            "label": "Catalog DB",
        },
    }


def render():
    if not require_login():
        return

    st.header("📊 Dashboard")
    st.caption("Processing status by Data Lake Pipeline step. Data cached 60s.")

    if not DATA_ROOT.exists():
        st.warning(f"Data root does not exist: {DATA_ROOT}")
        return

    if st.button("🔄 Refresh data", help="Clear cache and reload"):
        _count_inbox_files.clear()
        _count_raw_objects_catalog.clear()
        _count_ingest_log.clear()
        _count_zone_dirs.clear()
        _count_raw_files.clear()
        st.rerun()

    try:
        stats = _get_pipeline_stats()
    except Exception as e:
        st.error(f"Error reading stats: {e}")
        return

    st.subheader("Counts by zone")
    cols = st.columns(6)
    zone_order = ["000_inbox", "100_raw", "200_staging", "300_processed", "400_embeddings", "500_catalog"]
    for i, key in enumerate(zone_order):
        zkey, ztitle, _ = ZONES[key]
        with cols[i]:
            s = stats.get(key, {})
            if key == "500_catalog":
                raw_n = s.get("raw_objects")
                log_n = s.get("ingest_log")
                st.metric("Catalog", f"raw: {raw_n if raw_n is not None else '—'}", f"log: {log_n if log_n is not None else '—'}")
            else:
                count = s.get("count", 0)
                st.metric(ztitle, str(count), "")
    st.divider()

    st.subheader("📈 Pipeline flow (chart)")
    pipeline_labels = ["Inbox", "Raw", "Staging", "Processed", "Embeddings"]
    pipeline_counts = [
        stats["000_inbox"]["count"],
        stats["100_raw"]["count"],
        stats["200_staging"]["count"],
        stats["300_processed"]["count"],
        stats["400_embeddings"]["count"],
    ]
    df_pipeline = pd.DataFrame({"Step": pipeline_labels, "Count": pipeline_counts})
    ch1, ch2 = st.columns(2)
    with ch1:
        st.bar_chart(df_pipeline.set_index("Step"), height=280)
    with ch2:
        st.area_chart(df_pipeline.set_index("Step"), height=280)
    st.caption("Inbox → Raw → Staging → Processed → Embeddings → Qdrant")

    st.subheader("📊 Count comparison by zone")
    zone_titles = [ZONES[k][1] for k in zone_order]
    zone_counts = []
    for k in zone_order:
        s = stats.get(k, {})
        if k == "500_catalog":
            zone_counts.append(s.get("raw_objects") or 0)
        else:
            zone_counts.append(s.get("count", 0))
    df_zones = pd.DataFrame({"Zone": zone_titles, "Count": zone_counts})
    st.bar_chart(df_zones.set_index("Zone"), height=300)
    st.divider()

    st.subheader("👤 Q&A message stats")
    st.caption("Message count (Q&A questions) per account. Only admin can delete all messages of a user.")
    token = st.session_state.get("token")
    me = get_me(token) if token else None
    current_username = me.get("username") if me else None
    is_admin = current_username == "admin"
    try:
        users = admin_list_users(token) if token else []
    except Exception as exc:
        st.warning(f"Cannot load user list: {exc}")
        users = []
    if not users:
        st.info("No users with messages in the system yet.")
    else:
        # Bar chart: messages per user
        df_msgs = pd.DataFrame([
            {"User": u.get("username", ""), "Messages": u.get("message_count", 0)}
            for u in users
        ])
        st.bar_chart(df_msgs.set_index("User"), height=260)
        st.markdown("**Details & actions**")
        for u in users:
            username = u.get("username", "")
            count = u.get("message_count", 0)
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.write("**" + username + "**")
            with c2:
                st.metric("Messages", count)
            with c3:
                if is_admin:
                    if st.button("🗑️ Delete all messages", key=f"dashboard_del_{username}", type="secondary"):
                        try:
                            result = admin_delete_user_messages(username, token)
                            st.success(f"Deleted {result.get('deleted_count', 0)} messages for **{username}**.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {e}")
                else:
                    st.caption("(Admin only can delete)")
            st.divider()

    st.caption("Data read from filesystem and 500_catalog/catalog.sqlite. Pipeline Runner runs each step.")
