#mentors.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters.base import Filter
from aiogram.enums import ParseMode
import logging

from keyboards.mentors_keyboard import mentor_keyboard, mentor_booking_keyboard
from datas.db import show_mentors
from datas.api_client import APIClient
from loader import i18n

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MentorNameFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        try:
            mentors = await show_mentors()
            return any(mentor.lower() == message.text.lower() for mentor in mentors)
        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False

router = Router()
api_client = APIClient()


@router.message(F.text.in_(["🧑‍🏫 Mentors"]))
async def mentors(message: Message):
    try:
        keyboard = await mentor_keyboard()
        await message.answer("Choose a mentor:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error loading mentors keyboard: {e}")
        await message.answer("An error occurred while fetching the mentors list. Please try again later.")

@router.message(MentorNameFilter())
async def mentor_details(message: Message):
    mentor_name = message.text.strip()
    logger.info(f"Fetching details for mentor: {mentor_name}")
    try:
        mentor = await api_client.get_mentor_by_name(mentor_name)
        logger.info(f"{mentor}")
        if not mentor:
            await message.answer("Mentor not found. Please select a valid mentor.")
            return
        
        mentor_info = (
            f"👤 *{mentor['name']}*\n"
            f"📝 {mentor['bio']}\n\n"   
        )
        
        slot_keyboard = await mentor_booking_keyboard(mentor_name)
        # logger.info(f"{slot_keyboard}")
        logger.info(f"{mentor['profile_picture_id']}")
        if not slot_keyboard:
            await message.answer("No available slots for this mentor")
            return

        try:
            # Try to send with photo first
            if mentor.get('profile_picture_id'):
                await message.answer_photo(
                    photo=mentor['profile_picture_id'],
                    caption=mentor_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=slot_keyboard
                )
            else:
                # Fallback to text-only message if no photo ID
                await message.answer(
                    text=mentor_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=slot_keyboard
                )
        except Exception as photo_error:
            logger.error(f"Error sending photo: {photo_error}")
            # Fallback to text-only message if photo sending fails
            await message.answer(
                text=mentor_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=slot_keyboard
            )
            
    except Exception as e:
        logger.error(f"Error loading mentor booking keyboard: {e}")
        await message.answer("An error occurred while fetching the mentor details. Please try again later.")