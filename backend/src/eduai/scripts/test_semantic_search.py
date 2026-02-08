#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Semantic Search API - EDUAI
"""

import requests
import json
import sys

# =========================
# CẤU HÌNH
# =========================

API_URL = "http://127.0.0.1:8011/search/semantic"

# DÁN ACCESS TOKEN VÀO ĐÂY
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2OTE5MjM3OX0.r_P4ubr45-x5M7u4yrRIarwd71axXKEJPXlFV0Fkiao"

# =========================
# PAYLOAD TEST
# =========================

payload = {
    "query": "Kinh tế quốc dân",
    "top_k": 5
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def main():
    print("=== TEST SEMANTIC SEARCH API ===")

    if not TOKEN or TOKEN.startswith("PASTE_"):
        print("❌ ACCESS TOKEN chưa được cấu hình")
        sys.exit(1)

    print("Request payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        print("\n❌ Request failed:")
        print(str(exc))
        sys.exit(1)

    print("\nStatus code:", response.status_code)

    if response.status_code == 200:
        print("✅ Response:")
        try:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(response.text)
    else:
        print("❌ Error response:")
        try:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(response.text)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
