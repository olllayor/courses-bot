# utils/filters.py
from typing import Dict, Any, Union
from aiogram.types import Message
from aiogram.filters import BaseFilter
from data.api_client import APIClient
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MentorNameFilter(BaseFilter):
    async def __call__(self, message: Message, **kwargs) -> Union[bool, Dict[str, Any]]:
        try:
            api_client = kwargs.get("api_client")
            if not api_client:
                logger.error("api_client not found")
                return False

            mentors = await api_client.get_mentors(telegram_id=message.from_user.id)
            mentor_names = [mentor["name"].lower() for mentor in mentors]

            # Check if the message text matches any mentor name
            is_mentor = message.text.lower() in mentor_names

            if is_mentor:
                # Return True and include any data you want to pass to the handler
                return {"mentor_name": message.text}
            return False

        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False
