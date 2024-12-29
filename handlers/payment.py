# handlers/payment.py
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from data.api_client import APIClient
from keyboards.payment_keyboard import create_payment_keyboard
from keyboards.back_button import back_to_payment
from states.payment_state import PaymentState
from utils.state_utils import get_course_id
from loader import i18n
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.in_(["💳 Payment", "💳 To'lov"]))
async def initiate_payment(message: Message, state: FSMContext, api_client: APIClient):
    """Initiate payment flow"""
    try:
        course_id = await get_course_id(state)
        if not course_id:
            await message.answer("Please select a course first.")
            return

        await message.answer(i18n.get_text(message.from_user.id, "initiating_payment"))

        # Fetch payment details from the API
        payment_details = await api_client.get_payment_details(
            course_id=course_id,
            telegram_id=message.from_user.id,
        )

        if not payment_details:
            await message.answer(i18n.get_text(message.from_user.id, "no_payment_details"))
            return

        # Create a keyboard for payment options
        keyboard = create_payment_keyboard(payment_details, user_id=message.from_user.id)

        # Send the keyboard to the user
        await message.answer(
            i18n.get_text(message.from_user.id, "payment_options"),
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error initiating payment: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))