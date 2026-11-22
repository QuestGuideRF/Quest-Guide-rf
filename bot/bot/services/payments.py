from aiogram .types import LabeledPrice
from bot .config import PaymentConfig
class PaymentService :
    def __init__ (self ,config :PaymentConfig ):
        self .config =config
    def create_invoice (
    self ,
    route_name :str ,
    route_description :str ,
    price :int ,
    payload :str ,
    )->dict :
        return {
        "title":route_name ,
        "description":route_description ,
        "payload":payload ,
        "provider_token":self .config .provider_token ,
        "currency":"RUB",
        "prices":[
        LabeledPrice (label =route_name ,amount =price *100 ),
        ],
        }
    def generate_payload (self ,user_id :int ,route_id :int )->str :
        return f"route:{route_id }:user:{user_id }"
    def parse_payload (self ,payload :str )->dict :
        parts =payload .split (":")
        return {
        "route_id":int (parts [1 ]),
        "user_id":int (parts [3 ]),
        }