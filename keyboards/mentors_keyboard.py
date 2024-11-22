# keyboards/mentors_keyboard.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datas.db import show_mentors, show_mentor_availability
from datas.api_client import APIClient
from rich import print


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

async def mentor_details_keyboard(mentor_name: str):
    mentor = await api_client.get_mentor_by_name(mentor_name)
    if not mentor:
        return None
    
    buttons = []
    row = []
    

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
    
async def mentors_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Courses"),
            ],
            [
                KeyboardButton(text="⏳ Schedule meeting"),
            ],
            [
                KeyboardButton(text="💳 Payment"),
            ],
        ],
        resize_keyboard=True
    )