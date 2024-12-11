from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.db import fetch_mentor_details, fetch_mentors
from data.api_client import APIClient
from loader import i18n
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
api_client = APIClient()


# Utility: Create rows of buttons
def create_button_rows(
    items: List[str], row_width: int = 2
) -> List[List[KeyboardButton]]:
    """
    Creates button rows for keyboards.

    Args:
        items: List of item names or texts for buttons.
        row_width: Number of buttons per row.

    Returns:
        A list of rows (each row is a list of KeyboardButton).
    """
    rows = []
    row = []
    for item in items:
        row.append(KeyboardButton(text=item))
        if len(row) == row_width:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


# Mentor List Keyboard
async def mentor_keyboard(telegram_id: int = None) -> ReplyKeyboardMarkup:
    """Creates a keyboard to display all mentors."""
    try:
        if not telegram_id:
            logger.error("telegram_id is required for mentor_keyboard")
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⚠️ Authentication required")]],
                resize_keyboard=True
            )

        mentors = await api_client.get_mentors(telegram_id=telegram_id)
        
        if not mentors:
            logger.warning("No mentors found")
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="No mentors available")]],
                resize_keyboard=True
            )

        mentor_names = [mentor["name"] for mentor in mentors]
        buttons = create_button_rows(mentor_names)
        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )
    except Exception as e:
        logger.error(f"Error creating mentor keyboard: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching mentors")]],
            resize_keyboard=True
        )


# Mentor Booking Keyboard
async def mentor_booking_keyboard(mentor_name: str) -> Optional[ReplyKeyboardMarkup]:
    """
    Creates a keyboard for mentor booking based on their availability.

    Args:
        mentor_name: Name of the mentor.

    Returns:
        ReplyKeyboardMarkup or None if no slots are available.
    """
    try:
        mentor = await fetch_mentor_details(mentor_name)
        if not mentor or not mentor.get("availability"):
            return None

        available_slots = [
            f"{slot['start_time'].split('T')[1][:5]} - {slot['end_time'].split('T')[1][:5]} ({slot['start_time'].split('T')[0]})"
            for slot in mentor["availability"]
            if slot.get("is_available")
        ]
        if not available_slots:
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="No available slots")]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )

        buttons = create_button_rows(available_slots)
        return ReplyKeyboardMarkup(
            keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
        )
    except Exception as e:
        print(f"Error creating booking keyboard for {mentor_name}: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching slots")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )


# Mentor Menu Keyboard
async def mentors_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Creates a menu keyboard for mentor-related actions.

    Args:
        user_id: Telegram user ID to localize text.

    Returns:
        ReplyKeyboardMarkup with mentor actions.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get_text(user_id, "course") or "📚 Courses")],
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "schedule_meeting")
                    or "⏳ Schedule Meeting"
                )
            ],
            [KeyboardButton(text=i18n.get_text(user_id, "payment") or "💳 Payment")],
        ],
        resize_keyboard=True,
    )


# Courses Keyboard
async def mentor_courses(courses: List[Dict]) -> ReplyKeyboardMarkup:
    """
    Creates a keyboard to display mentor's courses.

    Args:
        courses: List of course dictionaries with titles.

    Returns:
        ReplyKeyboardMarkup with course titles as buttons.
    """
    try:
        course_titles = [course["title"] for course in courses]
        buttons = create_button_rows(course_titles)
        return ReplyKeyboardMarkup(
            keyboard=buttons, resize_keyboard=True, one_time_keyboard=True
        )
    except Exception as e:
        print(f"Error creating course keyboard: {e}")
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚠️ Error fetching courses")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )


# Lessons Menu Keyboard
async def lessons_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Creates a keyboard for lessons menu.

    Args:
        user_id: Telegram user ID to localize text.

    Returns:
        ReplyKeyboardMarkup with lessons-related actions.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "lessons_in_menu") or "📚 Lessons"
                )
            ],
            [KeyboardButton(text=i18n.get_text(user_id, "payment") or "💳 Payment")],
            [
                KeyboardButton(
                    text=i18n.get_text(user_id, "back_button") or "⬅️ Back to Courses"
                )
            ],
        ],
        resize_keyboard=True,
    )
