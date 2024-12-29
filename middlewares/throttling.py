# middlewares/throttling.py
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache
import time


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5, max_requests: int = 3) -> None:
        self.cache = TTLCache(maxsize=10000, ttl=rate_limit)
        self.max_requests = max_requests

    async def __call__(
        self, handler: Callable, event: Message, data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()

        if user_id not in self.cache:
            self.cache[user_id] = []

        user_requests = self.cache[user_id]

        # Remove old requests
        user_requests = [
            req_time for req_time in user_requests if now - req_time < self.cache.ttl
        ]

        if len(user_requests) >= self.max_requests:
            await event.answer("Too many requests! Please slow down!")
            return None

        user_requests.append(now)
        self.cache[user_id] = user_requests
        return await handler(event, data)
