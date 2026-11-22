#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
if [ $# -lt 1 ]; then
    echo "Использование: ./scripts/restore_db.sh <путь_к_бэкапу>"
    echo "Пример: ./scripts/restore_db.sh backups/quest_bot_20240101_120000.sql.gz"
    exit 1
fi
BACKUP_FILE=$1
if [ ! -f ${BACKUP_FILE} ]; then
    echo "❌ Файл не найден: ${BACKUP_FILE}"
    exit 1
fi
echo "⚠️  ВНИМАНИЕ! Это действие перезапишет текущую базу данных!"
read -p "Продолжить? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Восстановление отменено"
    exit 0
fi
if [ ! -f "${ENV_FILE}" ]; then
    echo "❌ Файл .env не найден: ${ENV_FILE}"
    exit 1
fi
set -a
source "${ENV_FILE}"
set +a
echo "📦 Восстановление БД из ${BACKUP_FILE}..."
if [[ ${BACKUP_FILE} == *.gz ]]; then
    gunzip -c ${BACKUP_FILE} | docker-compose exec -T postgres psql -U ${DB_USER} ${DB_NAME}
else
    cat ${BACKUP_FILE} | docker-compose exec -T postgres psql -U ${DB_USER} ${DB_NAME}
fi
if [ $? -eq 0 ]; then
    echo "✅ База данных восстановлена успешно!"
else
    echo "❌ Ошибка при восстановлении БД"
    exit 1
fi
