# Contributing to LakeFlow

Thank you for your interest in contributing to LakeFlow. This document explains how to set up a development environment and contribute effectively.

---

## Two ways to use LakeFlow

### 1. End user (run with Docker)

```bash
pip install lakeflow
lakeflow init my-project
cd my-project
docker compose up -d
```

Or with `pipx` (recommended — isolated environment):

```bash
pipx run lakeflow init my-project
```

### 2. Developer (contribute to source)

Clone the repository and install in editable mode so your changes take effect immediately:

```bash
git clone https://github.com/Lampx83/LakeFlow.git
cd LakeFlow/backend

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e ".[dev,full]"
```

- `-e` (editable): Edit code in the repo; no need to reinstall.
- `[dev]`: Lint (Ruff), tests (pytest).
- `[full]`: All pipeline dependencies (pandas, sentence-transformers, qdrant, etc.).

Run the backend:

```bash
cd ..
# Ensure .env exists (copy from .env.example)
python -m uvicorn lakeflow.main:app --reload --port 8011
```

Run the Streamlit UI:

```bash
streamlit run frontend/streamlit/app.py
```

---

## Code style

- **Python**: Use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Run before committing: `ruff check .` and `ruff format .`

---

## Pull requests

1. Open an issue first for large changes.
2. Fork the repo, create a branch, make your changes.
3. Ensure tests pass and lint is clean.
4. Submit a pull request with a clear description.

---

## Questions?

- **GitHub Issues**: [Lampx83/LakeFlow/issues](https://github.com/Lampx83/LakeFlow/issues)
- **Documentation**: [Read the Docs](https://lakeflow.readthedocs.io) (when published)
