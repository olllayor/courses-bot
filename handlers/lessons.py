# lessons.py
import os
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
import logging

from keyboards.payment_keyboard import (
    create_payment_keyboard,
    create_screenshot_keyboard,
)
from loader import i18n, bot
from handlers.mentors import get_mentor_id
from keyboards.lessons_keyboard import create_lessons_keyboard
from data.api_client import APIClient
from states.mentor_state import LessonState, CourseState
from states.payment_state import PaymentState
from dotenv import load_dotenv

load_dotenv()

router = Router()
api_client = APIClient()

ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_ID', '').split(',')]
CARD_NUMBER = os.getenv("CARD_NUMBER")
CARD_OWNER = os.getenv("CARD_OWNER")

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_course_id(state: FSMContext) -> int:
    """Helper function to get course_id from state"""
    data = await state.get_data()
    course_id = data.get("course_id")
    logger.info(f"Current course_id: {course_id}")
    return course_id

@router.message(CourseState.Course_ID, F.text.in_(["📖 Lessons", "📖 Darslar"]))
async def show_lessons(message: Message, state: FSMContext):
    """Handler to display available lessons for the selected course"""
    course_id = await get_course_id(state)
    if not course_id:
        await message.answer("Please select a course first.")
        return

    try:
        course = await api_client.get_course_by_id(course_id)
        if not course:
            await message.answer("Course not found.")
            return

        lessons = course.get("lessons", [])
        if not lessons:
            await message.answer("No lessons available for this course yet.")
            return

        # Check if user has purchased the course
        has_purchased = await api_client.check_user_purchase(
            message.from_user.id, course_id
        )

        # Create keyboard with lessons and user_id
        keyboard = await create_lessons_keyboard(
            lessons, message.from_user.id, has_purchased
        )

        # Show lessons list with indication of free/premium status
        lesson_list = "\n\n".join(
            [
                f"📚 *{lesson['title']}*\n"
                + (
                    f"🆓 Free Lesson"
                    if lesson["is_free"]
                    else "📖 Lesson" if has_purchased else "🔒 Premium Lesson"
                )
                for lesson in lessons
            ]
        )

        await message.answer(
            f"*Available Lessons:*\n\n{lesson_list}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

        await state.set_state(LessonState.Lesson_ID)

    except Exception as e:
        logger.error(f"Error showing lessons: {e}")
        await message.answer(
            "An error occurred while fetching the lessons. Please try again later."
        )

@router.message(LessonState.Lesson_ID)
async def handle_lesson_selection(message: Message, state: FSMContext):
    """Handle when user selects a specific lesson"""
    course_id = await get_course_id(state)
    if not course_id:
        await message.answer("Please select a course first.")
        return

    try:
        course = await api_client.get_course_by_id(course_id)
        if not course:
            await message.answer("Course not found.")
            return

        # Remove emoji prefix when matching lesson titles
        lesson_title = (
            message.text.split(" ", 1)[1]
            if "🆓" in message.text or "🔒" in message.text
            else message.text
        )
        
        selected_lesson = next(
            (
                lesson
                for lesson in course["lessons"]
                if lesson["title"].lower() == lesson_title.lower()
            ),
            None,
        )

        if not selected_lesson:
            return  # Silent return for invalid selections

        # Save selected lesson ID in state
        await state.update_data(lesson_id=selected_lesson["id"])

        # Check if user has purchased the course
        has_purchased = await api_client.check_user_purchase(
            message.from_user.id, course_id
        )

        # Show lesson content if it's free or user has purchased
        if selected_lesson["is_free"] or has_purchased:
            if selected_lesson.get("telegram_video_id"):
                try:
                    await message.answer_video(
                        video=selected_lesson["telegram_video_id"],
                        caption=f"*{selected_lesson['title']}*\n\n{selected_lesson['content']}",
                        parse_mode=ParseMode.MARKDOWN,
                        protect_content=True,
                    )
                except Exception as e:
                    logger.error(f"Error sending video: {e}")
                    await message.answer("Error playing video. Please try again later.")
            else:
                await message.answer(
                    f"*{selected_lesson['title']}*\n\n{selected_lesson['content']}",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            # Show purchase prompt for premium lessons
            await message.answer(
                "This is a premium lesson. Please purchase the course to access this content.",
                reply_markup=await create_payment_keyboard(
                    course_id, price=course["price"], user_id=message.from_user.id
                ),
            )

    except Exception as e:
        logger.error(f"Error handling lesson selection: {e}")
        await message.answer(
            "An error occurred while processing your selection. Please try again later."
        )

@router.callback_query(F.data.startswith("pay_"))
async def handle_payment(callback: CallbackQuery, state: FSMContext):
    """Handle payment callback query"""
    try:
        # Validate callback data
        parts = callback.data.split("_")
        logger.info(f"{parts}")
        if len(parts) != 3:
            await callback.answer("Invalid payment data", show_alert=True)
            return

        _, course_id, user_id = parts
        try:
            course_id, user_id = int(course_id), int(user_id)
        except ValueError:
            await callback.answer("Invalid payment data", show_alert=True)
            return

        logger.info(f"User {user_id} is purchasing course {course_id}")

        # Get course details
        course = await api_client.get_course_by_id(course_id)
        if not course:
            await callback.answer("Course not found", show_alert=True)
            return

        # Check purchase status
        has_purchased = await api_client.check_user_purchase(user_id, course_id)
        if has_purchased:
            await callback.answer(
                "You have already purchased this course.", show_alert=True
            )
            return

        try:
            # Create payment record
            payment = await api_client.create_payment(
                student_id=user_id,
                course_id=course_id,
                amount=float(course['price'])
            )
            
            
            if not payment:
                logger.error(f"Failed to create payment for user {user_id} and course {course_id}")
                await callback.answer("Error creating payment record", show_alert=True)
                return

            payment_id = payment.get('id')
            if not payment_id:
                logger.error(f"Payment created but no ID returned: {payment}")
                await callback.answer("Error processing payment", show_alert=True)
                return

            logger.info(f"Created payment with ID {payment_id} for user {user_id}")
            
            # Save course and payment data to state
            await state.update_data(
                course_id=course_id,
                payment_id=payment_id
            )

            # Send payment prompt
            await callback.message.answer(
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
            logger.error(f"Error creating payment record: {e}")
            await callback.answer("Error processing payment", show_alert=True)
            return

    except Exception as e:
        logger.error(f"Error handling payment: {e}", exc_info=True)
        await callback.answer("Error processing payment", show_alert=True)