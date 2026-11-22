<?php
define('APP_INIT', true);
session_start();
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/oauth.php';
require_once __DIR__ . '/functions.php';
