# handlers/courses.py
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from data.api_client import APIClient
from keyboards.courses_keyboard import create_courses_keyboard
from keyboards.back_button import back_to_courses
from keyboards.menu import menu_keyboard
from states.mentor_state import CourseState
from loader import i18n
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.in_(["📚 Courses", "📚 Kurslar"]))
async def list_courses(message: Message, state: FSMContext, api_client: APIClient):
    """Display available courses in a keyboard"""
    await message.answer(i18n.get_text(message.from_user.id, "coming_soon"),
                         reply_markup=menu_keyboard(user_id=message.from_user.id))
#     try:
#         await message.answer(i18n.get_text(message.from_user.id, "fetching_courses"))

#         # Fetch courses from the API
#         courses = await api_client.get_courses_by_mentor_id(
#             telegram_id=message.from_user.id
#         )

#         if not courses:
#             await message.answer(
#                 i18n.get_text(message.from_user.id, "no_courses_available")
#             )
#             return

#         # Create a keyboard with course titles
#         keyboard = create_courses_keyboard(courses, user_id=message.from_user.id)

#         # Send the keyboard to the user
#         await message.answer(
#             i18n.get_text(message.from_user.id, "available_courses"),
#             reply_markup=keyboard,
#         )

#     except Exception as e:
#         logger.error(f"Error listing courses: {e}")
#         await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))


# # handlers/courses.py
# @router.message(F.text.startswith("📚"))
# async def handle_course_selection(
#     message: Message, state: FSMContext, api_client: APIClient
# ):
#     """Handle course selection and display details"""
#     try:
#         # Extract the course title from the button text
#         course_title = message.text.replace("📚 ", "").strip()

#         # Fetch courses from the API
#         courses = await api_client.get_courses_by_mentor_id(
#             telegram_id=message.from_user.id
#         )

#         # Find the selected course
#         selected_course = next(
#             (course for course in courses if course["title"] == course_title),
#             None,
#         )

#         if not selected_course:
#             await message.answer(
#                 i18n.get_text(message.from_user.id, "course_not_found")
#             )
#             return

#         # Store course_id in state
#         await state.update_data(course_id=selected_course["id"])

#         # Display course details
#         course_details = (
#             f"📚 *{selected_course['title']}*\n"
#             f"🧑‍🏫 {i18n.get_text(message.from_user.id, 'mentor')}: {selected_course['mentor']['name']}\n"
#             f"💰 {i18n.get_text(message.from_user.id, 'price')}: UZS{float(selected_course['price']):,.2f}\n"
#             f"📝 {i18n.get_text(message.from_user.id, 'description')}: {selected_course.get('description', i18n.get_text(message.from_user.id, 'no_description_available'))}"
#         )

#         await message.answer(
#             course_details,
#             parse_mode="Markdown",
#             reply_markup=back_to_courses(user_id=message.from_user.id),
#         )

#     except Exception as e:
#         logger.error(f"Error handling course selection: {e}")
#         await message.answer(i18n.get_text(message.from_user.id, "error_occurred"))
