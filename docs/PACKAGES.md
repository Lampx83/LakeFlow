# Two independent packages: LakeFlow

Backend and frontend are packaged as **two separate libraries**, usable independently.

---

## Directory names and PyPI packages

| Directory in repo | PyPI package | Description |
|------------------|--------------|-------------|
| **lake-flow/** | `lake-flow-pipeline` | Backend: FastAPI, pipeline, CLI `lakeflow init`, API embed/search. |
| **lake-flow-ui/** | `lakeflow-ui` | Frontend: Streamlit control UI, calls backend API. |

- **lake-flow-pipeline** — For users who only need API/CLI: `pip install lake-flow-pipeline` (or `lake-flow-pipeline[full]` to run the server).
- **lakeflow_ui** — For users who need the UI: `pip install lakeflow-ui` then run `lakeflow-ui` (after the backend is running).

---

## Repo structure (after rename)

```
LakeFlow/
├── lake-flow/          # PyPI package: lake-flow-pipeline (backend)
│   ├── pyproject.toml
│   ├── src/lakeflow/
│   └── ...
├── lake-flow-ui/       # PyPI package: lakeflow-ui (Streamlit)
│   ├── pyproject.toml
│   ├── app.py, pages/, config/, ...
│   └── Dockerfile
├── website/            # Landing / intro page
├── docker-compose.yml
└── README.md
```

---

## Docker & CI/CD

- **docker-compose:** Builds backend from `./lake-flow`, frontend from `./lake-flow-ui`.
- **publish-pypi:** Builds and publishes `lake-flow-pipeline` from the `lake-flow/` directory. A separate workflow can be added to publish `lakeflow-ui` from `lake-flow-ui/` when needed.
