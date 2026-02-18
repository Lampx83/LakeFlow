# lakeflow-ui

Streamlit control UI for LakeFlow: pipelines, data lake explorer, semantic search, Q&A.

## Install

```bash
pip install lakeflow-ui
```

## Run

Backend must be running (e.g. http://localhost:8011). Then:

```bash
lakeflow-ui
```

Or from repo root: `streamlit run lake-flow-ui/app.py --server.port=8012`.

Set `API_BASE_URL` if backend is at a different URL.
