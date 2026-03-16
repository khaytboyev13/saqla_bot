import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


# =========================
# MAIN
# =========================
async def main():
    logger.info("Bot ishga tushmoqda...")

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi. .env yoki config.py ni tekshiring.")

    # kerakli papkalar
    os.makedirs("downloads", exist_ok=True)

    # bazani ishga tushirish
    await init_db()
    logger.info("Baza ishga tushirildi.")

    # bot va dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # routerlar
    from handlers.start import start_router
    from handlers.downloader import downloader_router
    from handlers.callbacks import callbacks_router
    from handlers.admin import admin_router

    # middleware
    from middlewares.check_subscribe import CheckSubscribe

    dp.message.outer_middleware(CheckSubscribe())
    dp.callback_query.outer_middleware(CheckSubscribe())

    # router ulash
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(downloader_router)
    dp.include_router(callbacks_router)

    try:
        logger.info("Polling boshlandi...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot session yopildi.")


# =========================
# STARTER
# =========================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot qo'lda to'xtatildi.")
    except Exception:
        logger.exception("Bot ishlashida jiddiy xatolik yuz berdi")