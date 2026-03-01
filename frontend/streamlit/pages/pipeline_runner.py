import pandas as pd
import streamlit as st
from services.pipeline_service import (
    STEPS_WITH_TREE,
    get_embed_models,
    get_pipeline_folders,
    get_pipeline_folder_children,
    get_pipeline_folder_files,
    get_pipeline_file_step_done,
    list_qdrant_collections,
    run_pipeline_step,
)
from config.settings import LAKEFLOW_MODE, qdrant_service_options, normalize_qdrant_url
from state.session import require_login

STEPS = [
    ("000 – Inbox Ingestion", "step0", "000_inbox"),
    ("100 – File Staging", "step1", "100_raw"),
    ("200 – Processing", "step2", "200_staging"),
    ("300 – Embedding", "step3", "300_processed"),
    ("400 – Qdrant Indexing", "step4", "400_embeddings"),
]

MAX_TREE_DEPTH = 20


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _render_tree_node(step: str, relative_path: str, depth: int) -> None:
    """Display directory tree: ▶/▼ expand (lazy), checkbox to select child folders."""
    if depth >= MAX_TREE_DEPTH:
        return
    children = get_pipeline_folder_children(step, relative_path)
    sel_key = f"pipeline_selected_{step}"
    exp_key = f"pipeline_expanded_{step}"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = set()
    if exp_key not in st.session_state:
        st.session_state[exp_key] = set()
    selected_set = st.session_state[sel_key]
    expanded_set = st.session_state[exp_key]

    for name, full_rel in children:
        safe_key = full_rel.replace("/", "_").replace("\\", "_") or "_root"
        is_expanded = full_rel in expanded_set

        # Indent: child folders; checkbox next to folder name. Expand = show files in right column
        indent_w = max(0.08, 0.15 * depth)
        col_indent, col_btn, col_cb, col_label = st.columns([indent_w, 0.3, 0.25, 4])
        with col_indent:
            st.write("")
        with col_btn:
            if is_expanded:
                if st.button("▼", key=f"tree_collapse_{step}_{safe_key}", help="Collapse"):
                    expanded_set.discard(full_rel)
                    st.rerun()
            else:
                if st.button("▶", key=f"tree_expand_{step}_{safe_key}", help="Expand (view files to the right)"):
                    expanded_set.add(full_rel)
                    st.session_state[f"pipeline_preview_{step}"] = full_rel
                    st.rerun()
        with col_cb:
            is_checked = st.checkbox(
                "Select",
                value=full_rel in selected_set,
                key=f"pipe_cb_{step}_{safe_key}",
                label_visibility="collapsed",
            )
            if is_checked:
                selected_set.add(full_rel)
            else:
                selected_set.discard(full_rel)
        with col_label:
            st.markdown(f"📁 **{name}**")

        if full_rel in expanded_set:
            _render_tree_node(step, full_rel, depth + 1)


