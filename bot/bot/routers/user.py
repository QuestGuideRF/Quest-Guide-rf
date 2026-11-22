import os
import gc
import logging
import time
from datetime import datetime
from aiogram import Router ,F
from aiogram .filters import Command ,StateFilter
from aiogram .fsm .context import FSMContext
from aiogram .types import Message ,CallbackQuery
from sqlalchemy .ext .asyncio import AsyncSession
from bot .config import load_config
from bot .fsm .states import UserStates
from bot .keyboards .user import UserKeyboards
from bot .loader import bot
from bot .models .user import User
from bot .repositories .city import CityRepository
from bot .repositories .route import RouteRepository
from bot .repositories .point import PointRepository
from bot .repositories .progress import ProgressRepository
from bot .repositories .payment import PaymentRepository
from bot .services .vision import VisionService
from bot .services .pose_movenet import PoseService
from bot .services .antifraud import AntiFraudService
from bot .services .admin_notifier import AdminNotifier
from bot .utils .helpers import download_photo ,format_duration ,format_distance
from sqlalchemy import text
logger =logging .getLogger (__name__ )
router =Router ()
config =load_config ()
@router .message (Command ("start"))
async def cmd_start (
message :Message ,
user :User ,
state :FSMContext ,
):
    await state .clear ()
    await message .answer (
    f"👋 Привет, {user .first_name }!\n\n"
    f"Я твой интерактивный экскурсовод-квест! 🎯\n\n"
    f"Вместе мы отправимся в увлекательное путешествие по городу. "
    f"Ты будешь находить локации, выполнять задания, фотографироваться — "
    f"и узнавать крутые факты и легенды!\n\n"
    f"Готов начать приключение? 🚀",
    reply_markup =UserKeyboards .main_menu (),
    )
@router .callback_query (F .data =="back_to_main")
async def back_to_main (callback :CallbackQuery ,state :FSMContext ):
    await state .clear ()
    await callback .message .edit_text (
    "🏠 Главное меню\n\nВыберите действие:",
    reply_markup =UserKeyboards .main_menu (),
    )
    await callback .answer ()
@router .callback_query (F .data =="select_city")
async def select_city (
callback :CallbackQuery ,
session :AsyncSession ,
state :FSMContext ,
):
    city_repo =CityRepository (session )
    cities =await city_repo .get_active ()
    if not cities :
        await callback .answer ("😔 Пока нет доступных городов",show_alert =True )
        return
    await state .set_state (UserStates .selecting_city )
    await callback .message .edit_text (
    "🏙️ Выберите город:",
    reply_markup =UserKeyboards .city_list (cities ),
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("city:"))
async def city_selected (
callback :CallbackQuery ,
session :AsyncSession ,
state :FSMContext ,
):
    city_id =int (callback .data .split (":")[1 ])
    route_repo =RouteRepository (session )
    routes =await route_repo .get_by_city (city_id ,active_only =True )
    if not routes :
        await callback .answer ("😔 В этом городе пока нет маршрутов",show_alert =True )
        return
    await state .update_data (city_id =city_id )
    await state .set_state (UserStates .selecting_route )
    await callback .message .edit_text (
    "🗺️ Выберите маршрут:",
    reply_markup =UserKeyboards .route_list (routes ),
    )
    await callback .answer ()
@router .callback_query (F .data =="back_to_routes")
async def back_to_routes (
callback :CallbackQuery ,
session :AsyncSession ,
state :FSMContext ,
):
    data =await state .get_data ()
    city_id =data .get ("city_id")
    if not city_id :
        await select_city (callback ,session ,state )
        return
    route_repo =RouteRepository (session )
    routes =await route_repo .get_by_city (city_id ,active_only =True )
    await state .set_state (UserStates .selecting_route )
    await callback .message .edit_text (
    "🗺️ Выберите маршрут:",
    reply_markup =UserKeyboards .route_list (routes ),
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("route:"))
async def route_selected (
callback :CallbackQuery ,
session :AsyncSession ,
user :User ,
state :FSMContext ,
):
    route_id =int (callback .data .split (":")[1 ])
    route_repo =RouteRepository (session )
    payment_repo =PaymentRepository (session )
    route =await route_repo .get_with_points (route_id )
    if not route :
        await callback .answer ("Маршрут не найден",show_alert =True )
        return
    has_paid =await payment_repo .has_paid_for_route (user .id ,route_id )
    description =f"📍 {route .name }\n\n"
    if route .description :
        description +=f"{route .description }\n\n"
    description +=f"📊 Информация:\n"
    description +=f"• Точек: {len (route .points )}\n"
    if route .estimated_duration :
        description +=f"• Время: ~{format_duration (route .estimated_duration )}\n"
    if route .distance :
        description +=f"• Расстояние: {format_distance (route .distance )}\n"
    description +=f"• Цена: {route .price }₽\n"
    if has_paid :
        description +="\n✅ Маршрут оплачен! Можете начинать квест."
    else :
        description +="\n💳 Для начала квеста необходимо оплатить маршрут."
    await state .update_data (route_id =route_id )
    await callback .message .edit_text (
    description ,
    reply_markup =UserKeyboards .route_detail (route_id ,has_paid ),
    )
    await callback .answer ()
