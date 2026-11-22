from aiogram import Router ,F
from aiogram .types import Message ,CallbackQuery ,PreCheckoutQuery ,ContentType
from sqlalchemy .ext .asyncio import AsyncSession
from bot .config import load_config
from bot .loader import bot
from bot .models .user import User
from bot .repositories .route import RouteRepository
from bot .repositories .payment import PaymentRepository
from bot .services .payments import PaymentService
router =Router ()
config =load_config ()
payment_service =PaymentService (config .payment )
@router .callback_query (F .data .startswith ("pay:"))
async def process_payment (
callback :CallbackQuery ,
session :AsyncSession ,
user :User ,
):
    route_id =int (callback .data .split (":")[1 ])
    route_repo =RouteRepository (session )
    payment_repo =PaymentRepository (session )
    has_paid =await payment_repo .has_paid_for_route (user .id ,route_id )
    if has_paid :
        await callback .answer ("Вы уже оплатили этот маршрут!",show_alert =True )
        return
    route =await route_repo .get (route_id )
    if not route :
        await callback .answer ("Маршрут не найден",show_alert =True )
        return
    payment =await payment_repo .create_payment (
    user_id =user .id ,
    route_id =route_id ,
    amount =route .price ,
    )
    payload =payment_service .generate_payload (user .telegram_id ,route_id )
    invoice_params =payment_service .create_invoice (
    route_name =route .name ,
    route_description =route .description or "Интерактивный квест-экскурсия",
    price =route .price ,
    payload =payload ,
    )
    if not config .payment .provider_token :
        await callback .message .answer (
        "⚠️ Платежи временно недоступны.\n"
        "В тестовом режиме маршрут открыт бесплатно!"
        )
        await payment_repo .mark_success (payment .id ,"test","test")
        await callback .answer ("✅ Тестовый доступ открыт!")
        return
    try :
        await bot .send_invoice (
        chat_id =callback .message .chat .id ,
        **invoice_params ,
        )
        await callback .answer ()
    except Exception as e :
        await callback .answer (f"Ошибка при создании платежа: {str (e )}",show_alert =True )
@router .pre_checkout_query ()
async def process_pre_checkout_query (
pre_checkout_query :PreCheckoutQuery ,
session :AsyncSession ,
):
    await pre_checkout_query .answer (ok =True )
@router .message (F .content_type ==ContentType .SUCCESSFUL_PAYMENT )
async def process_successful_payment (
message :Message ,
session :AsyncSession ,
user :User ,
):
    payment_info =message .successful_payment
    payload_data =payment_service .parse_payload (payment_info .invoice_payload )
    route_id =payload_data ["route_id"]
    payment_repo =PaymentRepository (session )
    payments =await payment_repo .get_all ()
    payment =next (
    (
    p
    for p in payments
    if p .user_id ==user .id
    and p .route_id ==route_id
    and p .status .value =="pending"
    ),
    None ,
    )
    if payment :
        await payment_repo .mark_success (
        payment .id ,
        payment_info .telegram_payment_charge_id ,
        payment_info .provider_payment_charge_id ,
        )
    route_repo =RouteRepository (session )
    route =await route_repo .get (route_id )
    await message .answer (
    f"✅ Оплата прошла успешно!\n\n"
    f"Маршрут '{route .name }' теперь доступен.\n"
    f"Используйте /start для начала квеста!"
    )