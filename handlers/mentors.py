# handlers/mentors.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums import ParseMode
from data.api_client import APIClient
from keyboards.mentors_keyboard import create_mentor_keyboard
from keyboards.back_button import back_to_mentors
from keyboards.menu import menu_keyboard
from loader import i18n
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.in_(["🧑‍🏫 Mentors", "🧑‍🏫 Mentorlar"]))
async def list_mentors(message: Message, state: FSMContext, api_client: APIClient):
    """Display available mentors in a keyboard"""
    try:
        # Fetch mentors from the API
        mentors = await api_client.get_mentors(telegram_id=message.from_user.id)

        if not mentors:
            await message.answer(
                i18n.get_text(message.from_user.id, "no_mentors_available")
            )
            return

        # Create a keyboard with mentor names
        keyboard = create_mentor_keyboard(mentors, user_id=message.from_user.id)

        # Send the keyboard to the user
        await message.answer(
            i18n.get_text(message.from_user.id, "choose_mentor"),
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error listing mentors: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


@router.message(F.text.startswith("👤"))
async def handle_mentor_selection(
    message: Message, state: FSMContext, api_client: APIClient
):
    """Handle mentor selection and display details"""
    try:
        # Extract the mentor name from the button text
        mentor_name = message.text.replace("👤 ", "").strip()
        logger.info(f"User Selected mentor: {mentor_name}")

        # Fetch mentors from the API
        mentors = await api_client.get_mentors(telegram_id=message.from_user.id)
        # logger.info(f"Mentors: {mentors}")

        # Find the selected mentor
        selected_mentor = next(
            (mentor for mentor in mentors if mentor["name"] == mentor_name),
            None,
        )
        # logger.info(f"Selected mentor: {selected_mentor}")

        if not selected_mentor:
            await message.answer(
                i18n.get_text(message.from_user.id, "mentor_not_found")
            )
            return

        # Display mentor details using HTML formatting
        mentor_details = (
            f"👤 <b>{selected_mentor['name']}</b>\n"
            f"📝 {i18n.get_text(message.from_user.id, 'bio')}: {selected_mentor.get('bio', i18n.get_text(message.from_user.id, 'no_bio_available'))}\n"
        )

        mentor_photo_id = selected_mentor.get("profile_picture_id")
        if mentor_photo_id:
            await message.answer_photo(
                photo=mentor_photo_id,
                caption=mentor_details,
                parse_mode="HTML",  # Use HTML parsing mode
                reply_markup=back_to_mentors(user_id=message.from_user.id),
            )
        else:
            await message.answer(
                mentor_details,
                parse_mode="HTML",  # Use HTML parsing mode
                reply_markup=back_to_mentors(user_id=message.from_user.id),
            )

        await message.answer(i18n.get_text(message.from_user.id, "coming_soon"))

    except Exception as e:
        logger.error(f"Error handling mentor selection: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


@router.message(F.text.in_(["ℹ️ Loyiha haqida", "ℹ️ About Project"]))
async def handle_about_project(message: Message):
    """Handle the about project button"""
    await message.answer(
        i18n.get_text(message.from_user.id, "about_our_project"),
        reply_markup=menu_keyboard(user_id=message.from_user.id),
    )


@router.message(F.text.in_(["⬅️ Mentorlarga qaytish", "⬅️ Back to Mentors"]))
async def handle_back_to_mentors(
    message: Message, state: FSMContext, api_client: APIClient
):
    """Handle the back button and return to the mentor list"""
    await list_mentors(message, state, api_client)
