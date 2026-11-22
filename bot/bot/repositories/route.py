from typing import List ,Optional
from sqlalchemy import select
from typing import List ,Optional
from sqlalchemy .ext .asyncio import AsyncSession
from typing import List ,Optional
from sqlalchemy .orm import selectinload
from bot .models .route import Route
from bot .repositories .base import BaseRepository
class RouteRepository (BaseRepository [Route ]):
    def __init__ (self ,session :AsyncSession ):
        super ().__init__ (Route ,session )
    async def get_with_points (self ,route_id :int )->Optional [Route ]:
        result =await self .session .execute (
        select (Route )
        .options (selectinload (Route .points ))
        .where (Route .id ==route_id )
        )
        return result .scalar_one_or_none ()
    async def get_by_city (self ,city_id :int ,active_only :bool =True )->List [Route ]:
        query =select (Route ).where (Route .city_id ==city_id )
        if active_only :
            query =query .where (Route .is_active ==True )
        query =query .order_by (Route .order )
        result =await self .session .execute (query )
        return list (result .scalars ().all ())
    async def get_active (self )->List [Route ]:
        result =await self .session .execute (
        select (Route ).where (Route .is_active ==True ).order_by (Route .order )
        )
        return list (result .scalars ().all ())