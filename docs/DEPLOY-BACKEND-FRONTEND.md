# Publishing both Backend and Frontend LakeFlow (PyPI + Docker)

LakeFlow has two main parts: **backend** (FastAPI) and **frontend** (Streamlit). There are two corresponding ways to “publish” them.

---

## 1. PyPI (package `lake-flow-pipeline` — for users who install via pip/pipx)

- **Already in place:** Backend package on PyPI under the name `lake-flow-pipeline`.
- When a user runs `pipx run lake-flow-pipeline init` or `pip install lake-flow-pipeline && lakeflow init`:
  - The `lake-flow-pipeline` package (CLI) is installed.
  - The `lakeflow init` command downloads the **entire repo** from GitHub → which already includes **both backend and frontend** (and docker-compose, website, etc.).
- **Conclusion:** You only need to publish **one** PyPI package (`lake-flow-pipeline`) for users to have both backend and frontend (via init). A separate PyPI package for the frontend is not required.

**How to publish the backend to PyPI:** see [PUBLISH-PYPI.md](PUBLISH-PYPI.md).

---

## 2. Docker (Backend + Frontend images to GitHub Container Registry)

When you want to **push Docker images** for both backend and frontend (for deployment with Kubernetes, docker pull, etc.):

### Automated: create a GitHub Release

1. Update the version (if needed), then commit & push.
2. On GitHub: **Releases** → **Create a new release** → create a tag (e.g. `v0.1.0`) → **Publish release**.
3. The **CD** workflow (`.github/workflows/cd.yml`) will run and:
   - Build & push **Backend** → `ghcr.io/<owner>/datalake-backend:v0.1.0` and `latest`.
   - Build & push **Frontend** → `ghcr.io/<owner>/datalake-frontend:v0.1.0` and `latest`.

After it finishes, go to **GitHub → Packages** (or https://github.com/orgs/Lampx83/packages if using an org) to see the two packages: `datalake-backend`, `datalake-frontend`.

### Manual: build and push from your machine

**Backend:**

```bash
cd /Users/mac/Cursor/AI/LakeFlow
docker build -t ghcr.io/Lampx83/datalake-backend:0.1.0 ./lake-flow
docker push ghcr.io/Lampx83/datalake-backend:0.1.0
```

**Frontend:**

```bash
docker build -t ghcr.io/Lampx83/datalake-frontend:0.1.0 ./lake-flow-ui -f lake-flow-ui/Dockerfile
docker push ghcr.io/Lampx83/datalake-frontend:0.1.0
```

Before pushing the first time: log in to GHCR:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

(Create a **Personal Access Token** with scope `write:packages` at GitHub → Settings → Developer settings.)

---

## Summary

| Goal | Backend | Frontend | How |
|------|---------|----------|-----|
| User installs via pip/pipx and has full code | ✅ Package `lake-flow-pipeline` on PyPI | ✅ Included in repo downloaded by `lakeflow init` | Follow [PUBLISH-PYPI.md](PUBLISH-PYPI.md) (one PyPI package only) |
| Docker images for deployment | ✅ `datalake-backend` | ✅ `datalake-frontend` | Create a **GitHub Release** (CD workflow pushes both) or build & push manually as above |

**“Publishing both frontend and backend”** = (1) PyPI: only need to publish the `lake-flow-pipeline` package (user runs init and gets both); (2) Docker: create a Release so CD pushes both images to GHCR, or build/push manually.
