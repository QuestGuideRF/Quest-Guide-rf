from enum import Enum
from sqlalchemy import BigInteger ,String ,Enum as SQLEnum
from sqlalchemy .orm import Mapped ,mapped_column ,relationship
from typing import List ,Optional
from bot .models .base import Base ,TimestampMixin
class UserRole (str ,Enum ):
    USER ="user"
    MODERATOR ="moderator"
    ADMIN ="admin"
class User (Base ,TimestampMixin ):
    __tablename__ ="users"
    id :Mapped [int ]=mapped_column (BigInteger ,primary_key =True )
    telegram_id :Mapped [int ]=mapped_column (BigInteger ,unique =True ,index =True )
    username :Mapped [Optional [str ]]=mapped_column (String (255 ),nullable =True )
    first_name :Mapped [Optional [str ]]=mapped_column (String (255 ),nullable =True )
    last_name :Mapped [Optional [str ]]=mapped_column (String (255 ),nullable =True )
    role :Mapped [UserRole ]=mapped_column (
    SQLEnum (UserRole ,native_enum =False ),
    default =UserRole .USER ,
    server_default =UserRole .USER .value ,
    )
    progresses :Mapped [List ["UserProgress"]]=relationship (
    "UserProgress",
    back_populates ="user",
    cascade ="all, delete-orphan",
    )
    payments :Mapped [List ["Payment"]]=relationship (
    "Payment",
    back_populates ="user",
    cascade ="all, delete-orphan",
    )
