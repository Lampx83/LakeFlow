FROM python:3.10-slim

WORKDIR /app

# =========================
# Install dependencies
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Copy toàn bộ source frontend
# =========================
COPY . .

# =========================
# Streamlit config
# =========================
ENV STREAMLIT_SERVER_PORT=8012
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
