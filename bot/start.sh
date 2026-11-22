#!/bin/bash
cd ~/www/questguiderf.ru/bot || exit 1
if pgrep -f "bot.main" > /dev/null; then
    echo "⚠️ Бот уже запущен! Остановите его перед запуском нового экземпляра."
    echo "Запущенные процессы:"
    ps aux | grep "bot.main" | grep -v grep
    echo ""
    echo "Для остановки используйте:"
    echo "  pkill -f 'bot.main'"
    echo "Или используйте скрипт: bash ~/www/questguiderf.ru/bot/stop_all_bots.sh"
    exit 1
fi
if [ ! -d "venv" ]; then
    echo "ОШИБКА: venv не найден! Создайте виртуальное окружение: python3 -m venv venv"
    exit 1
fi
source venv/bin/activate || exit 1
pip install --upgrade pip --quiet 2>/dev/null || true
if ! python -c "import aiogram" 2>/dev/null; then
    echo "Установка зависимостей..."
    pip install -r requirements.txt || {
        echo "ОШИБКА: Не удалось установить зависимости"
        echo "Попробуйте вручную: cd ~/www/questguiderf.ru/bot && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    }
fi
cd bot || exit 1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export PYTHONPATH="$(pwd)/..:${PYTHONPATH}"
python -m bot.main
