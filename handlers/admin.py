# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from loader import bot, api_client
import logging
from data.api_client import APIClient


router = Router()


@router.callback_query(lambda c: c.data.startswith("confirm_payment_"))
async def handle_payment_confirmation(callback: CallbackQuery):
    """Handle admin confirmation of payment"""
    try:
        _, user_id, course_id = callback.data.split("_")
        user_id, course_id = int(user_id), int(course_id)

        # Update user's purchased courses in database
        await api_client.add_user_purchase(user_id, course_id)

        # Notify user
        await bot.send_message(
            user_id,
            "Your payment has been confirmed! You now have access to all lessons in the course.",
        )

        # Update admin message
        await callback.message.edit_caption(
            callback.message.caption + "\n\n✅ Confirmed", reply_markup=None
        )

    except Exception as e:
        logging.error(f"Error confirming payment: {e}")
        await callback.answer("Error processing confirmation", show_alert=True)
