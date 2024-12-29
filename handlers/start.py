from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
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
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from states.settings import BotSettings
from states.mentor_state import MentorState, CourseState
from states.registration import RegistrationStates
import logging

router = Router()
logger = logging.getLogger(__name__)


class MediaState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_video = State()


def get_language_kb() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text="O'zbek 🇺🇿", callback_data="lang_uz")
    builder.button(text="English 🇬🇧", callback_data="lang_en")
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()


@router.message(Command("start"))
async def command_start(
    message: Message, state: FSMContext, api_client: APIClient
) -> None:
    try:
        user_id = message.from_user.id
        # Clear any existing states
        await state.clear()

        # Check if the user is already registered
        student = await api_client.get_student_by_telegram_id(str(user_id))
        logger.info(f"Student: {student}")
        if student:
            # If the user is already registered, skip registration
            await message.answer(
                i18n.get_text(user_id, "welcome_back"),
                reply_markup=menu_keyboard(user_id),
            )
            return

        # If the user is not registered, proceed with the registration process
        # Show language selection
        await message.answer(
            "👋 Welcome! Please select your preferred language:",
            reply_markup=get_language_kb(),
        )
    except Exception as e:
        logger.error(f"Error during start: {e}")
        await message.answer("⚠️ An error occurred. Please try again later.")


@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(
    callback: CallbackQuery, state: FSMContext, api_client: APIClient
) -> None:
    """Handle language selection"""
    try:
        user_id = callback.from_user.id
        language = callback.data.split("_")[1]
        i18n.set_user_language(user_id, language)

        # Clear any existing states when language is changed
        await state.clear()
        logger.info(
            f"States cleared for user {user_id} after language change to {language}"
        )

        # Get welcome text in new language
        welcome_text = i18n.get_text(user_id, "language_changed")

        # Edit message with new language confirmation
        await callback.message.edit_text(welcome_text, reply_markup=None)

        # Check if the user is already registered
        student = await api_client.get_student_by_telegram_id(str(user_id))
        if student:
            # Check if all required fields are present
            if not student.get("name") or not student.get("contact"):
                # If any information is missing, start re-registration
                await state.set_state(RegistrationStates.NAME)
                await callback.message.answer(
                    i18n.get_text(user_id, "ask_name"),
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                # Store auth data in state
                token = api_client._get_cached_token(user_id)
                await state.update_data(
                    user_id=user_id, student_id=student["id"], auth_token=token
                )

                # Send menu keyboard in a new message
                await callback.message.answer(
                    i18n.get_text(user_id, "choose_action"),
                    reply_markup=menu_keyboard(user_id),
                )
        else:
            # If user is not registered, start the registration process
            await state.set_state(RegistrationStates.NAME)
            await callback.message.answer(
                i18n.get_text(user_id, "ask_name"),
                reply_markup=ReplyKeyboardRemove(),
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
        logger.info(
            f"States cleared for user {message.from_user.id} on language command"
        )

        await message.answer(
            i18n.get_text(message.from_user.id, "select_language"),
            reply_markup=get_language_kb(),
        )
    except Exception as e:
        logger.error(f"Error in command_language: {e}")
        await message.answer("An error occurred. Please try again.")


@router.message(Command("help"))
async def command_help(message: Message) -> None:
    """Handle /help command"""
    try:
        help_text = i18n.get_text(message.from_user.id, "help")
        await message.answer(help_text)
    except Exception as e:
        logger.error(f"Error in command_help: {e}")
        await message.answer("An error occurred. Please try again.")


@router.message(Command("image"))
async def command_image(message: Message, state: FSMContext) -> None:
    """Handle /image command"""
    try:
        await message.answer("Please send me a photo 📸")
        await state.set_state(MediaState.waiting_for_photo)
    except Exception as e:
        logger.error(f"Error in command_image: {e}")
        await message.answer("⚠️ An error occurred. Please try again.")


@router.message(MediaState.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext) -> None:
    """Handle received photo"""
    try:
        # Get the file_id of the largest photo size
        file_id = message.photo[-1].file_id

        # Send the file_id back to the user
        await message.answer(
            f"Photo received!\nFile ID: `{file_id}`", parse_mode=ParseMode.MARKDOWN
        )

        # Clear the state
        await state.clear()
    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        await message.answer("⚠️ An error occurred while processing the photo.")
        await state.clear()


@router.message(Command("video"))
async def command_video(message: Message, state: FSMContext) -> None:
    """Handle /video command"""
    try:
        await message.answer("Please send me a video 📹")
        await state.set_state(MediaState.waiting_for_video)
    except Exception as e:
        logger.error(f"Error in command_video: {e}")
        await message.answer("⚠️ An error occurred. Please try again.")


@router.message(MediaState.waiting_for_video, F.video)
async def handle_video(message: Message, state: FSMContext) -> None:
    """Handle received video"""
    try:
        # Get the file_id of the video
        file_id = message.video.file_id

        # Send the file_id back to the user
        await message.answer(
            f"Video received!\nFile ID: `{file_id}`", parse_mode=ParseMode.MARKDOWN
        )

        # Clear the state
        await state.clear()
    except Exception as e:
        logger.error(f"Error in handle_video: {e}")
        await message.answer("⚠️ An error occurred while processing the video.")
        await state.clear()


@router.message(Command("test"))
async def command_test(message: Message) -> None:
    """Handle /test command"""
    try:
        await message.answer("This is a test command.")
        await message.answer_video(
            "BAACAgIAAxkBAAIBXGdw2iLUGi4hdx71pGclyftOaexDAAKyagACTl1BSxt80L0INJroNgQ",
            caption="Test video",
        )
    except Exception as e:
        logger.error(f"Error in command_test: {e}")
        await message.answer("An error occurred. Please try again.")
