# keyboards/back_button.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import i18n
import logging

logger = logging.getLogger(__name__)


def back_to_webinars(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button for webinars.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_webinars")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        ],
        resize_keyboard=True,
    )


def back_to_mentors(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button for mentors.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_mentors")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        ],
        resize_keyboard=True,
    )


def back_to_courses(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button for courses.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_courses")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        ],
        resize_keyboard=True,
    )


def back_to_lessons(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button for lessons.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_lessons")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        ],
        resize_keyboard=True,   
    )


def back_to_payment(user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with back button for payments.

    Returns:
        ReplyKeyboardMarkup with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_to_payment")
                    if user_id
                    else "Ortga qaytish"
                )
            ]
        ],
        resize_keyboard=True,
    )
