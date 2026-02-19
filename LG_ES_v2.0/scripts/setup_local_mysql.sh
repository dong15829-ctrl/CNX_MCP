#!/usr/bin/env bash
# EC2 등 앱 서버에 로컬 MySQL (Docker) 설치.
# 사용: bash scripts/setup_local_mysql.sh

set -e
cd "$(dirname "$0")/.."

MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-lg_ha}"
MYSQL_USER="${MYSQL_USER:-lg_ha}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-local_lg_ha_secret}"
CONTAINER_NAME="${CONTAINER_NAME:-lg_ha_local}"

if command -v docker >/dev/null 2>&1; then
  echo "Docker detected. Creating MySQL container: $CONTAINER_NAME"
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container $CONTAINER_NAME already exists. Start with: docker start $CONTAINER_NAME"
    exit 0
  fi
  docker run -d \
    --name "$CONTAINER_NAME" \
    -e MYSQL_ROOT_PASSWORD="${MYSQL_PASSWORD}" \
    -e MYSQL_DATABASE="$MYSQL_DATABASE" \
    -e MYSQL_USER="$MYSQL_USER" \
    -e MYSQL_PASSWORD="$MYSQL_PASSWORD" \
    -p "${MYSQL_PORT}:3306" \
    mysql:8.0 \
    --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
  echo "MySQL container started. Set in .env: MYSQL_HOST=127.0.0.1 MYSQL_PORT=$MYSQL_PORT"
  echo "Then run sync: .venv/bin/python scripts/sync_remote_to_local.py"
else
  echo "Docker not found. Install MySQL 8 locally and create database/user."
  exit 1
fi
