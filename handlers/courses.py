# courses.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums import ParseMode
import logging
from keyboards.mentors_keyboard import mentor_courses, mentor_keyboard
from loader import i18n
from handlers.mentors import get_mentor_id
from keyboards.lessons_keyboard import create_lessons_keyboard
from data.api_client import APIClient
from states.mentor_state import CourseState, LessonState

router = Router()
api_client = APIClient()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.message(F.text.in_(["📚 Courses", "📚 Kurslar"]))
async def courses(message: Message, state: FSMContext):
    """Handler to display available courses for the selected mentor"""
    try:
        mentor_id = await get_mentor_id(state)
        logger.info(f"Fetching courses for mentor_id: {mentor_id}")

        if not mentor_id:
            await message.answer("Please select a mentor first.")
            return

        courses = await api_client.get_courses_by_mentor_id(mentor_id)
        if not courses:
            await message.answer("No courses available at the moment.")
            return
        
        # Format courses list message
        courses_list = "\n\n".join([
            f"📚 *{course['title']}*\n" + 
            f"💰 Price: UZS{float(course['price']):,.2f}"
            for course in courses
        ])
        
        await state.set_state(CourseState.Course_ID)
        await message.answer(
            f"*Available Courses:*\n\n{courses_list}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await mentor_courses(courses)
        )
        
    except Exception as e:
        logger.error(f"Error in courses handler: {e}")
        await message.answer("An error occurred while fetching courses.")

@router.message(CourseState.Course_ID)
async def handle_course_selection(message: Message, state: FSMContext):
    """Handler for when user selects a specific course"""
    try:
        mentor_id = await get_mentor_id(state)
        logger.info(f"Processing course selection for mentor_id: {mentor_id}")

        if not mentor_id:
            await message.answer("Please select a mentor first.")
            return

        courses = await api_client.get_courses_by_mentor_id(mentor_id)
        if not courses:
            await message.answer("No courses available.")
            return

        message_text = message.text.lower().strip()
        
        # Handle back button
        # if message_text == "⬅️ back to mentors":
        #     await state.clear()
        #     await message.answer(
        #         "Returning to mentors list",
        #         reply_markup=await mentor_keyboard()
        #     )
        #     return

        selected_course = next(
            (course for course in courses 
             if course['title'].lower().strip() == message_text),
            None
        )

        if not selected_course:
            logger.warning(f"Invalid course selection: {message.text}")
            await message.answer("Please select a valid course from the list.")
            return

        # Update state with course_id
        await state.update_data(course_id=selected_course['id'])
        logger.info(f"Course selected: {selected_course['id']}")

        # Get course lessons
        course = await api_client.get_course_by_id(selected_course['id'])
        lessons = course.get('lessons', [])

        logger.info(f"Course lessons: {lessons}")
        # Format course details and lessons list
        course_details = (
            f"📚 *{selected_course['title']}*\n\n"
            f"💰 Price: UZS{float(selected_course['price']):,.2f}\n"
            f"📝 Description:\n{selected_course['description']}\n\n"
            f"*Available Lessons:*"
        )

        # Show course details first
        await message.answer(
            course_details,
            parse_mode=ParseMode.MARKDOWN
        )

        if not lessons:
            await message.answer("No lessons available for this course yet.")
            return

        # Show lessons list
        lessons_list = "\n\n".join([
            f"{'🆓' if lesson['is_free'] else '🔒'} *{lesson['title']}*"
            for lesson in lessons
        ])

        logger.info(f"Lessons list: {lessons_list}")

        # Create keyboard for lessons
        keyboard = await create_lessons_keyboard(lessons, message.from_user.id)
        
        await state.set_state(LessonState.Lesson_ID)
        await message.answer(
            lessons_list,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error in course selection handler: {e}")
        await message.answer("An error occurred while processing your selection.")
