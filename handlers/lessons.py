# handlers/lessons.py
import logging
import os

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dotenv import load_dotenv

from data.api_client import APIClient
from handlers.mentors import get_mentor_id
from handlers.payment import initiate_course_payment
from keyboards.lessons_keyboard import create_lessons_keyboard
from keyboards.payment_keyboard import (create_payment_keyboard,
                                        create_screenshot_keyboard)
from loader import bot, i18n
from states.mentor_state import CourseState, LessonState
from states.payment_state import PaymentState

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
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        
        # Ensure user exists before proceeding
        if not await api_client.ensure_user_exists(telegram_id=user_id, name=user_name):
            logger.error(f"Failed to register user {user_id}")
            await message.answer("Registration failed. Please try /start again.")
            return
            
        course = await api_client.get_course_by_id(course_id, telegram_id=user_id)
        if not course:
            await message.answer("Course not found.")
            return

        lessons = course.get("lessons", [])
        logger.info(f"Available lessons: {lessons}")

        if not lessons:
            await message.answer("No lessons available for this course yet.")
            return

        # Check if user has purchased the course
        has_purchased = await api_client.check_user_purchase(
            user_id, course_id
        )
        logger.info(f"User has purchased the course: {has_purchased}")

        # Create keyboard with lessons and user_id
        keyboard = await create_lessons_keyboard(
            lessons, user_id, has_purchased
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
    try:
        course_id = await get_course_id(state)
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        
        logger.info(f"Handling lesson selection for user {user_id}, course {course_id}")

        if not course_id:
            logger.error(f"No course_id found in state for user {user_id}")
            await message.answer("Please select a course first.")
            return

        # Try to get course details
        course = await api_client.get_course_by_id(course_id, telegram_id=user_id)
        if not course:
            logger.error(f"Failed to fetch course {course_id} for user {user_id}")
            await message.answer("Course not found or cannot be accessed right now. Please try again later.")
            return

        # Clean message text by removing icons for comparison
        clean_title = message.text.replace("🆓 ", "").replace("🔒 ", "").replace("📖 ", "").strip()
        
        # Find matching lesson
        selected_lesson = None
        for lesson in course.get("lessons", []):
            if lesson["title"].lower() == clean_title.lower():
                selected_lesson = lesson
                break
                
        if not selected_lesson:
            logger.error(f"User {user_id} selected invalid lesson: '{clean_title}'")
            await message.answer("Please select a valid lesson from the list.")
            return

        # Store the selected lesson ID in state
        await state.update_data(lesson_id=selected_lesson["id"])
        logger.info(f"User {user_id} selected lesson {selected_lesson['id']} - {selected_lesson['title']}")

        # Check if the lesson is free first
        if selected_lesson.get("is_free", False):
            logger.info(f"Serving free lesson {selected_lesson['id']} to user {user_id}")
            await serve_lesson_content(message, selected_lesson)
            return
            
        # Try to check purchase status
        logger.info(f"Checking purchase status for user {user_id}, course {course_id}")
        has_purchased = await api_client.check_user_purchase(
            user_id, 
            course_id,
            name=user_name
        )
        
        logger.info(f"User {user_id} ({user_name}) has purchased: {has_purchased}, Lesson is free: {selected_lesson.get('is_free', False)}")
        
        if has_purchased:
            # User has purchased, send the lesson content
            await serve_lesson_content(message, selected_lesson)
        else:
            # Initiate payment flow for premium content
            logger.info(f"Initiating payment flow for user {user_id}, course {course_id}")
            success = await initiate_course_payment(message, state, course)
            if success:
                logger.info(f"Payment flow initiated successfully for user {user_id}")
            else:
                logger.error(f"Failed to initiate payment flow for user {user_id}")
                await message.answer("There was an error processing your payment request. Please try again later.")

    except Exception as e:
        logger.error(f"Error handling lesson selection for user {message.from_user.id}: {e}")
        await message.answer("An error occurred while accessing the lesson. Please try again later.")

async def serve_lesson_content(message: Message, lesson: dict):
    """Helper function to serve lesson content to user"""
    try:
        if lesson.get("telegram_video_id"):
            await message.answer_video(
                video=lesson["telegram_video_id"],
                caption=f"*{lesson['title']}*\n\n{lesson['content']}",
                parse_mode=ParseMode.MARKDOWN,
                protect_content=True
            )
        else:
            await message.answer(
                f"*{lesson['title']}*\n\n{lesson['content']}",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as content_error:
        logger.error(f"Error sending lesson content: {content_error}")
        # Fallback to text-only if video fails
        await message.answer(
            f"*{lesson['title']}*\n\n{lesson['content']}",
            parse_mode=ParseMode.MARKDOWN
        )