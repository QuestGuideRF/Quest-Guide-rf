<?php
require_once __DIR__ . '/../includes/init.php';

$provider = $_GET['provider'] ?? '';
$code = $_GET['code'] ?? '';
$state = $_GET['state'] ?? '';

if (!in_array($provider, ['google', 'yandex'], true)) {
    http_response_code(400);
    die('Неизвестный OAuth провайдер');
}
if (!isOAuthProviderConfigured($provider)) {
    http_response_code(500);
    die('OAuth провайдер не настроен');
}
if (empty($code) || empty($state) || empty($_SESSION['oauth_state_' . $provider]) || !hash_equals($_SESSION['oauth_state_' . $provider], $state)) {
    http_response_code(400);
    die('Неверное состояние OAuth авторизации');
}
unset($_SESSION['oauth_state_' . $provider]);

try {
    $access_token = exchangeOAuthCode($provider, $code);
    $profile = fetchOAuthProfile($provider, $access_token);
    loginOAuthProfile($provider, $profile);
    header('Location: /dashboard.php');
    exit;
} catch (Throwable $e) {
    http_response_code(500);
    die('Ошибка OAuth авторизации: ' . e($e->getMessage()));
}
