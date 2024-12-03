from typing import Any, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.enums import ParseMode
from data.api_client import APIClient

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Skip auth for start command
        if event.text and event.text.startswith('/start'):
            return await handler(event, data)
            
        user_id = event.from_user.id
        api_client = APIClient()
        
        # Check if user has valid token
        token = api_client._tokens.get(user_id)
        if not token:
            # Try to reauthenticate
            token = await api_client.authenticate_user(
                telegram_id=user_id,
                name=event.from_user.full_name
            )
            
        if not token:
            await event.answer(
                "⚠️ Please start the bot again using /start command.",
                parse_mode=ParseMode.HTML
            )
            return None
            
        return await handler(event, data)