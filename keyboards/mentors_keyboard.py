# keyboards/mentors_keyboard.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from data.db import show_mentors, show_mentor_availability
from data.api_client import APIClient
from rich import print
from loader import i18n

api_client = APIClient()

async def mentor_keyboard():
    mentors = await show_mentors()
    # Create keyboard with 2 buttons per row
    buttons = []
    row = []
    for mentor in mentors:
        row.append(KeyboardButton(text=str(mentor)))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:  # Add any remaining buttons
        buttons.append(row)
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )


    

async def mentor_booking_keyboard(mentor_name: str):
    mentor = await api_client.get_mentor_by_name(mentor_name)
    if not mentor or not mentor.get('availability'):
        return None
    
    buttons = []
    row = []
    
    for slot in mentor['availability']:
        if slot.get('is_available'):
            start = slot['start_time'].split('T')[1][:5]
            end = slot['end_time'].split('T')[1][:5]
            date = slot['start_time'].split('T')[0]
            time_text = f"{start} - {end}({date})"
            row.append(KeyboardButton(text=time_text))
            if len(row) == 2:
                buttons.append(row)
                row = []
    
    if row:  # Add any remaining buttons
        buttons.append(row)
    
    if not buttons:
        buttons.append([KeyboardButton(text="No available slots")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
async def mentors_menu_keyboard(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get_text(user_id, 'course') if user_id else "📚 Courses"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'schedule_meeting') if user_id else "⏳ Schedule meeting"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'payment') if user_id else "💳 Payment"),
            ],
        ],
        resize_keyboard=True
    )

async def mentor_courses(courses: list):
    buttons = []
    for course in courses:
        buttons.append([KeyboardButton(text=course['title'])])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def lessons_menu_keyboard(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get_text(user_id, 'lessons_in_menu') if user_id else "📚 Lessons"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'payment') if user_id else "📚 Kurslar"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'back_button') if user_id else "⬅️ Back to Courses"),
            ],
        ],
        resize_keyboard=True
    )