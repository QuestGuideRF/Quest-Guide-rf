from sqlalchemy import String ,Boolean
from sqlalchemy .orm import Mapped ,mapped_column ,relationship
from typing import List ,Optional
from bot .models .base import Base ,TimestampMixin
class City (Base ,TimestampMixin ):
    __tablename__ ="cities"
    id :Mapped [int ]=mapped_column (primary_key =True )
    name :Mapped [str ]=mapped_column (String (255 ),unique =True ,index =True )
    description :Mapped [Optional [str ]]=mapped_column (String (1000 ),nullable =True )
    is_active :Mapped [bool ]=mapped_column (Boolean ,default =True )
    routes :Mapped [List ["Route"]]=relationship (
    "Route",
    back_populates ="city",
    cascade ="all, delete-orphan",
    )
