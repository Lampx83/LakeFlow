import streamlit as st
from services.pipeline_service import (
    STEPS_WITH_TREE,
    get_pipeline_folders,
    get_pipeline_folder_children,
    list_qdrant_collections,
    run_pipeline_step,
)
from config.settings import EDUAI_MODE, qdrant_service_options, normalize_qdrant_url
from state.session import require_login

STEPS = [
    ("000 – Inbox Ingestion", "step0", "000_inbox"),
    ("100 – File Staging", "step1", "100_raw"),
    ("200 – Processing", "step2", "200_staging"),
    ("300 – Embedding", "step3", "300_processed"),
    ("400 – Qdrant Indexing", "step4", "400_embeddings"),
]

MAX_TREE_DEPTH = 20


def _render_tree_node(step: str, relative_path: str, depth: int) -> None:
    """Hiển thị cây thư mục: ▶/▼ mở rộng (lazy), checkbox chọn thư mục con/cháu."""
    if depth >= MAX_TREE_DEPTH:
        return
    children = get_pipeline_folder_children(step, relative_path)
    indent = "　" * depth  # full-width space
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

        col_btn, col_cb, col_label = st.columns([0.4, 0.5, 4])
        with col_btn:
            if is_expanded:
                if st.button("▼", key=f"tree_collapse_{step}_{safe_key}", help="Thu gọn"):
                    expanded_set.discard(full_rel)
                    st.rerun()
            else:
                if st.button("▶", key=f"tree_expand_{step}_{safe_key}", help="Mở rộng"):
                    expanded_set.add(full_rel)
                    st.rerun()
        with col_cb:
            is_checked = st.checkbox(
                "Chọn",
                value=full_rel in selected_set,
                key=f"pipe_cb_{step}_{safe_key}",
                label_visibility="collapsed",
            )
            if is_checked:
                selected_set.add(full_rel)
            else:
                selected_set.discard(full_rel)
        with col_label:
            st.markdown(f"{indent}📁 **{name}**")

        if full_rel in expanded_set:
            _render_tree_node(step, full_rel, depth + 1)


def _render_tree_selector(step: str, zone_label: str) -> list[str]:
    """Hiển thị cây thư mục: ▶ mở rộng xem con/cháu, checkbox chọn thư mục để chạy; để trống = chạy toàn bộ."""
    st.caption(f"Cây thư mục **{zone_label}** — bấm ▶ để mở rộng, tích checkbox để chọn thư mục (con/cháu) cần chạy; để trống = chạy toàn bộ.")
    sel_key = f"pipeline_selected_{step}"
    exp_key = f"pipeline_expanded_{step}"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = set()
    if exp_key not in st.session_state:
        st.session_state[exp_key] = set()
    _render_tree_node(step, "", 0)
    return list(st.session_state.get(sel_key, set()))


def render():
    if not require_login():
        return

    if EDUAI_MODE != "DEV":
        st.info("Pipeline Runner chỉ khả dụng ở DEV mode")
        return

    st.header("🚀 Pipeline Runner")
    st.caption("Chọn thư mục để chạy từng bước (để trống = chạy toàn bộ).")

    token = st.session_state.get("token")

    for label, step, folder_label in STEPS:
        with st.expander(label, expanded=False):
            if step in STEPS_WITH_TREE:
                selected = _render_tree_selector(step, folder_label)
            else:
                try:
                    folders = get_pipeline_folders(step, token=token)
                except Exception as e:
                    st.warning(f"Không lấy được danh sách thư mục: {e}")
                    folders = []
                if not folders:
                    st.caption("Không có thư mục nào cho bước này.")
                    selected = []
                else:
                    selected = st.multiselect(
                        f"Chọn thư mục ({folder_label}) — để trống = chạy toàn bộ",
                        options=folders,
                        key=f"pipeline_folders_{step}",
                    )

            force_rerun = st.checkbox(
                "Cho phép chạy lại (kể cả đã làm rồi)",
                value=False,
                key=f"pipeline_force_{step}",
            )

            # Chỉ bước Qdrant Indexing: chọn Qdrant Service + collection
            collection_name = None
            pipeline_qdrant_url = None  # dùng khi step == "step4"
            if step == "step4":
                st.caption("**Qdrant Service** — chọn Qdrant để insert embeddings vào (mặc định: localhost khi dev, eduai-qdrant khi docker).")
                qdrant_opts = qdrant_service_options()
                qdrant_labels = [t[0] for t in qdrant_opts]
                qdrant_values = [t[1] for t in qdrant_opts]
                qdrant_idx = st.selectbox(
                    "Qdrant Service",
                    range(len(qdrant_labels)),
                    format_func=lambda i: qdrant_labels[i],
                    key="pipeline_qdrant_svc",
                    help="Chọn Qdrant để insert. Mặc định: localhost (dev) hoặc eduai-qdrant (docker).",
                )
                pipeline_qdrant_custom = st.text_input(
                    "Hoặc nhập địa chỉ Qdrant tùy chỉnh",
                    placeholder="http://host:6333 hoặc host:6333",
                    key="pipeline_qdrant_custom",
                    help="Nếu nhập URL ở đây, embeddings sẽ được insert vào Qdrant này.",
                )
                pipeline_qdrant_url = (
                    normalize_qdrant_url(pipeline_qdrant_custom)
                    if (pipeline_qdrant_custom and pipeline_qdrant_custom.strip())
                    else qdrant_values[qdrant_idx]
                )

                st.caption("**Collection Qdrant** — chọn có sẵn hoặc nhập tên mới (để trống = dùng mặc định `eduai_chunks`).")
                existing = list_qdrant_collections(token=token)
                opts = ["(Mặc định: eduai_chunks)", "(Nhập tên mới)"] + sorted(existing or [])
                col_choice = st.selectbox(
                    "Collection",
                    options=opts,
                    key="pipeline_qdrant_collection_choice",
                )
                if col_choice == "(Nhập tên mới)":
                    collection_name = st.text_input(
                        "Tên collection mới",
                        value="",
                        key="pipeline_qdrant_collection_new",
                        placeholder="vd: my_collection",
                    )
                elif col_choice and col_choice != "(Mặc định: eduai_chunks)":
                    collection_name = col_choice

            if st.button(f"Chạy {label}", key=f"run_{step}"):
                with st.spinner("Đang chạy..."):
                    try:
                        result = run_pipeline_step(
                            step,
                            only_folders=selected if selected else None,
                            force_rerun=force_rerun,
                            collection_name=collection_name if step == "step4" else None,
                            qdrant_url=pipeline_qdrant_url if step == "step4" else None,
                            token=token,
                        )
                        st.code(result.get("stdout", ""))
                        if result.get("stderr"):
                            st.text("stderr:")
                            st.code(result.get("stderr", ""))
                    except Exception as e:
                        st.error(str(e))
