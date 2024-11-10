from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()

@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Welcome to the Courses Bot!")