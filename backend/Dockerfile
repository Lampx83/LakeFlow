FROM python:3.10-slim

# ---------- System deps ----------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------- Workdir ----------
WORKDIR /app

# ---------- Python deps ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Project ----------
COPY . .

# ---------- Env ----------
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "eduai.main:app", "--host", "0.0.0.0", "--port", "8011"]