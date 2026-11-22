from sqlalchemy import String ,Integer ,ForeignKey ,Text ,Boolean ,Float
from sqlalchemy .orm import Mapped ,mapped_column ,relationship
from typing import List ,Optional
from bot .models .base import Base ,TimestampMixin
class Point (Base ,TimestampMixin ):
    __tablename__ ="points"
    id :Mapped [int ]=mapped_column (primary_key =True )
    route_id :Mapped [int ]=mapped_column (ForeignKey ("routes.id",ondelete ="CASCADE"))
    order :Mapped [int ]=mapped_column (Integer ,index =True )
    name :Mapped [str ]=mapped_column (String (255 ))
    address :Mapped [Optional [str ]]=mapped_column (String (500 ),nullable =True )
    task_text :Mapped [str ]=mapped_column (Text )
    fact_text :Mapped [Optional [str ]]=mapped_column (Text ,nullable =True )
    require_pose :Mapped [Optional [str ]]=mapped_column (String (100 ),nullable =True )
    min_people :Mapped [int ]=mapped_column (Integer ,default =1 )
    latitude :Mapped [Optional [float ]]=mapped_column (Float ,nullable =True )
    longitude :Mapped [Optional [float ]]=mapped_column (Float ,nullable =True )
    is_free :Mapped [bool ]=mapped_column (Boolean ,default =False )
    route :Mapped ["Route"]=relationship ("Route",back_populates ="points")
    reference_images :Mapped [List ["ReferenceImage"]]=relationship (
    "ReferenceImage",
    back_populates ="point",
    cascade ="all, delete-orphan",
    )
