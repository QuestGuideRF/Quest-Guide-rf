<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$user = getCurrentUser();
$route_filter = isset($_GET['route']) ? intval($_GET['route']) : null;
$photos = getUserPhotos($user['id'], $route_filter);
$user_routes = getDB()->fetchAll(
    'SELECT DISTINCT r.id, r.name, c.name as city_name
     FROM user_progress up
     JOIN routes r ON up.route_id = r.id
     JOIN cities c ON r.city_id = c.id
     WHERE up.user_id = ?
     ORDER BY r.name',
    [$user['id']]
);
$page_title = 'Фотографии';
$page_description = "Ваши фотографии с экскурсий-квестов QuestGuideRF. Просматривайте все фото, сделанные во время прохождения маршрутов по достопримечательностям.";
$page_keywords = "фотографии, фото квестов, фото экскурсий, фото достопримечательностей, галерея, QuestGuideRF";
require_once __DIR__ . '/includes/header.php';
?>
<main class="main-content">
<div class="container">
    <div class="page-header">
        <h1>📸 Фотографии</h1>
        <p class="text-muted">Ваши снимки из квестов</p>
    </div>
    <?php if (!empty($user_routes)): ?>
    <div class="filters">
        <label for="route-filter">Фильтр по маршруту:</label>
        <select id="route-filter" class="filter-select" onchange="filterByRoute(this.value)">
            <option value="">Все маршруты</option>
            <?php foreach ($user_routes as $route): ?>
            <option value="<?= $route['id'] ?>" <?= $route_filter == $route['id'] ? 'selected' : '' ?>>
                <?= e($route['city_name']) ?> - <?= e($route['name']) ?>
            </option>
            <?php endforeach; ?>
        </select>
    </div>
    <?php endif; ?>
    <?php if (empty($photos)): ?>
    <div class="empty-state">
        <div class="empty-icon">📸</div>
        <h2>Пока нет фотографий</h2>
        <p>Начните квест и делайте снимки!</p>
        <a href="https://t.me/<?= e(BOT_USERNAME) ?>" class="БТН БТН-первичный" target="_blank">
            Открыть бота
        </a>
    </div>
    <?php else: ?>
    <div class="photo-gallery">
        <?php foreach ($photos as $photo): ?>
        <div class="photo-item" data-photo-id="<?= $photo['id'] ?>">
            <div class="photo-wrapper">
                <?php
                $file_exists = file_exists(__DIR__ . $photo['file_path']);
                ?>
                <img src="<?= e($photo['file_path']) ?>"
                     alt="<?= e($photo['point_name']) ?>"
                     loading="lazy"
                     onerror="this.src='/assets/img/no-photo.png'; this.onerror=null;"
                     onclick="openPhotoModal(<?= $photo['id'] ?>)">
                <?php if (!$file_exists): ?>
                <div class="photo-error">Файл не найден</div>
                <?php endif; ?>
            </div>
            <div class="photo-info">
                <div class="photo-title"><?= e($photo['point_name']) ?></div>
                <div class="фото-мета-текст с приглушенным текстом-маленький">
                    <?= e($photo['route_name']) ?> • <?= formatDate($photo['created_at']) ?>
                </div>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>
<div id="photo-modal" class="modal">
    <div class="modal-content">
        <button class="modal-close" onclick="закрытьФотомодальный()">&times;</button>
        <div class="modal-body">
            <img id="modal-photo" src="" alt="">
            <div class="modal-info">
                <h3 id="modal-title"></h3>
                <p id="modal-meta" class="text-muted"></p>
            </div>
        </div>
    </div>
</div>
<script>
function filterByRoute(routeId) {
    if (routeId) {
        window.location.href = '/photos.php?route=' + routeId;
    } else {
        window.location.href = '/photos.php';
    }
}
const photos = <?= json_encode($photos) ?>;
function openPhotoModal(photoId) {
    const photo = photos.find(p => p.id == photoId);
    if (!photo) return;
    document.getElementById('modal-photo').src = photo.file_path;
    document.getElementById('modal-title').textContent = photo.point_name;
    document.getElementById('modal-meta').textContent =
        photo.route_name + ' • ' + new Date(photo.created_at).toLocaleDateString('ru-RU');
    document.getElementById('photo-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closePhotoModal() {
    document.getElementById('photo-modal').classList.remove('active');
    document.body.style.overflow = '';
}
document.getElementById('photo-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closePhotoModal();
    }
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePhotoModal();
    }
});
</script>
</main>
<?php require_once __DIR__ . '/includes/footer.php'; ?>