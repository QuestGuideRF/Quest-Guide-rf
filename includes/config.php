<?php
if (!defined('APP_INIT')) {
    http_response_code(403);
    die('Прямой доступ запрещен');
}
function loadEnv($path) {
    if (!file_exists($path)) {
        die('Файл .env не найден');
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || strpos($line, '#') === 0 || strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        if (!array_key_exists($name, $_ENV)) {
            $_ENV[$name] = $value;
        }
    }
}
loadEnv(__DIR__ . '/../.env');
define('DB_HOST', $_ENV['DB_HOST'] ?? 'localhost');
define('DB_NAME', $_ENV['DB_NAME'] ?? 'quest_bot');
define('DB_USER', $_ENV['DB_USER'] ?? 'root');
define('DB_PASS', $_ENV['DB_PASS'] ?? $_ENV['DB_PASSWORD'] ?? '');
define('DB_CHARSET', 'utf8mb4');
define('BOT_TOKEN', $_ENV['BOT_TOKEN'] ?? '');
define('BOT_USERNAME', $_ENV['BOT_USERNAME'] ?? '');
define('SITE_URL', $_ENV['SITE_URL'] ?? 'http://localhost');
define('SITE_NAME', 'QuestGuideRF');
define('UPLOAD_PATH', __DIR__ . '/../uploads/');
define('PHOTO_PATH', __DIR__ . '/../photos/');
define('SESSION_LIFETIME', 60 * 60 * 24 * 90);
date_default_timezone_set('Europe/Moscow');
$debug = $_ENV['DEBUG'] ?? false;
if ($debug) {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}
