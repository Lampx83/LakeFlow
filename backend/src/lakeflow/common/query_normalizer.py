# backend/src/lakeflow/common/query_normalizer.py

ENTITY_ALIASES = {
    "Đại học Kinh tế Quốc dân": [
        "NEU",
        "ĐH KTQD",
        "ĐHKTQD",
        "KTQD",
    ]
}


def expand_query(query: str) -> str:
    """
    Mở rộng query bằng cách thêm alias thực thể
    thay vì thay thế.
    """
    expanded = query
    lower_query = query.lower()

    for canonical, aliases in ENTITY_ALIASES.items():
        all_forms = [canonical] + aliases

        # Nếu query chứa bất kỳ alias nào
        if any(a.lower() in lower_query for a in all_forms):
            alias_block = ", ".join(all_forms)
            expanded = f"{query} ({alias_block})"
            break

    return expanded