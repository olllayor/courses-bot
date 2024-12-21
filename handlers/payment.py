# handlers/payment.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
import aiohttp
from data.api_client import APIClient
from keyboards.payment_keyboard import (
    create_screenshot_keyboard,
    admin_confirmation_keyboard,
)
from states.payment_state import PaymentState
from loader import bot
import logging
from typing import Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

router = Router()

# Convert ADMIN_IDS string to list of integers
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_ID", "").split(",")]
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_OWNER = os.getenv("CARD_OWNER")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_payment_data(
    state: FSMContext,
) -> Tuple[Optional[int], Optional[int]]:
    """Validate and get payment data from state"""
    try:
        data = await state.get_data()
        payment_id = data.get("payment_id")
        course_id = data.get("course_id")

        logger.info(
            f"Validating payment data - Payment ID: {payment_id}, Course ID: {course_id}"
        )

        if not payment_id or not course_id:
            logger.error(f"Missing payment data - State data: {data}")
            return None, None

        return payment_id, course_id
    except Exception as e:
        logger.error(f"Error validating payment data: {e}")
        return None, None


async def notify_admins(bot, photo_id: str, payment_info: dict):
    """Notify admins about new payment"""
    success_count = 0
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id,
                photo_id,
                caption=(
                    f"New payment screenshot\n"
                    f"Payment ID: {payment_info['id']}\n"
                    f"User ID: {payment_info['student']}\n"
                    f"Course: {payment_info['course_details']['title']}\n"
                    f"Amount: {payment_info['amount']} UZS"
                ),
                reply_markup=admin_confirmation_keyboard(
                    payment_info["student"], payment_info["id"]
                ),
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    return success_count > 0


async def initiate_course_payment(
    message: Message, state: FSMContext, course: dict, api_client: APIClient
):
    """Shared helper to initiate course payment flow"""
    try:
        # Ensure user is authenticated
        if not await api_client.ensure_authenticated(
            telegram_id=message.from_user.id, name=message.from_user.full_name
        ):
            await message.answer("Authentication failed. Please try /start again.")
            return False

        # Create payment record
        payment = await api_client.create_payment(
            student_id=message.from_user.id,
            course_id=course["id"],
            amount=float(course["price"]),
            telegram_id=message.from_user.id,
        )

        if not payment:
            await message.answer(
                "Error creating payment record. Please try again later."
            )
            return False

        # Store payment data
        await state.update_data(
            {"payment_id": payment["id"], "course_id": course["id"]}
        )

        await message.answer(
            f"To access premium content in *{course['title']}*, "
            f"please transfer {course['price']} UZS to:\n\n"
            f"Card Number: `{CARD_NUMBER}`\n"
            f"Card Owner: `{CARD_OWNER}`\n\n"
            "After payment, please send a screenshot.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_screenshot_keyboard(),
        )

        await state.set_state(PaymentState.AWAITING_SCREENSHOT)
        return True

    except Exception as e:
        logger.error(f"Error initiating payment: {e}")
        await message.answer("Error processing payment request. Please try again.")
        return False


@router.message(F.text.in_(["💳 Payment", "💳 To'lov"]))
async def show_payment_details(
    message: Message, state: FSMContext, api_client: APIClient
):
    """Show payment details and ask for screenshot"""
    try:
        data = await state.get_data()
        course_id = data.get("course_id")

        if not course_id:
            await message.answer("Please select a course first.")
            return

        # Check if user has already purchased the course
        has_purchased = await api_client.check_user_purchase(
            message.from_user.id, course_id
        )
        if has_purchased:
            await message.answer("You have already purchased this course!")
            return

        # Get course details with authentication
        course = await api_client.get_course_by_id(
            course_id, telegram_id=message.from_user.id
        )
        if not course:
            await message.answer("Course not found.")
            return

        # Create payment record
        payment = await api_client.create_payment(
            student_id=message.from_user.id,
            course_id=course_id,
            amount=course["price"],
            telegram_id=message.from_user.id,
        )

        if not payment:
            logger.error("Failed to create payment record")
            await message.answer(
                "Error creating payment record. Please try again later."
            )
            return

        # Store BOTH payment_id and course_id in state
        await state.update_data({"payment_id": payment["id"], "course_id": course_id})

        # Log state data after storing
        state_data = await state.get_data()
        logger.info(f"State data after payment creation: {state_data}")

        await message.answer(
            f"To purchase {course['title']}, please transfer {course['price']} UZS to:\n\n"
            f"Card Number: {CARD_NUMBER}\n"
            f"Card Owner: {CARD_OWNER}\n\n"
            "After payment, please send a screenshot of your payment confirmation.\n\n"
            "⚠️ Important: Make sure your screenshot clearly shows:\n"
            "• Transaction amount\n"
            "• Date and time\n"
            "• Transaction ID/reference number",
            reply_markup=create_screenshot_keyboard(),
        )
        await state.set_state(PaymentState.AWAITING_SCREENSHOT)

    except Exception as e:
        logger.error(f"Error showing payment details: {e}")
        await message.answer("An error occurred. Please try again later.")


