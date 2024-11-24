#utils/filters.py

import logging
from aiogram.types import Message
from aiogram.filters.base import Filter
from data.db import show_mentors 

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MentorNameFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        try:
            mentors = await show_mentors()
            return any(mentor.lower() == message.text.lower() for mentor in mentors)
        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False