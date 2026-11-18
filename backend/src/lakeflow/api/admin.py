"""
Admin API: user table, message counts, delete all messages per user.
"""
from fastapi import APIRouter, Depends

from lakeflow.core.auth import require_admin
from lakeflow.catalog.app_db import get_message_counts_by_user, delete_messages_by_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users_with_message_count(payload: dict = Depends(require_admin)):
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
def delete_all_user_messages(username: str, payload: dict = Depends(require_admin)):
    """
    Delete all messages for a user.
    Only admin account can call this.
    """
    deleted = delete_messages_by_user(username)
    return {"username": username, "deleted_count": deleted}
