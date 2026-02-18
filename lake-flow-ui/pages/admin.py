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

    st.header("👤 Admin – Bảng User")
    st.caption(
        "Thống kê số tin nhắn (câu hỏi Q&A) mỗi tài khoản gửi đến hệ thống. "
        "Chỉ admin có thể xóa toàn bộ tin nhắn của một user."
    )

    try:
        users = admin_list_users(token)
    except Exception as exc:
        st.error(f"Không tải được danh sách user: {exc}")
        return

    if not users:
        st.info("Chưa có user nào có tin nhắn trong hệ thống.")
        return

    # Bảng: User | Số tin nhắn | Thao tác
    for u in users:
        username = u.get("username", "")
        count = u.get("message_count", 0)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write("**" + username + "**")
        with col2:
            st.metric("Số tin nhắn", count)
        with col3:
            if is_admin:
                if st.button(
                    "🗑️ Xoá toàn bộ tin nhắn",
                    key=f"admin_del_{username}",
                    type="secondary",
                ):
                    try:
                        result = admin_delete_user_messages(username, token)
                        st.success(
                            f"Đã xóa {result.get('deleted_count', 0)} tin nhắn của **{username}**."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi xóa: {e}")
            else:
                st.caption("(Chỉ admin mới xóa được)")
        st.divider()
