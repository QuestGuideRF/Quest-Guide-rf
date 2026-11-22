import logging
import os
import shutil
from pathlib import Path
from datetime import datetime ,timedelta
from aiogram import Router ,F
from aiogram .filters import Command
from aiogram .types import Message ,CallbackQuery ,InlineKeyboardMarkup ,InlineKeyboardButton
from aiogram .fsm .context import FSMContext
from sqlalchemy .ext .asyncio import AsyncSession
from sqlalchemy import text ,func
from bot .loader import bot
from bot .repositories .progress import ProgressRepository
from bot .repositories .point import PointRepository
from bot .repositories .city import CityRepository
from bot .repositories .route import RouteRepository
from bot .repositories .user import UserRepository
from bot .keyboards .admin import (
get_admin_main_menu ,
get_cities_menu ,
get_city_actions ,
get_routes_menu ,
get_route_actions ,
get_points_menu ,
get_point_actions ,
get_users_pagination ,
get_user_actions ,
get_photo_history_pagination ,
get_confirm_keyboard ,
get_back_to_menu
)
from bot .fsm .admin_states import (
AdminCityStates ,
AdminRouteStates ,
AdminPointStates ,
AdminUserStates ,
AdminSettingsStates
)
from bot .config import load_config
from bot .utils .safe_edit import safe_edit_text
logger =logging .getLogger (__name__ )
router =Router ()
config =load_config ()
def is_admin (user_id :int )->bool :
    return user_id in config .bot .admin_ids
@router .message (Command ("admin"))
async def admin_menu_command (message :Message ,session :AsyncSession ):
    if not is_admin (message .from_user .id ):
        await message .answer ("❌ У вас нет прав администратора")
        return
    stats =await get_admin_stats (session )
    text =(
    f"🔐 <b>Админ-панель QuestGuideRF</b>\n\n"
    f"👥 Пользователей: {stats ['total_users']}\n"
    f"🗺 Маршрутов: {stats ['total_routes']}\n"
    f"📍 Точек: {stats ['total_points']}\n"
    f"📸 Фото на проверке: {stats ['pending_photos']}\n\n"
    f"Выберите раздел:"
    )
    await message .answer (text ,reply_markup =get_admin_main_menu (),parse_mode ="HTML")
