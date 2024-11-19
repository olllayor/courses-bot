from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    # Language = State()
    Name = State()
    Phone = State()
    Region = State()

