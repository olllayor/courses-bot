# states/payment_state.py
from aiogram.fsm.state import State, StatesGroup

class PaymentState(StatesGroup):
    AWAITING_SCREENSHOT = State()
    AWAITING_ADMIN_CONFIRMATION = State()
    AWAITING_PAYMENT = State()  # Add this state