@router .callback_query (F .data .startswith ("start_quest:"))
async def start_quest (
callback :CallbackQuery ,
session :AsyncSession ,
user :User ,
state :FSMContext ,
):
    route_id =int (callback .data .split (":")[1 ])
    route_repo =RouteRepository (session )
    point_repo =PointRepository (session )
    progress_repo =ProgressRepository (session )
    progress =await progress_repo .get_active_progress (user .id ,route_id )
    if not progress :
        route =await route_repo .get_with_points (route_id )
        if not route or not route .points :
            await callback .answer ("Маршрут пуст",show_alert =True )
            return
        first_point =route .points [0 ]
        progress =await progress_repo .start_route (
        user_id =user .id ,
        route_id =route_id ,
        first_point_id =first_point .id ,
        )
    current_point =await point_repo .get_with_images (progress .current_point_id )
    await state .set_state (UserStates .in_quest )
    await state .update_data (
    route_id =route_id ,
    progress_id =progress .id ,
    point_id =current_point .id ,
    )
    task_text =f"📍 Точка {progress .current_point_order +1 }\n\n"
    task_text +=f"📝 Задание:\n{current_point .task_text }\n\n"
    if current_point .require_pose :
        pose_names ={
        "hands_up":"руки вверх",
        "heart":"сердечко руками",
        "point":"указать пальцем",
        }
        task_text +=f"🤸 Поза: {pose_names .get (current_point .require_pose ,current_point .require_pose )}\n"
    if current_point .min_people >1 :
        task_text +=f"👥 Людей на фото: минимум {current_point .min_people }\n"
    task_text +="\n📸 Отправьте фото, когда будете на месте!"
    await callback .message .edit_text (
    task_text ,
    reply_markup =UserKeyboards .quest_menu (route_id ),
    )
    await callback .answer ()
