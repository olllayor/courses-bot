import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message

from loader import dp, bot, i18n
from config import API_TOKEN
from handlers import courses, help, lessons, mentors, payment, start
from utils.set_bot_commands import set_commands
import middlewares

logging.basicConfig(level=logging.INFO)

# Include routers instead of dispatchers
dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(mentors.router)
dp.include_router(courses.router)
dp.include_router(lessons.router)
dp.include_router(payment.router)

async def main():
    await set_commands(bot)  # Ensure this is called before starting the polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())