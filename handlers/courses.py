# handlers/courses.py
import logging
import click
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from rich.logging import RichHandler

from data.api_client import APIClient  # Import APIClient
from handlers.mentors import get_mentor_id, list_mentors
from keyboards.lessons_keyboard import create_lessons_keyboard
from keyboards.mentors_keyboard import mentor_courses, mentor_keyboard
from states.mentor_state import CourseState, LessonState

router = Router()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Rich logger with Click suppression
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])],
)


@router.message(F.text.in_(["📚 Courses", "📚 Kurslar"]))
async def courses(message: Message, state: FSMContext, api_client: APIClient):
    """Handler to display available courses for the selected mentor"""
    logger.info("Courses handler triggered")
    await message.answer("Fetching courses...")

    #Debug state data
    state_data = await state.get_data()
    logger.info(f"State data: {state_data}")

    try:
        mentor_id = await get_mentor_id(state)
        logger.info(f"Fetching courses for mentor_id: {mentor_id}")

        if not mentor_id:
            logger.warning("No mentor_id found in state")
            await message.answer(
                "Please select a mentor first.", 
                reply_markup=await mentor_keyboard(
                    telegram_id=message.from_user.id, 
                    api_client=api_client
                )
            )
            return

        courses = await api_client.get_courses_by_mentor_id(mentor_id)

        if not courses:
            await message.answer("No courses available at the moment.")
            return

        courses_list = "\n\n".join(
            [
                f"📚 *{course['title']}*\n"
                + f"💰 Price: UZS{float(course['price']):,.2f}"
                for course in courses
            ]
        )

        await state.set_state(CourseState.Course_ID)
        await message.answer(
            f"*Available Courses:*\n\n{courses_list}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await mentor_courses(courses),
        )

    except Exception as e:
        logger.error(f"Error in courses handler: {e}")
        await message.answer("An error occurred while fetching courses.")


@router.message(CourseState.Course_ID)
async def handle_course_selection(message: Message, state: FSMContext, api_client: APIClient):
    try:
        # Handle back button
        if message.text in ["⬅️ Back to Courses", "⬅️ Kurslarga qaytish"]:
            await state.set_state(CourseState.Course_ID)
            return await courses(message, state, api_client)

        mentor_id = await get_mentor_id(state)
        user_id = message.from_user.id

        courses_list = await api_client.get_courses_by_mentor_id(mentor_id)
        if not courses_list:
            await message.answer("No courses available.")
            return

        # Clean message text for comparison
        clean_message = message.text.replace("📚 ", "").strip()

        selected_course = next(
            (
                course
                for course in courses_list
                if course["title"].lower() == clean_message.lower()
            ),
            None,
        )

        if not selected_course:
            await message.answer("Please select a valid course.")
            return

        await state.update_data(course_id=selected_course["id"])

        # Get user's purchase status
        has_purchased = await api_client.check_user_purchase(
            user_id, selected_course["id"]
        )
        logger.info(f"User has purchased: {has_purchased}")

        lessons = selected_course.get("lessons", [])

        if not lessons:
            await message.answer("No lessons available for this course.")
            return

        keyboard = await create_lessons_keyboard(lessons, user_id, has_purchased)

        lessons_list = "\n\n".join(
            [
                f"{'🆓 ' if lesson['is_free'] else '🔒 '}*{lesson['title']}*"
                + (f"\n{'Free Lesson' if lesson['is_free'] else 'Premium Lesson'}")
                for lesson in lessons
            ]
        )

        await message.answer(
            f"*{selected_course['title']}*\n\n{lessons_list}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

        await state.set_state(LessonState.Lesson_ID)

    except Exception as e:
        logger.error(f"Error in course selection: {e}")
        await message.answer("An error occurred. Please try again.")