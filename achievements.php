<?php
require_once __DIR__ . '/includes/init.php';
requireAuth();
$user = getCurrentUser();
$all_achievements = getDB()->fetchAll('SELECT * FROM achievements ORDER BY category, `order`');
$user_achievements_ids = getDB()->fetchAll(
    'SELECT achievement_id, earned_at FROM user_achievements WHERE user_id = ?',
    [$user['id']]
);
$earned_map = [];
foreach ($user_achievements_ids as $ua) {
    $earned_map[$ua['achievement_id']] = $ua['earned_at'];
}
$achievements_by_category = [];
foreach ($all_achievements as $achievement) {
    $category = $achievement['category'] ?? 'Общие';
    if (!isset($achievements_by_category[$category])) {
        $achievements_by_category[$category] = [];
    }
    $achievement['earned'] = isset($earned_map[$achievement['id']]);
    $achievement['earned_at'] = $earned_map[$achievement['id']] ?? null;
    $achievements_by_category[$category][] = $achievement;
}
$total_achievements = count($all_achievements);
$earned_achievements = count($earned_map);
$progress_percent = $total_achievements > 0 ? round(($earned_achievements / $total_achievements) * 100) : 0;
$page_title = 'Достижения';
$page_description = "Ваши достижения в QuestGuideRF. Отслеживайте прогресс по получению всех наград за прохождение квестов и экскурсий.";
$page_keywords = "достижения, награды, прогресс, квесты, экскурсии, геймификация, QuestGuideRF";
require_once __DIR__ . '/includes/header.php';
?>
<main class="main-content">
<div class="container">
    <div class="page-header">
        <h1>🏆 Достижения</h1>
        <p class="text-muted">Собирайте достижения, проходя квесты</p>
    </div>
    <div class="achievements-progress">
        <div class="progress-header">
            <h3>Прогресс</h3>
            <span><?= $earned_achievements ?> / <?= $total_achievements ?></span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="ширина: <?= $progress_percent ?>%"></div>
        </div>
        <p class="текстовый центр с отключенным звуком"><?= $progress_percent ?>% достижений получено</p>
    </div>
    <?php foreach ($achievements_by_category as $category => $achievements): ?>
    <section class="section">
        <h2><?= e($category) ?></h2>
        <div class="achievements-grid">
            <?php foreach ($achievements as $achievement): ?>
            <div class="карта достижений <?= $achievement['earned'] ? 'заработано': 'заблокировано' ?>">
                <div class="achievement-icon">
                    <?= $achievement['earned'] ? e($achievement['icon']) : '🔒' ?>
                </div>
                <div class="achievement-content">
                    <h3><?= $achievement['earned'] || !$achievement['is_hidden'] ? e($achievement['name']) : '???' ?></h3>
                    <p class="text-muted">
                        <?= $achievement['earned'] || !$achievement['is_hidden'] ? e($achievement['description']) : 'Скрытое достижение' ?>
                    </p>
                    <?php if ($achievement['earned']): ?>
                    <p class="Текст с датой достижения и отключенным текстом">
                        Получено: <?= formatDate($achievement['earned_at']) ?>
                    </p>
                    <?php endif; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endforeach; ?>
</div>
</main>
<?php require_once __DIR__ . '/includes/footer.php'; ?>