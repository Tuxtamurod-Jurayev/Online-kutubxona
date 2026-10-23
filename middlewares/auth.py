from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from database.crud import check_admin_by_id, check_and_link_admin_by_username
from database.models import Admin


class AdminAuthMiddleware(BaseMiddleware):
    """
    Har bir xabar va callback da foydalanuvchi admin ekanligini tekshiruvchi
    va context data'ga 'is_admin' va 'admin_user' ni biriktiruvchi middleware.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = data.get("session")
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        is_admin = False
        admin_record: Admin | None = None

        if user and session:
            # 1. Configdagi super admin ID tekshiruvi (.env)
            if user.id in config.admin_id_list:
                is_admin = True

            # 2. Bazadagi telegram_id bo'yicha tekshirish
            if not is_admin:
                admin_record = await check_admin_by_id(session, user.id)
                if admin_record:
                    is_admin = True

            # 3. Bazadagi username bo'yicha tekshirish (agar birinchi marta kirayotgan bo'lsa, ID ni avtomatik bog'lash)
            if not is_admin and user.username:
                admin_record = await check_and_link_admin_by_username(session, user.id, user.username)
                if admin_record:
                    is_admin = True

        data["is_admin"] = is_admin
        data["admin_record"] = admin_record

        return await handler(event, data)
