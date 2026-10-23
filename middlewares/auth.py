from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from database.crud import (
    check_admin_by_id,
    check_and_link_admin_by_username,
    add_new_admin,
    clean_username
)
from database.models import Admin


class AdminAuthMiddleware(BaseMiddleware):
    """
    Har bir xabar va callback'da foydalanuvchi admin ekanligini xatosiz aniqlovchi
    va context data'ga 'is_admin' va 'admin_record' ni biriktiruvchi mustahkam middleware.
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
            # 1. Configdagi super admin ID tekshiruvi (.env ADMIN_IDS)
            if user.id in config.admin_id_list:
                is_admin = True
                # Bazada mavjudligini tekshiramiz va ma'lumotlarini sinxronlashtiramiz
                admin_record = await check_admin_by_id(session, user.id)
                if not admin_record:
                    admin_record = await add_new_admin(
                        session=session,
                        telegram_id=user.id,
                        username=user.username,
                        phone_number="998930406364" if user.id == 365446274 else None
                    )
                else:
                    if user.username and admin_record.username != clean_username(user.username):
                        admin_record.username = clean_username(user.username)
                        await session.commit()

            # 2. Bazadagi telegram_id bo'yicha tekshirish
            if not is_admin:
                admin_record = await check_admin_by_id(session, user.id)
                if admin_record:
                    is_admin = True
                    if user.username and not admin_record.username:
                        admin_record.username = clean_username(user.username)
                        await session.commit()

            # 3. Bazadagi username bo'yicha tekshirish (agar birinchi kirish bo'lsa ID avtomatik bog'lanadi)
            if not is_admin and user.username:
                admin_record = await check_and_link_admin_by_username(session, user.id, user.username)
                if admin_record:
                    is_admin = True

        data["is_admin"] = is_admin
        data["admin_record"] = admin_record

        return await handler(event, data)
