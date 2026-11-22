#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${BOT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
ENV_EXAMPLE="${ROOT_DIR}/.env.example"
cd "${BOT_DIR}" || exit 1
echo "🚀 Настройка Telegram Quest Bot..."
if [ ! -f "${ENV_FILE}" ]; then
    echo "📝 Создание .env файла..."
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    echo "⚠️  ВАЖНО: Заполните ${ENV_FILE} своими данными!"
else
    echo "✅ .env файл уже существует: ${ENV_FILE}"
fi
echo "📁 Создание необходимых директорий..."
mkdir -p photos
mkdir -p alembic/versions
echo "🐳 Запуск Docker контейнеров..."
docker-compose up -d postgres redis
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 5
echo "📊 Инициализация тестовых данных..."
python scripts/init_data.py
echo "✅ Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте ${ENV_FILE} (добавьте BOT_TOKEN и ADMIN_IDS)"
echo "2. Запустите бота: docker-compose up -d bot"
echo "   или локально: python -m bot.main"
echo ""
echo "Для просмотра логов: docker-compose logs -f bot"
