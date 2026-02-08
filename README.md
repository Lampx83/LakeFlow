# Project Overview

Hệ thống được thiết kế để chạy **toàn bộ bằng Docker**, đảm bảo tính nhất quán môi trường, dễ triển khai và dễ mở rộng. Người dùng **không cần cài đặt trực tiếp Python hay các thư viện phụ thuộc** trên máy host.

---

## Yêu cầu hệ thống

- Docker >= 20.x  
- Docker Compose >= 2.x  

Kiểm tra:
```bash
docker --version
docker compose version
````

---

## Cấu trúc triển khai (tổng quan)

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── env.example
├── ...
```

---

## Thiết lập môi trường

### 1. Tạo file biến môi trường

Sao chép file mẫu:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` theo cấu hình mong muốn (port, database, API key, … nếu có).

---

## Chạy DEV (frontend + backend trên máy, không Docker)

Khi phát triển trên máy (backend + Streamlit UI chạy trực tiếp, không qua Docker):

### 1. Cấu hình `.env` (tại thư mục gốc project)

- Dùng phần **“Chạy DEV”** trong `.env`: bỏ comment `EDUAI_MODE`, `EDUAI_DATA_BASE_PATH`, `QDRANT_HOST`, `API_BASE_URL`.
- Đặt `EDUAI_DATA_BASE_PATH` = đường dẫn folder NAS / Data Lake (ví dụ Synology Drive: `/Users/<user>/Library/CloudStorage/SynologyDrive-<tên>`).
- Bên trong folder đó phải có các zone: `000_inbox`, `100_raw`, `200_staging`, `300_processed`, `400_embeddings`, `500_catalog`.

Ví dụ:

```env
EDUAI_MODE=DEV
EDUAI_DATA_BASE_PATH=/Users/mac/Library/CloudStorage/SynologyDrive-research
QDRANT_HOST=localhost
API_BASE_URL=http://localhost:8011
```

### 2. (Tuỳ chọn) Chạy Qdrant

Nếu dùng Semantic Search / Qdrant:

```bash
docker compose up -d qdrant
```

### 3. Chạy Backend

Từ **thư mục gốc project** (EDUAI):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Load .env từ project root (backend đọc .env khi import)
python -m uvicorn eduai.main:app --reload --port 8011
```

Backend chạy tại: **http://localhost:8011**

### 4. Chạy Frontend (Streamlit)

Mở **terminal mới**, từ **thư mục gốc project**:

```bash
# Load biến từ .env rồi chạy Streamlit (có auto-reload khi đổi code)
export $(grep -v '^#' .env | xargs)
python frontend/streamlit/dev_with_reload.py
```

Hoặc chạy Streamlit trực tiếp:

```bash
cd frontend/streamlit
export $(grep -v '^#' ../../.env | xargs)
streamlit run app.py
```

Frontend chạy tại: **http://localhost:8501**

### 5. Thứ tự và kiểm tra

1. **Chạy Backend trước**, sau đó mới chạy Frontend.
2. Đăng nhập UI: `admin` / `admin123`.
3. Pipeline Runner chỉ hiện khi `EDUAI_MODE=DEV`.

---

## Chạy hệ thống bằng Docker

### 2. Build và khởi động toàn bộ hệ thống

```bash
docker compose up --build
```

Hoặc chạy ở chế độ nền:

```bash
docker compose up -d --build
```

Docker sẽ:

* Build image từ `Dockerfile`
* Cài đặt dependencies từ `requirements.txt`
* Khởi động toàn bộ service được định nghĩa trong `docker-compose.yml`

---

## Dừng hệ thống

```bash
docker compose down
```

Dừng và xóa toàn bộ container, network (không xóa image).

---

## Xem log hệ thống

```bash
docker compose logs -f
```

Hoặc theo từng service:

```bash
docker compose logs -f <service_name>
```

---

## Rebuild khi có thay đổi code

```bash
docker compose down
docker compose up --build
```

---

## Ghi chú

* Không chạy trực tiếp ứng dụng bằng `python main.py` trên host
* Mọi thao tác phát triển, test, deploy đều thực hiện **thông qua Docker**
* Khuyến nghị dùng Docker ngay cả trong môi trường development

---

## Triển khai (Deployment)

Hệ thống có thể triển khai trực tiếp trên:

* VPS
* Server vật lý
* Cloud (AWS / GCP / Azure)

### Deploy tự động khi push lên `main` (GitHub Actions)

Khi push code lên branch `main`, workflow `.github/workflows/deploy.yml` sẽ SSH vào server và chạy `git pull` + `docker compose up -d --build` (dùng `docker-compose.prod.yml` để chạy production).

**Bước 1 – Trên server (chỉ làm một lần):**

1. Cài Docker và Docker Compose.
2. Clone repo (ví dụ `$HOME/EDUAI`):  
   `git clone https://github.com/<org>/EDUAI.git`
3. Tạo file `.env` trong thư mục repo (copy từ `.env.example` và điền giá trị).
4. (Tùy chọn) Cấu hình SSH: user deploy có quyền pull (hoặc dùng SSH key cho GitHub Actions).

**Bước 2 – Trong GitHub repo:**

Vào **Settings → Secrets and variables → Actions**, thêm Secrets:

| Secret | Mô tả |
|--------|--------|
| `DEPLOY_HOST` | IP hoặc hostname server (ví dụ `1.2.3.4` hoặc `deploy.example.com`) |
| `DEPLOY_USER` | User SSH (ví dụ `ubuntu`) |
| `SSH_PRIVATE_KEY` | Nội dung private key SSH (đủ để SSH vào server) |
| `DEPLOY_REPO_DIR` | (Tùy chọn) Đường dẫn thư mục repo trên server (mặc định `$HOME/EDUAI`) |
| `DEPLOY_SSH_PORT` | (Tùy chọn) Cổng SSH, mặc định `22` |

Sau khi cấu hình, mỗi lần push lên `main`, workflow sẽ tự deploy lên server.

**Khi deploy – cần lưu ý:**

1. **File `.env` trên server**  
   Workflow **không** tạo hay sửa file `.env`. Trên server bạn phải tự tạo `.env` (copy từ `.env.example`, điền giá trị production). Ví dụ production:
   - `EDUAI_DATA_BASE_PATH=/data` (volume mount trong Docker)
   - `QDRANT_HOST=eduai-qdrant` (đã set trong `docker-compose.yml` cho backend; không chọn gì trong UI = dùng Qdrant trong Docker)
   - `API_BASE_URL` = URL để user truy cập backend (vd `http://<server-ip>:8011` hoặc domain reverse proxy)

2. **Qdrant khi chạy Docker**  
   Mặc định backend đã dùng `eduai-qdrant:6333`. Nếu cần **thêm** Qdrant service khác (vd Qdrant chạy ở máy khác), trong `.env` trên server thêm:
   - `QDRANT_SERVICES="http://qdrant-remote:6333"` hoặc `QDRANT_SERVICES="Production|https://qdrant.prod.example.com:6333"`  
   Frontend sẽ đọc và hiển thị thêm lựa chọn trong dropdown; backend kết nối tới URL được chọn.

3. **Volume dữ liệu (prod)**  
   `docker-compose.prod.yml` dùng named volume `eduai_data` (không bind path host). Data nằm trong volume Docker; cần backup hoặc mount path cụ thể nếu muốn lưu ra ổ đĩa server.