# keyboards/courses_keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from loader import i18n
import logging

logger = logging.getLogger(__name__)


def create_courses_keyboard(courses: List[Dict], user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with course titles.

    Args:
        courses: List of course dictionaries containing 'title' and 'id'.
        user_id: Telegram user ID for localization.

    Returns:
        ReplyKeyboardMarkup with course titles as buttons.
    """
    try:
        # Create buttons for each course with an emoji
        buttons = [[KeyboardButton(text=f"📚 {course['title']}")] for course in courses]

        # Add a back button
        buttons.append(
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_main_menu")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        )

        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    except Exception as e:
        logger.error(f"Error creating courses keyboard: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching courses")]],
            resize_keyboard=True,
        )