def _render_tree_selector(step: str, zone_label: str) -> list[str]:
    """Directory tree on left; file table on right auto-shows when folder expanded (▶)."""
    sel_key = f"pipeline_selected_{step}"
    exp_key = f"pipeline_expanded_{step}"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = set()
    if exp_key not in st.session_state:
        st.session_state[exp_key] = set()

    col_tree, col_table = st.columns([1, 1.2])
    with col_tree:
        st.caption(f"**{zone_label}** directory tree — click ▶ to expand (shows files on right), check to select.")
        _render_tree_node(step, "", 0)

    with col_table:
        preview = st.session_state.get(f"pipeline_preview_{step}")
        if preview:
            files = get_pipeline_folder_files(step, preview)
            st.caption(f"**Files in** `{preview}` — ✓ = processed at this step.")
            if not files:
                st.info("Directory has no files.")
            else:
                rows = []
                for name, sz in files:
                    done = get_pipeline_file_step_done(step, preview, name)
                    rows.append({
                        "File name": name,
                        "Size": _format_size(sz),
                        "Processed": done,
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("Click **▶** next to folder to expand and view files here.")

    return list(st.session_state.get(sel_key, set()))


def render():
    if not require_login():
        return

    if LAKEFLOW_MODE != "DEV":
        st.info("Pipeline Runner only available in DEV mode")
        return

    st.header("🚀 Pipeline Runner")
    st.caption("Select folders to run each step (empty = run all).")

    token = st.session_state.get("token")

    for label, step, folder_label in STEPS:
        with st.expander(label, expanded=False):
            if step in STEPS_WITH_TREE:
                selected = _render_tree_selector(step, folder_label)
            else:
                try:
                    folders = get_pipeline_folders(step, token=token)
                except Exception as e:
                    st.warning(f"Cannot get folder list: {e}")
                    folders = []
                if not folders:
                    st.caption("No folders for this step.")
                    selected = []
                else:
                    selected = st.multiselect(
                        f"Select folders ({folder_label}) — empty = run all",
                        options=folders,
                        key=f"pipeline_folders_{step}",
                    )

            force_rerun = st.checkbox(
                "Allow re-run (even if already done)",
                value=False,
                key=f"pipeline_force_{step}",
            )

            # Embedding step only: select embed model
            embed_model = None
            if step == "step3":
                try:
                    embed_models, default_model = get_embed_models(token=token)
                except Exception:
                    embed_models, default_model = ["qwen3-embedding:8b", "nomic-embed-text"], "qwen3-embedding:8b"
                st.caption("**Embed Model** — Ollama model for embedding. Pull first: `ollama pull &lt;model&gt;`. Set EMBED_MODEL to match for search/QA.")
                opts = ["(Default from EMBED_MODEL)"] + embed_models + ["(Custom)"]
                model_choice = st.selectbox(
                    "Embed model",
                    options=opts,
                    key="pipeline_embed_model_choice_step3",
                    help=f"Default: {default_model}. Use same model for search and indexing.",
                )
                if model_choice == "(Custom)":
                    embed_model = st.text_input(
                        "Custom model name",
                        placeholder="e.g. nomic-embed-text",
                        key="pipeline_embed_model_custom_step3",
                    )
                elif model_choice and model_choice != "(Default from EMBED_MODEL)":
                    embed_model = model_choice

            # Qdrant Indexing step only: select Qdrant Service + collection
            collection_name = None
            pipeline_qdrant_url = None  # used when step == "step4"
            if step == "step4":
                st.caption("**Qdrant Service** — select Qdrant to insert embeddings (default: localhost in dev, lakeflow-qdrant in docker).")
                qdrant_opts = qdrant_service_options()
                qdrant_labels = [t[0] for t in qdrant_opts]
                qdrant_values = [t[1] for t in qdrant_opts]
                qdrant_idx = st.selectbox(
                    "Qdrant Service",
                    range(len(qdrant_labels)),
                    format_func=lambda i: qdrant_labels[i],
                    key="pipeline_qdrant_svc",
                    help="Select Qdrant to insert. Default: localhost (dev) or lakeflow-qdrant (docker).",
                )
                pipeline_qdrant_custom = st.text_input(
                    "Or enter custom Qdrant address",
                    placeholder="http://host:6333 or host:6333",
                    key="pipeline_qdrant_custom",
                    help="If URL entered here, embeddings will be inserted into this Qdrant.",
                )
                pipeline_qdrant_url = (
                    normalize_qdrant_url(pipeline_qdrant_custom)
                    if (pipeline_qdrant_custom and pipeline_qdrant_custom.strip())
                    else qdrant_values[qdrant_idx]
                )

                st.caption("**Qdrant Collection** — select existing or enter new name (empty = default `lakeflow_chunks`).")
                existing = list_qdrant_collections(token=token)
                opts = ["(Default: lakeflow_chunks)", "(Enter new name)"] + sorted(existing or [])
                col_choice = st.selectbox(
                    "Collection",
                    options=opts,
                    key="pipeline_qdrant_collection_choice",
                )
                if col_choice == "(Enter new name)":
                    collection_name = st.text_input(
                        "New collection name",
                        value="",
                        key="pipeline_qdrant_collection_new",
                        placeholder="e.g.: my_collection",
                    )
                elif col_choice and col_choice != "(Default: lakeflow_chunks)":
                    collection_name = col_choice

            if st.button(f"Run {label}", key=f"run_{step}"):
                with st.spinner("Running..."):
                    try:
                        result = run_pipeline_step(
                            step,
                            only_folders=selected if selected else None,
                            force_rerun=force_rerun,
                            collection_name=collection_name if step == "step4" else None,
                            qdrant_url=pipeline_qdrant_url if step == "step4" else None,
                            embed_model=embed_model if step == "step3" else None,
                            token=token,
                        )
                        st.code(result.get("stdout", ""))
                        if result.get("stderr"):
                            st.text("stderr:")
                            st.code(result.get("stderr", ""))
                    except Exception as e:
                        st.error(str(e))
