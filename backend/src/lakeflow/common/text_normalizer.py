def canonicalize_text(text: str) -> str:
    if not text:
        return text

    t = text.lower()

    ALIAS_MAP = {
        "neu": "đại học kinh tế quốc dân",
        "đhktqd": "đại học kinh tế quốc dân",
        "đh ktqd": "đại học kinh tế quốc dân",
        "ktqd": "đại học kinh tế quốc dân",
    }

    for alias, canonical in ALIAS_MAP.items():
        t = t.replace(alias, canonical)

    return t