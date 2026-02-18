# Backend container Restarting / Connection refused

When `docker ps` shows `lakeflow-backend` with **STATUS = Restarting**, the backend is crashing and Docker is restarting it.

## 1. Check backend logs (required)

On the server run:

```bash
docker logs lakeflow-backend
```

Or the last 100 lines:

```bash
docker logs --tail 100 lakeflow-backend
```

The Python traceback or printed errors will show the cause (missing env, import error, cannot connect to Qdrant, etc.).

## 2. Common issues

- **Missing required environment variable**  
  The server must have a `.env` file (or env configured in compose). At minimum:  
  `LAKEFLOW_DATA_BASE_PATH=/data`, `QDRANT_HOST=lakeflow-qdrant`, `QDRANT_PORT=6333`.

- **Connection refused / Qdrant**  
  The backend needs Qdrant running first. Check: `docker ps` shows `lakeflow-qdrant` as Up. If Qdrant is starting slowly, the backend may crash on first Qdrant call; try restarting:  
  `docker compose -f docker-compose.yml -f docker-compose.deploy.yml restart lakeflow-backend`.

- **Permission / path**  
  If the log reports read/write errors on a directory (e.g. `/data`): check permissions on the bind mount (e.g. `/datalake/research`) and the user running the container.

After fixing (env, permissions, etc.), run again:

```bash
export LAKEFLOW_DATA_PATH=/datalake/research
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build
```
