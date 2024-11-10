import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_TOKEN
from handlers import help, start
from utils.set_bot_commands import set_commands


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Include routers instead of dispatchers
dp.include_router(start.router)
dp.include_router(help.router)

async def main():
    await set_commands(bot)  # Ensure this is called before starting the polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())