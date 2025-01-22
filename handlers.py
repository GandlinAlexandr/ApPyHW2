from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from states import ProfileSetup, Food, ProfileChange
from calculations import (
    calculate_calorie_target,
    calculate_water_norm,
    activity_water,
    graphics,
    get_mass_index,
    global_calorie,
    global_water,
)
from API import get_food_data, get_exercise_data, get_low_calorie, get_weather
import datetime
import httpx
import pandas as pd

router = Router()


# Перевод
async def translate(text, lang="ru", lang_to="en"):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": lang, "tl": lang_to, "dt": "t", "q": text}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            translation = response.json()[0][0][0]
            return translation
        else:
            raise Exception("Ошибка перевода")


users = {}


def add_today_data(users, chat_id, today):
    # Проверяем, есть ли данные для пользователя
    if chat_id not in users:
        return False  # Пользователь отсутствует

    # Проверяем, есть ли данные за сегодня
    if today not in users[chat_id]:
        # Ищем последний ближайший день с данными
        last_day = max(users[chat_id].keys())  # Находим последнюю дату
        users[chat_id][today] = users[chat_id][last_day].copy()  # Копируем данные
        if (
            users[chat_id][today]["calorie_goal_type"] == "calc"
        ):  # Если автоматом считали калории, пересчитываем
            users[chat_id][today]["calorie_goal"] = int(
                calculate_calorie_target(
                    weight=users[chat_id][today]["weight"],
                    height=users[chat_id][today]["height"],
                    age=users[chat_id][today]["age"],
                    activity=users[chat_id][today]["activity"],
                )
            )
        users[chat_id][today]["water_goal"] = int(
            calculate_water_norm(
                users[chat_id][today]["weight"],
                users[chat_id][today]["city"],
                users[chat_id][today]["activity"],
            )
        )
        users[chat_id][today]["logged_water"] = 0  # Сбрасываем данные воды
        users[chat_id][today]["logged_calories"] = 0  # Сбрасываем данные калорий
        users[chat_id][today][
            "burned_calories"
        ] = 0  # Сбрасываем данные сожжённых калорий
        return True  # Новый день добавлен
    return True


# Функция для обновления параметра для \edit_profile
async def update_user_parameter(users, chat_id, today, param, new_value):
    users[chat_id][today][param] = new_value


# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Вас приветствует фитнес-бот!"
        "Чтобы ознакомиться с возможностями бота, используйте кгоманду /help"
    )


# Хэндлер на команду /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/start - Начало работы\n"
        "/help - Помощь\n"
        "/set_profile - Заполнение формы для создания профиля. При создании нового старый профиль удаляется\n"
        "/my_propfile - Посмотреть свой профиль\n"
        "/log_water <количество воды в мл> - Добавляет количество выпитой воды в ваш профиль и рассчитывает количество воды до нормы\n"
        "/log_food <название продукта> - Рассчитывает количество поглощённых калорий по названию блюда и добавляет в профиль\n"
        "/log_workout <тип тренировки> <время (мин)> - Фиксирует сожжённые калории и учитывает расход воды на тренировке\n"
        "/check_progress - Показывает, сколько воды и калорий потреблено, сожжено и сколько осталось до выполнения цели на текущие сутки. Выводит соотвествующие диаграммы\n"
        "/recomend - Выдаёт рекомендации на основе ИМТ\n"
        "/global_progress - Выводит график глобального прогресса за последние 10 дней активности в чате бота \n"
        "/edit_profile - Позволяет изменить параметры профиля, не удаляя его и сохраняя историю \n"
    )


# Функция для обновления состояния, чтоб не дублироваться:
async def update_state_and_ask(state, key, value, next_state, message, question):
    await state.update_data({key: value})  # Обновляет состояние key до value
    await state.set_state(next_state)  # Готовимся установить значение next_state
    await message.answer(
        question
    )  # Для этого задаём вопрос, чтобы ответ на него был обновлением


