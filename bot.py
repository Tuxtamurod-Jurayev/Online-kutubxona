import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault, ErrorEvent
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.base import init_db, close_db
from middlewares.db import DbSessionMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.auth import AdminAuthMiddleware
from handlers import (
    admin_panel_router,
    admin_books_router,
    admin_manage_router,
    admin_broadcast_router,
    user_router
)

logger = logging.getLogger("online_kutubxona_bot")


async def setup_bot_commands(bot: Bot) -> None:
    """Telegram ilovasida pastki chap burchakdagi [Menu] tugmasi buyruqlarini o'rnatish"""
    commands = [
        BotCommand(command="start", description="📚 Bosh menyu va qidiruv"),
        BotCommand(command="search", description="🔍 Kitob qidirish"),
        BotCommand(command="top", description="🔥 Eng ko'p o'qilgan kitoblar"),
        BotCommand(command="admin", description="⚡️ Administrator paneli"),
        BotCommand(command="help", description="ℹ️ Qo'llanma va yordam"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Bot buyruqlari menyusi ([Menu]) muvaffaqiyatli o'rnatildi.")
    except Exception as e:
        logger.warning(f"Bot buyruqlarini o'rnatishda ogohlantirish: {e}")


async def global_error_handler(event: ErrorEvent) -> bool:
    """Kutilmagan xatoliklarni xavfsiz ushlab qoluvchi global handler"""
    logger.error(f"Kutilmagan xatolik yuz berdi: {event.exception}", exc_info=True)
    try:
        if event.update.message:
            await event.update.message.answer(
                "⚠️ <b>Texnik nosozlik yuz berdi.</b>\n"
                "Iltimos, birozdan so'ng qayta urinib ko'ring yoki /start bosing.",
                parse_mode="HTML"
            )
        elif event.update.callback_query:
            await event.update.callback_query.answer(
                "⚠️ Kutilmagan xatolik yuz berdi. Qayta urinib ko'ring.",
                show_alert=True
            )
    except Exception:
        pass
    return True


async def main() -> None:
    # 1. Log sozlamalari
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info("Bot ishga tushirilmoqda...")

    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Xatolik: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, token kiriting.")
        print("\n⚠️ XATOLIK: .env faylini oching va BOT_TOKEN ni kiriting!\n")
        return

    # 2. Ma'lumotlar bazasini initsializatsiya qilish
    try:
        await init_db()
        logger.info("Ma'lumotlar bazasi jadvallari muvaffaqiyatli tekshirildi/yaratildi.")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini initsializatsiya qilishda xatolik: {e}")
        return

    # 3. Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Global Error Handler
    dp.errors.register(global_error_handler)

    # 5. Middleware'larni ro'yxatdan o'tkazish
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.inline_query.middleware(DbSessionMiddleware())

    dp.message.middleware(ThrottlingMiddleware(limit=config.RATE_LIMIT))
    dp.callback_query.middleware(ThrottlingMiddleware(limit=config.RATE_LIMIT))

    dp.message.middleware(AdminAuthMiddleware())
    dp.callback_query.middleware(AdminAuthMiddleware())

    # 6. Handler routerlarini ulash
    dp.include_router(admin_panel_router)
    dp.include_router(admin_books_router)
    dp.include_router(admin_manage_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(user_router)

    # 7. Bot buyruqlarini o'rnatish
    await setup_bot_commands(bot)

    # 8. Botni ishga tushirish (Polling)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot faoliyatini boshladi (Polling rejimida)...")

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Bot to'xtatildi va resurslar tozalandi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot foydalanuvchi tomonidan to'xtatildi.")
