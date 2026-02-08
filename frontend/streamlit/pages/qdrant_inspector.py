# streamlit/pages/qdrant_inspector.py

import pandas as pd
import streamlit as st

from config.settings import qdrant_service_options, normalize_qdrant_url
from state.session import require_login
from services.qdrant_service import (
    list_collections,
    get_collection_detail,
    list_points,
    filter_points,
)

# =====================================================
# CONFIG
# =====================================================

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# =====================================================
# UI
# =====================================================

def render():
    if not require_login():
        return

    st.header("🧠 Qdrant Inspector")
    st.caption("Trình duyệt embeddings (read-only) – phục vụ debug & kiểm tra dữ liệu")

    token = st.session_state.token

    # -------------------------------------------------
    # Qdrant Service
    # -------------------------------------------------
    qdrant_opts = qdrant_service_options()
    qdrant_labels = [t[0] for t in qdrant_opts]
    qdrant_values = [t[1] for t in qdrant_opts]
    qdrant_idx = st.selectbox(
        "🔗 Qdrant Service",
        range(len(qdrant_labels)),
        format_func=lambda i: qdrant_labels[i],
        key="inspector_qdrant_svc",
        help="Chọn Qdrant để inspect. Mặc định: localhost (dev) hoặc eduai-qdrant (docker).",
    )
    qdrant_custom = st.text_input(
        "Hoặc nhập địa chỉ Qdrant tùy chỉnh",
        placeholder="http://host:6333 hoặc host:6333",
        key="inspector_qdrant_custom",
        help="Nếu nhập URL ở đây, hệ thống sẽ dùng Qdrant này thay vì lựa chọn trên.",
    )
    qdrant_url = normalize_qdrant_url(qdrant_custom) if (qdrant_custom and qdrant_custom.strip()) else qdrant_values[qdrant_idx]

    # -------------------------------------------------
    # LOAD COLLECTIONS
    # -------------------------------------------------
    try:
        collections = list_collections(token, qdrant_url=qdrant_url)
    except Exception as exc:
        st.error(f"Không lấy được danh sách collections: {exc}")
        return

    if not collections:
        st.info("Qdrant chưa có collection nào")
        return

    # -------------------------------------------------
    # SELECT COLLECTION
    # -------------------------------------------------
    col = st.selectbox(
        "📦 Collection",
        collections,
        format_func=lambda c: c["name"],
    )

    col_name = col["name"]

    # -------------------------------------------------
    # COLLECTION DETAIL (SOURCE OF TRUTH)
    # -------------------------------------------------
    try:
        detail = get_collection_detail(col_name, token, qdrant_url=qdrant_url)
    except Exception as exc:
        st.error(f"Lỗi khi lấy collection detail: {exc}")
        return

    st.subheader("📊 Collection Overview")
    st.caption(
        "Thông tin tổng quan: **Points** = tổng số vector; **Indexed** = số vector đã index; **Segments** = số segment; "
        "**Vector size** = chiều vector; **Distance** = hàm khoảng cách (Cosine, Euclid, …); **Status** = trạng thái collection."
    )

    points_count = detail.get("points_count", 0)
    indexed_count = detail.get("indexed_vectors_count", 0)
    segments_count = detail.get("segments_count", 0)
    status = detail.get("status", "—")
    coll_name = detail.get("name", col_name)

    vectors = detail.get("vectors", {})
    vector_size = "—"
    distance = "—"
    if isinstance(vectors, dict) and vectors:
        first = next(iter(vectors.values()))
        vector_size = first.get("size", "—")
        distance = first.get("distance", "—")

    st.text(f"📦 {coll_name}  •  Status: {status}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Points", points_count)
    c2.metric("Indexed", indexed_count)
    c3.metric("Segments", segments_count)
    c4.metric("Vector size", vector_size)
    c5.metric("Distance", distance)

    st.subheader("🧱 Payload Schema")
    st.caption(
        "Cấu trúc metadata gắn với mỗi point (key → kiểu dữ liệu). Payload dùng để lọc và hiển thị, không dùng khi tính khoảng cách vector. "
        "Schema được suy ra từ mẫu dữ liệu trong collection."
    )
    st.json(detail.get("payload_schema", {}))

    # =================================================
    # FILTER
    # =================================================
    st.divider()
    st.subheader("🔍 Filter points (payload)")
    st.caption(
        "Lọc points theo metadata (payload). Điền **file_hash**, **section_id** hoặc **chunk_id** rồi bật \"Áp dụng filter\" "
        "để chỉ xem các point thỏa điều kiện; để trống = không lọc theo trường đó."
    )

    f1, f2, f3 = st.columns(3)

    with f1:
        file_hash = st.text_input("file_hash")

    with f2:
        section_id = st.text_input("section_id")

    with f3:
        chunk_id = st.number_input(
            "chunk_id",
            min_value=0,
            step=1,
            value=0,
        )

    use_filter = st.checkbox("Áp dụng filter")

    # =================================================
    # PAGINATION
    # =================================================
    st.divider()
    st.subheader("📄 Browse points")
    st.caption(
        "Duyệt points theo trang: **Số point / trang** = bao nhiêu bản ghi mỗi lần; "
        "**Offset** = bỏ qua bao nhiêu point từ đầu collection rồi mới lấy. "
        "Ví dụ: Offset 0 + 50/trang → trang 1; Offset 50 + 50/trang → trang 2."
    )

    p1, p2 = st.columns(2)

    with p1:
        limit = st.slider(
            "Số point / trang",
            min_value=10,
            max_value=MAX_PAGE_SIZE,
            value=DEFAULT_PAGE_SIZE,
            step=10,
            help="Số point tối đa trả về mỗi lần (kích thước trang).",
        )

    with p2:
        offset = st.number_input(
            "Offset (bỏ qua N point đầu)",
            min_value=0,
            step=limit,
            value=0,
            help="Số point bỏ qua từ đầu collection trước khi lấy. Offset=0 là trang 1, Offset=limit là trang 2, Offset=2×limit là trang 3, ...",
        )

    # -------------------------------------------------
    # LOAD POINTS
    # -------------------------------------------------
    try:
        if use_filter:
            points = filter_points(
                collection=col_name,
                token=token,
                file_hash=file_hash or None,
                section_id=section_id or None,
                chunk_id=chunk_id if chunk_id > 0 else None,
                limit=limit,
                qdrant_url=qdrant_url,
            )
        else:
            points = list_points(
                collection=col_name,
                token=token,
                limit=limit,
                offset=offset,
                qdrant_url=qdrant_url,
            )

    except Exception as exc:
        st.error(f"Lỗi khi load points: {exc}")
        return

    if not points:
        st.info("Không có point nào phù hợp")
        return

    # =================================================
    # TABLE VIEW
    # =================================================
    # Chiều vector lấy từ collection (mọi point trong collection cùng dimension; API không trả vector khi scroll)
    collection_vector_size = None
    if detail.get("vectors"):
        first_vec = next(iter(detail["vectors"].values()), None)
        if first_vec and "size" in first_vec:
            collection_vector_size = first_vec["size"]

    # Thu thập mọi key payload (thứ tự ưu tiên rồi alphabet)
    known_order = ("file_hash", "chunk_id", "section_id", "token_estimate", "text", "content", "source")
    all_keys = set()
    for p in points:
        all_keys.update((p.get("payload") or {}).keys())
    ordered_keys = [k for k in known_order if k in all_keys]
    ordered_keys += sorted(all_keys - set(ordered_keys))

    def _preview(val, max_len=80):
        if val is None:
            return None
        s = str(val)
        return (s[:max_len] + "…") if len(s) > max_len else s

    st.caption(
        "Bảng hiển thị **id**, toàn bộ **payload** (text/content rút gọn 80 ký tự), **vector_dim**. "
        "Chi tiết đầy đủ từng point ở phần bên dưới."
    )
    rows = []
    for p in points:
        payload = p.get("payload") or {}
        row = {"id": p.get("id")}
        for k in ordered_keys:
            v = payload.get(k)
            if k in ("text", "content") and isinstance(v, str):
                row[k] = _preview(v, 80)
            elif isinstance(v, str) and len(v) > 60:
                row[k] = _preview(v, 60)
            else:
                row[k] = v
        row["vector_dim"] = p.get("vector_size") or collection_vector_size
        rows.append(row)

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True)

    # =================================================
    # DETAIL VIEW
    # =================================================
    st.subheader("🔎 Chi tiết point")

    point_ids = [p["id"] for p in points]

    selected_id = st.selectbox(
        "Chọn point",
        point_ids,
        format_func=lambda x: str(x),
    )

    selected_point = next(
        p for p in points if p["id"] == selected_id
    )

    st.text(f"Point ID: {selected_point.get('id')}")
    if selected_point.get("score") is not None:
        st.text(f"Score: {selected_point.get('score')}")

    payload = selected_point.get("payload") or {}
    if payload:
        st.caption("Payload (key → value)")
        for k in sorted(payload.keys()):
            v = payload[k]
            if isinstance(v, str) and len(v) > 200:
                st.text(f"  {k}: {v[:200]}…")
            else:
                st.text(f"  {k}: {v}")

    with st.expander("📌 Payload (JSON)"):
        st.json(payload)

    with st.expander("🧠 Vector info"):
        st.write(f"Vector dimension: {collection_vector_size or selected_point.get('vector_size') or '—'}")

    st.caption("⚠️ Vector raw không được hiển thị để đảm bảo hiệu năng & an toàn")
