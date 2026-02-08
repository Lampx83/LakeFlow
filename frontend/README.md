# EDUAI – Streamlit Frontend (Control & Test UI)

## 1. Mục đích

Đây là **Streamlit Control UI** phục vụ cho:

- Test và debug Backend API
- Vận hành pipeline dữ liệu (DEV / nội bộ)
- Kiểm tra semantic search, ingestion, embedding
- Duyệt Data Lake theo các zone (000 → 500)

⚠️ **Không phải frontend sản phẩm**  
⚠️ **Không dùng cho end-user hoặc production**

---

## 2. Kiến trúc tổng quan

```text
[ Streamlit UI ]  →  [ FastAPI Backend ]  →  [ Qdrant Vector DB ]
        8501                8011                   6333
````

Frontend **không xử lý nghiệp vụ**, chỉ đóng vai trò:

* Gọi API
* Hiển thị kết quả
* Trigger pipeline (DEV)

---

## 3. Yêu cầu hệ thống

### 3.1. Bắt buộc

* Docker
* Docker Compose
* Backend EDUAI đã cấu hình đầy đủ

### 3.2. Các service liên quan

Frontend **phụ thuộc** vào:

* `eduai-backend`
* `qdrant`

Do đó **không chạy frontend độc lập**.

---

## 4. Chạy frontend bằng Docker Compose (khuyến nghị)

### 4.1. Cấu trúc liên quan

```text
project-root/
├── docker-compose.yml
├── .env
├── backend/
└── frontend/
    └── streamlit/
        ├── Dockerfile
        ├── requirements.txt
        ├── app.py
        └── README.md
```

---

### 4.2. File `.env` (ví dụ)

Đặt tại **project root**:

```env
# =========================
# EDUAI ENV
# =========================

EDUAI_MODE=DEV

# Backend API
API_BASE_URL=http://eduai-backend:8011

# Data path (trong container)
EDUAI_DATA_BASE_PATH=/data

# Qdrant
QDRANT_HOST=eduai-qdrant
QDRANT_PORT=6333
```

---

### 4.3. Khởi động toàn bộ hệ thống

Tại **project root**:

```bash
docker-compose up --build
```

Hoặc chạy nền:

```bash
docker-compose up -d --build
```

---

### 4.4. Truy cập frontend

Mở trình duyệt:

```
http://localhost:8501
```

Giao diện chính:

* Login
* Semantic Search
* Pipeline Runner (DEV)
* Data Lake Explorer

---

## 5. Chạy frontend ở chế độ DEV (không khuyến nghị)

⚠️ Chỉ dùng khi debug UI, **không dùng cho pipeline thật**

### 5.0. Cấu hình folder NAS khi chạy dev

Cấu hình trong **file `.env`** tại **project root** (thư mục `EDUAI/`).

Khi chạy dev (backend + frontend trên máy, không dùng Docker):

1. Mở **`.env`** (nếu chưa có thì copy từ `.env.example`).
2. **Comment** phần “Chạy Docker” (3 dòng `EDUAI_DATA_BASE_PATH`, `QDRANT_HOST`, `API_BASE_URL` với giá trị docker).
3. **Bỏ comment** phần “Chạy DEV” và đặt **`EDUAI_DATA_BASE_PATH`** = đường dẫn folder NAS của bạn:
   - Mac + Synology Drive: thường là `/Users/<user>/Library/CloudStorage/SynologyDrive-<tên share>` (ví dụ: `SynologyDrive-education`).
   - Hoặc path tới thư mục local chứa Data Lake (có các folder `000_inbox`, `100_raw`, …).

Ví dụ trong `.env` khi chạy dev:

```env
# Chạy DEV – folder NAS (Synology Drive hoặc path local)
EDUAI_DATA_BASE_PATH=/Users/mac/Library/CloudStorage/SynologyDrive-education
QDRANT_HOST=localhost
API_BASE_URL=http://localhost:8011
```

Backend và frontend đều đọc **`EDUAI_DATA_BASE_PATH`** từ `.env` (sau khi bạn `export` hoặc load env trước khi chạy). Data Lake Explorer trong UI sẽ dùng đúng folder NAS này.

### 5.1. Cài dependency

```bash
cd frontend/streamlit
pip install -r requirements.txt
```

### 5.2. Chạy Streamlit

**Bắt buộc chạy từ thư mục `frontend/streamlit`** (để Streamlit nhận config và watch đúng file):

```bash
cd frontend/streamlit
export $(grep -v '^#' ../../.env | xargs)
streamlit run app.py
```

Hoặc dùng script (từ project root):

```bash
./frontend/streamlit/run_dev.sh
```

### 5.3. Tự reload khi đổi code (dev)

**Cách 1 – Dùng script Python (khuyến nghị, chắc chắn reload):**

Từ **project root** (EDUAI):

```bash
cd /path/to/EDUAI
export $(grep -v '^#' .env | xargs)
python frontend/streamlit/dev_with_reload.py
```

Script này **restart Streamlit** mỗi khi bạn lưu file `.py` hoặc `.toml` trong `frontend/streamlit`. Không phụ thuộc config Streamlit.

**Cách 2 – Config Streamlit (runOnSave):**

Streamlit đọc config từ **thư mục bạn chạy lệnh** (CWD):

- Đã thêm **project root** config: `EDUAI/.streamlit/config.toml` (runOnSave + poll). Khi chạy từ project root, dùng:
  ```bash
  cd /path/to/EDUAI
  streamlit run frontend/streamlit/app.py
  ```
- Hoặc chạy từ **frontend/streamlit** (config trong `frontend/streamlit/.streamlit/config.toml`):
  ```bash
  cd frontend/streamlit
  streamlit run app.py --server.runOnSave true --server.fileWatcherType poll
  ```

Nếu vẫn không reload: dùng **Cách 1** (`dev_with_reload.py`).

⚠️ Lưu ý:

* Backend **phải chạy trước**
* Không mount được `/data` như Docker
* Một số chức năng Data Lake sẽ không hoạt động

---

## 6. Chức năng chính của UI

### 6.1. Login

* Username: `admin`
* Password: `admin123`
* Nhận JWT token để gọi API

---

### 6.2. Semantic Search

* Nhập query ngôn ngữ tự nhiên
* Chọn Qdrant từ dropdown **hoặc gõ địa chỉ Qdrant tùy chỉnh** (vd. `http://host:6333`)
* Truy vấn Qdrant, hiển thị chunk, score, metadata

---

### 6.3. Pipeline Runner (DEV ONLY)

Chỉ hiển thị khi:

```env
EDUAI_MODE=DEV
```

Bao gồm:

* 000 – Inbox ingestion
* 200 – File staging
* 300 – Processing
* 400 – Embedding
* 401 – Qdrant indexing

⚠️ **Tuyệt đối không bật ở production**

---

### 6.4. Data Lake Explorer

Duyệt trực tiếp các zone:

* `000_inbox`
* `100_raw`
* `200_staging`
* `300_processed`
* `400_embeddings`
* `500_catalog`

Hỗ trợ preview:

* `.json`
* `.txt`

---

## 7. Lưu ý bảo mật & vận hành

* UI **không có phân quyền**
* Token hiển thị rõ trên màn hình
* Chỉ dùng trong:

  * Môi trường DEV
  * Mạng nội bộ
  * Người vận hành kỹ thuật

