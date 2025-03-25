# handlers/lessons.py
import logging
import os
import json

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from data.api_client import APIClient
from handlers.payment import initiate_course_payment
from keyboards.lessons_keyboard import create_lessons_keyboard
from states.mentor_state import CourseState, LessonState

from .quizzes import create_quiz_keyboard

load_dotenv()

router = Router()
api_client = APIClient()

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_ID", "").split(",")]
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
        has_purchased = await api_client.check_user_purchase(user_id, course_id)
        logger.info(f"User has purchased the course: {has_purchased}")

        # Create keyboard with lessons and user_id
        keyboard = await create_lessons_keyboard(lessons, user_id, has_purchased)

        # Show lessons list with indication of free/premium status
        lesson_list = "\n\n".join(
            [
                f"📚 *{lesson['title']}*\n"
                + (
                    "🆓 Free Lesson"
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
            await message.answer(
                "Course not found or cannot be accessed right now. Please try again later."
            )
            return

        # Clean message text by removing icons for comparison
        clean_title = (
            message.text.replace("🆓 ", "")
            .replace("🔒 ", "")
            .replace("📖 ", "")
            .strip()
        )

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
        lesson_id = selected_lesson["id"]
        await state.update_data(lesson_id=lesson_id)
        logger.info(
            f"User {user_id} selected lesson {lesson_id} - {selected_lesson['title']}"
        )

        # Check if the lesson is free first
        if selected_lesson.get("is_free", False):
            logger.info(f"Serving free lesson {lesson_id} to user {user_id}")
            await display_lesson(message, lesson_id, user_id, True)
            return

        # Try to check purchase status
        logger.info(f"Checking purchase status for user {user_id}, course {course_id}")
        has_purchased = await api_client.check_user_purchase(
            user_id, course_id, name=user_name
        )

        logger.info(
            f"User {user_id} ({user_name}) has purchased: {has_purchased}, "
            f"Lesson is free: {selected_lesson.get('is_free', False)}"
        )

        if has_purchased:
            # User has purchased, display the lesson content
            await display_lesson(message, lesson_id, user_id, has_purchased)
        else:
            # Initiate payment flow for premium content
            logger.info(
                f"Initiating payment flow for user {user_id}, course {course_id}"
            )
            success = await initiate_course_payment(message, state, course)
            if success:
                logger.info(f"Payment flow initiated successfully for user {user_id}")
            else:
                logger.error(f"Failed to initiate payment flow for user {user_id}")
                await message.answer(
                    "There was an error processing your payment request. Please try again later."
                )

    except Exception as e:
        logger.error(
            f"Error handling lesson selection for user {message.from_user.id}: {e}"
        )
        await message.answer(
            "An error occurred while accessing the lesson. Please try again later."
        )


async def serve_lesson_content(message: Message, lesson: dict):
    """Helper function to serve lesson content to user"""
    try:
        if lesson.get("telegram_video_id"):
            await message.answer_video(
                video=lesson["telegram_video_id"],
                caption=f"*{lesson['title']}*\n\n{lesson['content']}",
                parse_mode=ParseMode.MARKDOWN,
                protect_content=True,
            )
        else:
            await message.answer(
                f"*{lesson['title']}*\n\n{lesson['content']}",
                parse_mode=ParseMode.MARKDOWN,
            )
        
        return True
    except Exception as content_error:
        logger.error(f"Error sending lesson content: {content_error}")
        # Fallback to text-only if video fails
        await message.answer(
            f"*{lesson['title']}*\n\n{lesson['content']}", parse_mode=ParseMode.MARKDOWN
        )
        return True


async def display_lesson(message_or_callback, lesson_id, user_id, has_purchased):
    """Display a lesson and its video to the user"""
    try:
        # Fetch the lesson details
        lesson = await api_client.make_request(
            "GET", f"{api_client.base_url}/lessons/{lesson_id}/"
        )
        
        if not lesson:
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer("Lesson not found or cannot be accessed.")
                await message_or_callback.answer()
            else:
                await message_or_callback.answer("Lesson not found or cannot be accessed.")
            return False
        
        # Check if user can access this lesson (either free or purchased)
        if not (has_purchased or lesson.get("is_free", False)):
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(
                    "You need to purchase this course to access this lesson."
                )
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(
                    "You need to purchase this course to access this lesson."
                )
            return False
            
        # Serve the lesson content
        if isinstance(message_or_callback, CallbackQuery):
            await serve_lesson_content(message_or_callback.message, lesson)
        else:
            await serve_lesson_content(message_or_callback, lesson)
        
        # Check if this lesson has associated quizzes
        if lesson.get("quizzes"):
            # Add a Quiz button to the keyboard
            quiz_keyboard = create_quiz_keyboard(lesson_id)
            
            # Send message with quiz keyboard
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.answer(
                    "Want to test your knowledge? Take the quiz for this lesson!",
                    reply_markup=quiz_keyboard,
                )
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(
                    "Want to test your knowledge? Take the quiz for this lesson!",
                    reply_markup=quiz_keyboard,
                )
            
        return True
        
    except Exception as e:
        logger.error(f"Error displaying lesson {lesson_id} to user {user_id}: {e}")
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(
                "An error occurred while displaying the lesson. Please try again later."
            )
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(
                "An error occurred while displaying the lesson. Please try again later."
            )
        return False


# Add this import at the top if not already present
import re

# Update your existing back_to_lessons_handler with a more flexible matcher
# Instead of using lambda c: c.data == "back_to_lessons", use a regex pattern that's more flexible
@router.callback_query(lambda c: c.data and (c.data == "back_to_lessons" or re.match(r"back_to_lessons(_\w+)?", c.data)))
async def back_to_lessons_handler(callback: CallbackQuery, state: FSMContext):
    try:
        # Clear quiz state if it exists
        await state.clear()
        
        # Get course ID
        course_id = await get_course_id(state)
        if not course_id:
            await callback.message.answer("Please select a course first.")
            await callback.answer()
            return

        user_id = callback.from_user.id
        user_name = callback.from_user.full_name
        
        logger.info(f"Handling back_to_lessons for user {user_id}, course {course_id}")

        # Redirect to show_lessons function logic
        course = await api_client.get_course_by_id(course_id, telegram_id=user_id)
        if not course:
            await callback.message.answer("Course not found.")
            await callback.answer()
            return

        lessons = course.get("lessons", [])
        if not lessons:
            await callback.message.answer("No lessons available for this course yet.")
            await callback.answer()
            return

        # Check if user has purchased the course
        has_purchased = await api_client.check_user_purchase(user_id, course_id)
        logger.info(f"User has purchased course: {has_purchased}")
        
        # Create keyboard with lessons and user_id
        keyboard = await create_lessons_keyboard(lessons, user_id, has_purchased)

        # Show lessons list with indication of free/premium status
        lesson_list = "\n\n".join(
            [
                f"📚 *{lesson['title']}*\n"
                + (
                    "🆓 Free Lesson"
                    if lesson["is_free"]
                    else "📖 Lesson" if has_purchased else "🔒 Premium Lesson"
                )
                for lesson in lessons
            ]
        )

        await callback.message.answer(
            f"*Available Lessons:*\n\n{lesson_list}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

        await state.set_state(LessonState.Lesson_ID)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling back to lessons: {e}")
        await callback.message.answer(
            "An error occurred. Please try again later."
        )
        await callback.answer()

# Add a debug handler to catch and log all unhandled callbacks
@router.callback_query()
async def debug_unhandled_callback(callback: CallbackQuery):
    """Debug handler to log unhandled callbacks"""
    logger.warning(f"Unhandled callback with data: {callback.data}")
    # Don't answer this callback to let other routers handle it if possible
    # If no other handler processes it, it will stay as "unhandled"