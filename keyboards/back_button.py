#keyboard/back_button.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from loader import i18n
import logging

logger = logging.getLogger(__name__)

def back_to_webinars(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    buttons = []
    buttons.append([KeyboardButton(text=i18n.get_text(user_id, 'back_to_webinars') if user_id else "Ortga qaytish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)