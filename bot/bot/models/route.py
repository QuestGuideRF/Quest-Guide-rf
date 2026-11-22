from enum import Enum
from sqlalchemy import String ,Integer ,Boolean ,ForeignKey ,Text ,Enum as SQLEnum
from sqlalchemy .orm import Mapped ,mapped_column ,relationship
from typing import List ,Optional
from bot .models .base import Base ,TimestampMixin
class RouteType (str ,Enum ):
    WALKING ="walking"
    CYCLING ="cycling"
class Route (Base ,TimestampMixin ):
    __tablename__ ="routes"
    id :Mapped [int ]=mapped_column (primary_key =True )
    city_id :Mapped [int ]=mapped_column (ForeignKey ("cities.id",ondelete ="CASCADE"))
    name :Mapped [str ]=mapped_column (String (255 ),index =True )
    description :Mapped [Optional [str ]]=mapped_column (Text ,nullable =True )
    route_type :Mapped [RouteType ]=mapped_column (
    SQLEnum (RouteType ,native_enum =False ),
    default =RouteType .WALKING ,
    )
    price :Mapped [int ]=mapped_column (Integer ,default =399 )
    estimated_duration :Mapped [Optional [int ]]=mapped_column (Integer ,nullable =True )
    distance :Mapped [Optional [float ]]=mapped_column (nullable =True )
    is_active :Mapped [bool ]=mapped_column (Boolean ,default =True )
    order :Mapped [int ]=mapped_column (Integer ,default =0 )
    city :Mapped ["City"]=relationship ("City",back_populates ="routes")
    points :Mapped [List ["Point"]]=relationship (
    "Point",
    back_populates ="route",
    cascade ="all, delete-orphan",
    order_by ="Point.order",
    )
    progresses :Mapped [List ["UserProgress"]]=relationship (
    "UserProgress",
    back_populates ="route",
    cascade ="all, delete-orphan",
    )
