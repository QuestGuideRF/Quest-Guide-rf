<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$page_title = 'Мои экскурсии';
$page_description = "Просмотрите все ваши экскурсии-квесты в QuestGuideRF. Активные, завершенные и доступные маршруты по Москве и другим городам России.";
$page_keywords = "мои экскурсии, маршруты, квесты, активные квесты, завершенные квесты, маршруты Москвы, QuestGuideRF";
$user = getCurrentUser();
$user_routes = getDB()->fetchAll(
    'SELECT up.*, r.name as route_name, r.price, r.estimated_duration,
            r.distance, r.route_type, c.name as city_name
     FROM user_progress up
     JOIN routes r ON up.route_id = r.id
     JOIN cities c ON r.city_id = c.id
     WHERE up.user_id = ?
     ORDER BY
        CASE
            WHEN up.status = "in_progress" THEN 1
            WHEN up.status = "completed" THEN 2
            ELSE 3
        END,
        up.started_at DESC',
    [$user['id']]
);
$routes_by_status = [
    'in_progress' => [],
    'completed' => [],
    'abandoned' => [],
];
foreach ($user_routes as $route) {
    $total_points = getDB()->fetch(
        'SELECT COUNT(*) as count FROM points WHERE route_id = ?',
        [$route['route_id']]
    )['count'];
    $route['total_points'] = $total_points;
    $route['progress_percent'] = $total_points > 0
        ? round(($route['points_completed'] / $total_points) * 100)
        : 0;
    $route['points'] = getDB()->fetchAll(
        'SELECT p.*,
                uph.file_path as photo_path,
                uph.created_at as photo_taken_at,
                CASE
                    WHEN uph.id IS NOT NULL THEN "completed"
                    WHEN p.order = ? THEN "current"
                    ELSE "pending"
                END as point_status
         FROM points p
         LEFT JOIN user_photos uph ON p.id = uph.point_id AND uph.user_id = ?
         WHERE p.route_id = ?
         ORDER BY p.order',
        [$route['current_point_order'], $user['id'], $route['route_id']]
    );
    $routes_by_status[$route['status']][] = $route;
}
$page_title = 'Мои экскурсии';
require_once __DIR__ . '/includes/header.php';
?>
<main class="main-content">
<div class="container">
    <div class="page-header">
        <h1>🗺️ Мои экскурсии</h1>
        <p class="text-muted">Все ваши пройденные и текущие маршруты</p>
    </div>
    <?php if (empty($user_routes)): ?>
    <div class="empty-state">
        <div class="empty-icon">🗺️</div>
        <h2>У вас пока нет экскурсий</h2>
        <p>Начните свое первое приключение в боте!</p>
        <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-первичный" target="_blank">
            Открыть бота
        </a>
    </div>
    <?php else: ?>
    <?php if (!empty($routes_by_status['in_progress'])): ?>
    <section class="section">
        <h2>В процессе (<?= count($routes_by_status['in_progress']) ?>)</h2>
        <div class="routes-list">
            <?php foreach ($routes_by_status['in_progress'] as $route): ?>
            <div class="route-card">
                <div class="route-header" onclick="toggleRouteDetails(<?= $route['route_id'] ?>)">
                    <div class="route-type">
                        <?= $route['route_type'] == 'walking' ? '🚶' : '🚴' ?>
                    </div>
                    <div class="route-info">
                        <h3><?= e($route['route_name']) ?></h3>
                        <p class="text-muted"><?= e($route['city_name']) ?></p>
                    </div>
                    <div class="route-status">
                        <?= getStatusBadge($route['status']) ?>
                    </div>
                    <button class="route-toggle" type="button">
                        <span class="toggle-icon">▼</span>
                    </button>
                </div>
                <div class="route-meta">
                    <span>⏱️ <?= formatDuration($route['estimated_duration']) ?></span>
                    <span>📍 <?= formatDistance($route['distance']) ?></span>
                    <span>💰 <?= formatPrice($route['price']) ?></span>
                </div>
                <div class="route-progress-section">
                    <div class="progress-info">
                        <span>Пройдено: <?= $route['points_completed'] ?> / <?= $route['total_points'] ?></span>
                        <span><?= $route['progress_percent'] ?>%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="ширина: <?= $route['progress_percent'] ?>%"></div>
                    </div>
                </div>
                <div class="route-details" id="детали маршрута-<?= $route['route_id'] ?>" style="дисплей: нет;">
                    <div class="points-list">
                        <?php foreach ($route['points'] as $point): ?>
                        <div class="точка-элемент <?= $point['point_status'] ?>">
                            <div class="point-header">
                                <div class="point-status-icon">
                                    <?php if ($point['point_status'] == 'completed'): ?>
                                        ✅
                                    <?php elseif ($point['point_status'] == 'current'): ?>
                                        ⏳
                                    <?php else: ?>
                                        ⭕️
                                    <?php endif; ?>
                                </div>
                                <div class="point-info">
                                    <h4><?= $point['order'] ?>. <?= e($point['name']) ?></h4>
                                    <p class="text-muted"><?= e($point['description']) ?></p>
                                    <?php if ($point['require_pose']): ?>
                                    <span class="point-requirement">
                                        🤸 Требуется поза: <?php
                                            $poses = ['hands_up' => 'Руки вверх', 'heart' => 'Сердечко', 'point' => 'Указать'];
                                            echo $poses[$point['require_pose']] ?? $point['require_pose'];
                                        ?>
                                    </span>
                                    <?php endif; ?>
                                    <?php if ($point['min_people'] > 1): ?>
                                    <span class="point-requirement">
                                        👥 Минимум людей: <?= $point['min_people'] ?>
                                    </span>
                                    <?php endif; ?>
                                </div>
                            </div>
                            <?php if ($point['point_status'] == 'completed' && $point['photo_path']): ?>
                            <div class="point-photo">
                                <img src="<?= e($point['photo_path']) ?>"
                                     alt="<?= e($point['name']) ?>"
                                     loading="lazy"
                                     onerror="this.src='/assets/img/no-photo.png';">
                                <div class="photo-info">
                                    <span class="текст без звука">
                                        📅 <?= formatDate($point['photo_taken_at']) ?>
                                    </span>
                                </div>
                            </div>
                            <?php endif; ?>
                            <?php if ($point['task_text']): ?>
                            <div class="point-task">
                                <strong>Задание:</strong> <?= nl2br(e($point['task_text'])) ?>
                            </div>
                            <?php endif; ?>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
                <div class="route-footer">
                    <span class="текст без звука">
                        Начато: <?= formatDate($route['started_at']) ?>
                    </span>
                    <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-Первичный БТН-СМ" target="_blank">
                        Продолжить
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>
    <?php if (!empty($routes_by_status['completed'])): ?>
    <section class="section">
        <h2>Завершено (<?= count($routes_by_status['completed']) ?>)</h2>
        <div class="routes-list">
            <?php foreach ($routes_by_status['completed'] as $route): ?>
            <div class="маршрут-карта завершена">
                <div class="route-header" onclick="toggleRouteDetails(<?= $route['route_id'] ?>)">
                    <div class="route-type">
                        <?= $route['route_type'] == 'walking' ? '🚶' : '🚴' ?>
                    </div>
                    <div class="route-info">
                        <h3><?= e($route['route_name']) ?></h3>
                        <p class="text-muted"><?= e($route['city_name']) ?></p>
                    </div>
                    <div class="route-status">
                        <?= getStatusBadge($route['status']) ?>
                    </div>
                    <button class="route-toggle" type="button">
                        <span class="toggle-icon">▼</span>
                    </button>
                </div>
                <div class="route-meta">
                    <span>📍 <?= $route['points_completed'] ?> точек</span>
                    <?php if ($route['completed_at']):
                        $duration = (strtotime($route['completed_at']) - strtotime($route['started_at'])) / 60;
                    ?>
                    <span>⏱️ <?= formatDuration($duration) ?></span>
                    <?php endif; ?>
                </div>
                <div class="route-details" id="детали маршрута-<?= $route['route_id'] ?>" style="дисплей: нет;">
                    <div class="points-list">
                        <?php foreach ($route['points'] as $point): ?>
                        <div class="пункт-пункт завершен">
                            <div class="point-header">
                                <div class="point-status-icon">✅</div>
                                <div class="point-info">
                                    <h4><?= $point['order'] ?>. <?= e($point['name']) ?></h4>
                                    <p class="text-muted"><?= e($point['description']) ?></p>
                                </div>
                            </div>
                            <?php if ($point['photo_path']): ?>
                            <div class="point-photo">
                                <img src="<?= e($point['photo_path']) ?>"
                                     alt="<?= e($point['name']) ?>"
                                     loading="lazy"
                                     onerror="this.src='/assets/img/no-photo.png';">
                                <div class="photo-info">
                                    <span class="текст без звука">
                                        📅 <?= formatDate($point['photo_taken_at']) ?>
                                    </span>
                                </div>
                            </div>
                            <?php endif; ?>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
                <div class="route-footer">
                    <span class="текст без звука">
                        Завершено: <?= formatDate($route['completed_at']) ?>
                    </span>
                    <a href="/photos.php?route=<?= $route['route_id'] ?>" class="БТН БТН-Контур БТН-СМ">
                        Фотографии
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>
    <?php endif; ?>
</div>
</main>
<script>
function toggleRouteDetails(routeId) {
    const details = document.getElementById('route-details-' + routeId);
    const card = details.closest('.route-card');
    const icon = card.querySelector('.toggle-icon');
    if (details.style.display === 'none') {
        details.style.display = 'block';
        icon.textContent = '▲';
        card.classList.add('expanded');
    } else {
        details.style.display = 'none';
        icon.textContent = '▼';
        card.classList.remove('expanded');
    }
}
</script>
<?php require_once __DIR__ . '/includes/footer.php'; ?>