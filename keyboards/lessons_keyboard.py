# keyboards/lessons_keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import i18n

# keyboards/lessons_keyboard.py
async def create_lessons_keyboard(lessons: list, user_id: int, has_purchased: bool = False) -> ReplyKeyboardMarkup:
    """
    Create keyboard with lesson titles
    
    Args:
        lessons: List of lesson dictionaries
        user_id: Telegram user ID for i18n
        has_purchased: Whether user has purchased the course
    """
    buttons = []
    
    # Add lesson buttons
    for lesson in lessons:
        if lesson['is_free'] or has_purchased:
            indicator = "🆓 " if lesson['is_free'] else "📖 "
        else:
            indicator = "🔒 "
        buttons.append([KeyboardButton(text=f"{indicator}{lesson['title']}")])
    
    # Add navigation buttons
    buttons.extend([
        # [KeyboardButton(text=i18n.get_text(user_id, 'back_button') if user_id else "⬅️ Back")],
        [KeyboardButton(text=i18n.get_text(user_id, 'payment') if user_id else "💳 Payment")]
    ])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )


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