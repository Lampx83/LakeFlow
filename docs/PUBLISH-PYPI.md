# Guide: Publishing LakeFlow to PyPI (pip / pipx)

Goal: Users can install and run with:

```bash
pipx run lake-flow-pipeline init
# or
pip install lake-flow-pipeline && lakeflow init my-project
```

The package is published to [PyPI](https://pypi.org/project/lake-flow-pipeline/) — **live release:** [0.1.0](https://pypi.org/project/lake-flow-pipeline/0.1.0/). On production PyPI we use the name **lake-flow-pipeline** because **lake-flow** is rejected as too similar to an existing project (see [PyPI – project name](https://pypi.org/help/#project-name)). The repo has a GitHub Actions workflow to publish automatically when you create a **GitHub Release**.

---

## Summary of steps

1. Register on PyPI (if you don't have an account yet).
2. Create a project on PyPI and configure **Trusted Publisher** (no API token needed).
3. Update the version in `lake-flow/pyproject.toml` for each release.
4. Create a tag and **GitHub Release** → the workflow will build and push to PyPI.
5. Verify: `pipx run lake-flow-pipeline init`.

---

## Step 1: Register on PyPI

1. Go to [pypi.org](https://pypi.org) → **Register**.
2. Verify email, enable 2FA (recommended).

---

## Step 2: Create project and Trusted Publisher on PyPI

### 2.1. Create a new project (first time only)

1. Log in to PyPI → **Your projects** → **Add new project**.
2. **Project name:** `lake-flow-pipeline` (must match `name` in `lake-flow/pyproject.toml`).
3. You can leave the description empty and **Create**; the first publish will push metadata from `pyproject.toml`.

### 2.2. Configure Trusted Publisher (no API token needed)

1. Go to project **lake-flow-pipeline** on PyPI → **Settings** → **Publishing** → **Add a new trusted publisher**.
2. **PyPI Project name:** `lake-flow-pipeline`.
3. **Owner:** GitHub username or org (e.g. `Lampx83`).
4. **Repository name:** `LakeFlow` (exact repo name, case-sensitive).
5. **Workflow name:** `publish-pypi.yml` (exact file name in `.github/workflows/`).
6. **Environment name:** leave empty (or enter `pypi` if you create an environment in GitHub).
7. Save.

Documentation: [PyPI – Trusted publishers](https://docs.pypi.org/trusted-publishers/).

---

## Step 3: Version in pyproject.toml

For each new release, update the version in **`LakeFlow/lake-flow/pyproject.toml`** to match the tag you will create:

```toml
[project]
name = "lake-flow-pipeline"
version = "0.1.1"   # e.g. tag v0.1.1 → version = "0.1.1"
```

Commit and push to the branch (e.g. `main`) **before** creating the Release.

---

## Step 4: Create GitHub Release to trigger publish

1. On GitHub repo **Lampx83/LakeFlow** → **Releases** → **Create a new release**.
2. **Choose a tag:** create a new tag (e.g. `v0.1.0`, `v0.1.1`) — tag should match version in `pyproject.toml` (without the `v`).
3. **Release title:** e.g. `v0.1.0` or `LakeFlow 0.1.0`.
4. Release description (optional).
5. Click **Publish release**.

The **Publish to PyPI** workflow (`.github/workflows/publish-pypi.yml`) will run: build the package from the `lake-flow/` directory and push to PyPI. If the version already exists, the publish step is skipped (`skip-existing: true`).

---

## Step 5: Verify after publishing

```bash
# Run directly (without installing on the machine)
pipx run lake-flow-pipeline init my-data-lake

# Or install then run
pip install lake-flow-pipeline
lakeflow init my-data-lake
```

Open the PyPI page: [https://pypi.org/project/lake-flow-pipeline/](https://pypi.org/project/lake-flow-pipeline/).

---

## Current workflow (repo)

File **`.github/workflows/publish-pypi.yml`**:

- **Trigger:** when you create a **GitHub Release** (event `release`, type `published`).
- **Publish method:** uses [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no need to configure `PYPI_API_TOKEN` in GitHub Secrets.
- **Package directory:** `lake-flow/` (contains `pyproject.toml` and `src/lakeflow/`).
- **Skip existing:** `skip-existing: true` is enabled so the workflow does not fail when the version already exists on PyPI.

---

## Manual publish (without GitHub Actions)

Follow [Packaging Python Projects (PyPA)](https://packaging.python.org/en/latest/tutorials/packaging-projects/): build with `build`, upload with `twine`.

```bash
cd LakeFlow/lake-flow
pip install --upgrade build twine
python -m build
twine upload dist/*
```

When prompted, use **username:** `__token__` and **password:** API token from **pypi.org** (not test.pypi.org). Do not use legacy username/password.

**Upload to real PyPI (pypi.org) with API token:** Create the token at [pypi.org/manage/account/](https://pypi.org/manage/account/) → **API tokens** → Add API token (scope: Entire account or project `lake-flow-pipeline` only). Add a `[pypi]` section to `~/.pypirc` (see template below), set `password = pypi-...` to the token you created. Then run **without** `--repository testpypi`:

```bash
cd LakeFlow/lake-flow
twine upload dist/*
```

(If you don't have `~/.pypirc`, twine will prompt for username/password: enter `__token__` and paste the pypi.org token.)

**TestPyPI (optional — for testing only):** use [TestPyPI](https://test.pypi.org) to test upload and install before pushing to real PyPI. Register at [test.pypi.org/account/register/](https://test.pypi.org/account/register/), create an API token **on TestPyPI** (Account → API tokens), then:

```bash
twine upload --repository testpypi dist/*
# Username: __token__   (exactly two underscores on each side)
# Password: <paste token created from test.pypi.org>
pip install --index-url https://test.pypi.org/simple/ --no-deps lake-flow-pipeline
pipx run --index https://test.pypi.org/simple/ lake-flow-pipeline init my-test-app
```

**If you get 403 / "Invalid or non-existent authentication information" when uploading to TestPyPI:** (see [TestPyPI help](https://test.pypi.org/help/#invalid-auth))
1. **Username** must be exactly `__token__` (two underscores on each side).
2. **Token** must be created from [test.pypi.org/manage/account/](https://test.pypi.org/manage/account/) → API tokens. **PyPI (pypi.org) and TestPyPI (test.pypi.org) are separate systems** — a pypi.org token cannot be used for TestPyPI.
3. **When pasting the token:** use the full string (including the `pypi-` prefix), **no extra characters** (e.g. trailing newline). Paste and press Enter immediately, no extra spaces.
4. If it still fails: create a new token on TestPyPI, or use a `~/.pypirc` file to avoid paste issues (token in file won't get an extra newline when pasted).

**Using `~/.pypirc` (to avoid pasting token in terminal):** `~/.pypirc` must be a **file** (not a directory). If you get `[Errno 21] Is a directory: '/Users/.../.pypirc'`, remove the mistaken directory: `rm -rf ~/.pypirc` and create a **file** with the content below (replace `YOUR_TESTPYPI_TOKEN` with the token from test.pypi.org, keep it on one line, no trailing newline):

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_ORG_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN
```

- **Upload to real PyPI:** `twine upload dist/*` (uses token in `[pypi]`, from pypi.org).
- **Upload to TestPyPI (test):** `twine upload --repository testpypi dist/*` (uses token in `[testpypi]`, from test.pypi.org).

**If you get 400 Bad Request when uploading to PyPI:** run `twine upload dist/* --verbose` to see the error in the response. Common cases:
1. **Version already exists** — PyPI does not allow re-uploading the same version. Update `version` in `lake-flow/pyproject.toml` (e.g. `0.1.0` → `0.1.1`), run `rm -rf dist && python3 -m build` again, then `twine upload dist/*`.
2. **The name '...' is too similar to an existing project** — PyPI normalizes names (lowercase, no hyphens/underscores), so `lake-flow` and `lakeflow` are treated as the same; if `lakeflow` exists, you cannot use `lake-flow`. Fix: change `name` in `pyproject.toml` to a different name (e.g. `lake-flow-pipeline`), create a new project on PyPI with that name, then build and upload again. See [PyPI – project name](https://pypi.org/help/#project-name).
3. **Description failed to render** — README/long description has invalid Markdown or RST. Check `lake-flow/README.md`; you can run `twine check dist/*` before upload.
4. **Invalid URI** — URLs in `pyproject.toml` (Homepage, Documentation, Repository) must be valid (e.g. `https://...`).

**Upload only a fresh build:** if `dist/` contains old and new wheel names (e.g. `lake_flow_pipeline-*`), remove and rebuild: `rm -rf dist && python3 -m build`, then `twine upload --repository testpypi dist/*`.

---

## Notes

- **Package name on PyPI:** `lake-flow-pipeline` (lowercase). The name `lake-flow` is rejected because it is too similar to an existing project (`lakeflow`); PyPI normalizes names so they collide. If you need a different name, change `name` in `pyproject.toml` and create a new PyPI project.
- **CLI:** The package only needs default dependencies (stdlib); the `lakeflow init` command fetches code from GitHub. Users who want to run the full backend install `pip install lake-flow-pipeline[full]`.
- **Website:** After publishing to PyPI, you can also promote the project on [https://lake-flow.vercel.app/](https://lake-flow.vercel.app/) and in the README.

After completing the steps above, users can run `pipx run lake-flow-pipeline init` to create a LakeFlow project without cloning the repo.

---

## References

- **[Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)** — Official PyPA guide: project layout, `pyproject.toml`, build with `python -m build`, upload with twine, TestPyPI.
- [PyPI – Trusted publishers](https://docs.pypi.org/trusted-publishers/) — Configure OIDC so GitHub Actions can publish without an API token.
- [PyPI – Packaging guide](https://packaging.python.org/) — Overview and other guides.
- [DEPLOY-BACKEND-FRONTEND.md](DEPLOY-BACKEND-FRONTEND.md) — Publishing both backend and frontend (PyPI + Docker images to GHCR).
