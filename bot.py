import asyncio
from aiogram import Bot, Dispatcher

from config_data.config import BOT_TOKEN
from db.db import database
from handlers import admin_handlers, user_handlers, other_handlers


async def main():
    # Создаем объекты бота и диспетчера
    bot: Bot = Bot(token=BOT_TOKEN)
    dp: Dispatcher = Dispatcher()

    # Инициализируем Базу Данных
    await database.create_tables()
    await database.add_working_hours()

    # Регистрируем роутеры в диспетчере
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(other_handlers.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
