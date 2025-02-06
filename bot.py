from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router
import logging


async def main():
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