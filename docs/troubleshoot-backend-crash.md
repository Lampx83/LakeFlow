# Backend container Restarting / Connection refused

Khi `docker ps` thấy `lakeflow-backend` có **STATUS = Restarting**, backend đang crash và Docker tự khởi động lại.

## 1. Xem log backend (bắt buộc)

Trên server chạy:

```bash
docker logs lakeflow-backend
```

Hoặc 100 dòng gần nhất:

```bash
docker logs --tail 100 lakeflow-backend
```

Traceback Python hoặc lỗi in ra sẽ cho biết nguyên nhân (thiếu env, lỗi import, không kết nối được Qdrant, v.v.).

## 2. Các lỗi thường gặp

- **Missing required environment variable**  
  Trên server cần có file `.env` (hoặc cấu hình env trong compose). Ít nhất:  
  `LAKEFLOW_DATA_BASE_PATH=/data`, `QDRANT_HOST=lakeflow-qdrant`, `QDRANT_PORT=6333`.

- **Connection refused / Qdrant**  
  Backend cần Qdrant chạy trước. Kiểm tra: `docker ps` có `lakeflow-qdrant` đang Up. Nếu Qdrant đang khởi động chậm, backend có thể crash khi gọi Qdrant lần đầu; thử restart:  
  `docker compose -f docker-compose.yml -f docker-compose.deploy.yml restart lakeflow-backend`.

- **Permission / path**  
  Nếu log báo lỗi đọc/ghi thư mục (vd. `/data`): kiểm tra quyền thư mục bind mount (vd. `/datalake/research`) và user chạy container.

Sau khi sửa (env, quyền, v.v.), chạy lại:

```bash
export LAKEFLOW_DATA_PATH=/datalake/research
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build
```
