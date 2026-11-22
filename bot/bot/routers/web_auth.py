from datetime import datetime ,timedelta
from aiogram import Router
from aiogram .filters import Command
from aiogram .types import Message ,InlineKeyboardMarkup ,InlineKeyboardButton
from sqlalchemy .ext .asyncio import AsyncSession
from bot .models .user_session import UserSession
from bot .config import load_config
router =Router ()
config =load_config ()
@router .message (Command ("web"))
async def cmd_web (message :Message ,session :AsyncSession ):
    telegram_id =message .from_user .id
    token =UserSession .generate_token ()
    user_session =UserSession (
    telegram_id =telegram_id ,
    token =token ,
    is_used =False ,
    created_at =datetime .utcnow (),
    expires_at =datetime .utcnow ()+timedelta (minutes =5 ),
    )
    session .add (user_session )
    await session .commit ()
    auth_url =f"{config .web .site_url }/auth/telegram.php?token={token }"
    keyboard =InlineKeyboardMarkup (inline_keyboard =[
    [InlineKeyboardButton (text ="🌐 Войти на сайт",url =auth_url )]
    ])
    await message .answer (
    "🌐 Вход на сайт\n\n"
    "Нажмите кнопку ниже, чтобы войти в личный кабинет на сайте.\n\n"
    "⚠️ Ссылка действительна 5 минут.",
    reply_markup =keyboard
    )