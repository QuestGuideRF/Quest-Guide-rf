<?php
if (!defined('APP_INIT')) {
    die('Прямой доступ запрещен');
}

function envValue($name, $default = '') {
    $value = $_ENV[$name] ?? getenv($name);
    return ($value === false || $value === null || $value === '') ? $default : $value;
}

function getOAuthProviderConfig($provider) {
    $site_url = rtrim(SITE_URL, '/');
    $providers = [
        'google' => [
            'name' => 'Google',
            'client_id' => envValue('GOOGLE_OAUTH_CLIENT_ID'),
            'client_secret' => envValue('GOOGLE_OAUTH_CLIENT_SECRET'),
            'redirect_uri' => envValue('GOOGLE_OAUTH_REDIRECT_URI', $site_url . '/auth/oauth_callback.php?provider=google'),
            'auth_url' => 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url' => 'https://oauth2.googleapis.com/token',
            'userinfo_url' => 'https://www.googleapis.com/oauth2/v3/userinfo',
            'scope' => 'openid email profile',
        ],
        'yandex' => [
            'name' => 'Яндекс',
            'client_id' => envValue('YANDEX_OAUTH_CLIENT_ID'),
            'client_secret' => envValue('YANDEX_OAUTH_CLIENT_SECRET'),
            'redirect_uri' => envValue('YANDEX_OAUTH_REDIRECT_URI', $site_url . '/auth/oauth_callback.php?provider=yandex'),
            'auth_url' => 'https://oauth.yandex.ru/authorize',
            'token_url' => 'https://oauth.yandex.ru/token',
            'userinfo_url' => 'https://login.yandex.ru/info?format=json',
            'scope' => 'login:email login:info',
        ],
    ];
    return $providers[$provider] ?? null;
}

function isOAuthProviderConfigured($provider) {
    $config = getOAuthProviderConfig($provider);
    return $config && !empty($config['client_id']) && !empty($config['client_secret']);
}

function getOAuthAuthorizationUrl($provider) {
    $config = getOAuthProviderConfig($provider);
    if (!$config || !isOAuthProviderConfigured($provider)) {
        return null;
    }
    $state = bin2hex(random_bytes(16));
    $_SESSION['oauth_state_' . $provider] = $state;
    $params = [
        'response_type' => 'code',
        'client_id' => $config['client_id'],
        'redirect_uri' => $config['redirect_uri'],
        'scope' => $config['scope'],
        'state' => $state,
    ];
    if ($provider === 'google') {
        $params['access_type'] = 'online';
        $params['prompt'] = 'select_account';
    }
    return $config['auth_url'] . '?' . http_build_query($params);
}

function oauthHttpRequest($url, $method = 'GET', $data = null, $headers = []) {
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 20);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        }
        $response = curl_exec($ch);
        $error = curl_error($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($response === false || $status >= 400) {
            throw new Exception('OAuth HTTP error: ' . ($error ?: $status));
        }
        return $response;
    }
    $options = ['http' => ['method' => $method, 'header' => implode("\r\n", $headers), 'timeout' => 20]];
    if ($method === 'POST') {
        $options['http']['header'] .= "\r\nContent-Type: application/x-www-form-urlencoded";
        $options['http']['content'] = http_build_query($data);
    }
    $response = file_get_contents($url, false, stream_context_create($options));
    if ($response === false) {
        throw new Exception('OAuth HTTP request failed');
    }
    return $response;
}

function exchangeOAuthCode($provider, $code) {
    $config = getOAuthProviderConfig($provider);
    $response = oauthHttpRequest($config['token_url'], 'POST', [
        'grant_type' => 'authorization_code',
        'code' => $code,
        'client_id' => $config['client_id'],
        'client_secret' => $config['client_secret'],
        'redirect_uri' => $config['redirect_uri'],
    ]);
    $token = json_decode($response, true);
    if (empty($token['access_token'])) {
        throw new Exception('OAuth access token not received');
    }
    return $token['access_token'];
}

