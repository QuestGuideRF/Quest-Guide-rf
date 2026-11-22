<?php
require_once __DIR__ . '/../includes/init.php';
$token = $_GET['token'] ?? '';
if (empty($token)) {
    die('Токен не указан. Используйте команду /web в боте.');
}
$session = getDB()->fetch(
    'SELECT telegram_id, expires_at FROM user_sessions
     WHERE token = ? AND is_used = FALSE',
    [$token]
);
if (!$session) {
    die('
        <h1>Ошибка авторизации</h1>
        <p>Токен недействителен или уже использован.</p>
        <p>Получите новую ссылку в боте: отправьте /web</p>
    ');
}
$expires_at_utc = new DateTime($session['expires_at'], new DateTimeZone('UTC'));
$now_utc = new DateTime('now', new DateTimeZone('UTC'));
if ($now_utc > $expires_at_utc) {
    die('
        <h1>Ошибка авторизации</h1>
        <p>Токен истек (срок действия 5 минут).</p>
        <p>Получите новую ссылку в боте: отправьте /web</p>
    ');
}
getDB()->query(
    'UPDATE user_sessions SET is_used = TRUE, used_at = NOW() WHERE token = ?',
    [$token]
);
$user = getDB()->fetch(
    'SELECT * FROM users WHERE telegram_id = ?',
    [$session['telegram_id']]
);
if (!$user) {
    die('
        <h1>Ошибка авторизации</h1>
        <p>Пользователь не найден в системе.</p>
        <p>Сначала запустите бота: /start</p>
    ');
}
loginUser($user);
header('Location: /dashboard.php');
exit;
