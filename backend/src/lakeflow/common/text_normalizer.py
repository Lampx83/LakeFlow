def canonicalize_text(text: str) -> str:
    """Canonicalize text: expand aliases (e.g. NEU, KTQD) to full form for better semantic search."""
    if not text:
        return text

    t = text.lower()

    ALIAS_MAP = {
        "neu": "National Economics University",
        "đhktqd": "National Economics University",
        "đh ktqd": "National Economics University",
        "ktqd": "National Economics University",
    }

    for alias, canonical in ALIAS_MAP.items():
        t = t.replace(alias, canonical)

    return t