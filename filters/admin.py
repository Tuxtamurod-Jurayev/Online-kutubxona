from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union


class IsAdmin(Filter):
    """Foydalanuvchi admin ekanligini tekshiruvchi aiogram filtri"""

    async def __call__(self, event: Union[Message, CallbackQuery], is_admin: bool = False) -> bool:
        return is_admin
