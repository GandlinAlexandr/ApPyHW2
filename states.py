from aiogram.fsm.state import State, StatesGroup

# Состояние для формы анкеты
class ProfileSetup(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calorie_goal = State()

# Состояние для формы пищи
class Food(StatesGroup):
    eat_weight = State()
    calories_per_100_g = State()

class ProfileChange(StatesGroup):
    value = State()
    selected_params = State()