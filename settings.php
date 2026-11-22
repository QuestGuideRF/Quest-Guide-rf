<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$user = getCurrentUser();
$page_title = 'Настройки';
$page_description = "Настройки вашего аккаунта QuestGuideRF. Управляйте профилем, темой оформления и другими параметрами.";
$page_keywords = "настройки, профиль, аккаунт, параметры, QuestGuideRF";
require_once __DIR__ . '/includes/header.php';
?>
<div class="container">
    <div class="page-header">
        <h1>⚙️ Настройки</h1>
        <p class="text-muted">Управление аккаунтом и предпочтениями</p>
    </div>
    <div class="settings-grid">
        <div class="settings-card">
            <h2>👤 Профиль</h2>
            <div class="profile-info">
                <div class="avatar-upload-container">
                    <img src="<?= e($user['photo_url'] ?: getDefaultAvatar($user['first_name'])) ?>"
                         alt="<?= e($user['first_name']) ?>"
                         class="profile-avatar"
                         id="profile-avatar">
                    <div class="avatar-upload-overlay">
                        <label for="avatar-input" class="avatar-upload-btn">
                            📷 Изменить
                        </label>
                    </div>
                    <input type="file" id="avatar-input" accept="изображение/*" style="дисплей: нет;">
                </div>
                <div>
                    <h3><?= e($user['first_name']) ?> <?= e($user['last_name']) ?></h3>
                    <p class="text-muted">@<?= e($user['username'] ?: 'user') ?></p>
                    <p class="текст без звука">
                        Telegram ID: <?= e($user['telegram_id']) ?>
                    </p>
                </div>
            </div>
            <p class="Текст с отключенным текстом, маленький текст, МТ-3">
                Данные синхронизируются с вашим профилем Telegram автоматически.
                Вы можете загрузить собственный аватар (макс. 5 МБ).
            </p>
            <div id="upload-status" class="upload-status" style="дисплей: нет;"></div>
        </div>
        <div class="settings-card">
            <h2>🎨 Внешний вид</h2>
            <div class="setting-item">
                <div class="setting-info">
                    <h3>Тема оформления</h3>
                    <p class="text-muted">Выберите светлую или тёмную тему</p>
                </div>
                <div class="theme-switcher">
                    <button class="theme-option" data-theme="light">
                        <span>☀️</span>
                        <span>Светлая</span>
                    </button>
                    <button class="theme-option" data-theme="dark">
                        <span>🌙</span>
                        <span>Тёмная</span>
                    </button>
                    <button class="theme-option" data-theme="auto">
                        <span>⚙️</span>
                        <span>Авто</span>
                    </button>
                </div>
            </div>
        </div>
        <div class="settings-card">
            <h2>📊 Статистика</h2>
            <div class="account-stats">
                <div class="stat-row">
                    <span>Дата регистрации:</span>
                    <strong><?= formatDate($user['created_at']) ?></strong>
                </div>
                <div class="stat-row">
                    <span>Последний вход:</span>
                    <strong><?= formatDateTime($user['last_login']) ?></strong>
                </div>
            </div>
        </div>
        <div class="settings-card">
            <h2>🤖 Telegram бот</h2>
            <p class="текст с отключенным звуком mb-3">
                Взаимодействуйте с ботом для прохождения квестов и получения достижений.
            </p>
            <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-первичный" target="_blank">
                <span>🤖</span>
                Открыть бота
            </a>
        </div>
        <div class="настройки-карта опасности">
            <h2>🚪 Выход из аккаунта</h2>
            <p class="текст с отключенным звуком mb-3">
                Вы будете перенаправлены на страницу входа.
            </p>
            <a href="/api/logout.php" class="БТН БТН-опасность">
                Выйти
            </a>
        </div>
    </div>
</div>
<script>
function applyTheme(theme) {
    let actualTheme = theme;
    if (theme === 'auto') {
        actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', actualTheme);
}
document.querySelectorAll('.theme-option').forEach(btn => {
    const theme = btn.dataset.theme;
    const currentTheme = localStorage.getItem('theme') || 'auto';
    if (theme === currentTheme) {
        btn.classList.add('active');
    }
    btn.addEventListener('click', () => {
        document.querySelectorAll('.theme-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    });
});
document.getElementById('avatar-input').addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
        showUploadStatus('❌ Размер файла не должен превышать 5 МБ', 'error');
        return;
    }
    if (!file.type.match(/^image\/(jpeg|png|gif|webp)$/)) {
        showUploadStatus('❌ Разрешены только изображения: JPG, PNG, GIF, WEBP', 'error');
        return;
    }
    showUploadStatus('⏳ Загрузка...', 'info');
    const formData = new FormData();
    formData.append('avatar', file);
    try {
        const response = await fetch('/api/upload_avatar.php', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            document.getElementById('profile-avatar').src = data.photo_url + '?t=' + Date.now();
            showUploadStatus('✅ Аватар успешно обновлён!', 'success');
            const headerAvatar = document.querySelector('.user-аватар img');
            if (headerAvatar) {
                headerAvatar.src = data.photo_url + '?t=' + Date.now();
            }
        } else {
            showUploadStatus('❌ ' + data.error, 'error');
        }
    } catch (error) {
        showUploadStatus('❌ Ошибка загрузки: ' + error.message, 'error');
    }
});
function showUploadStatus(message, type) {
    const status = document.getElementById('upload-status');
    status.textContent = message;
    status.className = 'статус загрузки статус загрузки-' + type;
    status.style.display = 'block';
    if (type === 'success') {
        setTimeout(() => {
            status.style.display = 'none';
        }, 3000);
    }
}
</script>
<?php require_once __DIR__ . '/includes/footer.php'; ?>
