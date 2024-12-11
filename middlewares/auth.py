# middlewares/auth.py
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

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
            authenticated = await self.api_client.ensure_authenticated(
                telegram_id=user_id, name=event.from_user.full_name
            )

            if not authenticated:
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ Authentication failed. Please try /start again."
                    )
                else:
                    await event.message.answer(
                        "⚠️ Authentication failed. Please try /start again."
                    )
                return

            # Add api_client to handler data
            data["api_client"] = self.api_client
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            if isinstance(event, Message):
                await event.answer("Authentication error. Please try /start again.")
            else:
                await event.message.answer(
                    "Authentication error. Please try /start again."
                )
