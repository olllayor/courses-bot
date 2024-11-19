from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, types, Router

from keyboards.menu import menu_keyboard
from loader import dp, bot, i18n
from aiogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.settings import BotSettings

router = Router()







# @router.message(Command("video"))
# async def send_video(message: Message):
#     # Use the provided file_id to send the video
#     video = FSInputFile("handlers/video_x.mp4")
#     await message.reply_video(video, caption="Here is a free video about our courses", protect_content=True)
# Language selection keyboard
def get_language_kb() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="O'zbek 🇺🇿", callback_data="lang_uz")
    builder.button(text="English 🇬🇧", callback_data="lang_en")
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()

@router.message(CommandStart())
async def command_start(message: Message) -> None:
    """Handle /start command"""
    await message.answer(
        "Tilni tanlang / Choose language:",
        reply_markup=get_language_kb()
    )

@router.message(Command("language"))
async def command_language(message: Message) -> None:
    """Handle /language command"""
    await message.answer(
        i18n.get_text(message.from_user.id, 'select_language'),
        reply_markup=get_language_kb()
    )

@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery) -> None:
    """Handle language selection"""
    language = callback.data.split('_')[1]
    i18n.set_user_language(callback.from_user.id, language)
    
    # Get welcome text in new language
    welcome_text = i18n.get_text(callback.from_user.id, 'language_changed')
    
    
    
    # Edit message with new language confirmation
    await callback.message.edit_text(
        welcome_text,
        reply_markup=None
    )
    
    # Send menu keyboard in a new message
    await callback.message.answer(
        i18n.get_text(callback.from_user.id, 'choose_action'),
        reply_markup=menu_keyboard()
    )

@router.message(Command("help"))
async def command_help(message: Message) -> None:
    """Handle /help command"""
    help_text = i18n.get_text(message.from_user.id, 'help')
    await message.answer(help_text)
