import streamlit as st

from config.settings import EDUAI_MODE
from state.token_store import load_token


def init_session():
    if "token" not in st.session_state:
        st.session_state.token = load_token()
    # Dev: không cần đăng nhập thủ công — tự đăng nhập admin nếu chưa có token
    if EDUAI_MODE == "DEV" and not st.session_state.get("token"):
        try:
            from services.api_client import login as api_login
            token = api_login("admin", "admin123")
            if token:
                st.session_state.token = token
        except Exception:
            pass


def is_logged_in() -> bool:
    return bool(st.session_state.get("token"))


def require_login() -> bool:
    """
    Dùng trong page cần auth.
    Trả False nếu chưa login (và hiển thị warning).
    Ở chế độ DEV luôn cho qua (đã auto login).
    """
    if EDUAI_MODE == "DEV":
        return True
    if not is_logged_in():
        st.warning("🔒 Vui lòng đăng nhập để sử dụng chức năng này")
        return False
    return True
