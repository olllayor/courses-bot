# app.py
# app.py
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from data.api_client import APIClient
from loader import dp, bot, i18n
from config import API_TOKEN
from handlers import courses, help, lessons, mentors, payment, start
from utils.set_bot_commands import set_commands
from middlewares.auth import AuthMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create single APIClient instance
api_client = APIClient()

# Register middleware with APIClient instance
dp.message.middleware(AuthMiddleware(api_client))
dp.callback_query.middleware(AuthMiddleware(api_client))

# Include routers
dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(mentors.router)
dp.include_router(courses.router)
dp.include_router(lessons.router)
dp.include_router(payment.router)


async def main():
    try:
        logger.info("Starting bot setup...")

        # Set up handlers
        try:
            await mentors.setup_mentors_handler()
            logger.info("Mentor handlers set up successfully.")
        except Exception as e:
            logger.error(f"Failed to set up mentor handlers: {e}")

        await set_commands(bot)
        logger.info("Bot commands set successfully.")
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.critical(f"Unhandled exception in bot: {e}", exc_info=True)
    finally:
        if "api_client" in locals() and api_client:
            await api_client.close()
            logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
