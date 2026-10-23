from handlers.user import router as user_router
from handlers.admin_panel import router as admin_panel_router
from handlers.admin_books import router as admin_books_router
from handlers.admin_manage import router as admin_manage_router
from handlers.admin_broadcast import router as admin_broadcast_router

__all__ = [
    "user_router",
    "admin_panel_router",
    "admin_books_router",
    "admin_manage_router",
    "admin_broadcast_router"
]
