import asyncio
import logging
import traceback
from pathlib import Path
from aiogram import Dispatcher
from sqlalchemy import text
from bot .loader import bot ,dp ,engine
from bot .models import Base
from bot .middlewares import DbSessionMiddleware ,UserMiddleware
from bot .middlewares .ban_check import BanCheckMiddleware
from bot .routers import user_router ,admin_router ,payment_router ,web_auth_router
from bot .config import load_config
from bot .services .admin_notifier import AdminNotifier
logging .basicConfig (
level =logging .INFO ,
format ="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger =logging .getLogger (__name__ )
async def create_tables ():
    async with engine .begin ()as conn :
        await conn .run_sync (Base .metadata .create_all )
        await conn .execute (text ("""
            CREATE TABLE IF NOT EXISTS `system_settings` (
              `id` int UNSIGNED NOT NULL AUTO_INCREMENT,
              `key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
              `value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
              `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
              `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `key` (`key`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        await conn .execute (text ("""
            INSERT IGNORE INTO `system_settings` (`key`, `value`, `description`)
            VALUES ('restart_notifications_enabled', '1', 'Уведомления о перезапуске бота (1 - включено, 0 - выключено)')
        """))
    logger .info ("✅ Таблицы БД созданы")
async def check_db_connection ():
    try :
        async with engine .connect ()as conn :
            await conn .execute (text ("SELECT 1"))
        logger .info ("✅ Подключение к БД успешно")
        return True
    except Exception as e :
        logger .error (f"❌ Ошибка подключения к БД: {e }")
        return False
def setup_routers (dp :Dispatcher ):
    dp .include_router (user_router )
    dp .include_router (admin_router )
    dp .include_router (payment_router )
    dp .include_router (web_auth_router )
    logger .info ("✅ Роутеры подключены")
def setup_middlewares (dp :Dispatcher ):
    dp .message .middleware (DbSessionMiddleware ())
    dp .callback_query .middleware (DbSessionMiddleware ())
    dp .message .middleware (UserMiddleware ())
    dp .callback_query .middleware (UserMiddleware ())
    dp .message .middleware (BanCheckMiddleware ())
    dp .callback_query .middleware (BanCheckMiddleware ())
    logger .info ("✅ Middleware подключены")
async def on_startup ():
    logger .info ("🚀 Запуск бота...")
    error_log_path =Path ("bot_errors.log")
    error_log =None
    if error_log_path .exists ():
        try :
            with open (error_log_path ,'r',encoding ='utf-8')as f :
                error_log =f .read ()
            error_log_path .unlink ()
        except Exception as e :
            logger .error (f"Не удалось прочитать лог ошибок: {e }")
    if not await check_db_connection ():
        logger .error ("❌ Не удалось подключиться к БД. Остановка.")
        return False
    await create_tables ()
    setup_routers (dp )
    setup_middlewares (dp )
    logger .info ("✅ Бот успешно запущен!")
    try :
        config =load_config ()
        admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
        from bot .loader import SessionLocal
        async with SessionLocal ()as session :
            await admin_notifier .notify_bot_restart (error_log ,session =session )
    except Exception as e :
        logger .error (f"Не удалось отправить уведомление о запуске: {e }")
    return True
async def on_shutdown ():
    logger .info ("🛑 Остановка бота...")
    await bot .session .close ()
    await engine .dispose ()
    logger .info ("✅ Бот остановлен")
async def main ():
    try :
        if not await on_startup ():
            return
        await dp .start_polling (bot ,allowed_updates =dp .resolve_used_update_types ())
    except (KeyboardInterrupt ,SystemExit ):
        logger .info ("Получен сигнал остановки")
    except Exception as e :
        error_msg =f"Критическая ошибка: {str (e )}"
        error_details =traceback .format_exc ()
        logger .critical (error_msg ,exc_info =True )
        try :
            with open ("bot_errors.log","w",encoding ="utf-8")as f :
                f .write (f"{error_msg }\n\n{error_details }")
        except Exception :
            pass
        try :
            config =load_config ()
            admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
            await admin_notifier .notify_critical_error (error_msg ,error_details )
        except Exception as notify_error :
            logger .error (f"Не удалось отправить уведомление об ошибке: {notify_error }")
        raise
    finally :
        await on_shutdown ()
if __name__ =="__main__":
    asyncio .run (main ())
