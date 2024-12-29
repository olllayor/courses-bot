# handlers/mentors.py
from typing import Dict, Any
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
from utils.filters import MentorNameFilter

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.in_(["📂 Webinars", "📂 Webinarlar"]))
async def list_webinars(message: Message, state: FSMContext, api_client: APIClient):
    """Display available webinars"""
    await message.answer("Fetching webinars...")
    try:
        webinars = await api_client.get_webinars(telegram_id=message.from_user.id)

        if not webinars:
            await message.answer("⚠️ No webinars available. Please try again later.")
            return

        webinars_text = "\n".join(f"👤 {webinar['name']}" for webinar in webinars)
        await message.answer(
            text=f"Here are the available webinars:\n\n{webinars_text}",
            reply_markup=await mentor_keyboard(
                telegram_id=message.from_user.id, api_client=api_client
            ),
        )
    except Exception as e:
        logger.error(f"Error listing webinars: {e}")
        await message.answer("⚠️ An error occurred. Please try again later.")
