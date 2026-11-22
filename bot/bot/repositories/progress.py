from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy .ext .asyncio import AsyncSession
from bot .models .user_progress import UserProgress ,ProgressStatus
from bot .repositories .base import BaseRepository
class ProgressRepository (BaseRepository [UserProgress ]):
    def __init__ (self ,session :AsyncSession ):
        super ().__init__ (UserProgress ,session )
    async def get_active_progress (
    self ,
    user_id :int ,
    route_id :int ,
    )->Optional [UserProgress ]:
        result =await self .session .execute (
        select (UserProgress ).where (
        UserProgress .user_id ==user_id ,
        UserProgress .route_id ==route_id ,
        UserProgress .status ==ProgressStatus .IN_PROGRESS ,
        )
        )
        return result .scalar_one_or_none ()
    async def start_route (
    self ,
    user_id :int ,
    route_id :int ,
    first_point_id :int ,
    )->UserProgress :
        progress =await self .create (
        user_id =user_id ,
        route_id =route_id ,
        current_point_id =first_point_id ,
        current_point_order =0 ,
        status =ProgressStatus .IN_PROGRESS ,
        started_at =datetime .utcnow (),
        points_completed =0 ,
        )
        return progress
    async def complete_point (
    self ,
    progress :UserProgress ,
    next_point_id :Optional [int ]=None ,
    next_order :Optional [int ]=None ,
    )->UserProgress :
        progress .points_completed +=1
        if next_point_id :
            progress .current_point_id =next_point_id
            progress .current_point_order =next_order or (progress .current_point_order +1 )
        else :
            progress .status =ProgressStatus .COMPLETED
            progress .completed_at =datetime .utcnow ()
        await self .session .commit ()
        await self .session .refresh (progress )
        return progress
    async def get_user_stats (self ,user_id :int )->dict :
        result =await self .session .execute (
        select (UserProgress ).where (UserProgress .user_id ==user_id )
        )
        progresses =list (result .scalars ().all ())
        return {
        "total_routes":len (progresses ),
        "completed":sum (1 for p in progresses if p .status ==ProgressStatus .COMPLETED ),
        "in_progress":sum (1 for p in progresses if p .status ==ProgressStatus .IN_PROGRESS ),
        "total_points":sum (p .points_completed for p in progresses ),
        }