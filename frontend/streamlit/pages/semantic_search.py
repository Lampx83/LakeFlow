# streamlit/pages/semantic_search.py

import pandas as pd
import streamlit as st

from config.settings import qdrant_service_options, normalize_qdrant_url
from services.api_client import semantic_search
from services.qdrant_service import list_collections
from state.session import require_login


def render():
    if not require_login():
        return

    st.header("🔎 Semantic Search")
    st.caption(
        "Tìm kiếm theo nghĩa (semantic): nhập câu hỏi hoặc từ khóa bằng ngôn ngữ tự nhiên, hệ thống sẽ tìm các đoạn tài liệu **tương đồng về nghĩa** với query (dựa trên embedding vector). "
        "**Score** = độ tương đồng cosine (0–1): càng gần 1 càng liên quan."
    )

    token = st.session_state.token

    # --------------------------------------------------
    # Qdrant Service + Collection + PARAMS
    # --------------------------------------------------
    qdrant_opts = qdrant_service_options()
    qdrant_labels = [t[0] for t in qdrant_opts]
    qdrant_values = [t[1] for t in qdrant_opts]
    qdrant_idx = st.selectbox(
        "🔗 Qdrant Service",
        range(len(qdrant_labels)),
        format_func=lambda i: qdrant_labels[i],
        key="semantic_qdrant_svc",
        help="Chọn Qdrant để tìm kiếm. Mặc định: localhost (dev) hoặc eduai-qdrant (docker).",
    )
    qdrant_custom = st.text_input(
        "Hoặc nhập địa chỉ Qdrant tùy chỉnh",
        placeholder="http://host:6333 hoặc host:6333",
        key="semantic_qdrant_custom",
        help="Nếu nhập URL ở đây, hệ thống sẽ dùng Qdrant này thay vì lựa chọn trên.",
    )
    qdrant_url = normalize_qdrant_url(qdrant_custom) if (qdrant_custom and qdrant_custom.strip()) else qdrant_values[qdrant_idx]

    try:
        collections_resp = list_collections(token, qdrant_url=qdrant_url)
        collections = [c["name"] for c in collections_resp] if collections_resp else ["eduai_chunks"]
    except Exception:
        collections = ["eduai_chunks"]

    col1, col2, col3 = st.columns(3)

    with col1:
        collection_name = st.selectbox(
            "📦 Collection",
            collections,
            help="Collection Qdrant chứa embeddings để tìm kiếm.",
        )

    with col2:
        top_k = st.slider(
            "Top K",
            min_value=1,
            max_value=50,
            value=10,
            help="Số lượng kết quả tối đa trả về.",
        )

    with col3:
        use_threshold = st.checkbox("Dùng ngưỡng điểm (score threshold)", value=False)
        score_threshold = None
        if use_threshold:
            score_threshold = st.slider(
                "Score tối thiểu",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Chỉ hiển thị kết quả có score >= giá trị này.",
            )

    query = st.text_area(
        "Query (ngôn ngữ tự nhiên)",
        placeholder="Ví dụ: quy định về kinh tế quốc dân, điều kiện tuyển sinh, chính sách học phí...",
        height=100,
    )

    if st.button("🔍 Search", type="primary"):
        if not query.strip():
            st.warning("Query không được để trống")
            return

        with st.spinner("Đang tìm kiếm..."):
            try:
                data = semantic_search(
                    query=query.strip(),
                    top_k=top_k,
                    token=token,
                    collection_name=collection_name or None,
                    qdrant_url=qdrant_url,
                    score_threshold=score_threshold,
                )
            except Exception as exc:
                st.error(f"Lỗi khi gọi API: {exc}")
                return

        # ---------- Summary ----------
        results = data.get("results", [])
        st.subheader("📊 Tổng quan")
        st.metric("Số kết quả", len(results))
        if results:
            scores = [r["score"] for r in results]
            st.caption(f"Score trung bình: {sum(scores) / len(scores):.4f} | Min: {min(scores):.4f} | Max: {max(scores):.4f}")

        # ---------- Table view ----------
        if results:
            st.subheader("📋 Bảng kết quả")
            st.caption("Bấm vào từng dòng để xem chi tiết bên dưới. Cột **text** rút gọn 80 ký tự.")

            rows = []
            for idx, r in enumerate(results, start=1):
                text = r.get("text") or ""
                text_preview = (text[:80] + "…") if len(text) > 80 else text
                rows.append({
                    "#": idx,
                    "score": round(r["score"], 4),
                    "file_hash": r.get("file_hash"),
                    "chunk_id": r.get("chunk_id"),
                    "section_id": r.get("section_id"),
                    "text": text_preview,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

        # ---------- Detail cards ----------
        if results:
            st.subheader("📄 Chi tiết từng kết quả")
            for idx, r in enumerate(results, start=1):
                title = (
                    f"[{idx}] Score = {r['score']:.4f} | "
                    f"file_hash = {r.get('file_hash') or '—'} | "
                    f"chunk_id = {r.get('chunk_id')}"
                )
                with st.expander(title, expanded=(idx <= 2)):
                    st.caption("**Score** = độ tương đồng cosine (0–1). Càng gần 1 càng giống nghĩa với query.")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Metadata**")
                        st.write(f"- file_hash: `{r.get('file_hash') or '—'}`")
                        st.write(f"- chunk_id: `{r.get('chunk_id')}`")
                        st.write(f"- section_id: `{r.get('section_id') or '—'}`")
                        st.write(f"- token_estimate: `{r.get('token_estimate') or '—'}`")
                        st.write(f"- source: `{r.get('source') or '—'}`")
                        if r.get("id"):
                            st.write(f"- point id: `{r.get('id')}`")
                    with c2:
                        st.write("**Nội dung (text)**")
                        text = r.get("text") or "(trống)"
                        st.text_area(
                            "Nội dung",
                            value=text,
                            height=200,
                            key=f"semantic_text_{idx}_{r.get('id', idx)}",
                            disabled=True,
                            label_visibility="collapsed",
                        )
                        st.download_button(
                            "⬇️ Copy / Tải nội dung",
                            data=text,
                            file_name=f"chunk_{r.get('file_hash', '')}_{r.get('chunk_id', idx)}.txt",
                            mime="text/plain",
                            key=f"semantic_dl_{idx}_{r.get('id', idx)}",
                        )

        # ---------- Raw response (collapsed) ----------
        with st.expander("📦 Raw API Response", expanded=False):
            st.json(data)

        if not results:
            st.info("Không có kết quả phù hợp. Thử đổi query, tăng Top K hoặc giảm score threshold.")

    else:
        st.info("Nhập query và bấm **Search** để bắt đầu tìm kiếm theo nghĩa.")
