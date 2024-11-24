# mentors.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters.base import Filter
from aiogram.enums import ParseMode
import logging

from keyboards.mentors_keyboard import (
    mentor_courses,
    mentor_keyboard,
    mentor_booking_keyboard,
    mentors_menu_keyboard,
)

from data.api_client import APIClient
from loader import i18n, bot
from states.mentor_state import CourseState, MentorState
from utils.filters import MentorNameFilter

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





router = Router()
api_client = APIClient()


async def get_mentor_id(state: FSMContext):
    mentor_state = await state.get_data()
    mentor_id = mentor_state.get("mentor_id")
    return mentor_id


@router.message(F.text.in_(["🧑‍🏫 Mentors", "🧑‍🏫 Mentorlar"]))
async def mentors(message: Message):
    try:
        keyboard = await mentor_keyboard()
        await message.answer("Choose a mentor:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error loading mentors keyboard: {e}")
        await message.answer(
            "An error occurred while fetching the mentors list. Please try again later."
        )


@router.message(MentorNameFilter())
async def mentor_details(message: Message, state: FSMContext):
    mentor_name = message.text.strip()
    mentor_id = await api_client.get_mentor_id_by_name(mentor_name)

    # Save mentor_id in state
    await state.update_data(mentor_id=mentor_id)
    await state.set_state(MentorState.Mentor_ID)

    # Verify saved id
    data = await state.get_data()
    saved_mentor_id = data.get("mentor_id")
    logger.info(f"Saved mentor_id: {saved_mentor_id}")
    try:
        mentor = await api_client.get_mentor_by_id(mentor_id)
        # logger.info(f"{mentor}")
        if not mentor:
            await message.answer("Mentor not found. Please select a valid mentor.")
            return

        mentor_info = f"👤 *{mentor['name']}*\n" f"📝 {mentor['bio']}\n\n"

        # slot_keyboard = await mentor_booking_keyboard(mentor_name)
        # logger.info(f"{slot_keyboard}")

        # if not slot_keyboard:
        #     await message.answer("No available slots for this mentor")
        #     return
        mentor_photo = mentor.get("profile_picture_id")

        try:
            logger.info(f"Attempting to send photo with ID: {mentor_photo}")
            if mentor_photo:
                try:
                    await message.answer_photo(
                        photo=mentor_photo,
                        caption=mentor_info,  # Consider using caption instead of a separate message
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=await mentors_menu_keyboard(message.from_user.id),
                    )
                except Exception as photo_send_error:
                    logger.error(f"Detailed photo sending error: {photo_send_error}")
                    # Fallback to text message with more specific error logging
                    await message.answer(
                        text=f"Could not send photo. Error: {str(photo_send_error)}\n\n{mentor_info}",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=await mentors_menu_keyboard(message.from_user.id),
                    )
            else:
                logger.warning("No photo ID available for this mentor")
                await message.answer(
                    text=mentor_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=await mentors_menu_keyboard(message.from_user.id),
                )
        except Exception as e:
            logger.error(f"Comprehensive error in mentor details: {e}")
            await message.answer(
                "An unexpected error occurred while processing mentor details."
            )

    except Exception as e:
        logger.error(f"Error loading mentor booking keyboard: {e}")
        await message.answer(
            "An error occurred while fetching the mentor details. Please try again later."
        )
    logger.info('Exit from mentor handler')