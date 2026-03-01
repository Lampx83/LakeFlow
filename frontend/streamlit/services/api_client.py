import requests
from config.settings import API_BASE


def get_data_path_from_api() -> str | None:
    """Get Data Lake root path from backend (matches LAKE_ROOT backend uses)."""
    try:
        resp = requests.get(f"{API_BASE}/system/data-path", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data_base_path")
    except Exception:
        pass
    return None


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
    """Get current user info (username) from token. Used to filter history per account."""
    resp = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def admin_list_users(token: str) -> list[dict]:
    """List users with message count (Admin). Each item: {username, message_count}."""
    resp = requests.get(
        f"{API_BASE}/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def admin_delete_user_messages(username: str, token: str) -> dict:
    """Delete all messages for a user (admin only). Returns {username, deleted_count}."""
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
    if not resp.ok:
        detail = None
        try:
            data = resp.json()
            detail = data.get("detail")
        except Exception:
            pass
        err_msg = detail if detail else resp.text or resp.reason
        raise RuntimeError(f"{resp.status_code}: {err_msg}")
    return resp.json()
