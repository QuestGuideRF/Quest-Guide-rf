from aiogram .types import InlineKeyboardMarkup ,InlineKeyboardButton
from typing import List ,Optional
def get_admin_main_menu ()->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="🏙 Города",callback_data ="admin:cities")],
    [InlineKeyboardButton (text ="🗺 Маршруты",callback_data ="admin:routes")],
    [InlineKeyboardButton (text ="📍 Точки",callback_data ="admin:points")],
    [InlineKeyboardButton (text ="📸 История фото",callback_data ="admin:photos")],
    [InlineKeyboardButton (text ="👥 Пользователи",callback_data ="admin:users")],
    [InlineKeyboardButton (text ="📊 Статистика",callback_data ="admin:stats")],
    [InlineKeyboardButton (text ="⚙️ Настройки",callback_data ="admin:settings")],
    ])
    return keyboard
def get_cities_menu (cities :List [dict ])->InlineKeyboardMarkup :
    buttons =[]
    for city in cities :
        status ="✅"if city ['is_active']else "❌"
        buttons .append ([
        InlineKeyboardButton (
        text =f"{status } {city ['name']}",
        callback_data =f"admin:city:{city ['id']}"
        )
        ])
    buttons .append ([
    InlineKeyboardButton (text ="➕ Добавить город",callback_data ="admin:city:add")
    ])
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ])
    return InlineKeyboardMarkup (inline_keyboard =buttons )
def get_city_actions (city_id :int )->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="✏️ Редактировать",callback_data =f"admin:city:edit:{city_id }")],
    [InlineKeyboardButton (text ="👁 Показать/скрыть",callback_data =f"admin:city:toggle:{city_id }")],
    [InlineKeyboardButton (text ="🗑 Удалить",callback_data =f"admin:city:delete:{city_id }")],
    [InlineKeyboardButton (text ="« Назад",callback_data ="admin:cities")],
    ])
    return keyboard
def get_routes_menu (routes :List [dict ])->InlineKeyboardMarkup :
    buttons =[]
    for route in routes :
        status ="✅"if route ['is_active']else "❌"
        buttons .append ([
        InlineKeyboardButton (
        text =f"{status } {route ['name']} ({route ['city_name']})",
        callback_data =f"admin:route:{route ['id']}"
        )
        ])
    buttons .append ([
    InlineKeyboardButton (text ="➕ Добавить маршрут",callback_data ="admin:route:add")
    ])
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ])
    return InlineKeyboardMarkup (inline_keyboard =buttons )
def get_route_actions (route_id :int )->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="✏️ Редактировать",callback_data =f"admin:route:edit:{route_id }")],
    [InlineKeyboardButton (text ="📍 Точки маршрута",callback_data =f"admin:route:points:{route_id }")],
    [InlineKeyboardButton (text ="👁 Показать/скрыть",callback_data =f"admin:route:toggle:{route_id }")],
    [InlineKeyboardButton (text ="🗑 Удалить",callback_data =f"admin:route:delete:{route_id }")],
    [InlineKeyboardButton (text ="« Назад",callback_data ="admin:routes")],
    ])
    return keyboard
def get_points_menu (points :List [dict ],route_id :int )->InlineKeyboardMarkup :
    buttons =[]
    for point in points :
        buttons .append ([
        InlineKeyboardButton (
        text =f"{point ['order']}. {point ['name']}",
        callback_data =f"admin:point:{point ['id']}"
        )
        ])
    buttons .append ([
    InlineKeyboardButton (text ="➕ Добавить точку",callback_data =f"admin:point:add:{route_id }")
    ])
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:points")
    ])
    return InlineKeyboardMarkup (inline_keyboard =buttons )
def get_point_actions (point_id :int ,route_id :int )->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="✏️ Редактировать",callback_data =f"admin:point:edit:{point_id }")],
    [InlineKeyboardButton (text ="📸 Эталонные фото",callback_data =f"admin:point:refs:{point_id }")],
    [InlineKeyboardButton (text ="🗑 Удалить",callback_data =f"admin:point:delete:{point_id }")],
    [InlineKeyboardButton (text ="« Назад",callback_data =f"admin:route:points:{route_id }")],
    ])
    return keyboard
def get_users_pagination (page :int =1 ,total_pages :int =1 )->InlineKeyboardMarkup :
    buttons =[]
    nav_buttons =[]
    if page >1 :
        nav_buttons .append (InlineKeyboardButton (text ="◀️",callback_data =f"admin:users:page:{page -1 }"))
    nav_buttons .append (InlineKeyboardButton (text =f"{page }/{total_pages }",callback_data ="admin:users:page:current"))
    if page <total_pages :
        nav_buttons .append (InlineKeyboardButton (text ="▶️",callback_data =f"admin:users:page:{page +1 }"))
    if nav_buttons :
        buttons .append (nav_buttons )
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ])
    return InlineKeyboardMarkup (inline_keyboard =buttons )
def get_user_actions (user_id :int )->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="📊 Статистика",callback_data =f"admin:user:stats:{user_id }")],
    [InlineKeyboardButton (text ="🔄 Сбросить прогресс",callback_data =f"admin:user:reset:{user_id }")],
    [InlineKeyboardButton (text ="🚫 Заблокировать",callback_data =f"admin:user:ban:{user_id }")],
    [InlineKeyboardButton (text ="✅ Разблокировать",callback_data =f"admin:user:unban:{user_id }")],
    [InlineKeyboardButton (text ="💬 Отправить сообщение",callback_data =f"admin:user:message:{user_id }")],
    [InlineKeyboardButton (text ="« Назад",callback_data ="admin:users")],
    ])
    return keyboard
def get_photo_history_pagination (page :int =1 ,total_pages :int =1 )->InlineKeyboardMarkup :
    buttons =[]
    nav_buttons =[]
    if page >1 :
        nav_buttons .append (InlineKeyboardButton (text ="◀️",callback_data =f"admin:photos:page:{page -1 }"))
    if total_pages >1 :
        nav_buttons .append (InlineKeyboardButton (text =f"{page }/{total_pages }",callback_data ="admin:photos:page:current"))
    if page <total_pages :
        nav_buttons .append (InlineKeyboardButton (text ="▶️",callback_data =f"admin:photos:page:{page +1 }"))
    if nav_buttons :
        buttons .append (nav_buttons )
    buttons .append ([
    InlineKeyboardButton (text ="🔄 Обновить",callback_data ="admin:photos")
    ])
    buttons .append ([
    InlineKeyboardButton (text ="« Назад",callback_data ="admin:menu")
    ])
    return InlineKeyboardMarkup (inline_keyboard =buttons )
def get_confirm_keyboard (action :str ,entity_id :int )->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [
    InlineKeyboardButton (text ="✅ Да",callback_data =f"admin:confirm:{action }:{entity_id }"),
    InlineKeyboardButton (text ="❌ Нет",callback_data =f"admin:cancel:{action }:{entity_id }")
    ]
    ])
    return keyboard
def get_back_to_menu ()->InlineKeyboardMarkup :
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="« В главное меню",callback_data ="admin:menu")]
    ])
    return keyboard