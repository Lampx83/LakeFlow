# streamlit/pages/admin.py

import streamlit as st

from services.api_client import get_me, admin_list_users, admin_delete_user_messages
from state.session import require_login


def render():
    if not require_login():
        return

    token = st.session_state.token
    me = get_me(token)
    current_username = me.get("username") if me else None
    is_admin = current_username == "admin"

    st.header("👤 Admin – User Table")
    st.caption(
        "Message count (Q&A questions) per account sent to system. "
        "Only admin can delete all messages of a user."
    )

    try:
        users = admin_list_users(token)
    except Exception as exc:
        st.error(f"Cannot load user list: {exc}")
        return

    if not users:
        st.info("No users with messages in the system yet.")
        return

    # Table: User | Message count | Actions
    for u in users:
        username = u.get("username", "")
        count = u.get("message_count", 0)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write("**" + username + "**")
        with col2:
            st.metric("Messages", count)
        with col3:
            if is_admin:
                if st.button(
                    "🗑️ Delete all messages",
                    key=f"admin_del_{username}",
                    type="secondary",
                ):
                    try:
                        result = admin_delete_user_messages(username, token)
                        st.success(
                            f"Deleted {result.get('deleted_count', 0)} messages for **{username}**."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")
            else:
                st.caption("(Admin only can delete)")
        st.divider()
