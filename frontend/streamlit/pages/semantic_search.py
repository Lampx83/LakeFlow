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
        "Semantic search: enter question or keywords in natural language, system finds document chunks **semantically similar** to query (based on embedding vectors). "
        "**Score** = cosine similarity (0–1): closer to 1 = more relevant."
    )

    token = st.session_state.token

    qdrant_opts = qdrant_service_options()
    qdrant_labels = [t[0] for t in qdrant_opts]
    qdrant_values = [t[1] for t in qdrant_opts]
    qdrant_idx = st.selectbox(
        "🔗 Qdrant Service",
        range(len(qdrant_labels)),
        format_func=lambda i: qdrant_labels[i],
        key="semantic_qdrant_svc",
        help="Select Qdrant to search. Default: localhost (dev) or lakeflow-qdrant (docker).",
    )
    qdrant_custom = st.text_input(
        "Or enter custom Qdrant address",
        placeholder="http://host:6333 or host:6333",
        key="semantic_qdrant_custom",
        help="If URL entered here, system uses this Qdrant instead of selection above.",
    )
    qdrant_url = normalize_qdrant_url(qdrant_custom) if (qdrant_custom and qdrant_custom.strip()) else qdrant_values[qdrant_idx]

    try:
        collections_resp = list_collections(token, qdrant_url=qdrant_url)
        collections = [c["name"] for c in collections_resp] if collections_resp else ["lakeflow_chunks"]
    except Exception:
        collections = ["lakeflow_chunks"]

    col1, col2, col3 = st.columns(3)

    with col1:
        collection_name = st.selectbox(
            "📦 Collection",
            collections,
            help="Qdrant collection containing embeddings to search.",
        )

    with col2:
        top_k = st.slider(
            "Top K",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of results to return.",
        )

    with col3:
        use_threshold = st.checkbox("Use score threshold", value=False)
        score_threshold = None
        if use_threshold:
            score_threshold = st.slider(
                "Minimum score",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Only show results with score >= this value.",
            )

    query = st.text_area(
        "Query (natural language)",
        placeholder="e.g.: regulations on university admission, enrollment conditions, tuition policy...",
        height=100,
    )

    if st.button("🔍 Search", type="primary"):
        if not query.strip():
            st.warning("Query cannot be empty")
            return

        with st.spinner("Searching..."):
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
                st.error(f"API call error: {exc}")
                return

        results = data.get("results", [])
        st.subheader("📊 Overview")
        st.metric("Results count", len(results))
        if results:
            scores = [r["score"] for r in results]
            st.caption(f"Avg score: {sum(scores) / len(scores):.4f} | Min: {min(scores):.4f} | Max: {max(scores):.4f}")

        if results:
            st.subheader("📋 Results table")
            st.caption("Click each row to see detail below. **text** column truncated to 80 chars.")

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

        if results:
            st.subheader("📄 Result details")
            for idx, r in enumerate(results, start=1):
                title = (
                    f"[{idx}] Score = {r['score']:.4f} | "
                    f"file_hash = {r.get('file_hash') or '—'} | "
                    f"chunk_id = {r.get('chunk_id')}"
                )
                with st.expander(title, expanded=(idx <= 2)):
                    st.caption("**Score** = cosine similarity (0–1). Closer to 1 = more semantically similar to query.")
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
                        st.write("**Content (text)**")
                        text = r.get("text") or "(empty)"
                        st.text_area(
                            "Content",
                            value=text,
                            height=200,
                            key=f"semantic_text_{idx}_{r.get('id', idx)}",
                            disabled=True,
                            label_visibility="collapsed",
                        )
                        st.download_button(
                            "⬇️ Copy / Download content",
                            data=text,
                            file_name=f"chunk_{r.get('file_hash', '')}_{r.get('chunk_id', idx)}.txt",
                            mime="text/plain",
                            key=f"semantic_dl_{idx}_{r.get('id', idx)}",
                        )

        with st.expander("📦 Raw API Response", expanded=False):
            st.json(data)

        if not results:
            st.info("No matching results. Try changing query, increasing Top K or lowering score threshold.")

    else:
        st.info("Enter query and click **Search** to start semantic search.")
