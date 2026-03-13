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

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def render():
    if not require_login():
        return

    st.header("🧠 Qdrant Inspector")
    st.caption("Embedding browser (read-only) – for debugging & data inspection")

    token = st.session_state.token

    qdrant_opts = qdrant_service_options()
    qdrant_labels = [t[0] for t in qdrant_opts]
    qdrant_values = [t[1] for t in qdrant_opts]
    qdrant_idx = st.selectbox(
        "🔗 Qdrant Service",
        range(len(qdrant_labels)),
        format_func=lambda i: qdrant_labels[i],
        key="inspector_qdrant_svc",
        help="Select Qdrant to inspect. Default: localhost (dev) or lakeflow-qdrant (docker).",
    )
    qdrant_custom = st.text_input(
        "Or enter custom Qdrant address",
        placeholder="http://host:6333 or host:6333",
        key="inspector_qdrant_custom",
        help="If URL entered here, system uses this Qdrant instead of selection above.",
    )
    qdrant_url = normalize_qdrant_url(qdrant_custom) if (qdrant_custom and qdrant_custom.strip()) else qdrant_values[qdrant_idx]

    try:
        collections = list_collections(token, qdrant_url=qdrant_url)
    except Exception as exc:
        st.error(f"Failed to load collections list: {exc}")
        return

    if not collections:
        st.info("Qdrant has no collections yet")
        return

    col = st.selectbox(
        "📦 Collection",
        collections,
        format_func=lambda c: c["name"],
    )

    col_name = col["name"]

    try:
        detail = get_collection_detail(col_name, token, qdrant_url=qdrant_url)
    except Exception as exc:
        st.error(f"Error loading collection detail: {exc}")
        return

    st.subheader("📊 Collection Overview")
    st.caption(
        "Overview: **Points** = total vectors; **Indexed** = indexed vectors; **Segments** = segment count; "
        "**Vector size** = vector dimension; **Distance** = distance function (Cosine, Euclid, …); **Status** = collection status."
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
        "Metadata structure attached to each point (key → data type). Payload used for filtering and display, not for vector distance. "
        "Schema inferred from sample data in collection."
    )
    st.json(detail.get("payload_schema", {}))

    st.divider()
    st.subheader("🔍 Filter points (payload)")
    st.caption(
        "Filter points by metadata (payload). Fill **file_hash**, **section_id** or **chunk_id** then enable \"Apply filter\" "
        "to view only matching points; empty = no filter for that field."
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

    use_filter = st.checkbox("Apply filter")

    st.divider()
    st.subheader("📄 Browse points")
    st.caption(
        "Browse points by page: **Points per page** = records per load; "
        "**Offset** = how many points to skip from start before fetching. "
        "e.g.: Offset 0 + 50/page → page 1; Offset 50 + 50/page → page 2."
    )

    p1, p2 = st.columns(2)

    with p1:
        limit = st.slider(
            "Points per page",
            min_value=10,
            max_value=MAX_PAGE_SIZE,
            value=DEFAULT_PAGE_SIZE,
            step=10,
            help="Max points returned per request (page size).",
        )

    with p2:
        offset = st.number_input(
            "Offset (skip N points from start)",
            min_value=0,
            step=limit,
            value=0,
            help="Points to skip from start of collection before fetching. Offset=0 is page 1, Offset=limit is page 2, Offset=2×limit is page 3, ...",
        )

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
        st.error(f"Error loading points: {exc}")
        return

    if not points:
        st.info("No matching points")
        return

    collection_vector_size = None
    if detail.get("vectors"):
        first_vec = next(iter(detail["vectors"].values()), None)
        if first_vec and "size" in first_vec:
            collection_vector_size = first_vec["size"]

    # Collect all payload keys (priority order then alphabet)
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
        "Table shows **id**, full **payload** (text/content truncated to 80 chars), **vector_dim**. "
        "Full detail per point below."
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

    st.subheader("🔎 Point detail")

    point_ids = [p["id"] for p in points]

    selected_id = st.selectbox(
        "Select point",
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

    st.caption("⚠️ Raw vector not displayed for performance & safety")
