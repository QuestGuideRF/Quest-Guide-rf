from dataclasses import dataclass
from os import getenv
from pathlib import Path
from typing import Optional ,List
from dotenv import load_dotenv
env_path =Path (__file__ ).resolve ().parents [2 ]/'.env'
load_dotenv (dotenv_path =env_path )
@dataclass
class DatabaseConfig :
    host :str
    port :int
    user :str
    password :str
    database :str
    @property
    def url (self )->str :
        return f"mysql+aiomysql://{self .user }:{self .password }@{self .host }:{self .port }/{self .database }?charset=utf8mb4"
@dataclass
class BotConfig :
    token :str
    admin_ids :List [int ]
    moderator_ids :List [int ]
@dataclass
class PaymentConfig :
    provider_token :str
    default_price :int =399
@dataclass
class VisionConfig :
    google_credentials_path :Optional [str ]=None
    similarity_threshold :float =0.75
    pose_confidence :float =0.5
@dataclass
class WebConfig :
    site_url :str
    api_secret :str
@dataclass
class Config :
    bot :BotConfig
    db :DatabaseConfig
    payment :PaymentConfig
    vision :VisionConfig
    web :WebConfig
def load_config ()->Config :
    admin_ids_str =getenv ("ADMIN_IDS","")
    admin_ids =[int (x .strip ())for x in admin_ids_str .split (",")if x .strip ()]
    moderator_ids_str =getenv ("MODERATOR_IDS","")
    moderator_ids =[int (x .strip ())for x in moderator_ids_str .split (",")if x .strip ()]
    return Config (
    bot =BotConfig (
    token =getenv ("BOT_TOKEN",""),
    admin_ids =admin_ids ,
    moderator_ids =moderator_ids ,
    ),
    db =DatabaseConfig (
    host =getenv ("DB_HOST","localhost"),
    port =int (getenv ("DB_PORT","3306")),
    user =getenv ("DB_USER","root"),
    password =getenv ("DB_PASSWORD")or getenv ("DB_PASS",""),
    database =getenv ("DB_NAME","u3372144_schema"),
    ),
    payment =PaymentConfig (
    provider_token =getenv ("PAYMENT_PROVIDER_TOKEN",""),
    default_price =int (getenv ("DEFAULT_PRICE","399")),
    ),
    vision =VisionConfig (
    google_credentials_path =getenv ("GOOGLE_CREDENTIALS_PATH")or getenv ("GOOGLE_APPLICATION_CREDENTIALS"),
    similarity_threshold =float (getenv ("SIMILARITY_THRESHOLD","0.75")),
    pose_confidence =float (getenv ("POSE_CONFIDENCE","0.5")),
    ),
    web =WebConfig (
    site_url =getenv ("SITE_URL","https://questguiderf.ru"),
    api_secret =getenv ("API_SECRET")or getenv ("AUTH_SECRET",""),
    ),
    )
