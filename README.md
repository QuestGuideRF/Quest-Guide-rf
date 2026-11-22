# 🎯 QuestGuideRF - Интерактивный Экскурсовод + Веб-сайт

**Production-ready проект:** Telegram-бот для квест-экскурсий + веб-сайт личного кабинета для **единого хостинга REG.RU**.

## 🚀 Что это?

Полноценная система для проведения интерактивных городских квестов:

- **Telegram бот** (Python 3.8+) - ведет пользователя по маршруту, проверяет фото, выдает факты
- **Веб-сайт** (PHP 7.4+) - личный кабинет со статистикой, фотографиями, достижениями
- **Единая БД MySQL** - одна база для бота и сайта
- **Единая папка uploads/** - общее хранилище фото

## ✨ Возможности

### Telegram Бот
- 🗺️ Квест-экскурсии по городам
- 📸 Проверка фото (локация + позы + количество людей через MoveNet ONNX)
- 💰 Оплата через Telegram Payments (ЮКassa) - 399₽
- 🏆 Система достижений (10 готовых)
- 🔐 Админ-панель в боте
- 🛡️ Антифрод защита
- 🌐 Команда `/web` - вход на сайт
- 🔍 Ручная проверка фото администраторами (при ошибках автоматических проверок)

### Веб-сайт
- 🔐 Авторизация через Telegram (Login Widget + токены от `/web`), Google OAuth и Яндекс OAuth
- 📊 Dashboard с статистикой
- 🗺️ История экскурсий
- 📸 Галерея фотографий
- 💳 История покупок
- 🏆 Коллекция достижений
- 🌓 Светлая/тёмная тема (мгновенное переключение)
- 📱 Mobile-first дизайн
- 📷 Загрузка собственного аватара
- 🤖 SEO: robots.txt, sitemap.xml
- 📄 Кастомные страницы ошибок (404, 403, 500)

## 📁 Структура на хостинге REG.RU

```
/var/www/html/                      # Корень сайта (public_html)
│
├── index.php                       # Сайт (PHP 7.4+)
├── dashboard.php
├── routes.php
├── photos.php
├── payments.php
├── achievements.php
├── settings.php
├── 404.php, 403.php, 500.php      # Страницы ошибок
├── robots.txt                      # SEO
├── sitemap.xml                     # SEO
│
├── api/                            # API сайта
│   ├── upload_avatar.php          # Загрузка аватара
│   ├── logout.php
│   └── ...
│
├── auth/
│   └── telegram.php                # Авторизация через токены бота
│
├── includes/                       # PHP модули
├── assets/                         # CSS/JS
├── pages/
│
├── bot/                            # Telegram бот (Python 3.8+)
│   ├── bot/                        # Основной код
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── loader.py
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── pose_movenet.py    # MoveNet ONNX для проверки поз
│   │   │   ├── admin_notifier.py  # Уведомления админам
│   │   │   └── ...
│   │   ├── routers/
│   │   │   ├── admin.py            # Обработка принятия/отклонения фото
│   │   │   └── ...
│   │   └── ...
│   ├── requirements.txt
│   └── start.sh
│
├── photos/                         # Фото пользователей (создаётся ботом)
│   └── {telegram_id}/
│
├── uploads/                        # ОБЩАЯ папка для фото
│   ├── avatars/                    # Аватары пользователей
│   │   └── {user_id}/
│   ├── users/                      # Фото пользователей (legacy)
│   ├── reference/                  # Эталонные фото
│   └── temp/                       # Временные файлы
│
├── database/
│   └── schema.sql                  # ОБЩАЯ схема MySQL
│
├── .env                            # Единый конфиг сайта и бота
├── .env.example                    # Пример конфига без секретов
└── .htaccess                       # Apache настройки
```

## 🚀 Установка на REG.RU

### Шаг 1: Создание БД

**Через панель REG.RU:**
1. Базы данных → MySQL → Создать
2. Имя: `u3372144_schema`, кодировка: `utf8mb4_unicode_ci`
3. Создать пользователя с полными правами
4. Запомнить: хост, имя БД, пользователь, пароль

### Шаг 2: Загрузка файлов

**Через FTP (FileZilla/WinSCP):**
1. Подключиться к ftp.ваш-домен.ru
2. Перейти в `www`
3. Загрузить:
   - Все файлы из `Site/` → в корень
   - Папку `bot/` → как есть

### Шаг 3: Настройка

**Обновите единый `.env`** (в корне `www/Ваш домен/.env`):
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quest_bot
DB_USER=quest_bot_user
DB_PASS=ваш_пароль_mysql
BOT_TOKEN=ваш_токен_от_BotFather
BOT_USERNAME=ваш_бот_username
ADMIN_IDS=ваш_telegram_id,второй_админ_id
MODERATOR_IDS=
SITE_URL=https://ваш-домен.ru
DEBUG=false
API_SECRET=случайная_строка_123
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=https://ваш-домен.ru/auth/oauth_callback.php?provider=google
YANDEX_OAUTH_CLIENT_ID=
YANDEX_OAUTH_CLIENT_SECRET=
YANDEX_OAUTH_REDIRECT_URI=https://ваш-домен.ru/auth/oauth_callback.php?provider=yandex
PAYMENT_PROVIDER_TOKEN=
DEFAULT_PRICE=399
SIMILARITY_THRESHOLD=0.75
POSE_CONFIDENCE=0.5
```

Файл `bot/.env` больше не используется: бот находит корневой `.env` по пути относительно `bot/bot/config.py`.

### Шаг 4: Запуск бота

**Если есть SSH доступ:**
```bash
cd ~/www/questguiderf.ru/bot
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd bot
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export PYTHONPATH="$(pwd)/..:${PYTHONPATH}"
../venv/bin/python -m bot.main
```

**Полезные команды для screen:**
```bash
screen -ls                    # Список сессий
screen -r questbot            # Подключиться к сессии
# Внутри screen: Ctrl+A, затем D - отключиться
```

### Шаг 5:

1. ✅ Открыть https://ваш-домен.ru
2. ✅ Увидеть кнопку "Login with Telegram"
3. ✅ Авторизоваться
4. ✅ В боте отправить `/start`
5. ✅ В боте отправить `/web` → получить ссылку на сайт

## 🛠 Технологии

**Бот:**
- Python 3.8+
- aiogram 3.4
- MySQL 8.0 (aiomysql)
- OpenCV + MoveNet Lightning ONNX (вместо MediaPipe)
- ONNX Runtime для проверки поз

**Сайт:**
- PHP 7.4+
- MySQL 8.0 (PDO)
- Vanilla JS
- CSS3 (Mobile-first)

## 📋 База данных (ОБЩАЯ)

**11 таблиц:**
- `users` - пользователи
- `cities` - города
- `routes` - маршруты
- `points` - точки маршрутов
- `reference_images` - эталонные фото
- `user_progress` - прогресс (бот пишет → сайт читает)
- `payments` - платежи (бот пишет → сайт читает)
- `user_photos` - фотографии (бот пишет → сайт читает)
- `user_sessions` - токены входа (бот создает → сайт использует)
- `achievements` + `user_achievements` - достижения

## 🔗 Как работает интеграция

### 1. Общая БД MySQL

Бот и сайт работают с **одной** базой `quest_bot`:

```python
# bot/bot/config.py
return f"mysql+aiomysql://user:password@localhost:3306/quest_bot"
```

```php
// Site/includes/db.php
new PDO("mysql:host=localhost;dbname=quest_bot", "user", "password");
```

### 2. Общая папка для фото

```python
# Бот сохраняет в:
/var/www/html/photos/{telegram_id}/point_{id}_{timestamp}.jpg
```

```php
// Сайт читает из:
<img src="/photos/{telegram_id}/point_{id}_{timestamp}.jpg">
```

### 3. Авторизация через токены

**В боте:**
```
Пользователь → /web
Бот → генерирует токен в таблицу user_sessions
Бот → отправляет кнопку с ссылкой https://site.ru/auth/telegram?token=XXX
```

**На сайте:**
```php
// Site/auth/telegram.php
Проверяет токен → Авторизует пользователя → Перенаправляет на dashboard
```

## ⚙️ Конфигурация

Для настройки веб-сайта и бота используйте [шаблон окружения](.env.example).

Сайт и бот используют один файл окружения: `.env` в корне проекта. Для нового окружения скопируйте `.env.example` в `.env` и заполните реальные значения.

### Единый `.env` в корне

```env
# MySQL - ОБЩАЯ БД
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quest_bot
DB_USER=quest_bot_user
DB_PASS=replace_with_your_db_pass

# Telegram Bot
BOT_TOKEN=123456:ABC-DEF...
BOT_USERNAME=your_bot_username
ADMIN_IDS=123456789,987654321
MODERATOR_IDS=

# Site and Web Integration
SITE_URL=https://yourdomain.com
DEBUG=false
API_SECRET=replace_with_your_api_secret

# OAuth login
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/auth/oauth_callback.php?provider=google
YANDEX_OAUTH_CLIENT_ID=
YANDEX_OAUTH_CLIENT_SECRET=
YANDEX_OAUTH_REDIRECT_URI=https://yourdomain.com/auth/oauth_callback.php?provider=yandex

# Payments
PAYMENT_PROVIDER_TOKEN=
DEFAULT_PRICE=399

# Photo checks
GOOGLE_CREDENTIALS_PATH=
SIMILARITY_THRESHOLD=0.75
POSE_CONFIDENCE=0.5
```

## 🎯 Тестовые данные

После импорта schema.sql будут созданы:

**Город:** Москва
**Маршрут:** Исторический центр (399₽)
**Точки:** 3 (Красная площадь, Храм Василия Блаженного, ГУМ)
**Достижения:** 10 штук (от "Первые шаги" до "Легенда")

## 🔧 Управление
### Бот

**Полезные команды:**
```bash
screen -ls                    # Список сессий
screen -r questbot            # Подключиться
# Внутри screen: Ctrl+A, затем D - отключиться
```

### Очистка временных файлов

**Добавить в cron:**
```bash
crontab -e
```

```cron
# Очистка каждый день в 3:00
0 3 * * * /var/www/html/bot/venv/bin/python /var/www/html/bot/bot/utils/cleanup.py

# Бэкап БД каждый день в 4:00
0 4 * * * mysqldump -u quest_bot_user -pPASSWORD quest_bot > /var/www/html/backups/db_$(date +\%Y\%m\%d).sql
```

```bash
# Проверка бота
screen -r questbot
tail -f /var/www/html/bot/bot.log

# Проверка БД
mysql -u quest_bot_user -p quest_bot
> SELECT COUNT(*) FROM users;
> SELECT * FROM routes;

# Очистка временных файлов
cd /var/www/html/bot
source venv/bin/activate
python bot/utils/cleanup.py

# Перезапуск бота
screen -r questbot
# Ctrl+C для остановки
```

## 📱 Использование

### Пользователь:

1. **В Telegram:** отправить `/start` боту
2. Выбрать город и маршрут
3. Оплатить 399₽
4. Пройти квест (фото на каждой точке)
5. Получить достижения

6. **На сайте:** `/web` в боте → войти → смотреть статистику

### Администратор:

1. **В боте:** `/admin` → управление городами/маршрутами/точками
2. **Проверка фото:** при ошибках автоматических проверок админы получают уведомления с кнопками "Принять/Отклонить"
3. **В БД:** прямые SQL запросы для расширенной настройки

## 🏆 Достижения (автоматически)

- 🎯 **Первые шаги** - завершите 1 маршрут
- 🗺️ **Исследователь** - пройдите 5 маршрутов
- 🏆 **Мастер квестов** - 10 маршрутов
- 📍 **Коллекционер** - 50 точек
- 📸 **Фотограф** - 100 фото
- 💯 **Перфекционист** - 100% прохождение
- ⚡ **Быстрый** - быстрее ожидаемого времени
- 🌙 **Ночной странник** - квест ночью (22:00-06:00)
- 🌅 **Ранняя пташка** - квест до 8:00
- 👑 **Легенда** - все достижения

## 🔧 Ключевые особенности и реализованные фиксы

### Проверка фото

**Автоматическая проверка:**
1. Антифрод (повторное использование, EXIF, timing)
2. Количество людей (Haar Cascade)
3. Поза (MoveNet Lightning ONNX или упрощённая проверка через OpenCV)
4. Локация (OpenCV ORB)

**Ручная проверка админом:**
- При ошибках автоматических проверок фото отправляется админам
- Админы видят: фото, маршрут, точку, причину отклонения, количество людей, позу, совпадение локации
- Кнопки: "✅ Принять" / "❌ Отклонить"
- При принятии: фото сохраняется, точка засчитывается, пользователь переходит дальше
- При отклонении: пользователь получает уведомление с рекомендациями

### Оптимизация для shared hosting

- **MoveNet ONNX** вместо MediaPipe (легче на ресурсы)
- **Последовательная обработка** проверок (не параллельно)
- **Явное освобождение памяти** (`del`, `gc.collect()`)
- **Уменьшение размера изображений** перед обработкой
- **Ограничение потоков** (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`)

### Веб-сайт

- **Тема оформления:** применяется на всех страницах, мгновенное переключение без перезагрузки
- **Мобильное меню:** работает корректно на всех устройствах
- **Аватар:** круглый, без искажений, возможность загрузки собственного
- **SEO:** robots.txt, sitemap.xml, кастомные страницы ошибок
- **Загрузка аватара:** автоматическая обработка (300x300px), обрезка по центру

### Уведомления админам

- При запуске/перезапуске бота
- При критических ошибках (с логом)
- При ошибках проверки фото (для ручной проверки)

## ❓ FAQ

### Как получить токен бота?

@BotFather → `/newbot` → скопировать токен

### Как узнать свой Telegram ID?

@LeadConverterToolkitBot → отправить сообщение /get_my_id → скопировать ID

### Почему не работает Login Widget?

1. Проверьте `BOT_USERNAME` в .env (без @)
2. Зарегистрируйте домен в BotFather (Bot Settings → Domain)
3. Убедитесь, что сайт работает по HTTPS

### Сайт показывает ошибку БД?

1. Проверьте настройки в `.env`
2. Убедитесь, что схема импортирована
3. Проверьте права пользователя БД

### Фотографии не отображаются?

```bash
# Установите права
chmod 755 /var/www/html/photos
chmod -R 755 /var/www/html/photos/
```

## 📝 Команды бота

**Пользовательские:**
- `/start` - начало работы
- `/web` - вход на сайт (получить ссылку с токеном)

**Админские:**
- `/admin` - админ-панель (управление городами, маршрутами, точками, ценами)

| Проблема | Решение |
|----------|---------|
| Бот не запускается | Проверить .env, логи, установку зависимостей |
| Сайт не открывается | Проверить .env, права на файлы, PHP 7.4+ |
| Login не работает | Зарегистрировать домен в BotFather, HTTPS |
| БД ошибка | Проверить данные подключения, импорт схемы |
| Фото не видны | Права 755 на photos/, проверить пути в БД |
| Бот пропускает фото | Проверки исправлены, при ошибках отправляется админам |
| Админ не может принять фото | Исправлено: photo_file_id из сообщения |

## 🔐 Безопасность

- ✅ SQL-инъекции: PDO + SQLAlchemy ORM
- ✅ XSS: htmlspecialchars() везде
- ✅ Антифрод: хеши фото, timing, EXIF
- ✅ Токены: одноразовые, срок 5 минут
- ✅ Сессии: 90 дней, безопасное хранение
- ✅ API Secret: защита API endpoints
- ✅ .htaccess: защита конфигов

## 💰 Монетизация

**По умолчанию:** 399₽ за маршрут

**Тестовый режим:** Если `PAYMENT_PROVIDER_TOKEN` пустой - маршруты бесплатны

**Настройка ЮКassa:**
1. Зарегистрироваться на yookassa.ru
2. Получить токен для Telegram Payments
3. Добавить в корневой `.env`: `PAYMENT_PROVIDER_TOKEN=токен`

---

Автор: legenda  
Telegram: [@LEGENDA_SD](https://t.me/LEGENDA_SD)
