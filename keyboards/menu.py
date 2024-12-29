from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from loader import i18n

def menu_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text=i18n.get_text(user_id, 'about_project') if user_id else "📂 Webinars"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'mentors_button') if user_id else "🧑‍🏫 Mentors"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'webinars_button') if user_id else "📂 Webinars"),
            ],
            [
                KeyboardButton(text=i18n.get_text(user_id, 'course') if user_id else "📚 Courses"),
            ],
            
        ],
    )