@router .callback_query (F .data =="admin:menu")
async def admin_menu_callback (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    stats =await get_admin_stats (session )
    text =(
    f"🔐 <b>Админ-панель QuestGuideRF</b>\n\n"
    f"👥 Пользователей: {stats ['total_users']}\n"
    f"🗺 Маршрутов: {stats ['total_routes']}\n"
    f"📍 Точек: {stats ['total_points']}\n"
    f"📸 Фото на проверке: {stats ['pending_photos']}\n\n"
    f"Выберите раздел:"
    )
    await safe_edit_text (callback ,text ,reply_markup =get_admin_main_menu ())
    await callback .answer ()
@router .callback_query (F .data =="admin:cities")
async def admin_cities_list (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_repo =CityRepository (session )
    cities =await city_repo .get_all ()
    text =f"🏙 <b>Управление городами</b>\n\nВсего городов: {len (cities )}"
    await callback .message .edit_text (
    text ,
    reply_markup =get_cities_menu ([{
    'id':c .id ,
    'name':c .name ,
    'is_active':c .is_active
    }for c in cities ]),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:city:")&~F .data .contains ("add")&~F .data .contains ("edit")&~F .data .contains ("toggle")&~F .data .contains ("delete"))
async def admin_city_view (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_id =int (callback .data .split (":")[-1 ])
    city_repo =CityRepository (session )
    city =await city_repo .get (city_id )
    if not city :
        await callback .answer ("❌ Город не найден")
        return
    result =await session .execute (
    text ("SELECT COUNT(*) FROM routes WHERE city_id = :city_id"),
    {"city_id":city_id }
    )
    routes_count =result .scalar ()
    text =(
    f"🏙 <b>{city .name }</b>\n\n"
    f"📝 Описание: {city .description or 'Нет'}\n"
    f"📊 Статус: {'✅ Активен'if city .is_active else '❌ Неактивен'}\n"
    f"🗺 Маршрутов: {routes_count }\n"
    )
    await callback .message .edit_text (
    text ,
    reply_markup =get_city_actions (city_id ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:city:toggle:"))
async def admin_city_toggle (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_id =int (callback .data .split (":")[-1 ])
    await session .execute (
    text ("UPDATE cities SET is_active = NOT is_active WHERE id = :city_id"),
    {"city_id":city_id }
    )
    await session .commit ()
    await callback .answer ("✅ Статус изменён")
    await admin_city_view (callback ,session )
@router .callback_query (F .data =="admin:city:add")
async def admin_city_add_start (callback :CallbackQuery ,state :FSMContext ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    await callback .message .answer (
    "🏙 <b>Добавление города</b>\n\n"
    "Введите название города:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminCityStates .name )
    await callback .answer ()
@router .message (AdminCityStates .name )
async def admin_city_add_name (message :Message ,state :FSMContext ):
    await state .update_data (name =message .text )
    await message .answer (
    f"Название: <b>{message .text }</b>\n\n"
    "Теперь введите описание города:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminCityStates .description )
@router .message (AdminCityStates .description )
async def admin_city_add_description (message :Message ,state :FSMContext ,session :AsyncSession ):
    data =await state .get_data ()
    result =await session .execute (
    text ("""
            INSERT INTO cities (name, description, is_active)
            VALUES (:name, :description, 1)
        """),
    {
    "name":data ['name'],
    "description":message .text
    }
    )
    await session .commit ()
    await message .answer (
    f"✅ Город <b>{data ['name']}</b> добавлен!",
    parse_mode ="HTML"
    )
    await state .clear ()
@router .callback_query (F .data .startswith ("admin:city:edit:"))
async def admin_city_edit_start (callback :CallbackQuery ,state :FSMContext ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_id =int (callback .data .split (":")[-1 ])
    city_repo =CityRepository (session )
    city =await city_repo .get (city_id )
    if not city :
        await callback .answer ("❌ Город не найден")
        return
    await state .update_data (city_id =city_id ,old_name =city .name )
    await callback .message .answer (
    f"✏️ <b>Редактирование города</b>\n\n"
    f"Текущее название: <b>{city .name }</b>\n"
    f"Текущее описание: {city .description or 'Нет'}\n\n"
    f"Введите новое название (или /skip для пропуска):",
    parse_mode ="HTML"
    )
    await state .set_state (AdminCityStates .name )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:city:delete:"))
async def admin_city_delete (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT COUNT(*) FROM routes WHERE city_id = :city_id"),
    {"city_id":city_id }
    )
    routes_count =result .scalar ()
    if routes_count >0 :
        await callback .answer (f"❌ Нельзя удалить. У города есть {routes_count } маршрутов",show_alert =True )
        return
    await session .execute (
    text ("DELETE FROM cities WHERE id = :city_id"),
    {"city_id":city_id }
    )
    await session .commit ()
    await callback .answer ("✅ Город удалён")
    await admin_cities_list (callback ,session )
@router .callback_query (F .data =="admin:routes")
async def admin_routes_list (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    result =await session .execute (
    text ("""
            SELECT r.id, r.name, r.is_active, c.name as city_name
            FROM routes r
            JOIN cities c ON r.city_id = c.id
            ORDER BY c.name, r.name
        """)
    )
    routes =[dict (row ._mapping )for row in result .fetchall ()]
    msg_text =f"🗺 <b>Управление маршрутами</b>\n\nВсего маршрутов: {len (routes )}"
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_routes_menu (routes ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:route:")&~F .data .contains ("add")&~F .data .contains ("edit")&~F .data .contains ("toggle")&~F .data .contains ("delete")&~F .data .contains ("points"))
async def admin_route_view (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    route_id =int (callback .data .split (":")[-1 ])
    route_repo =RouteRepository (session )
    route =await route_repo .get (route_id )
    if not route :
        await callback .answer ("❌ Маршрут не найден")
        return
    result =await session .execute (
    text ("SELECT COUNT(*) FROM points WHERE route_id = :route_id"),
    {"route_id":route_id }
    )
    points_count =result .scalar ()
    result =await session .execute (
    text ("SELECT COUNT(*) FROM user_progress WHERE route_id = :route_id AND status = 'completed'"),
    {"route_id":route_id }
    )
    completed_count =result .scalar ()
    text =(
    f"🗺 <b>{route .name }</b>\n\n"
    f"🏙 Город: {route .city .name }\n"
    f"📝 Описание: {route .description or 'Нет'}\n"
    f"🚶 Тип: {route .route_type .value }\n"
    f"📏 Расстояние: {route .distance }м\n"
    f"⏱ Время: {route .estimated_duration }мин\n"
    f"💰 Цена: {route .price }₽\n"
    f"📊 Статус: {'✅ Активен'if route .is_active else '❌ Неактивен'}\n"
    f"📍 Точек: {points_count }\n"
    f"✅ Пройдено раз: {completed_count }\n"
    )
    await callback .message .edit_text (
    text ,
    reply_markup =get_route_actions (route_id ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data =="admin:points")
async def admin_points_list (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    result =await session .execute (
    text ("""
            SELECT r.id, r.name, r.is_active, c.name as city_name,
                   COUNT(p.id) as points_count
            FROM routes r
            JOIN cities c ON r.city_id = c.id
            LEFT JOIN points p ON r.id = p.route_id
            GROUP BY r.id
            ORDER BY c.name, r.name
        """)
    )
    routes =result .fetchall ()
    if not routes :
        msg_text ="📍 <b>Управление точками</b>\n\n❌ Нет маршрутов. Сначала создайте маршрут."
        await callback .message .edit_text (
        msg_text ,
        reply_markup =get_back_to_menu (),
        parse_mode ="HTML"
        )
        await callback .answer ()
        return
    msg_text =f"📍 <b>Управление точками</b>\n\nВыберите маршрут для просмотра точек:\n\n"
    buttons =[]
    for route in routes :
        status ="✅"if route .is_active else "❌"
        buttons .append ([
        InlineKeyboardButton (
        text =f"{status } {route .name } ({route .city_name }) - {route .points_count } точек",
        callback_data =f"admin:route:points:{route .id }"
        )
        ])
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ])
    keyboard =InlineKeyboardMarkup (inline_keyboard =buttons )
    await callback .message .edit_text (
    msg_text ,
    reply_markup =keyboard ,
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:route:points:"))
async def admin_route_points (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    route_id =int (callback .data .split (":")[-1 ])
    point_repo =PointRepository (session )
    points =await point_repo .get_by_route (route_id )
    msg_text =f"📍 <b>Точки маршрута</b>\n\nВсего точек: {len (points )}"
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_points_menu ([{
    'id':p .id ,
    'name':p .name ,
    'order':p .order
    }for p in points ],route_id ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:route:toggle:"))
async def admin_route_toggle (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    route_id =int (callback .data .split (":")[-1 ])
    await session .execute (
    text ("UPDATE routes SET is_active = NOT is_active WHERE id = :route_id"),
    {"route_id":route_id }
    )
    await session .commit ()
    await callback .answer ("✅ Статус изменён")
    await admin_route_view (callback ,session )
@router .callback_query (F .data .startswith ("admin:route:delete:"))
async def admin_route_delete (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    route_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT COUNT(*) FROM user_progress WHERE route_id = :route_id AND status = 'in_progress'"),
    {"route_id":route_id }
    )
    active_count =result .scalar ()
    if active_count >0 :
        await callback .answer (f"❌ Нельзя удалить. {active_count } пользователей проходят маршрут",show_alert =True )
        return
    await session .execute (text ("DELETE FROM reference_images WHERE point_id IN (SELECT id FROM points WHERE route_id = :route_id)"),{"route_id":route_id })
    await session .execute (text ("DELETE FROM user_photos WHERE point_id IN (SELECT id FROM points WHERE route_id = :route_id)"),{"route_id":route_id })
    await session .execute (text ("DELETE FROM points WHERE route_id = :route_id"),{"route_id":route_id })
    await session .execute (text ("DELETE FROM user_progress WHERE route_id = :route_id"),{"route_id":route_id })
    await session .execute (text ("DELETE FROM routes WHERE id = :route_id"),{"route_id":route_id })
    await session .commit ()
    await callback .answer ("✅ Маршрут удалён")
    await admin_routes_list (callback ,session )
@router .callback_query (F .data .startswith ("admin:point:")&~F .data .contains ("add")&~F .data .contains ("edit")&~F .data .contains ("delete")&~F .data .contains ("refs"))
async def admin_point_view (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    point_id =int (callback .data .split (":")[-1 ])
    point_repo =PointRepository (session )
    point =await point_repo .get (point_id )
    if not point :
        await callback .answer ("❌ Точка не найдена")
        return
    result =await session .execute (
    text ("SELECT COUNT(*) FROM user_photos WHERE point_id = :point_id"),
    {"point_id":point_id }
    )
    photos_count =result .scalar ()
    result =await session .execute (
    text ("SELECT COUNT(*) FROM reference_images WHERE point_id = :point_id"),
    {"point_id":point_id }
    )
    refs_count =result .scalar ()
    msg_text =(
    f"📍 <b>{point .order }. {point .name }</b>\n\n"
    f"📝 Описание: {point .description or 'Нет'}\n"
    f"📋 Задание: {point .task_text or 'Нет'}\n"
    f"💡 Факт: {point .fact_text or 'Нет'}\n"
    f"🤸 Поза: {point .require_pose or 'Не требуется'}\n"
    f"👥 Мин. людей: {point .min_people }\n"
    f"📸 Фото пользователей: {photos_count }\n"
    f"🖼 Эталонных фото: {refs_count }\n"
    )
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_point_actions (point_id ,point .route_id ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:point:delete:"))
async def admin_point_delete (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    point_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT route_id FROM points WHERE id = :point_id"),
    {"point_id":point_id }
    )
    route_id =result .scalar ()
    await session .execute (text ("DELETE FROM reference_images WHERE point_id = :point_id"),{"point_id":point_id })
    await session .execute (text ("DELETE FROM user_photos WHERE point_id = :point_id"),{"point_id":point_id })
    await session .execute (text ("DELETE FROM points WHERE id = :point_id"),{"point_id":point_id })
    await session .commit ()
    await callback .answer ("✅ Точка удалена")
    callback .data =f"admin:route:points:{route_id }"
    await admin_route_points (callback ,session )
@router .callback_query (F .data .startswith ("admin:point:refs:"))
async def admin_point_refs (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    point_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT id, file_path, created_at FROM reference_images WHERE point_id = :point_id ORDER BY created_at DESC"),
    {"point_id":point_id }
    )
    refs =result .fetchall ()
    msg_text =f"🖼 <b>Эталонные фото</b>\n\nВсего: {len (refs )}\n\n"
    if refs :
        msg_text +="Для добавления нового фото отправьте его в ответ.\n"
        msg_text +="Для удаления используйте команду /delref <id>"
    else :
        msg_text +="Эталонных фото нет. Отправьте фото для добавления."
    await callback .message .answer (msg_text ,parse_mode ="HTML")
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:users"))
async def admin_users_list (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    page =1
    if "page:"in callback .data :
        page =int (callback .data .split (":")[-1 ])
    per_page =10
    offset =(page -1 )*per_page
    result =await session .execute (
    text ("""
            SELECT u.id, u.telegram_id, u.username, u.first_name,
                   COUNT(DISTINCT up.id) as routes_count,
                   COUNT(DISTINCT uph.id) as photos_count,
                   u.created_at
            FROM users u
            LEFT JOIN user_progress up ON u.id = up.user_id AND up.status = 'completed'
            LEFT JOIN user_photos uph ON u.id = uph.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
    {"limit":per_page ,"offset":offset }
    )
    users =result .fetchall ()
    result =await session .execute (text ("SELECT COUNT(*) FROM users"))
    total =result .scalar ()
    total_pages =(total +per_page -1 )//per_page
    msg_text =f"👥 <b>Пользователи</b>\n\nВсего: {total }\nСтраница {page }/{total_pages }\n\n"
    for user in users :
        msg_text +=(
        f"👤 {user .first_name } (@{user .username or 'нет'})\n"
        f"   ID: {user .telegram_id }\n"
        f"   🗺 Маршрутов: {user .routes_count } | 📸 Фото: {user .photos_count }\n\n"
        )
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_users_pagination (page ,total_pages ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:user:")&~F .data .contains ("stats")&~F .data .contains ("reset")&~F .data .contains ("ban")&~F .data .contains ("unban")&~F .data .contains ("message"))
async def admin_user_view (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    user_telegram_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("""
            SELECT u.id, u.telegram_id, u.username, u.first_name, u.created_at,
                   COUNT(DISTINCT CASE WHEN up.status = 'completed' THEN up.id END) as completed_routes,
                   COUNT(DISTINCT CASE WHEN up.status = 'in_progress' THEN up.id END) as active_routes,
                   COUNT(DISTINCT uph.id) as photos_count
            FROM users u
            LEFT JOIN user_progress up ON u.id = up.user_id
            LEFT JOIN user_photos uph ON u.id = uph.user_id
            WHERE u.telegram_id = :telegram_id
            GROUP BY u.id
        """),
    {"telegram_id":user_telegram_id }
    )
    user =result .fetchone ()
    if not user :
        await callback .answer ("❌ Пользователь не найден")
        return
    text =(
    f"👤 <b>{user .first_name }</b>\n"
    f"@{user .username or 'нет username'}\n\n"
    f"🆔 Telegram ID: {user .telegram_id }\n"
    f"📅 Регистрация: {user .created_at .strftime ('%d.%m.%Y')}\n\n"
    f"📊 <b>Статистика:</b>\n"
    f"✅ Завершено маршрутов: {user .completed_routes }\n"
    f"🔄 В процессе: {user .active_routes }\n"
    f"📸 Загружено фото: {user .photos_count }\n"
    )
    await callback .message .edit_text (
    text ,
    reply_markup =get_user_actions (user_telegram_id ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:user:reset:"))
async def admin_user_reset (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    user_telegram_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT id FROM users WHERE telegram_id = :telegram_id"),
    {"telegram_id":user_telegram_id }
    )
    user_row =result .fetchone ()
    if not user_row :
        await callback .answer ("❌ Пользователь не найден")
        return
    user_id =user_row [0 ]
    await session .execute (text ("DELETE FROM user_photos WHERE user_id = :user_id"),{"user_id":user_id })
    await session .execute (text ("DELETE FROM user_progress WHERE user_id = :user_id"),{"user_id":user_id })
    await session .execute (text ("DELETE FROM user_achievements WHERE user_id = :user_id"),{"user_id":user_id })
    await session .commit ()
    try :
        await bot .send_message (
        user_telegram_id ,
        "⚠️ <b>Ваш прогресс был сброшен администратором</b>\n\n"
        "Вы можете начать заново!",
        parse_mode ="HTML"
        )
    except Exception as e :
        logger .error (f"Ошибка отправки уведомления: {e }")
    await callback .answer ("✅ Прогресс сброшен")
    callback .data =f"admin:user:{user_telegram_id }"
    await admin_user_view (callback ,session )
@router .callback_query (F .data .startswith ("admin:user:ban:"))
async def admin_user_ban (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    user_telegram_id =int (callback .data .split (":")[-1 ])
    await session .execute (
    text ("UPDATE users SET is_banned = 1 WHERE telegram_id = :telegram_id"),
    {"telegram_id":user_telegram_id }
    )
    await session .commit ()
    try :
        await bot .send_message (
        user_telegram_id ,
        "🚫 <b>Вы были заблокированы администратором</b>\n\n"
        "Обратитесь в поддержку для уточнения причины.",
        parse_mode ="HTML"
        )
    except Exception as e :
        logger .error (f"Ошибка отправки уведомления: {e }")
    await callback .answer ("✅ Пользователь заблокирован")
@router .callback_query (F .data .startswith ("admin:user:unban:"))
async def admin_user_unban (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    user_telegram_id =int (callback .data .split (":")[-1 ])
    await session .execute (
    text ("UPDATE users SET is_banned = 0 WHERE telegram_id = :telegram_id"),
    {"telegram_id":user_telegram_id }
    )
    await session .commit ()
    try :
        await bot .send_message (
        user_telegram_id ,
        "✅ <b>Вы были разблокированы</b>\n\n"
        "Теперь вы снова можете пользоваться ботом!",
        parse_mode ="HTML"
        )
    except Exception as e :
        logger .error (f"Ошибка отправки уведомления: {e }")
    await callback .answer ("✅ Пользователь разблокирован")
@router .callback_query (F .data .startswith ("admin:user:message:"))
async def admin_user_message_start (callback :CallbackQuery ,state :FSMContext ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    user_telegram_id =int (callback .data .split (":")[-1 ])
    await state .update_data (target_user_id =user_telegram_id )
    await callback .message .answer (
    "💬 <b>Отправка сообщения пользователю</b>\n\n"
    "Введите текст сообщения:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminUserStates .message )
    await callback .answer ()
@router .message (AdminUserStates .message )
async def admin_user_message_send (message :Message ,state :FSMContext ):
    data =await state .get_data ()
    target_user_id =data ['target_user_id']
    try :
        await bot .send_message (
        target_user_id ,
        f"📨 <b>Сообщение от администратора:</b>\n\n{message .text }",
        parse_mode ="HTML"
        )
        await message .answer ("✅ Сообщение отправлено!")
    except Exception as e :
        await message .answer (f"❌ Ошибка: {e }")
        logger .error (f"Ошибка отправки сообщения: {e }")
    await state .clear ()
@router .callback_query (F .data =="admin:route:add")
async def admin_route_add_start (callback :CallbackQuery ,state :FSMContext ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    city_repo =CityRepository (session )
    cities =await city_repo .get_all ()
    if not cities :
        await callback .answer ("❌ Сначала добавьте хотя бы один город",show_alert =True )
        return
    cities_text ="\n".join ([f"{c .id }. {c .name }"for c in cities ])
    await callback .message .answer (
    f"🗺 <b>Добавление маршрута</b>\n\n"
    f"Доступные города:\n{cities_text }\n\n"
    f"Введите ID города:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminRouteStates .city )
    await callback .answer ()
@router .message (AdminRouteStates .city )
async def admin_route_add_city (message :Message ,state :FSMContext ,session :AsyncSession ):
    try :
        city_id =int (message .text )
        city_repo =CityRepository (session )
        city =await city_repo .get (city_id )
        if not city :
            await message .answer ("❌ Город не найден. Попробуйте снова:")
            return
        await state .update_data (city_id =city_id ,city_name =city .name )
        await message .answer (
        f"Город: <b>{city .name }</b>\n\n"
        "Теперь введите название маршрута:",
        parse_mode ="HTML"
        )
        await state .set_state (AdminRouteStates .name )
    except ValueError :
        await message .answer ("❌ Введите число (ID города)")
@router .message (AdminRouteStates .name )
async def admin_route_add_name (message :Message ,state :FSMContext ):
    await state .update_data (name =message .text )
    await message .answer (
    f"Название: <b>{message .text }</b>\n\n"
    "Введите описание маршрута:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminRouteStates .description )
@router .message (AdminRouteStates .description )
async def admin_route_add_description (message :Message ,state :FSMContext ):
    await state .update_data (description =message .text )
    await message .answer (
    "Выберите тип маршрута:\n\n"
    "1 - Пеший (walking)\n"
    "2 - Велосипедный (cycling)\n\n"
    "Введите номер:"
    )
    await state .set_state (AdminRouteStates .route_type )
@router .message (AdminRouteStates .route_type )
async def admin_route_add_type (message :Message ,state :FSMContext ):
    route_types ={"1":"walking","2":"cycling"}
    route_type =route_types .get (message .text )
    if not route_type :
        await message .answer ("❌ Введите 1 или 2")
        return
    await state .update_data (route_type =route_type )
    await message .answer (
    f"Тип: <b>{route_type }</b>\n\n"
    "Введите расстояние в метрах (например: 2500):",
    parse_mode ="HTML"
    )
    await state .set_state (AdminRouteStates .distance )
@router .message (AdminRouteStates .distance )
async def admin_route_add_distance (message :Message ,state :FSMContext ):
    try :
        distance =int (message .text )
        await state .update_data (distance =distance )
        await message .answer (
        f"Расстояние: <b>{distance }м</b>\n\n"
        "Введите ориентировочное время в минутах (например: 60):",
        parse_mode ="HTML"
        )
        await state .set_state (AdminRouteStates .estimated_duration )
    except ValueError :
        await message .answer ("❌ Введите число (метры)")
@router .message (AdminRouteStates .estimated_duration )
async def admin_route_add_duration (message :Message ,state :FSMContext ):
    try :
        duration =int (message .text )
        await state .update_data (estimated_duration =duration )
        await message .answer (
        f"Время: <b>{duration }мин</b>\n\n"
        "Введите цену в рублях (например: 500):",
        parse_mode ="HTML"
        )
        await state .set_state (AdminRouteStates .price )
    except ValueError :
        await message .answer ("❌ Введите число (минуты)")
@router .message (AdminRouteStates .price )
async def admin_route_add_price (message :Message ,state :FSMContext ,session :AsyncSession ):
    try :
        price =int (message .text )
        data =await state .get_data ()
        await session .execute (
        text ("""
                INSERT INTO routes (city_id, name, description, route_type, distance, estimated_duration, price, is_active)
                VALUES (:city_id, :name, :description, :route_type, :distance, :duration, :price, 1)
            """),
        {
        "city_id":data ['city_id'],
        "name":data ['name'],
        "description":data ['description'],
        "route_type":data ['route_type'],
        "distance":data ['distance'],
        "duration":data ['estimated_duration'],
        "price":price
        }
        )
        await session .commit ()
        await message .answer (
        f"✅ Маршрут <b>{data ['name']}</b> добавлен!\n\n"
        f"Теперь добавьте точки для этого маршрута через /admin",
        parse_mode ="HTML"
        )
        await state .clear ()
    except ValueError :
        await message .answer ("❌ Введите число (рубли)")
@router .callback_query (F .data .startswith ("admin:point:add:"))
async def admin_point_add_start (callback :CallbackQuery ,state :FSMContext ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    route_id =int (callback .data .split (":")[-1 ])
    result =await session .execute (
    text ("SELECT COALESCE(MAX(`order`), 0) + 1 FROM points WHERE route_id = :route_id"),
    {"route_id":route_id }
    )
    next_order =result .scalar ()
    await state .update_data (route_id =route_id ,order =next_order )
    await callback .message .answer (
    f"📍 <b>Добавление точки</b>\n\n"
    f"Порядковый номер: {next_order }\n\n"
    f"Введите название точки:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminPointStates .name )
    await callback .answer ()
@router .message (AdminPointStates .name )
async def admin_point_add_name (message :Message ,state :FSMContext ):
    await state .update_data (name =message .text )
    await message .answer (
    f"Название: <b>{message .text }</b>\n\n"
    "Введите описание точки:",
    parse_mode ="HTML"
    )
    await state .set_state (AdminPointStates .description )
@router .message (AdminPointStates .description )
async def admin_point_add_description (message :Message ,state :FSMContext ):
    await state .update_data (description =message .text )
    await message .answer (
    "Введите текст задания для пользователя:"
    )
    await state .set_state (AdminPointStates .task_text )
@router .message (AdminPointStates .task_text )
async def admin_point_add_task (message :Message ,state :FSMContext ):
    await state .update_data (task_text =message .text )
    await message .answer (
    "Введите интересный факт о месте (или /skip):"
    )
    await state .set_state (AdminPointStates .fact_text )
@router .message (AdminPointStates .fact_text )
async def admin_point_add_fact (message :Message ,state :FSMContext ):
    fact =None if message .text =="/skip"else message .text
    await state .update_data (fact_text =fact )
    await message .answer (
    "Требуется ли поза?\n\n"
    "1 - Руки вверх (hands_up)\n"
    "2 - Сердечко (сердце)\n"
    "3 - Указать на объект (точку)\n"
    "4 - Не требуется\n\n"
    "Введите номер:"
    )
    await state .set_state (AdminPointStates .require_pose )
@router .message (AdminPointStates .require_pose )
async def admin_point_add_pose (message :Message ,state :FSMContext ):
    poses ={"1":"hands_up","2":"heart","3":"point","4":None }
    pose =poses .get (message .text )
    if message .text not in poses :
        await message .answer ("❌ Введите номер от 1 до 4")
        return
    await state .update_data (require_pose =pose )
    await message .answer (
    "Минимальное количество людей на фото?\n\n"
    "Введите число (например: 2) или 1 если не важно:"
    )
    await state .set_state (AdminPointStates .min_people )
@router .message (AdminPointStates .min_people )
async def admin_point_add_people (message :Message ,state :FSMContext ,session :AsyncSession ):
    try :
        min_people =int (message .text )
        data =await state .get_data ()
        await session .execute (
        text ("""
                INSERT INTO points (route_id, name, description, task_text, fact_text, `order`, require_pose, min_people)
                VALUES (:route_id, :name, :description, :task_text, :fact_text, :order, :require_pose, :min_people)
            """),
        {
        "route_id":data ['route_id'],
        "name":data ['name'],
        "description":data ['description'],
        "task_text":data ['task_text'],
        "fact_text":data .get ('fact_text'),
        "order":data ['order'],
        "require_pose":data .get ('require_pose'),
        "min_people":min_people
        }
        )
        await session .commit ()
        await message .answer (
        f"✅ Точка <b>{data ['name']}</b> добавлена!\n\n"
        f"Теперь загрузите эталонные фото для проверки локации.\n"
        f"Отправьте фото или используйте /admin для возврата в меню.",
        parse_mode ="HTML"
        )
        await state .clear ()
    except ValueError :
        await message .answer ("❌ Введите число")
@router .callback_query (F .data =="admin:stats")
async def admin_statistics (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    stats =await get_detailed_stats (session )
    msg_text =(
    f"📊 <b>Статистика QuestGuideRF</b>\n\n"
    f"👥 <b>Пользователи:</b>\n"
    f"   Всего: {stats ['total_users']}\n"
    f"   Активных (7 дней): {stats ['active_users']}\n"
    f"   Новых (сегодня): {stats ['new_users_today']}\n\n"
    f"🗺 <b>Маршруты:</b>\n"
    f"   Всего: {stats ['total_routes']}\n"
    f"   Активных: {stats ['active_routes']}\n"
    f"   Пройдено раз: {stats ['completed_routes']}\n\n"
    f"📍 <b>Точки:</b>\n"
    f"   Всего: {stats ['total_points']}\n\n"
    f"📸 <b>Фото:</b>\n"
    f"   Всего загружено: {stats ['total_photos']}\n"
    f"   На проверке: {stats ['pending_photos']}\n"
    f"   Принято: {stats ['approved_photos']}\n"
    f"   Отклонено: {stats ['rejected_photos']}\n\n"
    f"💰 <b>Платежи:</b>\n"
    f"   Всего: {stats ['total_payments']}₽\n"
    f"   Успешных: {stats ['successful_payments']}\n"
    )
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_back_to_menu (),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("admin:photos"))
async def admin_photo_history (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    page =1
    if "page:"in callback .data :
        try :
            page =int (callback .data .split (":")[-1 ])
        except :
            page =1
    per_page =5
    offset =(page -1 )*per_page
    result =await session .execute (
    text ("""
            SELECT uph.id, uph.user_id, uph.point_id, uph.file_path, uph.created_at,
                   u.telegram_id, u.username, u.first_name,
                   p.name as point_name, p.order as point_order,
                   r.name as route_name, r.id as route_id
            FROM user_photos uph
            JOIN users u ON uph.user_id = u.id
            JOIN points p ON uph.point_id = p.id
            JOIN routes r ON p.route_id = r.id
            ORDER BY uph.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
    {"limit":per_page ,"offset":offset }
    )
    photos =result .fetchall ()
    result =await session .execute (text ("SELECT COUNT(*) FROM user_photos"))
    total =result .scalar ()
    total_pages =(total +per_page -1 )//per_page if total >0 else 1
    msg_text =f"📸 <b>История проверки фото</b>\n\nВсего фото: {total }\nСтраница {page }/{total_pages }\n\n"
    if photos :
        for photo in photos :
            msg_text +=(
            f"📷 <b>{photo .point_name }</b> (Маршрут: {photo .route_name })\n"
            f"👤 Пользователь: {photo .first_name } (@{photo .username or 'нет'})\n"
            f"📅 Дата: {photo .created_at .strftime ('%d.%m.%Y %H:%M')}\n"
            f"📍 Точка #{photo .point_order }\n\n"
            )
    else :
        msg_text +="Нет фото для отображения."
    await callback .message .edit_text (
    msg_text ,
    reply_markup =get_photo_history_pagination (page ,total_pages ),
    parse_mode ="HTML"
    )
    await callback .answer ()
@router .callback_query (F .data =="admin:photos:refresh")
async def admin_photo_history_refresh (callback :CallbackQuery ,session :AsyncSession ):
    callback .data ="admin:photos"
    await admin_photo_history (callback ,session )
@router .callback_query (F .data =="admin:settings")
async def admin_settings (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    result =await session .execute (
    text ("SELECT value FROM system_settings WHERE `key` = 'restart_notifications_enabled'")
    )
    row =result .fetchone ()
    restart_notifications =row [0 ]=='1'if row else True
    vision_config =config .vision
    msg_text =(
    f"⚙️ <b>Настройки системы</b>\n\n"
    f"📊 <b>Текущие настройки:</b>\n\n"
    f"🎯 Порог уверенности локации: {vision_config .similarity_threshold *100 :.0f}%\n"
    f"📸 Макс. фото в час: Не ограничено\n"
    f"⏱ Время жизни токена: 5 минут\n"
    f"🤖 Автопроверки: Включены\n"
    f"🔄 Уведомления о перезапуске: {'✅ Включены'if restart_notifications else '❌ Выключены'}\n\n"
    f"💡 <i>Для изменения настроек отредактируйте файл .env или config.py</i>"
    )
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [
    InlineKeyboardButton (
    text =f"{'🔕 Выключить'if restart_notifications else '🔔 Включить'} уведомления о перезапуске",
    callback_data ="admin:settings:toggle_restart_notifications"
    )
    ],
    [
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ]
    ])
    await safe_edit_text (callback ,msg_text ,reply_markup =keyboard )
    await callback .answer ()
@router .callback_query (F .data =="admin:settings:toggle_restart_notifications")
async def admin_toggle_restart_notifications (callback :CallbackQuery ,session :AsyncSession ):
    if not is_admin (callback .from_user .id ):
        await callback .answer ("❌ Нет прав")
        return
    result =await session .execute (
    text ("SELECT value FROM system_settings WHERE `key` = 'restart_notifications_enabled'")
    )
    row =result .fetchone ()
    current_value =row [0 ]if row else '1'
    new_value ='0'if current_value =='1'else '1'
    await session .execute (
    text ("""
            INSERT INTO system_settings (`key`, `value`, `description`)
            VALUES ('restart_notifications_enabled', :value, 'Уведомления о перезапуске бота')
            ON DUPLICATE KEY UPDATE `value` = :value
        """),
    {"value":new_value }
    )
    await session .commit ()
    status ="включены"if new_value =='1'else "выключены"
    await callback .answer (f"✅ Уведомления о перезапуске {status }")
    await admin_settings (callback ,session )
async def get_admin_stats (session :AsyncSession )->dict :
    stats ={}
    result =await session .execute (text ("SELECT COUNT(*) FROM users"))
    stats ['total_users']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM routes"))
    stats ['total_routes']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM points"))
    stats ['total_points']=result .scalar ()
    stats ['pending_photos']=0
    return stats
async def get_detailed_stats (session :AsyncSession )->dict :
    stats ={}
    result =await session .execute (text ("SELECT COUNT(*) FROM users"))
    stats ['total_users']=result .scalar ()
    week_ago =datetime .utcnow ()-timedelta (days =7 )
    result =await session .execute (
    text ("SELECT COUNT(DISTINCT user_id) FROM user_progress WHERE updated_at > :week_ago"),
    {"week_ago":week_ago }
    )
    stats ['active_users']=result .scalar ()
    today =datetime .utcnow ().replace (hour =0 ,minute =0 ,second =0 ,microsecond =0 )
    result =await session .execute (
    text ("SELECT COUNT(*) FROM users WHERE created_at > :today"),
    {"today":today }
    )
    stats ['new_users_today']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM routes"))
    stats ['total_routes']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM routes WHERE is_active = 1"))
    stats ['active_routes']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM user_progress WHERE status = 'completed'"))
    stats ['completed_routes']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM points"))
    stats ['total_points']=result .scalar ()
    result =await session .execute (text ("SELECT COUNT(*) FROM user_photos"))
    stats ['total_photos']=result .scalar ()
    stats ['pending_photos']=0
    stats ['approved_photos']=0
    stats ['rejected_photos']=0
    result =await session .execute (text ("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'"))
    stats ['total_payments']=result .scalar ()or 0
    result =await session .execute (text ("SELECT COUNT(*) FROM payments WHERE status = 'completed'"))
    stats ['successful_payments']=result .scalar ()
    return stats
@router .callback_query (F .data .startswith ("appr:"))
async def admin_approve_photo (
callback :CallbackQuery ,
session :AsyncSession ,
):
    try :
        parts =callback .data .split (":",3 )
        if len (parts )<4 :
            await callback .answer ("❌ Неверный формат данных")
            return
        user_telegram_id =int (parts [1 ])
        point_id =int (parts [2 ])
        progress_id =int (parts [3 ])
        logger .info (f"Админ {callback .from_user .id } принимает фото от пользователя {user_telegram_id }")
        if not callback .message or not callback .message .photo :
            await callback .answer ("❌ Фото не найдено в сообщении")
            return
        photo =callback .message .photo [-1 ]
        photo_file_id =photo .file_id
        progress_repo =ProgressRepository (session )
        point_repo =PointRepository (session )
        progress =await progress_repo .get (progress_id )
        point =await point_repo .get (point_id )
        if not progress or not point :
            await callback .answer ("❌ Данные не найдены")
            return
        user_result =await session .execute (
        text ("SELECT id FROM users WHERE telegram_id = :telegram_id"),
        {"telegram_id":user_telegram_id }
        )
        user_row =user_result .fetchone ()
        if not user_row :
            await callback .answer ("❌ Пользователь не найден")
            return
        user_id =user_row [0 ]
        try :
            file =await bot .get_file (photo_file_id )
            temp_path =f"photos/temp_{photo_file_id }.jpg"
            Path ("photos").mkdir (exist_ok =True )
            await bot .download_file (file .file_path ,temp_path )
            user_photos_dir =Path ("../../photos")/str (user_telegram_id )
            user_photos_dir .mkdir (parents =True ,exist_ok =True )
            timestamp =datetime .utcnow ().strftime ('%Y%m%d_%H%M%S')
            filename =f"point_{point_id }_{timestamp }.jpg"
            permanent_path =user_photos_dir /filename
            shutil .copy2 (temp_path ,str (permanent_path ))
            os .remove (temp_path )
            relative_path =f"/photos/{user_telegram_id }/{filename }"
            await session .execute (
            text (
            "INSERT INTO user_photos (user_id, point_id, file_id, file_path, file_hash) "
            "VALUES (:user_id, :point_id, :file_id, :file_path, :file_hash)"
            ),
            {
            "user_id":user_id ,
            "point_id":point_id ,
            "file_id":photo_file_id ,
            "file_path":relative_path ,
            "file_hash":None ,
            }
            )
            await session .commit ()
            logger .info (f"Фото сохранено: {relative_path }, user_id={user_id }, point_id={point_id }")
        except Exception as e :
            logger .error (f"Ошибка при сохранении фото: {e }",exc_info =True )
            await callback .answer (f"❌ Ошибка сохранения: {str (e )}")
            return
        next_point =await point_repo .get_next_point (progress .route_id ,progress .current_point_order )
        if next_point :
            await progress_repo .complete_point (progress ,next_point .id ,next_point .order )
        else :
            await progress_repo .complete_point (progress ,None ,None )
        await session .commit ()
        try :
            if next_point :
                await bot .send_message (
                user_telegram_id ,
                f"✅ <b>Администратор принял ваше фото!</b>\n\n"
                f"📍 Точка засчитана: {point .name }\n\n"
                f"Следующая точка: {next_point .name }\n"
                f"📝 {next_point .task_text }",
                parse_mode ="HTML"
                )
            else :
                await bot .send_message (
                user_telegram_id ,
                f"✅ <b>Администратор принял ваше фото!</b>\n\n"
                f"🎉 Поздравляем! Квест завершён!",
                parse_mode ="HTML"
                )
        except Exception as e :
            logger .error (f"Ошибка отправки уведомления пользователю: {e }")
        await callback .message .edit_caption (
        caption =f"{callback .message .caption }\n\n✅ <b>ПРИНЯТО</b> администратором @{callback .from_user .username or callback .from_user .id }",
        parse_mode ="HTML"
        )
        await callback .answer ("✅ Фото принято! Пользователь уведомлён")
    except Exception as e :
        logger .error (f"Ошибка при принятии фото: {e }",exc_info =True )
        await callback .answer ("❌ Ошибка при обработке")
@router .callback_query (F .data .startswith ("rej:"))
async def admin_reject_photo (
callback :CallbackQuery ,
session :AsyncSession ,
):
    try :
        parts =callback .data .split (":",1 )
        if len (parts )<2 :
            await callback .answer ("❌ Неверный формат данных")
            return
        user_telegram_id =int (parts [1 ])
        try :
            await bot .send_message (
            user_telegram_id ,
            f"❌ <b>Администратор отклонил ваше фото</b>\n\n"
            f"Пожалуйста, попробуйте сделать новое фото и отправьте его снова.\n\n"
            f"💡 Убедитесь, что:\n"
            f"• Вы находитесь в нужном месте\n"
            f"• На фото видны все необходимые элементы\n"
            f"• Фото сделано чётко и ясно",
            parse_mode ="HTML"
            )
        except Exception as e :
            logger .error (f"Ошибка отправки уведомления пользователю: {e }")
        await callback .message .edit_caption (
        caption =f"{callback .message .caption }\n\n❌ <b>ОТКЛОНЕНО</b> администратором @{callback .from_user .username or callback .from_user .id }",
        parse_mode ="HTML"
        )
        await callback .answer ("❌ Фото отклонено. Пользователь уведомлён")
        logger .info (f"Админ {callback .from_user .id } отклонил фото от пользователя {user_telegram_id }")
    except Exception as e :
        logger .error (f"Ошибка при отклонении фото: {e }",exc_info =True )
        await callback .answer ("❌ Ошибка при обработке")
