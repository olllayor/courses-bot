# keyboards/mentors_keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from loader import i18n
import logging

logger = logging.getLogger(__name__)


def create_mentor_keyboard(mentors: List[Dict], user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with mentor names.

    Args:
        mentors: List of mentor dictionaries containing 'name' and 'id'.
        user_id: Telegram user ID for localization.

    Returns:
        ReplyKeyboardMarkup with mentor names as buttons.
    """
    try:
        # Create pairs of mentor buttons
        buttons = []
        for i in range(0, len(mentors), 2):
            row = [KeyboardButton(text=f"👤 {mentors[i]['name']}")]
            if i + 1 < len(mentors):  # Check if there's a second mentor for the row
                row.append(KeyboardButton(text=f"👤 {mentors[i + 1]['name']}"))
            buttons.append(row)

        # Add a back button
        buttons.append([KeyboardButton(text=i18n.get_text(user_id, 'back_to_main_menu') if user_id else "Ortga qaytish")])

        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    except Exception as e:
        logger.error(f"Error creating mentor keyboard: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching mentors")]],
            resize_keyboard=True,
        )