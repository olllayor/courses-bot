# handlers/webinars.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from data.api_client import APIClient
from keyboards.back_button import back_to_webinars
from keyboards.webinar_keyboard import create_webinar_keyboard
from keyboards.menu import menu_keyboard
import logging
from loader import i18n

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
api_client = APIClient()


@router.message(F.text.in_(["📂 Webinars", "📂 Vebinarlar"]))
async def show_webinars(message: Message, state: FSMContext = None):
    """Display available webinars in a keyboard"""
    try:
        # Fetch webinars from the API
        webinars = await api_client.get_webinars(telegram_id=message.from_user.id)

        if not webinars:
            await message.answer("⚠️ No webinars available. Please try again later.")
            return

        # Create a keyboard with webinar titles
        keyboard = create_webinar_keyboard(webinars, user_id=message.from_user.id)

        # Send the keyboard to the user
        await message.answer(
            i18n.get_text(message.from_user.id, "choose_webinar"),
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error listing webinars: {e}")
        await message.answer("⚠️ An error occurred. Please try again later.")


@router.message(F.text.startswith("📅"))
async def handle_webinar_selection(message: Message, state: FSMContext = None):
    """Handle webinar selection and display details"""
    try:
        # Extract the webinar title from the button text
        webinar_title = message.text.replace("📅 ", "").strip()

        # Fetch webinars from the API
        webinars = await api_client.get_webinars(telegram_id=message.from_user.id)

        # Find the selected webinar
        selected_webinar = next(
            (webinar for webinar in webinars if webinar["title"] == webinar_title),
            None,
        )

        if not selected_webinar:
            await message.answer("⚠️ Webinar not found. Please try again.")
            return

        # Display webinar details
        webinar_details = (
            f"📅 *{selected_webinar['title']}*\n"
            f"🧑‍🏫 {i18n.get_text(message.from_user.id, 'mentor')}: {selected_webinar['mentor_details']['name']}\n"
        )
        webinar_video_id = selected_webinar.get("video_telegram_id")
        logger.info(f"Webinar details: {webinar_video_id}")

        if webinar_video_id:
            await message.answer_video(
                video=webinar_video_id,
                caption=webinar_details,
                parse_mode="Markdown",
                reply_markup=back_to_webinars(user_id=message.from_user.id),
                protect_content=True,
            )
        else:
            await message.answer(
                webinar_details,
                parse_mode="Markdown",
                reply_markup=back_to_webinars(user_id=message.from_user.id),
            )

    except Exception as e:
        logger.error(f"Error handling webinar selection: {e}")
        await message.answer("⚠️ An error occurred. Please try again.")


@router.message(F.text.in_(["⬅️ Asosiy menyuga qaytish", "⬅️ Back to Main Menu"]))
async def handle_back_to_menu(message: Message, state: FSMContext = None):
    """Handle the back button and return to the main menu"""
    try:
        # Clear any state
        if state:
            await state.clear()
            
        await message.answer(
            i18n.get_text(message.from_user.id, "returning_to_main_menu"),
            reply_markup=menu_keyboard(message.from_user.id),
        )
    except Exception as e:
        logger.error(f"Error handling back to menu: {e}")
        await message.answer(
            "⚠️ An error occurred. Returning to main menu.",
            reply_markup=menu_keyboard(message.from_user.id),
        )


@router.message(F.text.in_(["⬅️ Vebinarlarga qaytish", "⬅️ Back to Webinars"]))
async def handle_back_to_webinars(message: Message, state: FSMContext = None):
    """Handle the back button and return to the webinar list"""
    try:
        # Simply call the show_webinars function with the message
        await show_webinars(message, state)
    except Exception as e:
        logger.error(f"Error handling back to webinars: {e}")
        await message.answer(
            "⚠️ An error occurred. Please try again.",
            reply_markup=menu_keyboard(message.from_user.id),
        )