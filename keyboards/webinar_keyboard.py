# keyboards/webinar_keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from loader import i18n
import logging

logger = logging.getLogger(__name__)


def create_webinar_keyboard(webinars: List[Dict], user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with webinar titles.

    Args:
        webinars: List of webinar dictionaries containing 'title' and 'id'.

    Returns:
        ReplyKeyboardMarkup with webinar titles as buttons.
    """
    try:
        # Create buttons for each webinar
        buttons = [
            [KeyboardButton(text=f"📅 {webinar['title']}")]
            for webinar in webinars
        ]

        # Add a back button
        buttons.append([KeyboardButton(text=i18n.get_text(user_id, 'back_to_main_menu') if user_id else "Ortga qaytish")])

        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    except Exception as e:
        logger.error(f"Error creating webinar keyboard: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching webinars")]],
            resize_keyboard=True,
        )