# keyboards/payment_keyboard.py
import logging

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

logger = logging.getLogger(__name__)

def create_screenshot_keyboard():
    """Create keyboard for screenshot submission"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Cancel Payment")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def admin_confirmation_keyboard(user_id: int, payment_id: int):
    """Create keyboard for admin payment confirmation"""
    logger.info(f"Creating admin confirmation keyboard for payment {payment_id} (user: {user_id})")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm Payment",
                    callback_data=f"confirm_payment_{payment_id}_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Reject Payment",
                    callback_data=f"reject_payment_{payment_id}_{user_id}"
                )
            ]
        ]
    )
    return keyboard

async def create_payment_keyboard(course_id: int, price: float, user_id: int = None):
    """Create payment keyboard for user"""
    callback_data = f"pay_{course_id}_{user_id}" if user_id else f"pay_{course_id}"
    logger.info(f"Creating payment keyboard for course {course_id}, user {user_id}, price {price}")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Pay {price:,.2f}",
                    callback_data=callback_data
                )
            ]
        ]
    )

