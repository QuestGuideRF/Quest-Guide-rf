<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$user = getCurrentUser();
$payments = getDB()->fetchAll(
    'SELECT p.*, r.name as route_name, c.name as city_name
     FROM payments p
     JOIN routes r ON p.route_id = r.id
     JOIN cities c ON r.city_id = c.id
     WHERE p.user_id = ?
     ORDER BY p.created_at DESC',
    [$user['id']]
);
$total_spent = array_sum(array_column(
    array_filter($payments, function($p) { return $p['status'] == 'success'; }),
    'amount'
));
$page_title = 'История покупок';
$page_description = "История ваших покупок экскурсий-квестов в QuestGuideRF. Просматривайте все платежи и купленные маршруты.";
$page_keywords = "история покупок, платежи, купленные квесты, транзакции, QuestGuideRF";
require_once __DIR__ . '/includes/header.php';
?>
<main class="main-content">
<div class="container">
    <div class="page-header">
        <h1>💳 История покупок</h1>
        <p class="text-muted">Все ваши платежи и покупки</p>
    </div>
    <?php if (!empty($payments)): ?>
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-content">
                <div class="stat-value"><?= formatPrice($total_spent) ?></div>
                <div class="stat-label">Всего потрачено</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🎫</div>
            <div class="stat-content">
                <div class="stat-value"><?= count($payments) ?></div>
                <div class="stat-label">Всего покупок</div>
            </div>
        </div>
    </div>
    <?php endif; ?>
    <?php if (empty($payments)): ?>
    <div class="empty-state">
        <div class="empty-icon">💳</div>
        <h2>Пока нет покупок</h2>
        <p>Приобретите первый маршрут в боте!</p>
        <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-первичный" target="_blank">
            Открыть бота
        </a>
    </div>
    <?php else: ?>
    <div class="payments-list">
        <?php foreach ($payments as $payment): ?>
        <div class="payment-card">
            <div class="payment-header">
                <div class="payment-icon">
                    <?= $payment['status'] == 'success' ? '✅' : ($payment['status'] == 'pending' ? '⏳' : '❌') ?>
                </div>
                <div class="payment-info">
                    <h3><?= e($payment['route_name']) ?></h3>
                    <p class="text-muted"><?= e($payment['city_name']) ?></p>
                </div>
                <div class="payment-amount">
                    <?= formatPrice($payment['amount']) ?>
                </div>
            </div>
            <div class="payment-details">
                <div class="payment-meta">
                    <span><?= getPaymentStatusBadge($payment['status']) ?></span>
                    <span class="text-muted">
                        <?= formatDateTime($payment['created_at']) ?>
                    </span>
                </div>
                <?php if ($payment['telegram_payment_charge_id']): ?>
                <div class="идентификатор платежа, отключенный текст, маленький текст">
                    ID: <?= e($payment['telegram_payment_charge_id']) ?>
                </div>
                <?php endif; ?>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>
</main>
<?php require_once __DIR__ . '/includes/footer.php'; ?>