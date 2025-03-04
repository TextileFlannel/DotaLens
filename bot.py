from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router
from database import init_db
import logging
from cache import cache


async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands([
        {"command": "start", "description": "Запустить бота"},
        {"command": "info", "description": "Информация о боте"}
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())