#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/quest_bot_${TIMESTAMP}.sql"
mkdir -p ${BACKUP_DIR}
echo "📦 Создание резервной копии БД..."
if [ ! -f "${ENV_FILE}" ]; then
    echo "❌ Файл .env не найден: ${ENV_FILE}"
    exit 1
fi
set -a
source "${ENV_FILE}"
set +a
docker-compose exec -T postgres pg_dump -U ${DB_USER} ${DB_NAME} > ${BACKUP_FILE}
if [ $? -eq 0 ]; then
    echo "✅ Резервная копия создана: ${BACKUP_FILE}"
    gzip ${BACKUP_FILE}
    echo "✅ Файл сжат: ${BACKUP_FILE}.gz"
    find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
    echo "🗑️  Старые бэкапы удалены"
else
    echo "❌ Ошибка при создании резервной копии"
    exit 1
fi
