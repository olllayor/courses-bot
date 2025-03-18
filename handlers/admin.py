# handlers/admin.py
import logging
import os

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from data.api_client import APIClient
from keyboards.menu import menu_keyboard
from loader import api_client, bot

logger = logging.getLogger(__name__)
router = Router()

# Get admin IDs from environment
ADMIN_IDS = [id.strip() for id in os.getenv("ADMIN_ID", "").split(",")]
logger.info(f"Admin IDs loaded: {ADMIN_IDS}")

@router.callback_query(lambda c: c.data.startswith("confirm_payment_"))
async def handle_payment_confirmation(callback: CallbackQuery):
    """Handle admin confirmation of payment"""
    try:
        # Check if user is admin
        admin_id = callback.from_user.id
        admin_name = callback.from_user.full_name
        
        logger.info(f"Payment confirmation attempt by user {admin_id} ({admin_name})")
        logger.info(f"Configured admin IDs: {ADMIN_IDS}")
        
        if str(admin_id) not in ADMIN_IDS:
            logger.warning(f"Unauthorized payment confirmation attempt by user ID: {admin_id}")
            await callback.answer("Unauthorized action", show_alert=True)
            return
            
        # Extract payment ID from callback data
        payment_id = callback.data.split("confirm_payment_")[1]
        logger.info(f"Admin {admin_id} confirming payment {payment_id}")
        
        # Ensure admin is authenticated
        if not await api_client.ensure_user_exists(telegram_id=admin_id, name=admin_name):
            logger.error(f"Failed to register admin {admin_id}")
            await callback.answer("Registration failed. Please try again.", show_alert=True)
            return
        
        # Get payment details to get the user ID and course ID
        payment_info = await api_client.get_payment_details(payment_id, admin_id)
        
        if not payment_info:
            logger.error(f"Failed to get payment information for payment {payment_id}")
            await callback.answer("Failed to get payment information", show_alert=True)
            return
            
        user_id = payment_info["student"]
        course_id = payment_info["course"]
        course_title = payment_info.get("course_details", {}).get("title", "the course")
        
        logger.info(f"Processing payment confirmation for user {user_id}, course {course_id}")

        # Confirm the payment using the new method
        result = await api_client.confirm_payment(payment_id, admin_id, admin_name)
        
        if not result:
            logger.error(f"Failed to confirm payment {payment_id}")
            await callback.answer("Failed to confirm payment", show_alert=True)
            return

        # Notify user
        try:
            # Get user's name for authentication
            user_info = await api_client.make_request(
                "GET",
                f"{api_client.base_url}/students/?telegram_id={user_id}",
                telegram_id=admin_id
            )
            
            user_name = user_info[0]["name"] if user_info and len(user_info) > 0 else None
            
            # Ensure user is authenticated before sending notification
            if user_name and await api_client.ensure_user_exists(telegram_id=user_id, name=user_name):
                await bot.send_message(
                    user_id,
                    f"✅ Your payment for *{course_title}* has been confirmed! You now have access to all lessons in the course.",
                    reply_markup=menu_keyboard(user_id),
                    parse_mode="Markdown",
                )
                logger.info(f"Notification sent to user {user_id} about confirmed payment")
            else:
                logger.error(f"Could not register user {user_id} for notification")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

        # Update admin message
        try:
            await callback.message.edit_caption(
                callback.message.caption + "\n\n✅ Confirmed",
                reply_markup=None,
            )
            logger.info(f"Updated admin message for payment {payment_id}")
        except Exception as e:
            logger.error(f"Failed to update admin message: {e}")
        
        await callback.answer("Payment confirmed successfully")

    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        await callback.answer("Error processing confirmation", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("reject_payment_"))
async def handle_payment_rejection(callback: CallbackQuery):
    """Handle admin rejection of payment"""
    try:
        # Check if user is admin
        admin_id = callback.from_user.id
        admin_name = callback.from_user.full_name
        
        logger.info(f"Payment rejection attempt by user {admin_id} ({admin_name})")
        
        if str(admin_id) not in ADMIN_IDS:
            logger.warning(f"Unauthorized payment rejection attempt by user ID: {admin_id}")
            await callback.answer("Unauthorized action", show_alert=True)
            return
            
        # Extract payment ID from callback data
        payment_id = callback.data.split("reject_payment_")[1]
        logger.info(f"Admin {admin_id} rejecting payment {payment_id}")
        
        # Ensure admin is authenticated
        if not await api_client.ensure_user_exists(telegram_id=admin_id, name=admin_name):
            logger.error(f"Failed to register admin {admin_id}")
            await callback.answer("Registration failed. Please try again.", show_alert=True)
            return
        
        # Get payment details to get the user ID
        payment_info = await api_client.get_payment_details(payment_id, admin_id)
        
        if not payment_info:
            logger.error(f"Failed to get payment information for payment {payment_id}")
            await callback.answer("Failed to get payment information", show_alert=True)
            return
            
        user_id = payment_info["student"]
        course_title = payment_info.get("course_details", {}).get("title", "the course")
        
        logger.info(f"Processing payment rejection for user {user_id}")

        # Cancel the payment using the new method
        result = await api_client.cancel_payment(payment_id, admin_id, admin_name)
        
        if not result:
            logger.error(f"Failed to reject payment {payment_id}")
            await callback.answer("Failed to reject payment", show_alert=True)
            return

        # Notify user
        try:
            # Get user's name for authentication
            user_info = await api_client.make_request(
                "GET",
                f"{api_client.base_url}/students/?telegram_id={user_id}",
                telegram_id=admin_id
            )
            
            user_name = user_info[0]["name"] if user_info and len(user_info) > 0 else None
            
            # Ensure user is authenticated before sending notification
            if user_name and await api_client.ensure_user_exists(telegram_id=user_id, name=user_name):
                await bot.send_message(
                    user_id,
                    f"❌ Your payment for *{course_title}* has been rejected. Please contact support for assistance or try again.",
                    reply_markup=menu_keyboard(user_id),
                    parse_mode="Markdown",
                )
                logger.info(f"Notification sent to user {user_id} about rejected payment")
            else:
                logger.error(f"Could not register user {user_id} for notification")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

        # Update admin message
        try:
            await callback.message.edit_caption(
                callback.message.caption + "\n\n❌ Rejected",
                reply_markup=None,
            )
            logger.info(f"Updated admin message for payment {payment_id}")
        except Exception as e:
            logger.error(f"Failed to update admin message: {e}")
        
        await callback.answer("Payment rejected successfully")

    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        await callback.answer("Error processing rejection", show_alert=True)
