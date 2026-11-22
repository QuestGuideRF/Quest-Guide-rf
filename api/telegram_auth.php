<?php
require_once __DIR__ . '/../includes/init.php';
$auth_data = $_GET;
if (!isset($auth_data['id']) || !isset($auth_data['hash'])) {
    die('Неверные данные авторизации');
}
if (!verifyTelegramAuth($auth_data)) {
    die('Проверка авторизации не удалась');
}
$user = getOrCreateUser($auth_data);
loginUser($user);
header('Location: /dashboard.php');
exit;
