# middlewares/auth.py
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


# middlewares/auth.py
class AuthMiddleware(BaseMiddleware):
    def __init__(self, api_client):
        self.api_client = api_client
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # Skip auth for /start command
        if isinstance(event, Message) and event.text and event.text == "/start":
            return await handler(event, data)

        try:
            user_id = event.from_user.id
            user_name = event.from_user.full_name
            
            # Make sure user exists in the system
            user_exists = await self.api_client.ensure_user_exists(
                telegram_id=user_id, name=user_name
            )

            if not user_exists:
                logger.warning(f"User {user_id} ({user_name}) doesn't exist and couldn't be created")
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ Registration failed. Please try /start again."
                    )
                else:
                    await event.message.answer(
                        "⚠️ Registration failed. Please try /start again."
                    )
                return

            # Add api_client to handler data
            data["api_client"] = self.api_client
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            if isinstance(event, Message):
                await event.answer("An error occurred. Please try /start again.")
            else:
                await event.message.answer(
                    "An error occurred. Please try /start again."
                )
