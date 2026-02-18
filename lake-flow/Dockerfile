# syntax=docker/dockerfile:1
# Build: DOCKER_BUILDKIT=1. TORCH_CPU=1 (mặc định): PyTorch CPU-only → server/CI nhanh, không kéo CUDA.
# Mac M1 dev dùng GPU (Metal/MPS): chạy backend bằng venv trên macOS (không Docker), pip install torch rồi requirements.txt.
FROM python:3.10-slim

# ---------- Build arg: 1 = PyTorch CPU (server/CI), 0 = PyTorch từ PyPI (Linux có GPU hoặc Docker trên Mac) ----------
ARG TORCH_CPU=1

# ---------- System deps ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------- Workdir ----------
WORKDIR /app

# ---------- Python deps ----------
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$TORCH_CPU" = "1" ]; then \
        pip install 'torch~=2.4.0' --index-url https://download.pytorch.org/whl/cpu; \
    else \
        pip install 'torch~=2.4.0'; \
    fi
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# ---------- Project ----------
COPY . .

# ---------- Entrypoint: tạo thư mục /data (500_catalog, ...) và chmod để tránh "unable to open database file" ----------
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# ---------- Env ----------
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "lakeflow.main:app", "--host", "0.0.0.0", "--port", "8011"]