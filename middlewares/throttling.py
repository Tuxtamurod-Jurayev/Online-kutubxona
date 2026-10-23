import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import config


class ThrottlingMiddleware(BaseMiddleware):
    """
    Foydalanuvchilar tomonidan botga tez-tez so'rov yuborishdan
    himoya qiluvchi (Rate Limiting / Anti-flood) middleware.
    """

    def __init__(self, limit: float = config.RATE_LIMIT):
        self.limit = limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            current_time = time.time()
            last_time = self.user_timestamps.get(user_id, 0)

            if current_time - last_time < self.limit:
                # Agar limit buzilgan bo'lsa
                if isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Iltimos, biroz kuting...", show_alert=False)
                elif isinstance(event, Message):
                    # Xabar yuborilmaydi yoki ogohlantirish beriladi
                    pass
                return None

            self.user_timestamps[user_id] = current_time

            # Xotirani tozalab turish (1000 tadan oshganda eski yozuvlar tozalanadi)
            if len(self.user_timestamps) > 1000:
                expired = [uid for uid, t in self.user_timestamps.items() if current_time - t > 60]
                for uid in expired:
                    del self.user_timestamps[uid]

        return await handler(event, data)
