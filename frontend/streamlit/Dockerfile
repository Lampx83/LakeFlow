# syntax=docker/dockerfile:1
# Requires DOCKER_BUILDKIT=1 for pip cache
FROM python:3.10-slim

WORKDIR /app

# =========================
# Install dependencies
# =========================
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# =========================
# Copy source
# =========================
COPY . .

ENV STREAMLIT_SERVER_PORT=8012
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8012

CMD ["streamlit", "run", "app.py", "--server.port=8012", "--server.address=0.0.0.0"]
