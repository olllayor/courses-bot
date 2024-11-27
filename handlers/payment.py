from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import aiohttp
from data.api_client import APIClient
from keyboards.payment_keyboard import (
    create_screenshot_keyboard,
    admin_confirmation_keyboard
)
from states.payment_state import PaymentState
from loader import bot
import logging
import os
from dotenv import load_dotenv

load_dotenv()

router = Router()
api_client = APIClient()

# Convert ADMIN_IDS string to list of integers
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_ID', '').split(',')]
CARD_NUMBER = os.getenv('CARD_NUMBER')
CARD_OWNER = os.getenv('CARD_OWNER')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.message(F.text.in_(["💳 Payment", "💳 To'lov"]))
async def show_payment_details(message: Message, state: FSMContext):
    """Show payment details and ask for screenshot"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    if not course_id:
        await message.answer("Please select a course first.")
        return
    
    try:
        # Check if user has already purchased the course
        has_purchased = await api_client.check_user_purchase(message.from_user.id, course_id)
        if has_purchased:
            await message.answer("You have already purchased this course!")
            return
            
        course = await api_client.get_course_by_id(course_id)
        if not course:
            await message.answer("Course not found.")
            return
            
        # Create payment record
        payment = await api_client.create_payment(
            student_id=message.from_user.id,
            course_id=course_id,
            amount=course['price']
        )
        
        if not payment:
            await message.answer("Error creating payment record. Please try again later.")
            return
            
        # Store payment ID in state
        await state.update_data(payment_id=payment['id'])
            
        await message.answer(
            f"To purchase {course['title']}, please transfer {course['price']} UZS to:\n\n"
            f"Card Number: {CARD_NUMBER}\n"
            f"Card Owner: {CARD_OWNER}\n\n"
            "After payment, please send a screenshot of your payment confirmation.\n\n"
            "⚠️ Important: Make sure your screenshot clearly shows:\n"
            "• Transaction amount\n"
            "• Date and time\n"
            "• Transaction ID/reference number",
            reply_markup=create_screenshot_keyboard()
        )
        await state.set_state(PaymentState.AWAITING_SCREENSHOT)
        
    except Exception as e:
        logger.error(f"Error showing payment details: {e}")
        await message.answer("An error occurred. Please try again later.")

@router.message(PaymentState.AWAITING_SCREENSHOT)
async def handle_screenshot(message: Message, state: FSMContext):
    """Handle payment screenshot submission"""
    if not message.photo:
        await message.answer("Please send a screenshot image of your payment.")
        return

    try:
        data = await state.get_data()
        payment_id = data.get('payment_id')
        
        # Get the largest photo size
        photo = message.photo[-1]
        
        # Update payment with screenshot
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{api_client.base_url}/payments/{payment_id}/save_screenshot/",
                json={'file_id': photo.file_id}
            ) as response:
                response.raise_for_status()

        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_photo(
                    admin_id,
                    photo.file_id,
                    caption=f"New payment screenshot\nPayment ID: {payment_id}"
                )
                # Add confirm/reject buttons
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_{payment_id}"),
                        InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{payment_id}")
                    ]
                ])
                await bot.send_message(admin_id, "Please verify the payment:", reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        await message.answer("Thank you! Your payment is being verified by administrators.")
        await state.clear()

    except Exception as e:
        logger.error(f"Error handling screenshot: {e}")
        await message.answer("Error processing your screenshot. Please try again.")

@router.callback_query(F.data.startswith(("confirm_", "reject_")))
async def handle_admin_verification(callback: CallbackQuery):
    """Handle admin payment verification"""
    try:
        action, payment_id = callback.data.split('_')
        payment_id = int(payment_id)
        
        # Update payment status
        async with aiohttp.ClientSession() as session:
            endpoint = f"{api_client.base_url}/payments/{payment_id}/"
            action_endpoint = f"{endpoint}confirm/" if action == "confirm" else f"{endpoint}cancel/"
            
            async with session.post(action_endpoint) as response:
                response.raise_for_status()
                payment = await response.json()

        # Notify user
        message = "Your payment has been confirmed! You now have access to the course." if action == "confirm" \
                 else "Your payment was rejected. Please contact support."
                 
        await bot.send_message(payment['student'], message)
        await callback.answer("Payment status updated")

    except Exception as e:
        logger.error(f"Error in admin verification: {e}")
        await callback.answer("Error updating payment status")