# Хэндлер на команду /set_profile
@router.message(Command("set_profile"))
async def set_profile_start(message: Message, state: FSMContext):
    await state.set_state(ProfileSetup.weight)  # Устанавливаем состояние для веса
    await message.answer(
        "Пожалуйста, введите ваш вес (в кг):"
    )  # Вопрос, ответ на который - вес


# Устанавливаем вес
@router.message(ProfileSetup.weight)
async def set_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        await update_state_and_ask(
            state,
            "weight",
            weight,
            ProfileSetup.height,
            message,
            "Введите ваш рост (в см):",
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число для веса.")


# Устанавливаем рост
@router.message(ProfileSetup.height)
async def set_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        await update_state_and_ask(
            state, "height", height, ProfileSetup.age, message, "Введите ваш возраст:"
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число для роста.")


# Устанавливаем возраст
@router.message(ProfileSetup.age)
async def set_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await update_state_and_ask(
            state,
            "age",
            age,
            ProfileSetup.activity,
            message,
            "Сколько минут активности у вас в день?",
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число для возраста.")


# Устанавливаем активность
@router.message(ProfileSetup.activity)
async def set_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        await update_state_and_ask(
            state,
            "activity",
            activity,
            ProfileSetup.city,
            message,
            "В каком городе вы находитесь?",
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число для активности.")


# Устанавливаем город
@router.message(ProfileSetup.city)
async def set_city(message: Message, state: FSMContext):
    city = message.text
    if get_weather(city) != {}:
        await update_state_and_ask(
            state,
            "city",
            city,
            ProfileSetup.calorie_goal,
            message,
            "Введите цель по калориям или напишите '0', чтобы использовать рассчитанную норму:",
        )
    else:
        await message.answer(
            "Пожалуйста, проверьте корректность написание названия города. "
            "Введите корректное название:"
        )


# Устанавливаем цель по калориям
@router.message(ProfileSetup.calorie_goal)
async def set_calorie_target(message: Message, state: FSMContext):
    data = await state.get_data()
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if message.text == "0":  # Если 0, то рассчитываем
        calorie_goal_type = "calc"
        calorie_goal = calculate_calorie_target(
            weight=data["weight"],
            height=data["height"],
            age=data["age"],
            activity=data["activity"],
        )
        await state.update_data(calorie_goal=int(calorie_goal))
    else:
        try:
            calorie_goal = int(message.text)
            calorie_goal_type = "manual"
            await state.update_data(calorie_goal=calorie_goal)
        except ValueError:
            await message.answer("Пожалуйста, введите число для цели по калориям.")
            return

    data = await state.get_data()  # Записываем состояния в переменную
    # Сохраняем данные пользователя
    users[chat_id] = {
        today: {
            "weight": int(data["weight"]),
            "height": int(data["height"]),
            "age": int(data["age"]),
            "activity": data["activity"],
            "city": data["city"],
            "calorie_goal": data["calorie_goal"],
            "water_goal": int(
                calculate_water_norm(data["weight"], data["city"], data["activity"])
            ),
            "logged_water": 0,
            "logged_calories": 0,
            "burned_calories": 0,
            "calorie_goal_type": calorie_goal_type,
        }
    }
    # Выводим данные пользователя
    await message.answer(
        "✅ Профиль успешно настроен!\n"
        f"Вес: {users[chat_id][today]['weight']} кг\n"
        f"Рост: {users[chat_id][today]['height']} см\n"
        f"Возраст: {users[chat_id][today]['age']} лет\n"
        f"Активность: {users[chat_id][today]['activity']} минут\n"
        f"Город: {users[chat_id][today]['city']}\n"
        f"Цель по калориям: {users[chat_id][today]['calorie_goal']} ккал\n"
        f"Норма воды: {users[chat_id][today]['water_goal']} мл\n"
        f"Выпито воды: {users[chat_id][today]['logged_water']} мл\n"
        f"Потреблено калорий: {users[chat_id][today]['logged_calories']} ккал\n"
        f"Сожжено калорий: {users[chat_id][today]['burned_calories']} ккал\n"
    )
    await state.clear()  # Очищаем состояние


# Хэндлер на команду /my_propfile
@router.message(Command("my_propfile"))
async def cmd_my_propfile(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if add_today_data(users, chat_id, today):
        await message.answer(
            "👤 Ваш профиль:\n"
            f"Вес: {users[chat_id][today]['weight']} кг\n"
            f"Рост: {users[chat_id][today]['height']} см\n"
            f"Возраст: {users[chat_id][today]['age']} лет\n"
            f"Активность: {users[chat_id][today]['activity']} минут\n"
            f"Город: {users[chat_id][today]['city']}\n"
            f"Цель по калориям: {users[chat_id][today]['calorie_goal']} ккал\n"
            f"Норма воды: {users[chat_id][today]['water_goal']} мл\n"
            f"Выпито воды: {users[chat_id][today]['logged_water']} мл\n"
            f"Потреблено калорий: {users[chat_id][today]['logged_calories']} ккал\n"
            f"Сожжено калорий: {users[chat_id][today]['burned_calories']} ккал\n"
        )
    else:
        await message.answer(
            "Вы не создавали профиль. Воспользуйтесь командой /set_profile для его создания."
        )


# Хэндлер на команду /log_water <количество воды в мл>
@router.message(Command("log_water"))
async def cmd_log_water(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    try:
        water = int(message.text.split()[1])
        users[chat_id][today]["logged_water"] += water
        await message.answer(
            f"Выпито {water} мл воды. Осталось выпить {users[chat_id][today]['water_goal'] - users[chat_id][today]['logged_water']} мл воды."
        )
    except (IndexError, ValueError):
        await message.answer(
            "Используй команду так: /log_water <количество воды в мл>."
        )


# Хэндлер на команду /log_food <название продукта>
@router.message(Command("log_food"))
async def cmd_log_food(message: Message, state: FSMContext):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    try:
        name = " ".join(message.text.split()[1::]).lower()
    except (IndexError, ValueError):
        await message.answer("Используйте команду так: /log_food <название продукта>.")
        return
    english_name = await translate(name)  # Перевод названия на англ
    info = get_food_data(english_name)  # Обращение к АПИ и получение данных
    if info:
        calories_per_100_g = float(info["foods"][0]["nf_calories"])
        full_name = await translate(
            info["foods"][0]["food_name"], lang="en", lang_to="ru"
        )
        await state.set_state(
            Food.eat_weight
        )  # Готовимся установить состояние - вес пищи
        await state.update_data(calories_per_100_g=calories_per_100_g)
        await message.answer(
            f"{full_name} — {int(calories_per_100_g)} ккал на 100 г. Сколько грамм вы съели?"
        )
    else:
        await message.answer(
            f"Не удалось распознать продукт '{name}'. Попробуйте задать его иначе."
        )


@router.message(Food.eat_weight)  # ЕУ
async def eat_weight(message: Message, state: FSMContext):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    try:
        eat_weight = float(message.text)
        await state.update_data(
            eat_weight=eat_weight
        )  # Устанавливаем состояние - вес пищи
        data_eat = await state.get_data()  # Сохраняем состояние в переменную
        eat_calories = int(
            data_eat["eat_weight"] / 100 * data_eat["calories_per_100_g"]
        )  # Рассчитываем калораж с учётом веса пищи
        users[chat_id][today]["logged_calories"] += eat_calories
        await message.answer(f"Записано: {eat_calories} ккал.")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("Пожалуйста, введите число для веса.")


# Хэндлер на команду /check_progress
@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    graph = graphics(users, today, chat_id)
    await message.answer(
        f"📊 Прогресс:\n"
        f"Вода:\n"
        f"- Выпито: {users[chat_id][today]['logged_water']} мл из {users[chat_id][today]['water_goal']} мл.\n"
        f"- Осталось: {users[chat_id][today]['water_goal'] - users[chat_id][today]['logged_water']} мл.\n"
        f"Калории:\n"
        f"- Потреблено: {users[chat_id][today]['logged_calories']} ккал из {users[chat_id][today]['calorie_goal']} ккал.\n"
        f"- Сожжено: {users[chat_id][today]['burned_calories']} ккал.\n"
        f"- Баланс: {users[chat_id][today]['logged_calories'] - users[chat_id][today]['burned_calories']} ккал!\n"
    )
    input_file = BufferedInputFile(graph.read(), filename="progress_graph.png")
    graph.close()
    await message.answer_photo(photo=input_file)


# Хэндлер на команду /log_workout <тип тренировки> <время (мин)>
@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    try:
        time_activity = int(message.text.split()[-1])
        water = activity_water(time_activity)
        activity_name = " ".join(message.text.split()[1:-1]).lower()
        english_activity_name = await translate(activity_name)
        activity_data = get_exercise_data(
            english_activity_name,
            users[chat_id][today]["weight"],
            users[chat_id][today]["height"],
            users[chat_id][today]["age"],
        )
        if activity_data:
            activity_calorie = int(
                activity_data[0]["nf_calories"]
                * time_activity
                / activity_data[0]["duration_min"]
            )
            activity_name_api = await translate(
                activity_data[0]["name"], lang="en", lang_to="ru"
            )
            users[chat_id][today]["burned_calories"] += int(activity_calorie)
            await message.answer(
                f"{activity_name_api}: {time_activity} минут — {activity_calorie} ккал. Дополнительно: выпейте {int(water)} мл воды."
            )
        else:
            await message.answer(
                f"Не удалось распознать активность '{activity_name}'. Попробуйте задать её иначе."
            )
    except (IndexError, ValueError):
        await message.answer(
            f"Пожалуйста, введите команду в формате /log_workout <тип тренировки> <время (мин)>."
        )


# Хэндлер на команду /recomend
@router.message(Command("recomend"))
async def cmd_recomend(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return
    imt = round(
        get_mass_index(
            users[chat_id][today]["weight"], users[chat_id][today]["height"]
        ),
        2,
    )
    if imt >= 25:
        eng_names_food = get_low_calorie()
        food_recomendation = "\n".join(
            [
                f"✔️ {await translate(food, lang='en', lang_to='ru')} (100 грамм ≈ {get_food_data(food)['foods'][0]['nf_calories']} ккал)"
                for food in eng_names_food
            ]
        )
        await message.answer(
            f"Ваш ИМТ выше нормы (ИМТ = {imt}).\n"
            f"🍏 Рекомендуемые низкокалорийные продукты:\n"
            f" {food_recomendation}"
        )
        return
    elif imt < 25 and imt > 18.5:
        await message.answer(
            f"Ваш ИМТ в пределах нормы (ИМТ = {imt}).\n"
            f"🍏 ✔️ Рекомндаций не требуется.\n"
        )
    else:
        await message.answer(
            f"Ваш ИМТ ниже нормы (ИМТ = {imt}).\n"
            f"💊 Рекомндуется обратиться за консультацией к врачу.\n"
        )


# Хэндлер на команду /global_progress
@router.message(Command("global_progress"))
async def cmd_global(message: Message):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer(
            "У вас нет истории. Настройте профиль с помощью /set_profile, чтобы её начать."
        )
        return
    if len(users[chat_id]) == 1:
        await message.answer(
            "Вы используете бот первый день. "
            "Используйте бот хотя бы два дня. "
            "Для отслеживания прогресса за день используйте /check_progress"
        )
        return

    df = pd.DataFrame.from_dict(
        users[chat_id], orient="index"
    ).reset_index()  # Создание датафрейса из данных пользователя
    df.rename(columns={"index": "date"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
    df = df.sort_values(by="date", ascending=True)
    df["date"] = df["date"].dt.strftime("%d.%m.%Y")
    df = df.tail(10)  # Отбор последних десяти дней активности в чате

    calorie_df = pd.melt(
        df,
        id_vars=["date"],
        value_vars=["calorie_goal", "logged_calories", "burned_calories"],
        var_name="calorie_type",
        value_name="calorie",
    )
    water_df = pd.melt(
        df,
        id_vars=["date"],
        value_vars=["water_goal", "logged_water"],
        var_name="water_type",
        value_name="water",
    )
    graph_calorie = global_calorie(calorie_df)
    input_file_calorie = BufferedInputFile(
        graph_calorie.read(), filename="global_calorie.png"
    )
    graph_calorie.close()
    graph_water = global_water(water_df)
    input_file_water = BufferedInputFile(
        graph_water.read(), filename="global_water.png"
    )
    graph_water.close()
    await message.answer_photo(photo=input_file_calorie)
    await message.answer_photo(photo=input_file_water)


from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime


# Хэндлер на команду /change
# Функция для добавления данных на текущую дату (если их нет)
def add_today_data(users, chat_id, today):
    if chat_id not in users:
        return False
    if today not in users[chat_id]:
        users[chat_id][today] = users[chat_id][list(users[chat_id].keys())[0]].copy()
    return True


# Хэндлер на команду /edit_profile
@router.message(Command("edit_profile"))
async def cmd_edit_profile(message: types.Message, state: FSMContext):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)

    # Проверка наличия профиля
    if not add_today_data(users, chat_id, today):
        await message.answer(
            "У вас нет профиля. Настройте профиль с помощью /set_profile"
        )
        return

    # Создание кнопок для параметров
    keyboard = InlineKeyboardBuilder()
    parameters_visible = [
        "Вес",
        "Рост",
        "Возраст",
        "Активность",
        "Город",
        "Цель по калориям",
    ]
    for visible_param in parameters_visible:
        keyboard.add(
            InlineKeyboardButton(
                text=visible_param, callback_data=f"change_{visible_param}"
            )
        )
    keyboard.adjust(2)  # Настройка количества кнопок в ряду
    await message.answer(
        "Выберите параметр для изменения:", reply_markup=keyboard.as_markup()
    )

    # Сохраняем состояние, что нужно изменить
    await state.set_state(ProfileChange.selected_params)


# Обработка нажатий кнопок
@router.callback_query(lambda cb: cb.data.startswith("change_"))
async def process_change(callback: CallbackQuery, state: FSMContext):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(callback.message.chat.id)
    parameters = ["weight", "height", "age", "activity", "city", "calorie_goal"]
    parameters_visible = [
        "Вес",
        "Рост",
        "Возраст",
        "Активность",
        "Город",
        "Цель по калориям",
    ]

    visible_param = callback.data.split("_")[1]
    param = parameters[
        parameters_visible.index(visible_param)
    ]  # Извлекаем внутреннее имя параметра

    # Сохраняем выбранный параметр в состояние
    await state.update_data(selected_params=[param, visible_param])

    await callback.message.answer(
        f"Введите новое значение для параметра {visible_param}:"
    )
    await callback.answer()  # Убираем "часики" в интерфейсе
    await state.set_state(ProfileChange.value)


# Обработка ввода нового значения
@router.message(ProfileChange.value)
async def set_value(message: Message, state: FSMContext):
    today = datetime.date.today().strftime("%d.%m.%Y")
    chat_id = str(message.chat.id)
    if not add_today_data(users, chat_id, today):
        await message.answer("Сначала настройте профиль с помощью /set_profile.")
        return

    # Получаем данные из состояния
    data = await state.get_data()
    selected_params = data["selected_params"]

    # Новый вес
    if selected_params[0] == "weight":
        try:
            new_value = int(message.text)
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            calorie_goal = int(
                calculate_calorie_target(
                    weight=users[chat_id][today]["weight"],
                    height=users[chat_id][today]["height"],
                    age=users[chat_id][today]["age"],
                    activity=users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(
                users, chat_id, today, "calorie_goal", calorie_goal
            )
            water_goal = int(
                calculate_water_norm(
                    users[chat_id][today]["weight"],
                    users[chat_id][today]["city"],
                    users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(users, chat_id, today, "water_goal", water_goal)
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"⚖️ Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value} кг.\n\n"
                f"Вслед за ним обновились параметры:\n\n"
                f"🔥 Цель по калориям — теперь {calorie_goal} ккал. "
                f"Этот параметр можно изменить вручную.\n\n"
                f"💦 Норма воды — теперь {water_goal} мл."
            )
        except ValueError:
            await message.answer("Пожалуйста, введите число для изменения веса в кг.")
            return

    # Новый рост
    if selected_params[0] == "height":
        try:
            new_value = int(message.text)
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            calorie_goal = int(
                calculate_calorie_target(
                    weight=users[chat_id][today]["weight"],
                    height=users[chat_id][today]["height"],
                    age=users[chat_id][today]["age"],
                    activity=users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(
                users, chat_id, today, "calorie_goal", calorie_goal
            )
            users[chat_id][today]["calorie_goal_type"] = "calc"
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"📏 Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value} см.\n\n"
                f"Вслед за ним обновился параметр:\n\n"
                f"🔥 Цель по калориям — теперь {calorie_goal} ккал. "
                f"Этот параметр можно изменить вручную."
            )
        except ValueError:
            await message.answer("Пожалуйста, введите число для изменения роста в см.")
            return

    # Новый возраст
    if selected_params[0] == "age":
        try:
            new_value = int(message.text)
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            calorie_goal = int(
                calculate_calorie_target(
                    weight=users[chat_id][today]["weight"],
                    height=users[chat_id][today]["height"],
                    age=users[chat_id][today]["age"],
                    activity=users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(
                users, chat_id, today, "calorie_goal", calorie_goal
            )
            users[chat_id][today]["calorie_goal_type"] = "calc"
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"🗓 Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value} лет.\n\n"
                f"Вслед за ним обновился параметр:\n\n"
                f"🔥 Цель по калориям — теперь {calorie_goal} ккал. "
                f"Этот параметр можно изменить вручную."
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число для изменения возраста в годах."
            )
            return

    # Новая длительность активности
    if selected_params[0] == "activity":
        try:
            new_value = int(message.text)
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            calorie_goal = int(
                calculate_calorie_target(
                    weight=users[chat_id][today]["weight"],
                    height=users[chat_id][today]["height"],
                    age=users[chat_id][today]["age"],
                    activity=users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(
                users, chat_id, today, "calorie_goal", calorie_goal
            )
            users[chat_id][today]["calorie_goal_type"] = "calc"
            water_goal = int(
                calculate_water_norm(
                    users[chat_id][today]["weight"],
                    users[chat_id][today]["city"],
                    users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(users, chat_id, today, "water_goal", water_goal)
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"🏃 Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value} мин.\n\n"
                f"Вслед за ним обновились параметры:\n\n"
                f"🔥 Цель по калориям — теперь {calorie_goal} ккал. "
                f"Этот параметр можно изменить вручную.\n\n"
                f"💦 Норма воды — теперь {water_goal} мл."
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число для изменения длительность ежедневной активности в минутах."
            )
            return

    # Новый город
    if selected_params[0] == "city":
        new_value = message.text
        if get_weather(new_value) != {}:
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            water_goal = int(
                calculate_water_norm(
                    users[chat_id][today]["weight"],
                    users[chat_id][today]["city"],
                    users[chat_id][today]["activity"],
                )
            )
            await update_user_parameter(users, chat_id, today, "water_goal", water_goal)
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"🌃 Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value}.\n\n"
                f"Вслед за ним обновился параметр:\n\n"
                f"💦 Норма воды — теперь {water_goal} мл."
            )
        else:
            await message.answer(
                "Пожалуйста, проверьте корректность написание названия города. "
                "Введите корректное название:"
            )
            return

    # Новая цель по калориям
    if selected_params[0] == "calorie_goal":
        try:
            new_value = int(message.text)
            await update_user_parameter(
                users, chat_id, today, selected_params[0], new_value
            )
            users[chat_id][today]["calorie_goal_type"] = "calc"
            await message.answer(
                f"Пользовательское изменение:\n\n"
                f"🔥 Параметр {selected_params[1]} успешно обновлен: "
                f"новое значение — {new_value} ккал."
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число для изменеия цели по калориям в ккал."
            )
            return

    await state.clear()
