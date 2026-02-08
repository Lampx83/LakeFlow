# frontend/streamlit/pages/data_lake_explorer.py

from pathlib import Path
import hashlib
import json
import os
import shutil
import tempfile
import time

import streamlit as st

from config.settings import DATA_ROOT
from state.session import require_login
from utils.sqlite_viewer import (
    connect_readonly,
    list_tables,
    get_table_schema,
    preview_table,
)

# File viewer: giới hạn kích thước (tránh treo)
MAX_VIEW_TEXT_BYTES = 10 * 1024 * 1024   # 10 MB cho txt/json/jsonl
MAX_VIEW_NPY_BYTES = 5 * 1024 * 1024     # 5 MB cho npy
MAX_VIEW_PDF_BYTES = 50 * 1024 * 1024    # 50 MB cho pdf
MAX_JSONL_LINES = 500

# =====================================================
# DATA ZONES
# =====================================================

ZONES = {
    "000_inbox": DATA_ROOT / "000_inbox",
    "100_raw": DATA_ROOT / "100_raw",
    "200_staging": DATA_ROOT / "200_staging",
    "300_processed": DATA_ROOT / "300_processed",
    "400_embeddings": DATA_ROOT / "400_embeddings",
    "500_catalog": DATA_ROOT / "500_catalog",
}

MAX_TREE_DEPTH = 30  # Giới hạn độ sâu tránh đệ quy vô hạn
CACHE_TTL_TREE = 90  # Giây cache cho list_dir (NAS chậm)


# =====================================================
# CACHE ĐỌC NAS (giảm lag, tránh đọc lại cùng path)
# =====================================================

@st.cache_data(ttl=CACHE_TTL_TREE)
def _list_dir_cached(path_str: str) -> tuple[list[str], list[tuple[str, int]]]:
    """
    Đọc thư mục từ NAS, trả về (tên thư mục, [(tên file, size)]).
    Dùng thread để không block UI; kết quả được cache.
    """
    path = Path(path_str)
    dirs, files = [], []
    try:
        for p in sorted(path.iterdir()):
            if p.name.startswith("."):
                continue
            if p.is_dir():
                dirs.append(p.name)
            elif p.is_file():
                try:
                    files.append((p.name, p.stat().st_size))
                except OSError:
                    files.append((p.name, 0))
    except (PermissionError, OSError):
        pass
    return (sorted(dirs, key=str.lower), sorted(files, key=lambda x: x[0].lower()))


# =====================================================
# TREE VIEW — LAZY LOADING
# =====================================================

def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _path_to_key(path_str: str) -> str:
    """Tạo key widget duy nhất từ path (tránh trùng khi path dài)."""
    return hashlib.md5(path_str.encode()).hexdigest()[:24]


def render_lazy_tree(
    root: Path,
    zone_name: str,
    expanded_set: set[str],
    depth: int = 0,
) -> None:
    """
    Lazy loading: chỉ gọi _list_dir_cached cho root và các path đã được user bấm mở (trong expanded_set).
    Khi vào trang chỉ load root. Bấm ▶ mới load thư mục con.
    """
    if depth >= MAX_TREE_DEPTH:
        st.caption("… (đạt giới hạn độ sâu)")
        return

    path_str = str(root.resolve())
    try:
        dir_names, file_infos = _list_dir_cached(path_str)
    except Exception as e:
        st.caption(f"⚠️ Lỗi: {e}")
        return

    indent = "　" * depth  # full-width space cho thụt dòng

    # Thư mục con trước: ▶ = chưa mở (bấm để load), ▼ = đã mở (bấm để đóng)
    for d_name in dir_names:
        child_path = root / d_name
        child_str = str(child_path.resolve())
        key_suffix = _path_to_key(child_str)

        if child_str not in expanded_set:
            if st.button(f"{indent}▶ 📁 **{d_name}**", key=f"expand_{zone_name}_{key_suffix}"):
                expanded_set.add(child_str)
                st.rerun()
        else:
            if st.button(f"{indent}▼ 📁 **{d_name}**", key=f"collapse_{zone_name}_{key_suffix}"):
                expanded_set.discard(child_str)
                st.rerun()
            # Đã mở → load và hiển thị nội dung bên trong
            render_lazy_tree(child_path, zone_name, expanded_set, depth + 1)

    # File trong thư mục hiện tại: bấm để xem nội dung
    for f_name, size in file_infos:
        file_path = root / f_name
        file_key = _path_to_key(str(file_path.resolve()))
        if st.button(
            f"{indent}📄 **{f_name}** — {_format_size(size)}",
            key=f"file_{zone_name}_{file_key}",
            help="Bấm để xem nội dung file",
        ):
            st.session_state["datalake_selected_file"] = str(file_path.resolve())
            st.rerun()


