# Two independent packages: LakeFlow

Backend and frontend are packaged as **two separate libraries**, usable independently.

---

## Directory names and PyPI packages

| Directory in repo | PyPI package | Description |
|------------------|--------------|-------------|
| **backend/** | `lake-flow-pipeline` | Backend: FastAPI, pipeline, CLI `lakeflow init`, API embed/search. |
| **frontend/streamlit/** | `lakeflow-ui` | Frontend: Streamlit control UI, calls backend API. |

- **lake-flow-pipeline** — For users who only need API/CLI: `pip install lake-flow-pipeline` (or `lake-flow-pipeline[full]` to run the server).
- **lakeflow_ui** — For users who need the UI: `pip install lakeflow-ui` then run `lakeflow-ui` (after the backend is running).

---

## Repo structure (after rename)

```
LakeFlow/
├── backend/            # PyPI package: lake-flow-pipeline (backend)
│   ├── pyproject.toml
│   ├── src/lakeflow/
│   └── ...
├── frontend/streamlit/  # PyPI package: lakeflow-ui (Streamlit)
│   ├── pyproject.toml
│   ├── app.py, pages/, config/, ...
│   └── Dockerfile
├── website/            # Landing / intro page
├── docker-compose.yml
└── README.md
```

---

## Docker & CI/CD

- **docker-compose:** Builds backend from `./backend`, frontend from `./frontend/streamlit`.
- **publish-pypi:** Builds and publishes `lake-flow-pipeline` from the `backend/` directory. Package `lakeflow-ui` from `frontend/streamlit/` when needed.
