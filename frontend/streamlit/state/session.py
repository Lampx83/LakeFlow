import streamlit as st

from config.settings import LAKEFLOW_MODE
from state.token_store import load_token


def init_session():
    if "token" not in st.session_state:
        st.session_state.token = load_token()
    # Dev: no manual login needed — auto-login admin if no token
    if LAKEFLOW_MODE == "DEV" and not st.session_state.get("token"):
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
    Use in pages that need auth.
    Returns False if not logged in (and shows warning).
    In DEV mode always allows (already auto-logged in).
    """
    if LAKEFLOW_MODE == "DEV":
        return True
    if not is_logged_in():
        st.warning("🔒 Please log in to use this feature")
        return False
    return True