def _is_safe_path(file_path: Path, zone_root: Path) -> bool:
    """Đảm bảo file nằm trong zone (tránh path traversal)."""
    try:
        return file_path.resolve().is_relative_to(zone_root.resolve())
    except (ValueError, OSError):
        return False


def render_file_content(file_path: Path) -> None:
    """
    Hiển thị nội dung file theo định dạng: txt, json, jsonl, npy, pdf, csv.
    Giới hạn kích thước để tránh treo.
    """
    if not file_path.is_file():
        st.warning("File không tồn tại hoặc không đọc được.")
        return

    try:
        size = file_path.stat().st_size
    except OSError:
        st.error("Không đọc được thông tin file.")
        return

    suffix = file_path.suffix.lower()

    # ---------- TXT ----------
    if suffix == ".txt":
        if size > MAX_VIEW_TEXT_BYTES:
            st.warning(f"File quá lớn ({size / (1024*1024):.1f} MB). Chỉ hỗ trợ xem file ≤ {MAX_VIEW_TEXT_BYTES // (1024*1024)} MB.")
            _download_button(file_path)
            return
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            st.code(text, language="text")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

    # ---------- JSON ----------
    elif suffix == ".json":
        if size > MAX_VIEW_TEXT_BYTES:
            st.warning(f"File quá lớn. Chỉ hỗ trợ xem file ≤ {MAX_VIEW_TEXT_BYTES // (1024*1024)} MB.")
            _download_button(file_path)
            return
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            st.json(data)
        except Exception as e:
            st.error(f"Lỗi đọc JSON: {e}")

    # ---------- JSONL ----------
    elif suffix == ".jsonl":
        if size > MAX_VIEW_TEXT_BYTES:
            st.warning(f"File quá lớn. Chỉ hiển thị tối đa {MAX_JSONL_LINES} dòng đầu.")
        try:
            lines = []
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f):
                    if i >= MAX_JSONL_LINES:
                        st.caption(f"… Chỉ hiển thị {MAX_JSONL_LINES} dòng đầu. Tổng file có thể nhiều hơn.")
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        lines.append({"raw": line})
            if lines:
                st.dataframe(lines, use_container_width=True)
            else:
                st.info("File rỗng hoặc không có dòng JSON hợp lệ.")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

    # ---------- NPY ----------
    elif suffix == ".npy":
        if size > MAX_VIEW_NPY_BYTES:
            st.warning(f"File quá lớn ({size / (1024*1024):.1f} MB). Chỉ hỗ trợ xem file ≤ {MAX_VIEW_NPY_BYTES // (1024*1024)} MB.")
            _download_button(file_path)
            return
        try:
            import numpy as np
            arr = np.load(file_path, allow_pickle=False)
            st.write("**Shape:**", arr.shape)
            st.write("**Dtype:**", str(arr.dtype))
            if arr.size <= 100:
                st.write("**Dữ liệu:**")
                st.write(arr)
            else:
                st.write("**Mẫu (100 phần tử đầu):**")
                st.write(arr.flat[:100])
        except ImportError:
            st.info("Cần cài `numpy` để xem file .npy. Bạn có thể tải file xuống.")
            _download_button(file_path)
        except Exception as e:
            st.error(f"Lỗi đọc file .npy: {e}")

    # ---------- PDF ----------
    elif suffix == ".pdf":
        if size > MAX_VIEW_PDF_BYTES:
            st.warning(f"File quá lớn. Chỉ hỗ trợ thông tin file ≤ {MAX_VIEW_PDF_BYTES // (1024*1024)} MB.")
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            n_pages = len(reader.pages)
            st.write(f"**Số trang:** {n_pages}")
            _download_button(file_path)
        except ImportError:
            st.info("Cần cài `pypdf` để xem thông tin PDF. Bạn có thể tải file xuống.")
            _download_button(file_path)
        except Exception as e:
            st.error(f"Lỗi đọc PDF: {e}")
            _download_button(file_path)

    # ---------- CSV ----------
    elif suffix == ".csv":
        if size > MAX_VIEW_TEXT_BYTES:
            st.warning(f"File quá lớn. Chỉ hiển thị một phần.")
        try:
            import pandas as pd
            df = pd.read_csv(file_path, nrows=1000, encoding="utf-8", on_bad_lines="skip")
            st.dataframe(df, use_container_width=True)
            if size > 1024 * 1024:
                st.caption("Chỉ hiển thị 1000 dòng đầu.")
        except ImportError:
            st.info("Cần cài `pandas` để xem CSV. Bạn có thể tải file xuống.")
            _download_button(file_path)
        except Exception as e:
            st.error(f"Lỗi đọc CSV: {e}")

    # ---------- Khác ----------
    else:
        st.info(f"Định dạng `{suffix}` chưa hỗ trợ xem trực tiếp. Bạn có thể tải file xuống.")
        _download_button(file_path)


