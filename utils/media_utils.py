import logging
from typing import Optional
from aiogram.types import Message
from loader import bot
from utils.renew_file_id import update_mentor_photo_id, update_lesson_video_id
from data.api_client import APIClient

logger = logging.getLogger(__name__)
api_client = APIClient()

async def refresh_file_id(
    old_file_id: str, old_unique_id: str = None, file_type: str = "photo"
) -> tuple[Optional[str], Optional[str]]:
    """
    Attempt to get a fresh file_id by downloading and re-uploading the file

    Returns:
        Tuple of (new_file_id, new_file_unique_id) or (None, None) if refresh fails
    """
    try:
        file = await bot.get_file(old_file_id)
        file_content = await bot.download_file(file.file_path)

        if file_type == "photo":
            result = await bot.send_photo(chat_id=bot.id, photo=file_content)
            new_file_id = result.photo[-1].file_id
            new_unique_id = result.photo[-1].file_unique_id
        elif file_type == "video":
            result = await bot.send_video(chat_id=bot.id, video=file_content)
            new_file_id = result.video.file_id
            new_unique_id = result.video.file_unique_id
        else:
            return None, None

        await result.delete()
        return new_file_id, new_unique_id

    except Exception as e:
        logger.error(f"Error refreshing file_id: {e}")
        return None, None


async def send_media_safely(
    message: Message, media_id: str, file_type: str = "photo", **kwargs
) -> bool:
    """Safely send media with automatic file_id refresh"""
    try:
        if file_type == "photo":
            result = await message.answer_photo(photo=media_id, **kwargs)
            return True
        elif file_type == "video":
            result = await message.answer_video(video=media_id, **kwargs)
            return True

    except Exception as e:
        if "wrong file identifier" in str(e).lower():
            logger.warning(f"File ID expired: {media_id}")
            new_file_id, new_unique_id = await refresh_file_id(
                media_id, file_type=file_type
            )

            if new_file_id:
                try:
                    if file_type == "photo":
                        await message.answer_photo(photo=new_file_id, **kwargs)
                        # Update in database
                        await update_media_id(file_type, new_file_id, new_unique_id)
                    elif file_type == "video":
                        await message.answer_video(video=new_file_id, **kwargs)
                        # Update in database
                        await update_media_id(file_type, new_file_id, new_unique_id)
                    return True
                except Exception as e2:
                    logger.error(f"Failed to send media with refreshed ID: {e2}")
        return False


async def update_media_id(file_type: str, entity_id: int, new_file_id: str, new_unique_id: str, api_client: APIClient) -> bool:
    """Update media IDs in database"""
    try:
        if file_type == 'photo':
            return await update_mentor_photo_id(entity_id, new_file_id, new_unique_id, api_client)
        elif file_type == 'video':
            return await update_lesson_video_id(entity_id, new_file_id, new_unique_id, api_client)
        return False
    except Exception as e:
        logger.error(f"Failed to update media ID: {e}")
        return False
