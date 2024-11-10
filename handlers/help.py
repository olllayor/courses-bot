from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()


@router.message(Command("help"))
async def send_help(message: Message):
    await message.answer("This is the help message!")