@router .message (StateFilter (UserStates .in_quest ),F .photo )
async def process_quest_photo (
message :Message ,
session :AsyncSession ,
user :User ,
state :FSMContext ,
):
    start_time =time .time ()
    logger .info (f"[USER {user .telegram_id }] Получено фото, начинаем обработку")
    data =await state .get_data ()
    route_id =data .get ("route_id")
    point_id =data .get ("point_id")
    status_msg =await message .answer ("📸 Фото получено! Начинаю проверку...")
    logger .info (f"[USER {user .telegram_id }] Отправлено подтверждение получения фото")
    point_repo =PointRepository (session )
    progress_repo =ProgressRepository (session )
    photo =message .photo [-1 ]
    try :
        logger .info (f"[USER {user .telegram_id }] Скачиваю фото...")
        await status_msg .edit_text ("📸 Фото получено! Скачиваю...")
        photo_path =await download_photo (bot ,photo )
        logger .info (f"[USER {user .telegram_id }] Фото скачано: {photo_path }, время: {time .time ()-start_time :.2f}с")
        logger .info (f"[USER {user .telegram_id }] Загружаю данные точки...")
        await status_msg .edit_text ("📸 Фото получено! Загружаю данные...")
        point =await point_repo .get_with_images (point_id )
        progress =await progress_repo .get (data .get ("progress_id"))
        logger .info (f"[USER {user .telegram_id }] Данные загружены, время: {time .time ()-start_time :.2f}с")
        logger .info (f"[USER {user .telegram_id }] [ШАГ 1/4] Проверяю на фрод...")
        await status_msg .edit_text ("🔍 Проверяю фото... (1/4 - Антифрод)")
        antifraud_service =AntiFraudService ()
        fraud_ok ,fraud_messages =await antifraud_service .perform_all_checks (
        photo_path ,user .telegram_id ,route_id ,progress .current_point_order
        )
        del antifraud_service
        gc .collect ()
        logger .info (f"[USER {user .telegram_id }] Антифрод: {fraud_ok }, время: {time .time ()-start_time :.2f}с")
        if not fraud_ok :
            admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
            await admin_notifier .notify_photo_verification_needed (
            photo_path =photo_path ,
            user_id =user .telegram_id ,
            username =user .username ,
            point_name =point .name ,
            point_id =point_id ,
            progress_id =progress .id ,
            photo_file_id =photo .file_id ,
            route_name =data .get ("route_name","Неизвестный маршрут"),
            error_reason =fraud_messages [-1 ]
            )
            await status_msg .edit_text (f"❌ {fraud_messages [-1 ]}\n\n⏳ Фото отправлено на проверку администратору.")
            return
        if point .min_people >1 :
            logger .info (f"[USER {user .telegram_id }] [ШАГ 2/4] Проверяю количество людей (min {point .min_people })...")
            await status_msg .edit_text ("🔍 Проверяю фото... (2/4 - Подсчёт людей)")
            try :
                import cv2
                img =cv2 .imread (photo_path )
                h ,w =img .shape [:2 ]
                img_area =h *w
                max_size =640
                if max (h ,w )>max_size :
                    scale =max_size /max (h ,w )
                    img =cv2 .resize (img ,(int (w *scale ),int (h *scale )),interpolation =cv2 .INTER_AREA )
                gray =cv2 .cvtColor (img ,cv2 .COLOR_BGR2GRAY )
                face_cascade =cv2 .CascadeClassifier (cv2 .data .haarcascades +'haarcascade_frontalface_default.xml')
                faces =face_cascade .detectMultiScale (
                gray ,
                scaleFactor =1.2 ,
                minNeighbors =8 ,
                minSize =(100 ,100 ),
                maxSize =(400 ,400 )
                )
                valid_faces =[]
                for (x ,y ,w ,h )in faces :
                    face_area =w *h
                    face_ratio =face_area /img_area
                    if 0.02 <=face_ratio <=0.50 :
                        valid_faces .append ((x ,y ,w ,h ))
                        logger .debug (f"[USER {user .telegram_id }] Лицо {len (valid_faces )}: размер {w }x{h }, площадь {face_ratio :.2%}")
                people_count =len (valid_faces )
                del img ,gray ,face_cascade
                gc .collect ()
                logger .info (f"[USER {user .telegram_id }] Обнаружено людей: {people_count } (всего лиц: {len (faces )}), требуется: {point .min_people }, время: {time .time ()-start_time :.2f}с")
                if people_count <point .min_people :
                    admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
                    await admin_notifier .notify_photo_verification_needed (
                    photo_path =photo_path ,
                    user_id =user .telegram_id ,
                    username =user .username ,
                    point_name =point .name ,
                    point_id =point_id ,
                    progress_id =progress .id ,
                    photo_file_id =photo .file_id ,
                    route_name =data .get ("route_name","Неизвестный маршрут"),
                    error_reason =f"На фото {people_count } человек(а), нужно минимум {point .min_people }",
                    people_count =people_count
                    )
                    await status_msg .edit_text (f"❌ На фото {people_count } человек(а), нужно минимум {point .min_people }\n\n⏳ Фото отправлено на проверку администратору.")
                    return
            except Exception as e :
                logger .error (f"[USER {user .telegram_id }] Ошибка при проверке количества людей: {e }",exc_info =True )
                admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
                await admin_notifier .notify_photo_verification_needed (
                photo_path =photo_path ,
                user_id =user .telegram_id ,
                username =user .username ,
                point_name =point .name ,
                point_id =point_id ,
                progress_id =progress .id ,
                photo_file_id =photo .file_id ,
                route_name =data .get ("route_name","Неизвестный маршрут"),
                error_reason =f"Ошибка проверки количества людей: {str (e )}",
                people_count =None
                )
                await status_msg .edit_text (f"❌ Ошибка проверки. Фото отправлено на проверку администратору.")
                return
        if point .require_pose :
            logger .info (f"[USER {user .telegram_id }] [ШАГ 3/4] Проверяю позу {point .require_pose }...")
            await status_msg .edit_text ("🔍 Проверяю фото... (3/4 - Анализ позы 🧘)")
            pose_service =None
            try :
                pose_service =PoseService (config .vision )
                pose_ok ,pose_msg =await pose_service .check_pose (
                photo_path ,point .require_pose
                )
                logger .info (f"[USER {user .telegram_id }] Поза: {pose_ok }, время: {time .time ()-start_time :.2f}с")
                if not pose_ok :
                    admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
                    await admin_notifier .notify_photo_verification_needed (
                    photo_path =photo_path ,
                    user_id =user .telegram_id ,
                    username =user .username ,
                    point_name =point .name ,
                    point_id =point_id ,
                    progress_id =progress .id ,
                    photo_file_id =photo .file_id ,
                    route_name =data .get ("route_name","Неизвестный маршрут"),
                    error_reason =pose_msg ,
                    pose_required =point .require_pose
                    )
                    await status_msg .edit_text (f"❌ {pose_msg }\n\n⏳ Фото отправлено на проверку администратору.")
                    return
            finally :
                if pose_service :
                    del pose_service
                gc .collect ()
                logger .info (f"[USER {user .telegram_id }] PoseService освобождён")
        if point .reference_images :
            reference_paths =[
            ref .file_path for ref in point .reference_images if ref .file_path
            ]
            if reference_paths :
                logger .info (f"[USER {user .telegram_id }] [ШАГ 4/4] Проверяю локацию (ref images: {len (reference_paths )})...")
                await status_msg .edit_text ("🔍 Проверяю фото... (4/4 - Проверка места 📍)")
                vision_service =None
                try :
                    vision_service =VisionService (config .vision )
                    location_ok ,score =await vision_service .check_location (
                    photo_path ,reference_paths
                    )
                    logger .info (f"[USER {user .telegram_id }] Локация: {location_ok }, score: {score :.2%}, время: {time .time ()-start_time :.2f}с")
                    if not location_ok :
                        admin_notifier =AdminNotifier (bot ,config .bot .admin_ids )
                        await admin_notifier .notify_photo_verification_needed (
                        photo_path =photo_path ,
                        user_id =user .telegram_id ,
                        username =user .username ,
                        point_name =point .name ,
                        point_id =point_id ,
                        progress_id =progress .id ,
                        photo_file_id =photo .file_id ,
                        route_name =data .get ("route_name","Неизвестный маршрут"),
                        error_reason =f"Похоже, это не та локация (уверенность: {score :.1%})",
                        location_match =score *100
                        )
                        await status_msg .edit_text (
                        f"❌ Похоже, это не та локация (уверенность: {score :.1%})\n"
                        f"Попробуйте сделать фото ближе к объекту!\n\n"
                        f"⏳ Фото отправлено на проверку администратору."
                        )
                        return
                finally :
                    if vision_service :
                        del vision_service
                    gc .collect ()
                    logger .info (f"[USER {user .telegram_id }] VisionService освобождён")
        total_time =time .time ()-start_time
        logger .info (f"[USER {user .telegram_id }] ✅ Все проверки пройдены! Общее время: {total_time :.2f}с")
        try :
            import shutil
            from pathlib import Path
            user_photos_dir =Path ("../../photos")/str (user .telegram_id )
            user_photos_dir .mkdir (parents =True ,exist_ok =True )
            timestamp =datetime .utcnow ().strftime ('%Y%m%d_%H%M%S')
            file_extension =photo_path .split ('.')[-1 ]
            filename =f"point_{point_id }_{timestamp }.{file_extension }"
            permanent_path =user_photos_dir /filename
            shutil .copy2 (photo_path ,permanent_path )
            relative_path =f"/photos/{user .telegram_id }/{filename }"
            from sqlalchemy import text
            await session .execute (
            text (
            "INSERT INTO user_photos (user_id, point_id, file_id, file_path, file_hash) "
            "VALUES (:user_id, :point_id, :file_id, :file_path, :file_hash)"
            ),
            {
            "user_id":user .id ,
            "point_id":point_id ,
            "file_id":photo .file_id ,
            "file_path":relative_path ,
            "file_hash":None ,
            }
            )
            await session .commit ()
            logger .info (f"[USER {user .telegram_id }] Фото сохранено: {relative_path }")
        except Exception as e :
            logger .error (f"[USER {user .telegram_id }] Ошибка при сохранении фото: {e }",exc_info =True )
        await status_msg .edit_text ("✅ Отлично! Точка засчитана!")
        if point .fact_text :
            await message .answer (
            f"💡 Интересный факт:\n\n{point .fact_text }"
            )
        next_point =await point_repo .get_next_point (route_id ,progress .current_point_order )
        if next_point :
            await progress_repo .complete_point (
            progress ,next_point .id ,next_point .order
            )
            task_text =f"📍 Точка {next_point .order +1 }\n\n"
            task_text +=f"📝 Задание:\n{next_point .task_text }\n\n"
            if next_point .require_pose :
                pose_names ={
                "hands_up":"руки вверх",
                "heart":"сердечко руками",
                "point":"указать пальцем",
                }
                task_text +=f"🤸 Поза: {pose_names .get (next_point .require_pose ,next_point .require_pose )}\n"
            if next_point .min_people >1 :
                task_text +=f"👥 Людей на фото: минимум {next_point .min_people }\n"
            task_text +="\n📸 Отправьте фото, когда будете на месте!"
            await state .update_data (point_id =next_point .id )
            await message .answer (
            task_text ,
            reply_markup =UserKeyboards .quest_menu (route_id ),
            )
        else :
            await progress_repo .complete_point (progress ,None ,None )
            completion_time =datetime .utcnow ()-progress .started_at
            minutes =int (completion_time .total_seconds ()/60 )
            await message .answer (
            f"🎉 Поздравляем! Квест завершен!\n\n"
            f"📊 Статистика:\n"
            f"• Пройдено точек: {progress .points_completed }\n"
            f"• Время: {format_duration (minutes )}\n\n"
            f"Спасибо за участие! Надеемся, вам понравилось! 🌟",
            reply_markup =UserKeyboards .quest_completed (),
            )
            await state .clear ()
    except Exception as e :
        logger .error (f"[USER {user .telegram_id }] ❌ ОШИБКА при обработке фото: {type (e ).__name__ }: {str (e )}",exc_info =True )
        try :
            await status_msg .edit_text (
            f"❌ Произошла ошибка при обработке фото.\n"
            f"Попробуйте еще раз или обратитесь в поддержку.\n\n"
            f"Код ошибки: {type (e ).__name__ }"
            )
        except :
            await message .answer (
            f"❌ Произошла ошибка при обработке фото.\n"
            f"Попробуйте еще раз или обратитесь в поддержку."
            )
    finally :
        try :
            if 'photo_path'in locals ()and os .path .exists (photo_path ):
                os .remove (photo_path )
                logger .info (f"[USER {user .telegram_id }] Временное фото удалено")
        except Exception as e :
            logger .error (f"[USER {user .telegram_id }] Ошибка при удалении фото: {e }")
