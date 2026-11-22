from typing import List
from typing import List
from aiogram .types import InlineKeyboardMarkup ,InlineKeyboardButton ,ReplyKeyboardMarkup ,KeyboardButton
from aiogram .utils .keyboard import InlineKeyboardBuilder
from bot .models .city import City
from bot .models .route import Route
class UserKeyboards :
    @staticmethod
    def main_menu ()->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        builder .row (
        InlineKeyboardButton (text ="🏙️ Выбрать город",callback_data ="select_city"),
        )
        builder .row (
        InlineKeyboardButton (text ="📊 Моя статистика",callback_data ="my_stats"),
        )
        builder .row (
        InlineKeyboardButton (text ="ℹ️ О боте",callback_data ="about"),
        )
        return builder .as_markup ()
    @staticmethod
    def city_list (cities :List [City ])->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        for city in cities :
            builder .row (
            InlineKeyboardButton (
            text =city .name ,
            callback_data =f"city:{city .id }",
            )
            )
        builder .row (
        InlineKeyboardButton (text ="◀️ Назад",callback_data ="back_to_main"),
        )
        return builder .as_markup ()
    @staticmethod
    def route_list (routes :List [Route ])->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        for route in routes :
            icon ="🚶"if route .route_type .value =="walking"else "🚴"
            text =f"{icon } {route .name } - {route .price }₽"
            builder .row (
            InlineKeyboardButton (
            text =text ,
            callback_data =f"route:{route .id }",
            )
            )
        builder .row (
        InlineKeyboardButton (text ="◀️ Назад",callback_data ="select_city"),
        )
        return builder .as_markup ()
    @staticmethod
    def route_detail (route_id :int ,has_paid :bool =False )->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        if has_paid :
            builder .row (
            InlineKeyboardButton (
            text ="▶️ Начать квест",
            callback_data =f"start_quest:{route_id }",
            )
            )
        else :
            builder .row (
            InlineKeyboardButton (
            text ="💳 Оплатить",
            callback_data =f"pay:{route_id }",
            )
            )
        builder .row (
        InlineKeyboardButton (text ="◀️ Назад",callback_data ="back_to_routes"),
        )
        return builder .as_markup ()
    @staticmethod
    def quest_menu (route_id :int )->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        builder .row (
        InlineKeyboardButton (
        text ="❌ Прервать квест",
        callback_data =f"cancel_quest:{route_id }",
        )
        )
        return builder .as_markup ()
    @staticmethod
    def quest_completed ()->InlineKeyboardMarkup :
        builder =InlineKeyboardBuilder ()
        builder .row (
        InlineKeyboardButton (text ="🏠 Главное меню",callback_data ="back_to_main"),
        )
        builder .row (
        InlineKeyboardButton (text ="🔄 Выбрать другой маршрут",callback_data ="select_city"),
        )
        return builder .as_markup ()
    @staticmethod
    def cancel_keyboard ()->ReplyKeyboardMarkup :
        return ReplyKeyboardMarkup (
        keyboard =[
        [KeyboardButton (text ="❌ Отмена")],
        ],
        resize_keyboard =True ,
        )