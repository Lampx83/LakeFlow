"""
System Settings – Full configuration overview and management.

Sections:
- Health: Backend, Qdrant connectivity
- Config: Runtime config (no secrets)
- Zones: Status per zone, create missing
- Qdrant: Default service info
- Data Lake Path: Configure path (DEV/PROD)
"""

from pathlib import Path
import requests
import streamlit as st

from config.settings import (
    API_BASE,
    LAKEFLOW_MODE,
    DATA_ROOT,
    QDRANT_DEFAULT_DEV,
    QDRANT_DEFAULT_DOCKER,
    is_running_in_docker,
    LAKEFLOW_MOUNT_DESCRIPTION,
)
from state.session import require_login


REQUIRED_ZONES = [
    "000_inbox",
    "100_raw",
    "200_staging",
    "300_processed",
    "400_embeddings",
    "500_catalog",
]

# PROD only
PROD_DATA_PATHS = {
    "Education – Training": "/data/education",
    "Research": "/data/research",
    "Test": "/data/test",
}


def _headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def api_get_data_path(token: str) -> str | None:
    resp = requests.get(
        f"{API_BASE}/system/data-path",
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("data_base_path")


def api_set_data_path(path: str, token: str) -> None:
    resp = requests.post(
        f"{API_BASE}/system/data-path",
        json={"path": path},
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()


def api_get_config(token: str) -> dict | None:
    try:
        resp = requests.get(
            f"{API_BASE}/system/config",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def api_get_zones_status(token: str) -> dict | None:
    try:
        resp = requests.get(
            f"{API_BASE}/system/zones-status",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def api_create_zones(token: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/system/create-zones",
        headers=_headers(token),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def api_get_health_detail(token: str) -> dict | None:
    try:
        resp = requests.get(
            f"{API_BASE}/system/health-detail",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def validate_local_path(path: str) -> tuple[bool, str]:
    try:
        p = Path(path).expanduser().resolve()
    except Exception as exc:
        return False, f"Invalid path: {exc}"

    if not p.exists():
        return False, "Path does not exist"

    if not p.is_dir():
        return False, "Path is not a directory"

    missing = [z for z in REQUIRED_ZONES if not (p / z).exists()]
    if missing:
        return False, f"Missing required directories: {', '.join(missing)}"

    return True, ""


def render():
    if not require_login():
        return

    st.header("⚙️ System Settings")
    st.caption("System configuration – Data Lake, Runtime, Connectivity")

    token = st.session_state.token

    # ---------- Health ----------
    with st.expander("🏥 Connection status", expanded=True):
        health = api_get_health_detail(token)
        if health:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Backend", "✅ OK" if health.get("backend") == "ok" else "❌")
            with col2:
                qdrant_ok = health.get("qdrant_connected", False)
                st.metric("Qdrant", "✅ Connected" if qdrant_ok else "❌ Not connected")
                if not qdrant_ok and health.get("qdrant_error"):
                    st.caption(f"Error: {health['qdrant_error']}")
            st.caption(f"Qdrant URL: `{health.get('qdrant_url', 'N/A')}`")
        else:
            st.warning("Could not fetch status (backend may not be running)")

    # ---------- Config Overview ----------
    with st.expander("📋 Runtime configuration (read-only)", expanded=True):
        config = api_get_config(token)
        if config:
            config_rows = [
                ("Data Lake path", config.get("data_base_path") or "(not set)"),
                ("Qdrant URL", config.get("qdrant_url", "N/A")),
                ("Embed model", config.get("embed_model", "N/A")),
                ("LLM model", config.get("llm_model", "N/A")),
                ("LLM base URL", config.get("llm_base_url_display", "N/A")),
                ("OpenAI API key", "Set" if config.get("openai_api_key_set") else "Not set"),
                ("LAKEFLOW_MODE", config.get("lakeflow_mode") or "(empty)"),
            ]
            if config.get("mount_description"):
                config_rows.append(("Mount description", config["mount_description"]))
            for k, v in config_rows:
                st.text(f"{k}: {v}")
        else:
            st.caption("Could not fetch config")

    # ---------- Zones Status ----------
    with st.expander("📂 Zone status", expanded=True):
        zones_data = api_get_zones_status(token)
        if zones_data and zones_data.get("zones"):
            all_ok = zones_data.get("all_zones_exist", False)
            st.metric("All zones", "✅ Complete" if all_ok else "⚠️ Missing zones", delta=None)

            cols = st.columns(2)
            for i, z in enumerate(zones_data["zones"]):
                with cols[i % 2]:
                    status = "✅" if z["exists"] else "❌"
                    count = z.get("file_count", 0) if z["exists"] else "-"
                    st.markdown(f"**{z['zone']}** {status} — {count} file(s)")

            if not all_ok:
                st.divider()
                if st.button("➕ Create missing zones", type="primary", use_container_width=True):
                    try:
                        result = api_create_zones(token)
                        st.success(result.get("message", "Zones created"))
                        st.rerun()
                    except requests.HTTPError as exc:
                        st.error(f"Error: {exc.response.text if exc.response else exc}")
                    except Exception as exc:
                        st.error(f"Error: {exc}")
        else:
            st.info("Data Lake path not configured or backend did not return zones")

    # ---------- Qdrant ----------
    with st.expander("🔗 Qdrant Service"):
        default_qdrant = QDRANT_DEFAULT_DOCKER if is_running_in_docker() else QDRANT_DEFAULT_DEV
        st.info(
            f"**Default:** `{default_qdrant}`\n\n"
            "Choose a different Qdrant on each page: **Semantic Search**, **Qdrant Inspector** "
            "(dropdown « Qdrant Service » or enter custom URL)."
        )

    # ---------- Data Lake Path Config ----------
    st.divider()
    st.subheader("🔧 Configure Data Lake Path")

    try:
        current_path = api_get_data_path(token)
    except Exception as exc:
        st.error(f"Could not fetch current path: {exc}")
        return

    if current_path:
        st.code(current_path)
        if is_running_in_docker():
            mount_note = (
                LAKEFLOW_MOUNT_DESCRIPTION
                if LAKEFLOW_MOUNT_DESCRIPTION
                else "Docker: this path is the mount point in the container (typically /data). "
                "Volume is configured in docker-compose."
            )
            st.caption(f"📌 {mount_note}")
    else:
        st.warning("Data Lake path not configured")

    selected_path: str | None = None

    if LAKEFLOW_MODE == "DEV":
        st.info("DEV mode: enter any Data Lake path")

        _default_path = (current_path or str(DATA_ROOT)).strip() or ""
        _key = "system_settings_data_path"
        if _key not in st.session_state:
            st.session_state[_key] = _default_path
        selected_path = st.text_input(
            "Data Lake root path",
            key=_key,
            placeholder="/Users/mac/Library/CloudStorage/... or /datalake/research",
        )

    else:
        st.warning("PROD mode: select from list")

        label = st.selectbox(
            "Select Data Lake",
            list(PROD_DATA_PATHS.keys()),
        )
        selected_path = PROD_DATA_PATHS[label]
        st.code(selected_path)

    if selected_path:
        is_valid, error = validate_local_path(selected_path)
        if is_valid:
            st.success("✔️ Data Lake structure valid")
        else:
            st.error(f"❌ {error}")

    if st.button("💾 Apply configuration", use_container_width=True):
        if not selected_path:
            st.warning("Data Lake path not selected")
            return

        ok, error = validate_local_path(selected_path)
        if not ok:
            st.error(f"Could not apply: {error}")
            return

        try:
            api_set_data_path(selected_path, token)
            st.success("✅ Data Lake path updated")
            st.rerun()
        except requests.HTTPError as exc:
            st.error(f"Backend error: {exc.response.text if exc.response else exc}")
        except Exception as exc:
            st.error(f"Error: {exc}")
