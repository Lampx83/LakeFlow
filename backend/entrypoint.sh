#!/bin/sh
# Create data lake directories and ensure write permissions (avoid "unable to open database file" when volume mounted from host).
DATA="${LAKE_ROOT:-/data}"
for dir in 000_inbox 100_raw 200_staging 300_processed 400_embeddings 500_catalog; do
  mkdir -p "$DATA/$dir"
  chmod 777 "$DATA/$dir"
done
exec "$@"
