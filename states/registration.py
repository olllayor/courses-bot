# states/registration.py
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    NAME = State()  # State for collecting the user's name
    CONTACT = State()  # State for collecting the user's contact information