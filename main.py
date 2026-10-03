import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

import database.db as db
from config import BOT_TOKEN, PORT
from handlers import admin, circle, kino, music, start
from middleware import SubMiddleware

logging.basicConfig(level=logging.INFO)


async def health(_):
    return web.Response(text="OK")


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi")
    await db.init()

    bot = Bot(BOT_TOKEN, session=AiohttpSession(timeout=300))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(SubMiddleware())
    dp.callback_query.outer_middleware(SubMiddleware())
    # Tartib muhim: musiqa routeri eng oxirida
    dp.include_routers(start.router, admin.router, kino.router, circle.router, music.router)

    # Render uchun port ochamiz (health-check)
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
