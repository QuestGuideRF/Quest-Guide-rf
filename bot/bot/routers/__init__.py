from bot .routers .user import router as user_router
from bot .routers .admin import router as admin_router
from bot .routers .payments import router as payment_router
from bot .routers .web_auth import router as web_auth_router
__all__ =["admin_router","user_router","payment_router","web_auth_router"]