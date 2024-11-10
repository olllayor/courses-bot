import logging
from aiogram import Bot
from aiogram.types import BotCommand





async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/menu", description="Show the main menu"),
        BotCommand(command="/help", description="Get help"),
        BotCommand(command="/cancel", description="Cancel current operation"),
    ]
    await bot.set_my_commands(commands)
    logging.info("Bot commands have been set successfully.")