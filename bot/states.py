"""FSM holatlari (aiogram)."""
from aiogram.fsm.state import State, StatesGroup


class Auth(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()


class Compose(StatesGroup):
    waiting_template = State()
    waiting_interval = State()
