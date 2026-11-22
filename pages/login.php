<?php
if (!defined('APP_INIT')) {
    require_once __DIR__ . '/../includes/init.php';
}
$page_title = 'Вход';
$page_description = "Войдите в личный кабинет QuestGuideRF через Telegram. Просматривайте свои экскурсии, достижения и фотографии.";
$page_keywords = "войти, авторизация, QuestGuideRF, Telegram, личный кабинет, экскурсии, квесты";
$current_url = 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
$site_url = rtrim(SITE_URL, '/');
$og_image = $site_url . '/favicons/android-chrome-512x512.png';
$yandex_auth_url = getOAuthAuthorizationUrl('yandex');
$google_auth_url = getOAuthAuthorizationUrl('google');
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= e($page_title) ?> - <?= SITE_NAME ?></title>
    <meta name="description" content="<?= e($page_description) ?>">
    <meta name="keywords" content="<?= e($page_keywords) ?>">
    <meta name="author" content="<?= SITE_NAME ?>">
    <meta name="robots" content="noindex, nofollow">
    <meta name="language" content="Russian">
    <link rel="canonical" href="<?= $current_url ?>">
    <meta property="og:type" content="website">
    <meta property="og:url" content="<?= $current_url ?>">
    <meta property="og:title" content="<?= e($page_title) ?> - <?= SITE_NAME ?>">
    <meta property="og:description" content="<?= e($page_description) ?>">
    <meta property="og:image" content="<?= $og_image ?>">
    <meta property="og:site_name" content="<?= SITE_NAME ?>">
    <meta property="og:locale" content="ru_RU">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="<?= $current_url ?>">
    <meta name="twitter:title" content="<?= e($page_title) ?> - <?= SITE_NAME ?>">
    <meta name="twitter:description" content="<?= e($page_description) ?>">
    <meta name="twitter:image" content="<?= $og_image ?>">
    <meta name="theme-color" content="#4a90e2">
    <link rel="apple-touch-icon" sizes="180x180" href="/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicons/favicon-16x16.png">
    <link rel="manifest" href="/favicons/site.webmanifest">
    <link rel="shortcut icon" href="/favicons/favicon.ico">
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body class="login-page">
    <div class="login-container">
        <div class="login-card">
            <div class="login-header">
                <div class="logo">🎯</div>
                <h1>QuestGuideRF</h1>
                <p>Интерактивные экскурсии-квесты</p>
            </div>
            <div class="login-content">
                <p class="text-muted mb-4">
                    Войдите через Telegram, Яндекс или Google, чтобы увидеть свою статистику,
                    пройденные маршруты и достижения.
                </p>
                <div id="telegram-login-container">
                    <script async src="https://telegram.org/js/telegram-widget.js?22"
                            data-telegram-login="<?= e(BOT_USERNAME) ?>"
                            data-size="large"
                            data-auth-url="<?= e($site_url) ?>/api/telegram_auth.php"
                            data-request-access="write">
                    </script>
                </div>
                <div class="oauth-login-options" aria-label="Другие способы входа">
                    <a href="<?= e($yandex_auth_url ?: '#') ?>"
                       class="oauth-button oauth-button-yandex <?= $yandex_auth_url ? '' : 'is-disabled' ?>"
                       <?= $yandex_auth_url ? '' : 'aria-disabled="true" onclick="return false;" title="OAuth через Яндекс пока не настроен"' ?>>
                        <span class="oauth-icon">Я</span>
                        <span>Войти через Яндекс</span>
                    </a>
                    <a href="<?= e($google_auth_url ?: '#') ?>"
                       class="oauth-button oauth-button-google <?= $google_auth_url ? '' : 'is-disabled' ?>"
                       <?= $google_auth_url ? '' : 'aria-disabled="true" onclick="return false;" title="OAuth через Google пока не настроен"' ?>>
                        <span class="oauth-icon">G</span>
                        <span>Войти через Google</span>
                    </a>
                </div>
                <div class="login-info mt-4">
                    <p class="text-small text-muted">
                        💡 Если вы входите через Telegram и еще не пользовались ботом,
                        начните с команды /start.
                    </p>
                </div>
            </div>
            <div class="login-footer">
                <a href="https://t.me/<?= e(BOT_USERNAME) ?>" target="_blank" class="btn btn-outline">
                    Открыть бота
                </a>
            </div>
        </div>
    </div>
    <script src="/assets/js/theme.js"></script>
</body>
</html>
