from aiogram.fsm.state import State, StatesGroup


class BookSearchStates(StatesGroup):
    waiting_for_query = State()


class AddBookStates(StatesGroup):
    title = State()
    author = State()
    photo = State()
    description = State()
    pdf = State()
    confirm = State()


class EditBookStates(StatesGroup):
    waiting_for_search = State()
    select_field = State()
    waiting_new_value = State()


class AdminManageStates(StatesGroup):
    waiting_for_admin_input = State()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirm = State()
