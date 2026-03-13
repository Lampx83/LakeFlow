import streamlit as st
import streamlit.components.v1 as components

from config.settings import LAKEFLOW_MODE
from state.session import init_session, is_logged_in
from state.navigation import init_navigation, set_page, get_page
from state.token_store import clear_token

from pages import (
    login,
    semantic_search,
    qa,
    pipeline_runner,
    pipeline_dashboard,
    data_lake_explorer,
    sqlite_viewer,
    system_settings,
    qdrant_inspector,
)


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="LakeFlow – Backend Control & Test UI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# INIT
# =====================================================
init_session()
init_navigation()

# Auto redirect if already logged in
# Auto redirect only when app first loads
if is_logged_in() and "page" not in st.session_state:
    set_page("semantic_search")

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 📚 LakeFlow Control")
    st.divider()

    # ---------- AUTH STATUS ----------
    if is_logged_in():
        st.success("🔓 Logged in")
    else:
        st.warning("🔒 Not logged in")

    # ---------- LOGIN (ALWAYS AVAILABLE) ----------
    st.button(
        "🔐 Login / Token",
        on_click=set_page,
        args=("login",),
        use_container_width=True,
    )

    if is_logged_in():
        st.divider()
        # ---------- NAV (AUTHED) ----------
        st.button("📊 Dashboard", on_click=set_page, args=("pipeline_dashboard",), use_container_width=True)
        st.button("📂 Data Lake Explorer", on_click=set_page, args=("data_lake_explorer",), use_container_width=True)
        st.button("🚀 Pipeline Runner", on_click=set_page, args=("pipeline_runner",), use_container_width=True)
        st.button("🗄️ SQLite Viewer", on_click=set_page, args=("sqlite_viewer",), use_container_width=True)
        st.button("🧠 Qdrant Inspector", on_click=set_page, args=("qdrant_inspector",), use_container_width=True)
        st.button("🔎 Semantic Search", on_click=set_page, args=("semantic_search",), use_container_width=True)
        st.button("🤖 Q&A with AI", on_click=set_page, args=("qa",), use_container_width=True)
        st.button("⚙️ System Settings", on_click=set_page, args=("system_settings",), use_container_width=True)


# =====================================================
# ROUTER
# =====================================================
page = get_page()

if page == "login":
    login.render()
elif page == "semantic_search":
    semantic_search.render()
elif page == "qa":
    qa.render()
elif page == "pipeline_runner":
    pipeline_runner.render()
elif page == "data_lake_explorer":
    data_lake_explorer.render()
elif page == "pipeline_dashboard":
    pipeline_dashboard.render()
elif page == "sqlite_viewer":
    sqlite_viewer.render()
elif page == "system_settings":
    system_settings.render()
elif page == "qdrant_inspector":
    qdrant_inspector.render()
elif page == "admin":
    pipeline_dashboard.render()
else:
    st.error(f"Unknown page: {page}")

# Dev: when server restarts (dev_with_reload), auto refresh page when server is back
if LAKEFLOW_MODE == "DEV":
    _auto_reload_js = """
    <script>
    (function() {
        var serverDown = false;
        var check = function() {
            fetch(window.parent.location.href, { method: 'HEAD', cache: 'no-store' })
                .then(function() {
                    if (serverDown) {
                        serverDown = false;
                        window.parent.location.reload();
                    }
                })
                .catch(function() { serverDown = true; });
        };
        setInterval(check, 1500);
    })();
    </script>
    """
    components.html(_auto_reload_js, height=0)
