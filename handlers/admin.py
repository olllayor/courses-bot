import asyncio
import logging
from aiogram import Bot, types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from data.api_client import APIClient
from aiogram.fsm.state import State, StatesGroup
from loader import bot, i18n
from config import ADMIN_IDS

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
ADMIN_IDS = [int(id) for id in ADMIN_IDS.split(",")]


# State for broadcast
class BroadcastState(StatesGroup):
    WAITING_FOR_MESSAGE = State()


# Get all users from the database
async def get_users(api_client: APIClient):
    """
    Return a list of all users from the database.
    """
    try:
        users = await api_client.get_all_users()
        return [user["telegram_id"] for user in users]
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []


# Safe message sender
async def send_message(
    user_id: int, text: str, disable_notification: bool = False
) -> bool:
    """
    Safely send a message to a user.

    Args:
        user_id: The user's Telegram ID.
        text: The message text.
        disable_notification: Whether to disable notifications.

    Returns:
        True if the message was sent successfully, otherwise False.
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
        logger.info(f"Target [ID:{user_id}]: success")
        return True
    except Exception as e:
        logger.error(f"Target [ID:{user_id}]: failed - {e}")
        return False


# Broadcast handler
async def broadcast_message(text: str, api_client: APIClient) -> int:
    """
    Broadcast a message to all users.

    Args:
        text: The message to broadcast.
        api_client: The API client to fetch users.

    Returns:
        The number of messages successfully sent.
    """
    count = 0
    try:
        for user_id in await get_users(api_client):
            if await send_message(user_id, text):
                count += 1
            await asyncio.sleep(
                0.05
            )  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logger.info(f"{count} messages successfully sent.")
    return count


# /broadcast command
@router.message(Command("broadcast"))
async def command_broadcast(message: Message, state: FSMContext):
    """Start the broadcast process."""
    # Check if the user is an admin
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("You are not authorized to use this command.")
        return

    # Ask the admin for the broadcast message
    await message.answer("What do you want to broadcast to users?")
    await state.set_state(BroadcastState.WAITING_FOR_MESSAGE)


# Handle broadcast message
@router.message(BroadcastState.WAITING_FOR_MESSAGE)
async def process_broadcast_message(
    message: Message, state: FSMContext, api_client: APIClient
):
    """Process the broadcast message and send it to all users."""
    try:
        # Get the broadcast message
        broadcast_text = message.text

        # Broadcast the message
        count = await broadcast_message(broadcast_text, api_client)

        # Notify the admin
        await message.answer(f"Broadcast completed. {count} messages sent.")
    except Exception as e:
        logger.error(f"Error during broadcast: {e}")
        await message.answer("An error occurred during the broadcast.")
    finally:
        # Clear the state
        await state.clear()


# Handle payment confirmation
@router.callback_query(lambda c: c.data.startswith("confirm_payment_"))
async def handle_payment_confirmation(callback: CallbackQuery, api_client: APIClient):
    """Handle admin confirmation of payment"""
    try:
        _, user_id, course_id = callback.data.split("_")
        user_id, course_id = int(user_id), int(course_id)

        # Update user's purchased courses in the database
        success = await api_client.add_user_purchase(
            user_id, course_id, telegram_id=callback.from_user.id
        )

        if not success:
            await callback.answer("Failed to confirm payment.", show_alert=True)
            return

        # Notify the user
        await bot.send_message(
            user_id,
            "Your payment has been confirmed! You now have access to all lessons in the course.",
        )

        # Update the admin message
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Confirmed", reply_markup=None
        )

    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        await callback.answer("Error processing confirmation.", show_alert=True)
