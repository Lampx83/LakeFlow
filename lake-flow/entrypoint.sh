#!/bin/sh
# Tạo các thư mục data lake và đảm bảo quyền ghi (tránh "unable to open database file" khi volume mount từ host).
DATA="${LAKEFLOW_DATA_BASE_PATH:-/data}"
for dir in 000_inbox 100_raw 200_staging 300_processed 400_embeddings 500_catalog; do
  mkdir -p "$DATA/$dir"
  chmod 777 "$DATA/$dir"
done
exec "$@"
