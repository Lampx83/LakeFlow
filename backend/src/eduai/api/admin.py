"""
API Admin: bảng User, thống kê số tin nhắn, xóa toàn bộ tin nhắn theo user.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from eduai.core.auth import verify_token
from eduai.catalog.app_db import get_message_counts_by_user, delete_messages_by_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(payload: dict) -> None:
    """Chỉ admin mới được gọi API admin (xóa tin nhắn)."""
    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản admin mới được thực hiện thao tác này",
        )


@router.get("/users")
def list_users_with_message_count(payload: dict = Depends(verify_token)):
    """
    Danh sách user kèm số tin nhắn (câu hỏi Q&A đã gửi).
    Trả về: [ {"username": "...", "message_count": N}, ... ]
    """
    rows = get_message_counts_by_user()
    return [
        {"username": username, "message_count": count}
        for username, count in rows
    ]


@router.delete("/users/{username}/messages")
def delete_all_user_messages(username: str, payload: dict = Depends(verify_token)):
    """
    Xóa toàn bộ tin nhắn của một user.
    Chỉ tài khoản admin mới được gọi.
    """
    _require_admin(payload)
    deleted = delete_messages_by_user(username)
    return {"username": username, "deleted_count": deleted}
