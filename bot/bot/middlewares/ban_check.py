import logging
from typing import Callable ,Dict ,Any ,Awaitable ,Union
from aiogram import BaseMiddleware
from aiogram .types import Message ,CallbackQuery
from sqlalchemy .ext .asyncio import AsyncSession
from sqlalchemy import text
logger =logging .getLogger (__name__ )
class BanCheckMiddleware (BaseMiddleware ):
    async def __call__ (
    self ,
    handler :Callable [[Union [Message ,CallbackQuery ],Dict [str ,Any ]],Awaitable [Any ]],
    event :Union [Message ,CallbackQuery ],
    data :Dict [str ,Any ]
    )->Any :
        session :AsyncSession =data .get ("session")
        user_id =event .from_user .id
        if session :
            try :
                result =await session .execute (
                text ("SELECT is_banned FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id":user_id }
                )
                row =result .fetchone ()
                if row and row [0 ]==1 :
                    if isinstance (event ,Message ):
                        await event .answer (
                        "🚫 <b>Вы заблокированы</b>\n\n"
                        "Обратитесь в поддержку для уточнения причины.",
                        parse_mode ="HTML"
                        )
                    elif isinstance (event ,CallbackQuery ):
                        await event .answer ("🚫 Вы заблокированы",show_alert =True )
                    return
            except Exception as e :
                logger .error (f"Ошибка проверки блокировки: {e }")
        return await handler (event ,data )