import logging
from typing import List ,Optional
from aiogram import Bot
from aiogram .types import InlineKeyboardMarkup ,InlineKeyboardButton ,FSInputFile
from sqlalchemy .ext .asyncio import AsyncSession
from sqlalchemy import text
logger =logging .getLogger (__name__ )
class AdminNotifier :
    def __init__ (self ,bot :Bot ,admin_ids :List [int ]):
        self .bot =bot
        self .admin_ids =admin_ids
    async def is_restart_notifications_enabled (self ,session :AsyncSession )->bool :
        try :
            result =await session .execute (
            text ("SELECT value FROM system_settings WHERE `key` = 'restart_notifications_enabled'")
            )
            row =result .fetchone ()
            if row :
                return row [0 ]=='1'or row [0 ].lower ()=='true'
            return True
        except Exception as e :
            logger .error (f"Ошибка проверки настройки уведомлений: {e }")
            return True
    async def notify_photo_verification_needed (
    self ,
    photo_path :str ,
    user_id :int ,
    username :Optional [str ],
    point_name :str ,
    point_id :int ,
    progress_id :int ,
    photo_file_id :str ,
    route_name :str ,
    error_reason :str ,
    people_count :Optional [int ]=None ,
    pose_required :Optional [str ]=None ,
    location_match :Optional [float ]=None ,
    ):
        user_link =f"@{username }"if username else f"ID: {user_id }"
        message =(
        f"🔍 <b>Требуется проверка фото</b>\n\n"
        f"👤 Пользователь: {user_link }\n"
        f"🗺️ Маршрут: {route_name }\n"
        f"📍 Точка: {point_name }\n\n"
        f"❌ <b>Причина отклонения:</b>\n{error_reason }\n\n"
        )
        if people_count is not None :
            message +=f"👥 Людей на фото: {people_count }\n"
        if pose_required :
            pose_names ={
            'hands_up':'Руки вверх',
            'heart':'Сердечко руками',
            'point':'Указать на объект'
            }
            message +=f"🤸 Требуемая поза: {pose_names .get (pose_required ,pose_required )}\n"
        if location_match is not None :
            message +=f"📸 Совпадение локации: {location_match :.1f}%\n"
        message +="\n<b>Принять фото?</b>"
        callback_approve =f"appr:{user_id }:{point_id }:{progress_id }"
        callback_reject =f"rej:{user_id }"
        keyboard =InlineKeyboardMarkup (inline_keyboard =[
        [
        InlineKeyboardButton (
        text ="✅ Принять",
        callback_data =callback_approve [:64 ]
        ),
        InlineKeyboardButton (
        text ="❌ Отклонить",
        callback_data =callback_reject [:64 ]
        )
        ]
        ])
        for admin_id in self .admin_ids :
            try :
                photo =FSInputFile (photo_path )
                await self .bot .send_photo (
                chat_id =admin_id ,
                photo =photo ,
                caption =message ,
                reply_markup =keyboard ,
                parse_mode ="HTML"
                )
                logger .info (f"Отправлено уведомление админу {admin_id } о фото от пользователя {user_id }")
            except Exception as e :
                logger .error (f"Ошибка отправки уведомления админу {admin_id }: {e }",exc_info =True )
    async def notify_critical_error (self ,error_message :str ,error_details :Optional [str ]=None ):
        message =f"🚨 <b>КРИТИЧЕСКАЯ ОШИБКА</b>\n\n{error_message }"
        if error_details :
            if len (error_details )>3000 :
                error_details =error_details [:3000 ]+"...\n\n(обрезано)"
            message +=f"\n\n<pre>{error_details }</pre>"
        for admin_id in self .admin_ids :
            try :
                await self .bot .send_message (
                chat_id =admin_id ,
                text =message ,
                parse_mode ="HTML"
                )
                logger .info (f"Отправлено уведомление о критической ошибке админу {admin_id }")
            except Exception as e :
                logger .error (f"Ошибка отправки критической ошибки админу {admin_id }: {e }")
    async def notify_bot_restart (self ,error_log :Optional [str ]=None ,session :Optional [AsyncSession ]=None ):
        if session :
            if not await self .is_restart_notifications_enabled (session ):
                logger .info ("Уведомления о перезапуске отключены в настройках")
                return
        message ="🔄 <b>Бот перезапущен</b>\n\n"
        if error_log :
            message +="📋 <b>Последние ошибки:</b>\n"
            if len (error_log )>3000 :
                error_log =error_log [-3000 :]
            message +=f"<pre>{error_log }</pre>"
        else :
            message +="✅ Перезапуск прошёл успешно, ошибок не обнаружено."
        for admin_id in self .admin_ids :
            try :
                await self .bot .send_message (
                chat_id =admin_id ,
                text =message ,
                parse_mode ="HTML"
                )
            except Exception as e :
                logger .error (f"Ошибка отправки уведомления о перезапуске админу {admin_id }: {e }")