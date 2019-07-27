from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    Language = State()
    WaitForCategory = State()
