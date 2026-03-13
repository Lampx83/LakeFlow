# backend/src/lakeflow/common/query_normalizer.py
"""
Expand query by adding entity aliases. Canonical forms (e.g. National Economics University)
and their aliases improve semantic search recall.
"""

ENTITY_ALIASES = {
    "National Economics University": [
        "NEU",
        "ĐH KTQD",
        "ĐHKTQD",
        "KTQD",
    ]
}


def expand_query(query: str) -> str:
    """
    Expand query by adding entity aliases
    instead of replacing.
    """
    expanded = query
    lower_query = query.lower()

    for canonical, aliases in ENTITY_ALIASES.items():
        all_forms = [canonical] + aliases

        # If query contains any alias
        if any(a.lower() in lower_query for a in all_forms):
            alias_block = ", ".join(all_forms)
            expanded = f"{query} ({alias_block})"
            break

    return expanded