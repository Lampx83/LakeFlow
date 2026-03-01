"""
Admin API: user table, message counts, delete all messages per user.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from lakeflow.core.auth import verify_token
from lakeflow.catalog.app_db import get_message_counts_by_user, delete_messages_by_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(payload: dict) -> None:
    """Only admin can call admin API (delete messages)."""
    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=i18n_detail("admin.admin_only"),
        )


@router.get("/users")
def list_users_with_message_count(payload: dict = Depends(verify_token)):
    """
    List users with message count (Q&A questions sent).
    Returns: [ {"username": "...", "message_count": N}, ... ]
    """
    rows = get_message_counts_by_user()
    return [
        {"username": username, "message_count": count}
        for username, count in rows
    ]


@router.delete("/users/{username}/messages")
def delete_all_user_messages(username: str, payload: dict = Depends(verify_token)):
    """
    Delete all messages for a user.
    Only admin account can call this.
    """
    _require_admin(payload)
    deleted = delete_messages_by_user(username)
    return {"username": username, "deleted_count": deleted}
