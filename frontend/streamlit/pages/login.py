import streamlit as st

from config.settings import EDUAI_MODE
from services.api_client import login
from state.session import init_session, is_logged_in
from state.navigation import set_page
from state.token_store import save_token, clear_token


def render():
    init_session()

    st.header("🔐 Authentication")

    # ==================================================
    # ALREADY LOGGED IN → SHOW TOKEN ONLY
    # ==================================================
    if is_logged_in():
        st.success("✅ Đã đăng nhập")

        st.subheader("🔑 Access Token")
        st.code(st.session_state.token, language="text")

        st.caption("Token đang được sử dụng cho toàn bộ hệ thống frontend")

        if st.button("🚪 Logout", use_container_width=True):
            clear_token()
            st.session_state.token = None
            set_page("login")
            st.rerun()

        return

    # ==================================================
    # NOT LOGGED IN → SHOW LOGIN FORM
    # ==================================================
    st.info("Vui lòng đăng nhập để tiếp tục")

    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input(
            "Password",
            type="password",
            value="admin123" if EDUAI_MODE == "DEV" else "",
        )
        remember = st.checkbox("🔒 Nhớ đăng nhập")
        submitted = st.form_submit_button("Login")

    if not submitted:
        return

    token = login(username, password)

    if not token:
        st.error("❌ Login failed")
        return

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------
    st.session_state.token = token

    if remember:
        save_token(token)
    else:
        clear_token()

    st.success("✅ Login successful")
    set_page("semantic_search")
    st.rerun()
