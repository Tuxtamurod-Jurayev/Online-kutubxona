import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.base import init_db
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


async def main() -> None:
    # 1. Log sozlamalari
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("online_kutubxona_bot")
    logger.info("Bot ishga tushirilmoqda...")

    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Xatolik: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, token kiriting.")
        print("\n⚠️ XATOLIK: .env faylini oching va BOT_TOKEN ni kiriting!\n")
        return

    # 2. Ma'lumotlar bazasini initsializatsiya qilish (jadvallarni yaratish)
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

    # 4. Middleware'larni ro'yxatdan o'tkazish (Ketma-ketlik muhim!)
    # a) Har bir so'rovga DB sessiyasini ulaymiz
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # b) Tez-tez so'rov yuborishdan himoya (Anti-flood / Rate Limiting)
    dp.message.middleware(ThrottlingMiddleware(limit=config.RATE_LIMIT))
    dp.callback_query.middleware(ThrottlingMiddleware(limit=config.RATE_LIMIT))

    # c) Admin autentifikatsiyasini tekshiruvchi middleware
    dp.message.middleware(AdminAuthMiddleware())
    dp.callback_query.middleware(AdminAuthMiddleware())

    # 5. Handler routerlarini ulash
    dp.include_router(admin_panel_router)
    dp.include_router(admin_books_router)
    dp.include_router(admin_manage_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(user_router)

    # 6. Botni ishga tushirish (Polling)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot faoliyatini boshladi (Polling rejimida)...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot foydalanuvchi tomonidan to'xtatildi.")
