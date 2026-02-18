import streamlit as st

def init_navigation():
    if "page" not in st.session_state:
        st.session_state.page = "login"

def set_page(page: str):
    st.session_state.page = page

def get_page() -> str:
    return st.session_state.page