def _download_button(file_path: Path) -> None:
    try:
        data = file_path.read_bytes()
        st.download_button(
            "⬇️ Tải file xuống",
            data=data,
            file_name=file_path.name,
            mime="application/octet-stream",
            key=f"dl_{hashlib.md5(str(file_path).encode()).hexdigest()[:16]}",
        )
    except Exception:
        pass


def _sqlite_copy_to_local(db_path: Path) -> Path:
    """
    Copy SQLite file từ NAS sang temp local — tránh disk I/O error trên NFS.
    Retry khi đọc từ NAS; ghi vào thư mục tạm của process (local).
    """
    db_path = Path(db_path).resolve()
    # Dùng thư mục tạm trong thư mục hiện tại nếu có (thường là local), kẻo /tmp trên một số môi trường vẫn là mount
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


def render_sqlite_viewer(zone_path: Path) -> None:
    """
    SQLite viewer (chỉ cho 500_catalog).
    Copy DB sang file tạm local trước khi mở để tránh lỗi disk I/O trên NAS/NFS.
    """
    sqlite_files = [
        p for p in zone_path.iterdir()
        if p.is_file() and p.suffix in {".sqlite", ".db"}
    ]

    if not sqlite_files:
        st.info("Không tìm thấy SQLite database trong 500_catalog")
        return

    st.divider()
    st.subheader("📊 SQLite Database Viewer")
    st.caption("Chế độ chỉ đọc – phục vụ kiểm tra catalog & ingest log. DB được copy tạm ra ổ local để tránh lỗi I/O trên NAS.")

    db_file = st.selectbox(
        "🗄️ Chọn database",
        sqlite_files,
        format_func=lambda p: p.name,
    )

    # Cache bản copy local theo path DB đã chọn; chỉ dùng lại nếu file tạm còn tồn tại
    cache_key = "sqlite_local_copy"
    path_key = "sqlite_local_copy_path"
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
        st.warning("Database không có bảng nào")
        return

    table = st.selectbox("📋 Chọn bảng", tables)

    # ---------- Schema ----------
    st.markdown("### 🧱 Schema")
    schema_df = get_table_schema(conn, table)
    st.dataframe(schema_df, use_container_width=True)

    # ---------- Data preview ----------
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


# =====================================================
# MAIN PAGE
# =====================================================

def render():
    if not require_login():
        return

    st.header("🗂️ Data Lake Explorer")

    # --------------------------------------------------
    # SELECT ZONE
    # --------------------------------------------------
    zone_name = st.selectbox(
        "📂 Chọn data zone",
        list(ZONES.keys()),
    )

    zone_path = ZONES[zone_name]

    if not zone_path.exists():
        st.warning(f"Zone chưa tồn tại: {zone_path}")
        return

    st.subheader(f"📁 {zone_name}")

    # --------------------------------------------------
    # TREE VIEW — LAZY: chỉ load root khi vào; bấm ▶ mới load thư mục con
    # --------------------------------------------------
    if "datalake_expanded" not in st.session_state:
        st.session_state.datalake_expanded = {}
    expanded_set = st.session_state.datalake_expanded.setdefault(zone_name, set())

    with st.spinner("Đang tải..."):
        render_lazy_tree(zone_path, zone_name, expanded_set)

    # --------------------------------------------------
    # FILE CONTENT VIEWER (khi bấm vào 1 file trong cây)
    # --------------------------------------------------
    selected = st.session_state.get("datalake_selected_file")
    if selected:
        sel_path = Path(selected)
        if sel_path.is_file() and _is_safe_path(sel_path, zone_path):
            st.divider()
            st.subheader(f"📄 Nội dung file: `{sel_path.name}`")
            if st.button("✕ Đóng xem file", key="datalake_close_file"):
                del st.session_state["datalake_selected_file"]
                st.rerun()
            render_file_content(sel_path)
        else:
            # File không còn tồn tại hoặc không thuộc zone → xóa lựa chọn
            if "datalake_selected_file" in st.session_state:
                del st.session_state["datalake_selected_file"]

    # --------------------------------------------------
    # SQLITE VIEWER (ONLY 500_catalog)
    # --------------------------------------------------
    if zone_name == "500_catalog":
        render_sqlite_viewer(zone_path)
