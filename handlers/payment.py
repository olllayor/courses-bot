from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
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

@router.message(PaymentState.AWAITING_SCREENSHOT, F.photo)
async def handle_payment_screenshot(message: Message, state: FSMContext):
    """Handle payment screenshot submission"""
    try:
        data = await state.get_data()
        course_id = data.get("course_id")
        payment_id = data.get("payment_id")

        logger.info(f"Course ID: {course_id}, Payment ID: {payment_id}")    


        if not all([course_id, payment_id]):
            await message.answer("Payment session expired. Please start over.")
            await state.clear()
            return
            
        course = await api_client.get_course_by_id(course_id)
        if not course:
            await message.answer("Course information not found. Please try again.")
            return
        
        logger.info(f"Processing payment screenshot from user {message.from_user.id} for course {course_id}")
        
        # Store the file_id in state for later reference
        await state.update_data(screenshot_file_id=message.photo[-1].file_id)
        
        # Forward screenshot to admins
        admin_msg = (
            f"🔔 New Payment Confirmation\n\n"
            f"👤 User: {message.from_user.full_name}\n"
            f"🆔 User ID: {message.from_user.id}\n"
            f"📚 Course: {course['title']}\n"
            f"💰 Amount: {course['price']} UZS\n"
            f"🆔 Payment ID: {payment_id}"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_photo(
                    chat_id=admin_id,
                    photo=message.photo[-1].file_id,
                    caption=admin_msg,
                    reply_markup=admin_confirmation_keyboard(message.from_user.id, course_id, payment_id)
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")
            
        await message.answer(
            "✅ Thank you! Your payment screenshot has been submitted for verification.\n"
            "We will process it as soon as possible. You will be notified once confirmed."
        )
        await state.set_state(PaymentState.AWAITING_ADMIN_CONFIRMATION)
        
    except Exception as e:
        logger.error(f"Error handling payment screenshot: {e}")
        await message.answer("An error occurred processing your payment. Please try again later.")

@router.callback_query(F.data.startswith(("confirm_payment_", "reject_payment_")))
async def handle_admin_payment_action(callback: CallbackQuery, state: FSMContext):
    """Handle admin's payment confirmation or rejection"""
    try:
        action, user_id, course_id, payment_id = callback.data.split('_')
        user_id, course_id, payment_id = map(int, [user_id, course_id, payment_id])
        
        is_confirm = action == "confirm"
        
        if str(callback.from_user.id) not in ADMIN_IDS:
            await callback.answer("You are not authorized to perform this action.", show_alert=True)
            return
            
        if is_confirm:
            # Update payment status in database
            if await api_client.confirm_payment(payment_id):
                await api_client.add_user_purchase(user_id, course_id)
                
                # Notify user
                await bot.send_message(
                    user_id,
                    "🎉 Your payment has been confirmed!\n"
                    "You now have access to all course materials."
                )
                
                # Update admin message
                await callback.message.edit_caption(
                    callback.message.caption + "\n\n✅ Payment Confirmed",
                    reply_markup=None
                )
            else:
                logger.error(f"Failed to confirm payment {payment_id}")
                await callback.answer("Error confirming payment", show_alert=True)
                return
        else:
            # Handle rejection
            await bot.send_message(
                user_id,
                "❌ Your payment was not approved.\n"
                "Please ensure you've sent the correct amount and try again."
            )
            await callback.message.edit_caption(
                callback.message.caption + "\n\n❌ Payment Rejected",
                reply_markup=None
            )
            
        await callback.answer("Payment processed successfully")
        
    except Exception as e:
        logger.error(f"Error handling admin payment action: {e}")
        await callback.answer("Error processing payment action", show_alert=True)

# Cancel payment handler
@router.message(PaymentState.AWAITING_SCREENSHOT, F.text == "❌ Cancel Payment")
async def cancel_payment(message: Message, state: FSMContext):
    """Handle payment cancellation"""
    try:
        await state.clear()
        await message.answer(
            "Payment cancelled. You can start over when you're ready.",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Error cancelling payment: {e}")
        await message.answer("Error cancelling payment. Please try again.")