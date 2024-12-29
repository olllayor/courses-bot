# handlers/lessons.py
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from data.api_client import APIClient
from keyboards.lessons_keyboard import create_lessons_keyboard
from keyboards.back_button import back_to_lessons
from states.mentor_state import LessonState
from utils.state_utils import get_course_id
import logging
from loader import i18n

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.in_(["📖 Lessons", "📖 Darslar"]))
async def list_lessons(message: Message, state: FSMContext, api_client: APIClient):
    """Display available lessons in a keyboard"""
    try:
        course_id = await get_course_id(state)
        if not course_id:
            await message.answer("Please select a course first.")
            return

        await message.answer(i18n.get_text(message.from_user.id, "fetching_lessons"))

        # Fetch lessons from the API
        lessons = await api_client.get_lessons_by_course_id(
            course_id=course_id,
            telegram_id=message.from_user.id,
        )

        if not lessons:
            await message.answer(i18n.get_text(message.from_user.id, "no_lessons_available"))
            return

        # Create a keyboard with lesson titles
        keyboard = create_lessons_keyboard(lessons, user_id=message.from_user.id)

        # Send the keyboard to the user
        await message.answer(
            i18n.get_text(message.from_user.id, "available_lessons"),
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error listing lessons: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


@router.message(F.text.startswith("📖"))
async def handle_lesson_selection(message: Message, state: FSMContext, api_client: APIClient):
    """Handle lesson selection and display details"""
    try:
        course_id = await get_course_id(state)
        if not course_id:
            await message.answer("Please select a course first.")
            return

        # Extract the lesson title from the button text
        lesson_title = message.text.replace("📖 ", "").strip()

        # Fetch lessons from the API
        lessons = await api_client.get_lessons_by_course_id(
            course_id=course_id,
            telegram_id=message.from_user.id,
        )

        # Find the selected lesson
        selected_lesson = next(
            (lesson for lesson in lessons if lesson["title"] == lesson_title),
            None,
        )

        if not selected_lesson:
            await message.answer(i18n.get_text(message.from_user.id, "lesson_not_found"))
            return

        # Display lesson details
        lesson_details = (
            f"📖 *{selected_lesson['title']}*\n"
            f"📝 {i18n.get_text(message.from_user.id, 'content')}: {selected_lesson.get('content', i18n.get_text(message.from_user.id, 'no_content_available'))}"
        )

        await message.answer(
            lesson_details,
            parse_mode="Markdown",
            reply_markup=back_to_lessons(user_id=message.from_user.id),
        )

    except Exception as e:
        logger.error(f"Error handling lesson selection: {e}")
        await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


@router.message(F.text.in_(["⬅️ Darslarga qaytish", "⬅️ Back to Lessons"]))
async def handle_back_to_lessons(message: Message, state: FSMContext, api_client: APIClient):
    """Handle the back button and return to the lesson list"""
    await list_lessons(message, state, api_client)