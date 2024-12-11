# handlers/lessons.py
import os
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
import logging

from handlers.payment import initiate_course_payment
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
        course = await api_client.get_course_by_id(course_id, telegram_id=message.from_user.id)
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
            message.from_user.id, course_id
        )
        logger.info(f"User has purchased the course: {has_purchased}")

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
    try:
        course_id = await get_course_id(state)
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        course = await api_client.get_course_by_id(course_id, telegram_id=user_id)
        if not course:
            await message.answer("Course not found.")
            return

        clean_title = message.text.replace("🆓 ", "").replace("🔒 ", "").strip()
        selected_lesson = next(
            (lesson for lesson in course["lessons"] 
             if lesson["title"].lower() == clean_title.lower()),
            None
        )

        if not selected_lesson:
            await message.answer("Please select a valid lesson.")
            return

        await state.update_data(lesson_id=selected_lesson["id"])

        has_purchased = await api_client.check_user_purchase(
            user_id, 
            course_id,
            name=user_name
        )
        
        if selected_lesson["is_free"] or has_purchased:
            # Send lesson content
            if selected_lesson.get("telegram_video_id"):
                await message.answer_video(
                    video=selected_lesson["telegram_video_id"],
                    caption=f"*{selected_lesson['title']}*\n\n{selected_lesson['content']}",
                    parse_mode=ParseMode.MARKDOWN,
                    protect_content=True
                )
            else:
                await message.answer(
                    f"*{selected_lesson['title']}*\n\n{selected_lesson['content']}",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            # Initiate payment flow
            await initiate_course_payment(message, state, course)

    except Exception as e:
        logger.error(f"Error handling lesson: {e}")
        await message.answer("An error occurred. Please try again.")