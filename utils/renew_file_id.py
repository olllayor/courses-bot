import logging
from data.api_client import APIClient

logger = logging.getLogger(__name__)


async def update_mentor_photo_id(mentor_id: int, new_photo_id: str, new_unique_id: str, api_client: APIClient) -> bool:
    """Update mentor's photo file IDs in database"""
    try:
        await api_client.update_mentor(
            mentor_id, 
            {
                "profile_picture_id": new_photo_id,
                "profile_picture_unique_id": new_unique_id
            }
             
        )
        logger.info(f"Updated photo IDs for mentor {mentor_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update photo IDs: {e}")
        return False

async def update_lesson_video_id(lesson_id: int, new_video_id: str, new_unique_id: str, api_client: APIClient) -> bool:
    """Update lesson's video file IDs in database"""
    try:
        await api_client.update_lesson(
            lesson_id, 
            {
                "telegram_video_id": new_video_id,
                "telegram_video_unique_id": new_unique_id
            }
        )
        logger.info(f"Updated video IDs for lesson {lesson_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update video IDs: {e}")
        return False