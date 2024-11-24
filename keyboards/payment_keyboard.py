# keyboards/payment_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def create_screenshot_keyboard():
    """Create keyboard for screenshot submission"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Cancel Payment")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def admin_confirmation_keyboard(user_id: int, course_id: int):
    """Create keyboard for admin payment confirmation"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm Payment",
                    callback_data=f"confirm_payment_{user_id}_{course_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Reject Payment",
                    callback_data=f"reject_payment_{user_id}_{course_id}"
                )
            ]
        ]
    )

async def create_payment_keyboard(course_id: int, price: float, user_id: int = None):
    """Create payment keyboard for user"""
    callback_data = f"pay_{course_id}_{user_id}" if user_id else f"pay_{course_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Pay {price}",
                    callback_data=callback_data
                )
            ]
        ]
    )

