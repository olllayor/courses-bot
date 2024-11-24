# keyboards/lessons_keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import i18n

async def create_lessons_keyboard(lessons: list, user_id: int):
    """Create keyboard with lesson titles"""
    buttons = []
    
    # Add lesson buttons
    for lesson in lessons:
        indicator = "🆓 " if lesson['is_free'] else "🔒 "
        buttons.append([KeyboardButton(text=f"{indicator}{lesson['title']}")])
    
    # Add navigation buttons
    buttons.extend([
        # [KeyboardButton(text=i18n.get_text(user_id, 'back_to_courses') if user_id else "⬅️ Back to Courses")],
        [KeyboardButton(text=i18n.get_text(user_id, 'payment') if user_id else "💳 Payment")]
    ])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

# keyboards/mentors_keyboard.py
async def lessons_menu_keyboard(user_id: int):
    """Create keyboard for lessons menu"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get_text(user_id, 'lessons') if user_id else "📚 Lessons"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'payment') if user_id else "💳 Payment"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'back_to_courses') if user_id else "⬅️ Back to Courses"),
            ],
        ],
        resize_keyboard=True
    )