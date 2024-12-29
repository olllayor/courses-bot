from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.enums import ParseMode
from data.api_client import APIClient
from keyboards.menu import menu_keyboard
from states.registration import RegistrationStates
from utils.regex import format_phone, is_valid_name, validate_phone
from loader import i18n
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(RegistrationStates.NAME)
async def process_name(message: Message, state: FSMContext, api_client: APIClient):
    """Process the user's name and ask for their contact information."""
    try:
        # Validate the name
        if not is_valid_name(message.text):
            await message.answer(i18n.get_text(message.from_user.id, "invalid_name"))
            return

        # Save the name to the state
        await state.update_data(name=message.text)
        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Share Contact", request_contact=True)]],
            resize_keyboard=True,
        )

        # Ask for the contact information
        await message.answer(
            i18n.get_text(message.from_user.id, "ask_contact"),
            reply_markup=contact_keyboard,
        )
        await state.set_state(RegistrationStates.CONTACT)

    except Exception as e:
        logger.error(f"Error processing name: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


@router.message(RegistrationStates.CONTACT)
async def process_contact(message: Message, state: FSMContext, api_client: APIClient):
    """Process the user's contact information and save it to the database."""
    try:
        contact = None

        # Check if message contains contact from button

        if message.contact:
            contact = message.contact.phone_number
        else:
            contact = message.text

        if not contact:
            await message.answer(
                i18n.get_text(message.from_user.id, "invalid_contact"),
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📱 Share Contact", request_contact=True)]
                    ],
                    resize_keyboard=True,
                ),
            )
            return

        # Format and validate phone
        formatted_phone = format_phone(contact)
        # logger.info(f"Formatted phone: {formatted_phone}")

        if not validate_phone(formatted_phone):
            await message.answer(
                i18n.get_text(message.from_user.id, "invalid_phone_format"),
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📱 Share Contact", request_contact=True)]
                    ],
                    resize_keyboard=True,
                ),
            )
            return

        # Get the name from state
        state_data = await state.get_data()
        name = state_data.get("name")

        # Save user information
        user_data = {
            "telegram_id": message.from_user.id,
            "name": name,
            "phone_number": formatted_phone,
        }
        # logger.info(f"Saving user data: {user_data}")

        # Check if the user already exists
        student = await api_client.get_student_by_telegram_id(str(message.from_user.id))
        if student:
            # Update existing user
            success = await api_client.update_student(student["id"], user_data)
        else:
            # Create new user
            success = await api_client.create_user(user_data)

        if not success:
            await message.answer(
                i18n.get_text(message.from_user.id, "registration_failed")
            )
            return

        # Clear state and confirm
        await state.clear()
        await message.answer(
            i18n.get_text(message.from_user.id, "registration_success"),
            reply_markup=menu_keyboard(user_id=message.from_user.id),
        )

    except Exception as e:
        logger.error(f"Error processing contact: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))
