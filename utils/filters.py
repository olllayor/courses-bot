from typing import Dict, Any, Union
from aiogram.types import Message
from aiogram.filters import BaseFilter
from data.api_client import APIClient
import logging

logger = logging.getLogger(__name__)

class MentorNameFilter(BaseFilter):
    async def __call__(self, message: Message, api_client: APIClient = None) -> Union[bool, Dict[str, Any]]:
        try:
            if not api_client:
                return False
                
            mentors = await api_client.get_mentors(telegram_id=message.from_user.id)
            mentor_names = [mentor["name"].lower() for mentor in mentors]
            
            is_mentor = message.text.lower() in mentor_names
            return {"mentor_name": message.text} if is_mentor else False

        except Exception as e:
            logger.error(f"Error in MentorNameFilter: {e}")
            return False