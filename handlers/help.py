from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from loader import bot, i18n


router = Router()


@router.message(Command("help"))
async def send_help(message: Message):
    await message.answer(i18n.t("help_message"))

