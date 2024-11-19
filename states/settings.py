from aiogram.fsm.state import State, StatesGroup

class BotSettings(StatesGroup):
    ChannelCheck = State()