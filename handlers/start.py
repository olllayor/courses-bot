from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from data.api_client import APIClient
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
from states.mentor_state import MentorState, CourseState
import logging


router = Router()
api_client = APIClient()
logger = logging.getLogger(__name__)

def get_language_kb() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="O'zbek 🇺🇿", callback_data="lang_uz")
    builder.button(text="English 🇬🇧", callback_data="lang_en")
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    """
    Handle /start command
    - First authenticate with API
    - Then create/retrieve user
    - Start language selection flow
    """
    try:
        # Clear all states
        await state.clear()
        logger.info(f"States cleared for user {message.from_user.id}")
        
        # First authenticate with API
        auth_token = await api_client.authenticate_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name
        )
        
        if not auth_token:
            logger.error("Initial authentication failed")
            await message.answer("Unable to connect to service. Please try again later.")
            return
            
        # Now try to get or create student with auth token
        try:
            existing_student = await api_client.get_student_by_telegram_id(str(message.from_user.id))
            
            if not existing_student:
                student_data = {
                    "name": message.from_user.full_name,
                    "telegram_id": message.from_user.id,
                    "phone_number": ""
                }
                api_student = await api_client.create_student(student_data)
                
                if not api_student:
                    logger.error("Failed to create student in API")
                    await message.answer("Registration failed. Please try again later.")
                    return
                    
            logger.info(f"Student {'created' if not existing_student else 'retrieved'} successfully")
                    
        except Exception as e:
            logger.error(f"Failed to save/retrieve user: {str(e)}")
            await message.answer("Error during registration. Please try again.")
            return
        
        # Start language selection
        await message.answer(
            "Tilni tanlang / Choose language:",
            reply_markup=get_language_kb()
        )
        
    except Exception as e:
        logger.error(f"Error in command_start: {e}")
        await message.answer("An error occurred. Please try again.")

@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle language selection"""
    try:
        language = callback.data.split('_')[1]
        i18n.set_user_language(callback.from_user.id, language)
        
        # Clear any existing states when language is changed
        await state.clear()
        logger.info(f"States cleared for user {callback.from_user.id} after language change to {language}")
        
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
            reply_markup=menu_keyboard(callback.from_user.id)
        )
    except Exception as e:
        logger.error(f"Error in handle_language_selection: {e}")
        await callback.message.answer("An error occurred. Please try again.")

@router.message(Command("language"))
async def command_language(message: Message, state: FSMContext) -> None:
    """Handle /language command"""
    try:
        # Clear states when language is being changed
        await state.clear()
        logger.info(f"States cleared for user {message.from_user.id} on language command")
        
        await message.answer(
            i18n.get_text(message.from_user.id, 'select_language'),
            reply_markup=get_language_kb()
        )
    except Exception as e:
        logger.error(f"Error in command_language: {e}")
        await message.answer("An error occurred. Please try again.")

@router.message(Command("help"))
async def command_help(message: Message) -> None:
    """Handle /help command"""
    try:
        help_text = i18n.get_text(message.from_user.id, 'help')
        await message.answer(help_text)
    except Exception as e:
        logger.error(f"Error in command_help: {e}")
        await message.answer("An error occurred. Please try again.")

# @router.message(F.video)
# async def handle_video(message: Message) -> None:
#     """
#     Handle incoming videos and return their file_id
#     This is useful for getting video IDs to use later in the bot
#     """
#     try:
#         video = message.video
#         file_id = video.file_id
#         file_size = video.file_size  # size in bytes
#         duration = video.duration     # duration in seconds
        
#         # Format file size to MB
#         size_mb = round(file_size / (1024 * 1024), 2)
        
#         # Format duration to minutes and seconds
#         minutes = duration // 60
#         seconds = duration % 60
        
#         info_text = (
#             f"📹 Video Information:\n\n"
#             f"File ID: {file_id}\n"
#             f"Size: {size_mb} MB\n"
#             f"Duration: {minutes}m {seconds}s\n"
#             f"Width: {video.width}px\n"
#             f"Height: {video.height}px"
#         )
        
#         logger.info(f"Video received from user {message.from_user.id}: {file_id}")
#         await message.reply(info_text)
        
#     except Exception as e:
#         logger.error(f"Error handling video from user {message.from_user.id}: {e}")
#         await message.answer("Error processing video. Please try again.")
