import requests
from config.settings import API_BASE

def login(username: str, password: str) -> str | None:
    resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def get_me(token: str) -> dict | None:
    """Lấy thông tin user hiện tại (username) từ token. Dùng để lọc lịch sử theo tài khoản."""
    resp = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def admin_list_users(token: str) -> list[dict]:
    """Danh sách user kèm số tin nhắn (Admin). Mỗi item: {username, message_count}."""
    resp = requests.get(
        f"{API_BASE}/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def admin_delete_user_messages(username: str, token: str) -> dict:
    """Xóa toàn bộ tin nhắn của một user (chỉ admin). Trả về {username, deleted_count}."""
    resp = requests.delete(
        f"{API_BASE}/admin/users/{username}/messages",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def semantic_search(
    query: str,
    top_k: int,
    token: str,
    *,
    collection_name: str | None = None,
    score_threshold: float | None = None,
    qdrant_url: str | None = None,
):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query, "top_k": top_k}
    if collection_name:
        payload["collection_name"] = collection_name
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold
    if qdrant_url:
        payload["qdrant_url"] = qdrant_url
    resp = requests.post(
        f"{API_BASE}/search/semantic",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def qa(
    question: str,
    top_k: int,
    temperature: float,
    token: str,
    *,
    collection_name: str | None = None,
    score_threshold: float | None = None,
    qdrant_url: str | None = None,
):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "question": question,
        "top_k": top_k,
        "temperature": temperature,
    }
    if collection_name:
        payload["collection_name"] = collection_name
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold
    if qdrant_url:
        payload["qdrant_url"] = qdrant_url
    resp = requests.post(
        f"{API_BASE}/search/qa",
        json=payload,
        headers=headers,
        timeout=90,  # Q&A: embedding + search + LLM
    )
    resp.raise_for_status()
    return resp.json()
