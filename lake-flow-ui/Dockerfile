FROM python:3.10-slim

WORKDIR /app

# =========================
# Install dependencies (context = lake-flow-ui/)
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Copy source
# =========================
COPY . .
WORKDIR /app

ENV STREAMLIT_SERVER_PORT=8012
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8012

CMD ["streamlit", "run", "app.py", "--server.port=8012", "--server.address=0.0.0.0"]