function fetchOAuthProfile($provider, $access_token) {
    $config = getOAuthProviderConfig($provider);
    $authorization = $provider === 'yandex'
        ? 'Authorization: OAuth ' . $access_token
        : 'Authorization: Bearer ' . $access_token;
    $response = oauthHttpRequest($config['userinfo_url'], 'GET', null, [
        $authorization,
    ]);
    $profile = json_decode($response, true);
    if (!is_array($profile)) {
        throw new Exception('OAuth profile response is invalid');
    }
    return normalizeOAuthProfile($provider, $profile);
}

function normalizeOAuthProfile($provider, $profile) {
    if ($provider === 'google') {
        return [
            'provider_user_id' => $profile['sub'] ?? null,
            'email' => $profile['email'] ?? null,
            'username' => $profile['email'] ?? null,
            'first_name' => $profile['given_name'] ?? ($profile['name'] ?? 'Google user'),
            'last_name' => $profile['family_name'] ?? null,
            'photo_url' => $profile['picture'] ?? null,
        ];
    }
    if ($provider === 'yandex') {
        $avatar = null;
        if (!empty($profile['default_avatar_id'])) {
            $avatar = 'https://avatars.yandex.net/get-yapic/' . $profile['default_avatar_id'] . '/islands-200';
        }
        return [
            'provider_user_id' => $profile['id'] ?? null,
            'email' => $profile['default_email'] ?? null,
            'username' => $profile['login'] ?? ($profile['default_email'] ?? null),
            'first_name' => $profile['first_name'] ?? ($profile['display_name'] ?? 'Yandex user'),
            'last_name' => $profile['last_name'] ?? null,
            'photo_url' => $avatar,
        ];
    }
    throw new Exception('Unknown OAuth provider');
}

function ensureOAuthAccountsTable() {
    getDB()->execute(
        'CREATE TABLE IF NOT EXISTS oauth_accounts (
            id int UNSIGNED NOT NULL AUTO_INCREMENT,
            provider varchar(20) NOT NULL,
            provider_user_id varchar(255) NOT NULL,
            user_id int UNSIGNED NOT NULL,
            email varchar(255) DEFAULT NULL,
            created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY provider_user (provider, provider_user_id),
            KEY user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );
}

function syntheticTelegramId($provider, $provider_user_id) {
    return 900000000000000000 + (int) sprintf('%u', crc32($provider . ':' . $provider_user_id));
}

function loginOAuthProfile($provider, $profile) {
    if (empty($profile['provider_user_id'])) {
        throw new Exception('OAuth profile does not contain user id');
    }
    ensureOAuthAccountsTable();
    $db = getDB();
    $account = $db->fetch(
        'SELECT u.* FROM oauth_accounts oa JOIN users u ON oa.user_id = u.id
         WHERE oa.provider = ? AND oa.provider_user_id = ?',
        [$provider, $profile['provider_user_id']]
    );
    if ($account) {
        $db->execute('UPDATE users SET last_login = NOW() WHERE id = ?', [$account['id']]);
        loginUser($account);
        return;
    }
    $telegram_id = syntheticTelegramId($provider, $profile['provider_user_id']);
    $existing = $db->fetch('SELECT * FROM users WHERE telegram_id = ?', [$telegram_id]);
    if (!$existing) {
        $db->execute(
            'INSERT INTO users (telegram_id, username, first_name, last_name, photo_url, created_at, last_login)
             VALUES (?, ?, ?, ?, ?, NOW(), NOW())',
            [
                $telegram_id,
                $profile['username'],
                $profile['first_name'],
                $profile['last_name'],
                $profile['photo_url'],
            ]
        );
        $existing = $db->fetch('SELECT * FROM users WHERE telegram_id = ?', [$telegram_id]);
    }
    $db->execute(
        'INSERT INTO oauth_accounts (provider, provider_user_id, user_id, email)
         VALUES (?, ?, ?, ?)',
        [$provider, $profile['provider_user_id'], $existing['id'], $profile['email']]
    );
    loginUser($existing);
}
