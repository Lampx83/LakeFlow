"""
DB lưu dữ liệu ứng dụng: tin nhắn Q&A theo user (để thống kê và xóa trong Admin).
"""
import logging
from pathlib import Path
from datetime import datetime

from eduai.catalog.db import get_connection
from eduai.config.paths import catalog_path

log = logging.getLogger(__name__)


def _app_db_path() -> Path:
    return catalog_path() / "eduai_app.sqlite"


def _get_conn():
    conn = get_connection(_app_db_path())
    _init_app_db(conn)
    return conn


def _init_app_db(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_messages_username ON user_messages(username)")


def insert_message(username: str, question: str) -> None:
    """Ghi một tin nhắn (câu hỏi Q&A) của user."""
    conn = _get_conn()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        "INSERT INTO user_messages (username, question, created_at) VALUES (?, ?, ?)",
        (username, question[:10000], now),  # giới hạn độ dài
    )
    conn.commit()


def get_message_counts_by_user() -> list[tuple[str, int]]:
    """Trả về danh sách (username, số tin nhắn) sắp xếp theo username."""
    conn = _get_conn()
    cur = conn.execute(
        "SELECT username, COUNT(*) AS cnt FROM user_messages GROUP BY username ORDER BY username"
    )
    return [(row[0], row[1]) for row in cur.fetchall()]


def delete_messages_by_user(username: str) -> int:
    """Xóa toàn bộ tin nhắn của user. Trả về số dòng đã xóa."""
    conn = _get_conn()
    cur = conn.execute("DELETE FROM user_messages WHERE username = ?", (username,))
    conn.commit()
    return cur.rowcount
