# handlers/mentors.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters.base import Filter
from aiogram.enums import ParseMode
import logging
import os
from keyboards.mentors_keyboard import (
    mentor_keyboard,
    mentors_menu_keyboard,
)
from data.api_client import APIClient
from loader import bot
from states.mentor_state import MentorState

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
api_client = APIClient()


class MentorNameFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        try:
            mentors = await api_client.get_mentors(telegram_id=message.from_user.id)
            if not mentors:
                return False

            mentor_names = [mentor.get("name", "").lower() for mentor in mentors]
            message_text = message.text

            if not message_text:
                return False

            return message_text.lower() in mentor_names
        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False


async def setup_mentors_handler():
    """Initialize mentors handler and filters"""
    try:
        # Register message handlers
        router.message.register(
            list_mentors, F.text.in_(["🧑‍🏫 Mentors", "🧑‍🏫 Mentorlar"])
        )
        router.message.register(mentor_details, MentorNameFilter())
        logger.info("Mentors handlers registered successfully")
    except Exception as e:
        logger.error(f"Error setting up mentors handlers: {e}")
        raise


async def get_mentor_id(state: FSMContext) -> int:
    """Get mentor ID from state"""
    data = await state.get_data()
    return data.get("mentor_id")


@router.message(F.text.in_(["🧑‍🏫 Mentors", "🧑‍🏫 Mentorlar"]))
async def list_mentors(message: Message, state: FSMContext):
    """Display available mentors"""
    try:
        mentors = await api_client.get_mentors(telegram_id=message.from_user.id)

        if not mentors:
            await message.answer("⚠️ No mentors available. Please try again later.")
            return

        mentors_text = "\n".join(f"👤 {mentor['name']}" for mentor in mentors)
        await message.answer(
            text=f"Here are the available mentors:\n\n{mentors_text}",
            reply_markup=await mentor_keyboard(telegram_id=message.from_user.id),
        )
    except Exception as e:
        logger.error(f"Error listing mentors: {e}")
        await message.answer("Error fetching mentors list")
    finally:
        await api_client.close()


@router.message(MentorNameFilter())
async def mentor_details(message: Message, state: FSMContext):
    """Handle mentor selection and display details"""
    try:
        mentor_name = message.text.strip()
        mentor = await api_client.get_mentor_by_name(mentor_name)

        if not mentor:
            await message.answer("Mentor not found. Please select a valid mentor.")
            return

        await state.update_data(mentor_id=mentor["id"])
        await state.set_state(MentorState.Mentor_ID)

        mentor_info = f"👤 *{mentor['name']}*\n" f"📝 {mentor['bio']}\n\n"

        keyboard = await mentors_menu_keyboard(message.from_user.id)
        mentor_photo = mentor.get("profile_picture_id")

        if mentor_photo:
            try:
                await message.answer_photo(
                    photo=mentor_photo,
                    caption=mentor_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
            except Exception as photo_error:
                logger.error(f"Failed to send photo: {photo_error}")
                await message.answer(
                    text=mentor_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
        else:
            await message.answer(
                text=mentor_info, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in mentor_details: {e}")
        await message.answer(
            "An error occurred while fetching mentor details. Please try again later."
        )
    finally:
        await api_client.close()