@router.message(PaymentState.AWAITING_SCREENSHOT)
async def handle_screenshot(message: Message, state: FSMContext, api_client: APIClient):
    """Handle payment screenshot submission"""
    try:
        if message.text == "❌ Cancel Payment":
            await state.clear()
            await message.answer("Payment cancelled.", reply_markup=None)
            return

        if not message.photo:
            await message.answer("Please send a screenshot image of your payment.")
            return

        payment_id, _ = await validate_payment_data(state)
        if not payment_id:
            await message.answer("Payment session expired. Please try again.")
            return

        # Get largest photo
        photo = message.photo[-1]
        logger.info(f"Received photo: {photo.file_id}")

        # Save screenshot
        result = await api_client.make_authenticated_request(
            "PUT",
            f"{api_client.base_url}/payments/{payment_id}/save_screenshot/",
            telegram_id=message.from_user.id,
            json={"file_id": photo.file_id},
        )

        if not result:
            await message.answer("Failed to save screenshot. Please try again.")
            return

        # Get payment details
        payment_info = await api_client.get_payment_details(
            payment_id, message.from_user.id
        )
        if not payment_info:
            await message.answer("Failed to get payment details. Please try again.")
            return

        # Notify admins
        if await notify_admins(bot, photo.file_id, payment_info):
            await message.answer(
                "Thank you! Your payment is being verified by administrators.",
                reply_markup=None,
            )
            await state.clear()
        else:
            await message.answer(
                "Failed to notify administrators. Please contact support.",
                reply_markup=None,
            )

    except Exception as e:
        logger.error(f"Error handling screenshot: {e}")
        await message.answer("Error processing screenshot. Please try again.")


@router.callback_query(F.data.startswith(("confirm_payment_", "reject_payment_")))
async def handle_admin_verification(callback: CallbackQuery, api_client: APIClient):
    """Handle admin payment verification"""
    try:
        # Validate admin
        if str(callback.from_user.id) not in os.getenv("ADMIN_ID", "").split(","):
            await callback.answer("Unauthorized action", show_alert=True)
            return

        action, payment_id = callback.data.split("_payment_")
        is_confirm = action == "confirm"

        # Get payment details before updating
        payment_details = await api_client.get_payment_details(
            payment_id, callback.from_user.id
        )

        if not payment_details:
            await callback.answer("Payment details not found", show_alert=True)
            return

        if payment_details.get("status") != "pending":
            await callback.answer("Payment already processed.", show_alert=True)
            return

        # Update payment status
        result = await api_client.make_authenticated_request(
            "POST",
            f"{api_client.base_url}/payments/{payment_id}/{'confirm' if is_confirm else 'cancel'}/",
            telegram_id=callback.from_user.id,
        )

        if not result:
            await callback.answer("Failed to update payment status", show_alert=True)
            return

        user_id = result.get("student")
        if not user_id:
            await callback.answer("Invalid response from server", show_alert=True)
            return

        # Notify user
        message = (
            "✅ Payment confirmed! You now have access to all course lessons."
            if is_confirm
            else "❌ Payment rejected. Please contact support for assistance."
        )

        await bot.send_message(user_id, message)

        # Update admin message
        await callback.message.edit_caption(
            callback.message.caption
            + f"\n\n{'✅ Confirmed' if is_confirm else '❌ Rejected'}",
            reply_markup=None,
        )
        await callback.answer("Payment status updated")

    except Exception as e:
        logger.error(f"Error in admin verification: {e}")
        await callback.answer("Error updating payment status", show_alert=True)
