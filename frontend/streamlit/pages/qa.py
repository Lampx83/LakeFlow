# streamlit/pages/qa.py

import pandas as pd
import streamlit as st

from config.settings import qdrant_service_options, normalize_qdrant_url
from services.api_client import qa
from services.qdrant_service import list_collections
from state.session import require_login


def render():
    if not require_login():
        return

    token = st.session_state.token

    st.header("🤖 Q&A with AI")
    st.caption(
        "**Demo RAG:** This feature demos RAG (Retrieval-Augmented Generation). "
        "The system (1) finds relevant document passages (semantic search), (2) sends them as context to the AI, "
        "(3) AI **answers only based on the provided context** — no external knowledge. "
        "If context is insufficient, the AI will clearly state there is no information. Answers in Vietnamese."
    )

    # --------------------------------------------------
    # Qdrant Service + PARAMS
    # --------------------------------------------------
    qdrant_opts = qdrant_service_options()
    qdrant_labels = [t[0] for t in qdrant_opts]
    qdrant_values = [t[1] for t in qdrant_opts]
    qdrant_idx = st.selectbox(
        "🔗 Qdrant Service",
        range(len(qdrant_labels)),
        format_func=lambda i: qdrant_labels[i],
        key="qa_qdrant_svc",
        help="Select Qdrant for context lookup. Default: localhost (dev) or lakeflow-qdrant (docker).",
    )
    qdrant_custom = st.text_input(
        "Or enter custom Qdrant address",
        placeholder="http://host:6333 or host:6333",
        key="qa_qdrant_custom",
        help="If you enter a URL here, the system will use this Qdrant instead of the selection above.",
    )
    qdrant_url = normalize_qdrant_url(qdrant_custom) if (qdrant_custom and qdrant_custom.strip()) else qdrant_values[qdrant_idx]

    try:
        collections_resp = list_collections(token, qdrant_url=qdrant_url)
        collections = [c["name"] for c in collections_resp] if collections_resp else ["lakeflow_chunks"]
    except Exception:
        collections = ["lakeflow_chunks"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        collection_name = st.selectbox(
            "📦 Collection",
            collections,
            help="Qdrant collection containing embeddings for context lookup.",
        )

    with col2:
        top_k = st.slider(
            "Context count (Top K)",
            min_value=1,
            max_value=20,
            value=5,
            help="Max document passages to send as context to the LLM.",
        )

    with col3:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="0 = precise, 2 = more creative.",
        )

    with col4:
        use_threshold = st.checkbox("Context score threshold", value=False)
        score_threshold = None
        if use_threshold:
            score_threshold = st.slider(
                "Min score",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                key="qa_score_threshold",
            )

    question = st.text_area(
        "Your question",
        placeholder="E.g.: Regulations on economics? Admission requirements? Tuition policy?",
        height=120,
        key="qa_question",
    )

    data_to_show = None
    if st.button("🔍 Ask AI", type="primary"):
        if not question.strip():
            st.warning("Please enter a question")
        else:
            with st.spinner("Finding context and calling LLM..."):
                try:
                    data = qa(
                        question=question.strip(),
                        top_k=top_k,
                        temperature=temperature,
                        token=token,
                        collection_name=collection_name or None,
                        score_threshold=score_threshold,
                        qdrant_url=qdrant_url,
                    )
                    st.session_state.qa_last_result = data
                    st.session_state.qa_last_question = question.strip()
                    st.session_state.qa_feedback = None
                    data_to_show = data
                except Exception as exc:
                    err_msg = str(exc)
                    st.error(f"API error: {err_msg}")
                    if "Curl to test:" in err_msg or "Curl that ran:" in err_msg:
                        sep = "Curl to test:" if "Curl to test:" in err_msg else "Curl that ran:"
                        parts = err_msg.split(sep, 1)
                        if len(parts) > 1:
                            curl_part = parts[1].split("\n\nError:")[0].split("\n\nNo matching")[0].strip()
                            with st.expander("📋 Curl command (copy to test)"):
                                st.code(curl_part, language="bash")

    if data_to_show is None and st.session_state.get("qa_last_result"):
        data_to_show = st.session_state.qa_last_result

    if data_to_show:
        data = data_to_show
        # ---------- Question (echo) ----------
        st.subheader("❓ Question")
        st.write(data.get("question", ""))

        # ---------- Answer ----------
        st.subheader("💡 Answer")
        answer = data.get("answer") or "No answer."
        model_used = data.get("model_used")

        if model_used:
            st.caption(f"Model: **{model_used}**")

        st.markdown(answer)

        # ---------- Debug: Curl commands + step progress ----------
        debug_info = data.get("debug_info")
        if debug_info:
            with st.expander("🔧 Curl commands to test + step progress", expanded=True):
                steps = debug_info.get("steps_completed", [])
                st.markdown("**✅ Completed up to:**")
                for s in steps:
                    st.markdown(f"- {s}")
                st.markdown("---")
                st.markdown("**1. Embed question (Ollama)**")
                curl_embed = debug_info.get("curl_embed")
                if curl_embed:
                    st.code(curl_embed, language="bash")
                st.markdown("**2. Search (Qdrant)**")
                curl_search = debug_info.get("curl_search")
                if curl_search:
                    st.code(curl_search, language="bash")
                st.markdown("**3. Complete (LLM)**")
                curl_complete = debug_info.get("curl_complete")
                if curl_complete:
                    st.code(curl_complete, language="bash")

        # ---------- Like / Dislike (click same button again to clear) ----------
        feedback = st.session_state.get("qa_feedback") or None
        bl, br = st.columns(2)
        with bl:
            label_like = "👍 Liked (click to unlike)" if feedback == "like" else "👍 Like"
            if st.button(label_like, key="qa_like"):
                if feedback == "like":
                    st.session_state.qa_feedback = None
                else:
                    st.session_state.qa_feedback = "like"
                st.rerun()
        with br:
            label_dislike = "👎 Disliked (click to remove)" if feedback == "dislike" else "👎 Dislike"
            if st.button(label_dislike, key="qa_dislike"):
                if feedback == "dislike":
                    st.session_state.qa_feedback = None
                else:
                    st.session_state.qa_feedback = "dislike"
                st.rerun()

        st.download_button(
            "⬇️ Download answer (TXT)",
            data=answer,
            file_name="qa_answer.txt",
            mime="text/plain",
            key="qa_download_answer",
        )

        # ---------- Contexts summary ----------
        contexts = data.get("contexts", [])
        st.subheader("📚 Context used for answer")
        st.caption(
            "Document passages found by semantic search and sent to the LLM. "
            "Score = similarity to the question (0–1)."
        )

        if not contexts:
            st.info("No context was used")
        else:
            scores = [c["score"] for c in contexts]
            st.metric("Context count", len(contexts))
            st.caption(f"Avg score: {sum(scores) / len(scores):.4f} | Min: {min(scores):.4f} | Max: {max(scores):.4f}")

            # ---------- Table ----------
            st.markdown("**Context table**")
            rows = []
            for idx, ctx in enumerate(contexts, start=1):
                text = ctx.get("text") or ""
                text_preview = (text[:80] + "…") if len(text) > 80 else text
                rows.append({
                    "#": idx,
                    "score": round(ctx["score"], 4),
                    "file_hash": ctx.get("file_hash"),
                    "chunk_id": ctx.get("chunk_id"),
                    "section_id": ctx.get("section_id"),
                    "text": text_preview,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # ---------- Detail per context ----------
            st.markdown("**Context details**")
            for idx, ctx in enumerate(contexts, start=1):
                title = (
                    f"[{idx}] score = {ctx['score']:.4f} | "
                    f"file_hash = {ctx.get('file_hash') or '—'} | "
                    f"chunk_id = {ctx.get('chunk_id')}"
                )
                with st.expander(title, expanded=(idx <= 2)):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Metadata**")
                        st.write(f"- file_hash: `{ctx.get('file_hash') or '—'}`")
                        st.write(f"- chunk_id: `{ctx.get('chunk_id')}`")
                        st.write(f"- section_id: `{ctx.get('section_id') or '—'}`")
                        st.write(f"- token_estimate: `{ctx.get('token_estimate') or '—'}`")
                        st.write(f"- source: `{ctx.get('source') or '—'}`")
                        if ctx.get("id"):
                            st.write(f"- point id: `{ctx.get('id')}`")
                    with c2:
                        text = ctx.get("text") or "(empty)"
                        st.write("**Content**")
                        st.text_area(
                            "Content",
                            value=text,
                            height=180,
                            key=f"qa_ctx_text_{idx}_{ctx.get('id', idx)}",
                            disabled=True,
                            label_visibility="collapsed",
                        )
                        st.download_button(
                            "⬇️ Download context content",
                            data=text,
                            file_name=f"context_{ctx.get('file_hash', '')}_{ctx.get('chunk_id', idx)}.txt",
                            mime="text/plain",
                            key=f"qa_ctx_dl_{idx}_{ctx.get('id', idx)}",
                        )

        # ---------- Raw response ----------
        with st.expander("📦 Raw API Response", expanded=False):
            st.json(data)

    else:
        st.info("Enter a question and click **Ask AI** to start.")
