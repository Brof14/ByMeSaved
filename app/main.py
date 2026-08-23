import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.db.database import connect, close
from app.ai.openrouter import OpenRouter
from app.bot.handlers import router, setup_ai

async def main():
    await connect()
    ai = OpenRouter()
    setup_ai(ai)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await ai.close()
        await bot.session.close()
        await close()

if __name__ == "__main__":
    asyncio.run(main())
