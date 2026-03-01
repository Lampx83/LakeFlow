"""
LLM chat service: supports both OpenAI-compatible (/v1/chat/completions) and native Ollama (/api/chat).
Uses LLM_BASE_URL from .env. Proxy may only support native API → use USE_OLLAMA_NATIVE_CHAT=true.
"""
import os
import requests
from typing import List, Dict, Any

from lakeflow.core.config import LLM_BASE_URL, LLM_MODEL, OPENAI_API_KEY

USE_OLLAMA_NATIVE_CHAT = os.getenv("USE_OLLAMA_NATIVE_CHAT", "").lower() in ("1", "true", "yes")


def chat_completion(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> tuple[str, str]:
    """
    Call LLM chat. Returns (answer, model_used).
    Supports OpenAI-compatible and native Ollama (/api/chat).
    """
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    base = LLM_BASE_URL.rstrip("/")

    if USE_OLLAMA_NATIVE_CHAT:
        # Native Ollama /api/chat (some proxies only support this path)
        url = f"{base}/api/chat"
        payload: Dict[str, Any] = {
            "model": LLM_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
    else:
        # OpenAI-compatible /v1/chat/completions
        url = f"{base}/v1/chat/completions"
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if USE_OLLAMA_NATIVE_CHAT:
        # Response: { model, message: { role, content }, ... }
        answer = (data.get("message") or {}).get("content", "")
        model_used = data.get("model", LLM_MODEL)
    else:
        # Response: { choices: [ { message: { content } } ], model, ... }
        answer = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        model_used = data.get("model", LLM_MODEL)

    return answer, model_used
