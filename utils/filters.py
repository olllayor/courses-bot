import logging
from typing import List
from aiogram.types import Message
from aiogram.filters.base import Filter

from data.api_client import APIClient

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MentorNameFilter(Filter):
    def __init__(self):
        self.api_client = APIClient()
        
    async def __call__(self, message: Message) -> bool:
        try:
            mentors = await self.api_client.get_mentors()
            mentor_names = [mentor["name"].lower() for mentor in mentors]
            return message.text.lower() in mentor_names
        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False