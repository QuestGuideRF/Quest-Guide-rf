import asyncio
from sqlalchemy .ext .asyncio import create_async_engine ,async_sessionmaker
from bot .config import load_config
from bot .models import Base ,City ,Route ,Point ,RouteType
async def init_test_data ():
    config =load_config ()
    engine =create_async_engine (config .db .url ,echo =True )
    async with engine .begin ()as conn :
        await conn .run_sync (Base .metadata .create_all )
    SessionLocal =async_sessionmaker (engine ,expire_on_commit =False )
    async with SessionLocal ()as session :
        moscow =City (
        name ="Москва",
        description ="Столица России с богатой историей",
        is_active =True ,
        )
        session .add (moscow )
        await session .flush ()
        route =Route (
        city_id =moscow .id ,
        name ="Исторический центр",
        description ="Квест по главным достопримечательностям Москвы",
        route_type =RouteType .WALKING ,
        price =399 ,
        estimated_duration =120 ,
        distance =3.5 ,
        is_active =True ,
        order =1 ,
        )
        session .add (route )
        await session .flush ()
        point1 =Point (
        route_id =route .id ,
        order =0 ,
        name ="Красная площадь",
        address ="Красная площадь, Москва",
        task_text =(
        "Найдите главную площадь страны! 🏛️\n\n"
        "Подсказка: Здесь находятся Кремль, ГУМ и храм Василия Блаженного.\n"
        "Сделайте фото на фоне Спасской башни с поднятыми руками!"
        ),
        fact_text =(
        "Красная площадь появилась в конце XV века. Вопреки распространённому мнению, "
        "название «Красная» означает не цвет, а «красивая». "
        "Площадь стала «красной» задолго до революции 1917 года! 🏰"
        ),
        require_pose ="hands_up",
        min_people =1 ,
        is_free =True ,
        )
        session .add (point1 )
        point2 =Point (
        route_id =route .id ,
        order =1 ,
        name ="Храм Василия Блаженного",
        address ="Красная площадь, 2, Москва",
        task_text =(
        "Найдите самый узнаваемый храм России! 🕌\n\n"
        "Его разноцветные купола не спутаешь ни с чем.\n"
        "Сфоткайтесь, указывая на купола пальцем!"
        ),
        fact_text =(
        "По легенде, Иван Грозный приказал ослепить архитектора, "
        "чтобы тот не смог построить ничего прекраснее. "
        "На самом деле, это миф — архитектор Постник Яковлев позже строил другие храмы! 👁️"
        ),
        require_pose ="point",
        min_people =1 ,
        )
        session .add (point2 )
        point3 =Point (
        route_id =route .id ,
        order =2 ,
        name ="ГУМ",
        address ="Красная площадь, 3, Москва",
        task_text =(
        "Зайдите в знаменитый универмаг напротив Кремля! 🏬\n\n"
        "Найдите главный вход и сделайте фото с друзьями, "
        "сложив руки сердечком! ❤️"
        ),
        fact_text =(
        "ГУМ — это аббревиатура от «Главный Универсальный Магазин». "
        "Здание построено в 1893 году и является памятником архитектуры. "
        "Внутри всегда работают знаменитые фонтаны, а зимой заливают каток! ⛸️"
        ),
        require_pose ="heart",
        min_people =2 ,
        )
        session .add (point3 )
        await session .commit ()
        print ("✅ Тестовые данные созданы!")
if __name__ =="__main__":
    asyncio .run (init_test_data ())