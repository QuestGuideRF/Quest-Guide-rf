<?php
http_response_code(404);
$page_title = 'Страница не найдена';
require_once __DIR__ . '/includes/init.php';
$is_logged_in = isLoggedIn();
if ($is_logged_in) {
    require_once __DIR__ . '/includes/header.php';
}
?>
<!DOCTYPE html>
<html lang="ru">
<?php if (!$is_logged_in): ?>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Страница не найдена | QuestGuideRF</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <script>
        (function() {
            function getPreferredTheme() {
                const stored = localStorage.getItem('theme');
                if (stored) return stored;
                if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    return 'dark';
                }
                return 'light';
            }
            function applyTheme(theme) {
                let actualTheme = theme;
                if (theme === 'auto') {
                    actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }
                document.documentElement.setAttribute('data-theme', actualTheme);
            }
            applyTheme(getPreferredTheme());
        })();
    </script>
</head>
<body>
<?php endif; ?>
<main class="main-content">
    <div class="container">
        <div class="error-page">
            <div class="error-code">404</div>
            <div class="error-icon">🗺️</div>
            <h1>Страница не найдена</h1>
            <p class="error-description">
                К сожалению, запрашиваемая страница не существует.<br>
                Возможно, вы перешли по устаревшей ссылке или ввели неверный адрес.
            </p>
            <div class="error-actions">
                <?php if ($is_logged_in): ?>
                    <a href="/dashboard.php" class="БТН БТН-первичный">
                        <span>🏠</span>
                        На главную
                    </a>
                    <a href="/routes.php" class="кнопка btn-контур">
                        <span>🗺️</span>
                        К экскурсиям
                    </a>
                <?php else: ?>
                    <a href="/" class="БТН БТН-первичный">
                        <span>🏠</span>
                        На главную
                    </a>
                    <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="кнопка btn-контур" target="_blank">
                        <span>🤖</span>
                        Открыть бота
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</main>
<?php if (!$is_logged_in): ?>
    <script src="/assets/js/theme.js"></script>
    <script src="/assets/js/main.js"></script>
</body>
</html>
<?php else: ?>
    <?php require_once __DIR__ . '/includes/footer.php'; ?>
<?php endif; ?>
