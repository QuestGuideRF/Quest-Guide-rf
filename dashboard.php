<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$page_title = 'Главная';
$page_description = "Главная страница QuestGuideRF - ваш личный кабинет с статистикой, активными квестами и достижениями. Отслеживайте прогресс по экскурсиям-квестам.";
$page_keywords = "личный кабинет, статистика, квесты, экскурсии, достижения, прогресс, QuestGuideRF";
$user = getCurrentUser();
$stats = getUserStats($user['id']);
$level_info = getUserLevel($stats['total_points']);
$active_quests = getDB()->fetchAll(
    'SELECT up.*, r.name as route_name, r.price, c.name as city_name
     FROM user_progress up
     JOIN routes r ON up.route_id = r.id
     JOIN cities c ON r.city_id = c.id
     WHERE up.user_id = ? AND up.status = "in_progress"
     ORDER BY up.started_at DESC
     LIMIT 5',
    [$user['id']]
);
$recent_achievements = getDB()->fetchAll(
    'SELECT ua.*, a.name, a.description, a.icon
     FROM user_achievements ua
     JOIN achievements a ON ua.achievement_id = a.id
     WHERE ua.user_id = ?
     ORDER BY ua.earned_at DESC
     LIMIT 3',
    [$user['id']]
);
$page_title = 'Dashboard';
require_once __DIR__ . '/includes/header.php';
?>
<main class="main-content">
<div class="container">
    <div class="welcome-section">
        <div class="user-avatar">
            <img src="<?= e($user['photo_url'] ?: getDefaultAvatar($user['first_name'])) ?>"
                 alt="<?= e($user['first_name']) ?>">
        </div>
        <div class="user-info">
            <h1>Привет, <?= e($user['first_name']) ?>! 👋</h1>
            <p class="level-badge">
                Уровень <?= $level_info['level'] ?>
                <span class="level-progress">
                    (<?= $level_info['current_points'] ?>/<?= $level_info['points_to_next'] + $level_info['current_points'] ?>)
                </span>
            </p>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon">🗺️</div>
            <div class="stat-content">
                <div class="stat-value"><?= $stats['completed_routes'] ?></div>
                <div class="stat-label">Пройдено маршрутов</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📍</div>
            <div class="stat-content">
                <div class="stat-value"><?= $stats['total_points'] ?></div>
                <div class="stat-label">Пройдено точек</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">⏱️</div>
            <div class="stat-content">
                <div class="stat-value"><?= formatDuration($stats['total_time']) ?></div>
                <div class="stat-label">Время в квестах</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <div class="stat-content">
                <div class="stat-value"><?= $stats['achievements_count'] ?></div>
                <div class="stat-label">Достижений</div>
            </div>
        </div>
    </div>
    <?php if (count($active_quests) > 0): ?>
    <section class="section">
        <div class="section-header">
            <h2>Активные квесты</h2>
            <a href="/routes.php" class="БТН БТН-Контур БТН-СМ">Все маршруты</a>
        </div>
        <div class="quests-list">
            <?php foreach ($active_quests as $quest):
                $progress = getRouteProgress($quest['id']);
            ?>
            <div class="quest-card">
                <div class="quest-info">
                    <h3><?= e($quest['route_name']) ?></h3>
                    <p class="text-muted"><?= e($quest['city_name']) ?></p>
                    <div class="progress-info">
                        <span>Пройдено: <?= $quest['points_completed'] ?> / <?= $progress['total_points'] ?></span>
                    </div>
                </div>
                <div class="quest-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="ширина: <?= $progress['progress_percent'] ?>%"></div>
                    </div>
                    <div class="progress-percent"><?= $progress['progress_percent'] ?>%</div>
                </div>
                <div class="quest-actions">
                    <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-Первичный БТН-СМ" target="_blank">
                        Продолжить в боте
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>
    <?php if (count($recent_achievements) > 0): ?>
    <section class="section">
        <div class="section-header">
            <h2>Последние достижения</h2>
            <a href="/achievements.php" class="БТН БТН-Контур БТН-СМ">Все достижения</a>
        </div>
        <div class="achievements-grid">
            <?php foreach ($recent_achievements as $achievement): ?>
            <div class="achievement-card">
                <div class="achievement-icon"><?= e($achievement['icon']) ?></div>
                <div class="achievement-info">
                    <h3><?= e($achievement['name']) ?></h3>
                    <p class="текст без звука"><?= e($achievement['description']) ?></p>
                    <p class="текст без звука">
                        <?= formatDate($achievement['earned_at']) ?>
                    </p>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>
    <section class="section">
        <h2>Быстрые действия</h2>
        <div class="quick-actions">
            <a href="/routes.php" class="action-card">
                <div class="action-icon">🗺️</div>
                <div class="action-text">Мои экскурсии</div>
            </a>
            <a href="/photos.php" class="action-card">
                <div class="action-icon">📸</div>
                <div class="action-text">Фотографии</div>
            </a>
            <a href="/payments.php" class="action-card">
                <div class="action-icon">💳</div>
                <div class="action-text">Покупки</div>
            </a>
            <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="action-card" target="_blank">
                <div class="action-icon">🤖</div>
                <div class="action-text">Открыть бота</div>
            </a>
        </div>
    </section>
</div>
</main>
<?php require_once __DIR__ . '/includes/footer.php'; ?>