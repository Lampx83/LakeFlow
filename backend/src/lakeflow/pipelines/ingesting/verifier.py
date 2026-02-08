# src/lakeflow/ingesting/verifier.py
from pathlib import Path
from lakeflow.common.hashing import sha256_file


def verify_hash(path: Path, expected_hash: str) -> bool:
    return sha256_file(path) == expected_hash