@router .callback_query (F .data .startswith ("cancel_quest:"))
async def cancel_quest (
callback :CallbackQuery ,
session :AsyncSession ,
user :User ,
state :FSMContext ,
):
    await state .clear ()
    await callback .message .edit_text (
    "❌ Квест прерван.\n\nВы можете начать заново в любой момент.",
    reply_markup =UserKeyboards .main_menu (),
    )
    await callback .answer ()
@router .callback_query (F .data =="my_stats")
async def my_stats (
callback :CallbackQuery ,
session :AsyncSession ,
user :User ,
):
    progress_repo =ProgressRepository (session )
    stats =await progress_repo .get_user_stats (user .id )
    text ="📊 Ваша статистика:\n\n"
    text +=f"• Всего маршрутов: {stats ['total_routes']}\n"
    text +=f"• Завершено: {stats ['completed']}\n"
    text +=f"• В процессе: {stats ['in_progress']}\n"
    text +=f"• Пройдено точек: {stats ['total_points']}\n"
    await callback .message .edit_text (
    text ,
    reply_markup =UserKeyboards .main_menu (),
    )
    await callback .answer ()
@router .callback_query (F .data =="about")
async def about (callback :CallbackQuery ):
    text =(
    "ℹ️ О боте\n\n"
    "Я — интерактивный экскурсовод-квест! 🎯\n\n"
    "Как это работает:\n"
    "1️⃣ Выбираешь город и маршрут\n"
    "2️⃣ Оплачиваешь (399₽)\n"
    "3️⃣ Получаешь задание найти локацию\n"
    "4️⃣ Доходишь до места\n"
    "5️⃣ Фотографируешься (иногда с условиями)\n"
    "6️⃣ Узнаешь крутой факт\n"
    "7️⃣ Переходишь к следующей точке\n\n"
    "Путешествуй в своем темпе, без скучных экскурсий! 🚀"
    )
    await callback .message .edit_text (
    text ,
    reply_markup =UserKeyboards .main_menu (),
    )
    await callback .answer ()
