<?php
if (!defined('APP_INIT')) {
    die('Прямой доступ запрещен');
}
function verifyTelegramAuth($auth_data) {
    $check_hash = $auth_data['hash'];
    unset($auth_data['hash']);
    $data_check_arr = [];
    foreach ($auth_data as $key => $value) {
        $data_check_arr[] = $key . '=' . $value;
    }
    sort($data_check_arr);
    $data_check_string = implode("\n", $data_check_arr);
    $secret_key = hash('sha256', BOT_TOKEN, true);
    $hash = hash_hmac('sha256', $data_check_string, $secret_key);
    if (strcmp($hash, $check_hash) !== 0) {
        return false;
    }
    if ((time() - $auth_data['auth_date']) > 86400) {
        return false;
    }
    return true;
}
function getOrCreateUser($telegram_data) {
    $db = getDB();
    $telegram_id = $telegram_data['id'];
    $user = $db->fetch(
        'SELECT * FROM users WHERE telegram_id = ?',
        [$telegram_id]
    );
    if (!$user) {
        $db->query(
            'INSERT INTO users (telegram_id, username, first_name, last_name, photo_url, created_at)
             VALUES (?, ?, ?, ?, ?, NOW())',
            [
                $telegram_id,
                $telegram_data['username'] ?? null,
                $telegram_data['first_name'] ?? null,
                $telegram_data['last_name'] ?? null,
                $telegram_data['photo_url'] ?? null,
            ]
        );
        $user = $db->fetch(
            'SELECT * FROM users WHERE telegram_id = ?',
            [$telegram_id]
        );
    } else {
        $db->query(
            'UPDATE users SET
                username = ?,
                first_name = ?,
                last_name = ?,
                photo_url = ?,
                last_login = NOW()
             WHERE telegram_id = ?',
            [
                $telegram_data['username'] ?? null,
                $telegram_data['first_name'] ?? null,
                $telegram_data['last_name'] ?? null,
                $telegram_data['photo_url'] ?? null,
                $telegram_id,
            ]
        );
    }
    return $user;
}
function loginUser($user) {
    $_SESSION['user_id'] = $user['id'];
    $_SESSION['telegram_id'] = $user['telegram_id'];
    $_SESSION['logged_in'] = true;
}
function isLoggedIn() {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}
function getCurrentUser() {
    if (!isLoggedIn()) {
        return null;
    }
    $db = getDB();
    return $db->fetch(
        'SELECT * FROM users WHERE id = ?',
        [$_SESSION['user_id']]
    );
}
function logout() {
    session_destroy();
    header('Location: /');
    exit;
}
function requireAuth() {
    if (!isLoggedIn()) {
        header('Location: /');
        exit;
    }
}
