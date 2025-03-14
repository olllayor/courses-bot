from aiogram import Dispatcher
from loader import dp
from .throttling import ThrottlingMiddleware

if __name__ == "middlewares":
    # New way to setup middleware in aiogram 3.x
    dp.message.middleware(ThrottlingMiddleware())