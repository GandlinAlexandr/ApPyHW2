from API import get_weather
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns
from io import BytesIO


# Расчёт калорий
def calculate_calorie_target(weight, height, age, activity):
    base_calories = 10 * weight + 6.25 * height - 5 * age
    activity_calories = activity * 5  # Условный коэффициент активности
    return base_calories + activity_calories


# Норма воды
def calculate_water_norm(weight, city, activity):
    water_goal = weight * 30 + 500 * (activity / 30)
    weather = get_weather(city)  # Погода
    if weather.get("temp", 20) > 25:
        water_goal += 500
    return int(water_goal)


# Восполнение воды при активности
def activity_water(time):
    water = 200 * time / 30  # Простая формула для расчёта трат воды
    return water


# Графики для \check_progress
def graphics(data, today, chat_id):
    sns.set_theme(style="darkgrid")
    water = data[chat_id][today]["logged_water"]
    water_goal = data[chat_id][today]["water_goal"]
    calorie_in = data[chat_id][today]["logged_calories"]
    calorie_out = data[chat_id][today]["burned_calories"]
    calorie_goal = data[chat_id][today]["calorie_goal"]

    fig, axs = plt.subplots(1, 2, figsize=(10, 5), sharey=False)

    # Калории
    bars_calories = sns.barplot(
        x=["Потреблено", "Сожжено"],
        y=[calorie_in, calorie_out],
        ax=axs[0],
        hue=["Потреблено", "Сожжено"],
    )
    axs[0].axhline(y=calorie_goal, color="#FF6347", linewidth=2)  # Цель
    axs[0].set(title="Калории", ylabel="Количество калорий, ккал")

    # Вода
    bars_water = sns.barplot(x=["Выпито"], y=water, ax=axs[1])
    axs[1].axhline(y=water_goal, color="#FF6347", linewidth=2)  # Цель
    axs[1].set(title="Вода", ylabel="Количество воды, мл")

    bars_calories.patches[0].set_facecolor("#66c2a5")
    bars_calories.patches[1].set_facecolor("#8da0cb")
    bars_water.patches[0].set_facecolor("#4682B4")

    # Добавляем столбцы и линию в легенду для калорий
    handles_calories = [
        Line2D([0], [0], color="#FF6347", linewidth=2, label="Цель"),  # Линия
        bars_calories.patches[0],  # Столбец "Потреблено"
        bars_calories.patches[1],  # Столбец "Сожжено"
    ]
    labels_calories = ["Цель", "Потреблено", "Сожжено"]
    axs[0].legend(
        handles=handles_calories, labels=labels_calories, loc="best", title="Калории"
    )

    # Добавляем столбцы и линию в легенду для воды
    handles_water = [
        Line2D([0], [0], color="#FF6347", linewidth=2, label="Цель"),  # Линия
        bars_water.patches[0],  # Столбец "Выпито"
    ]
    labels_water = ["Цель", "Выпито"]
    axs[1].legend(handles=handles_water, labels=labels_water, loc="best", title="Вода")

    fig.suptitle(f"Прогресс на {today}")
    plt.tight_layout()

    img_stream = BytesIO()
    fig.savefig(img_stream, format="png", dpi=300, bbox_inches="tight")
    img_stream.seek(0)
    plt.close(fig)  # Закрываем график
    return img_stream


# Расчет ИМТ
def get_mass_index(mass, height):
    mass_index = mass / (height / 100) ** 2
    return mass_index


# Графики для команды \global
# Для калорй
def global_calorie(calorie_df):
    sns.set_theme(style="darkgrid")

    fig, ax = plt.subplots(figsize=(7, 5))
    new_palette = ["#FF6347", "#66c2a5", "#8da0cb"]

    sns.lineplot(
        data=calorie_df, x="date", y="calorie", hue="calorie_type", palette=new_palette
    )

    plt.xticks(rotation=45)
    plt.xlabel("Дата")
    plt.ylabel("Количество калорий")
    plt.title("Глобальный прогресс по калориям")
    handles, labels = plt.gca().get_legend_handles_labels()
    new_labels = ["Цель", "Потреблено", "Сожжено"]
    plt.legend(handles, new_labels, title="Тип калорий", loc="best")

    img_stream = BytesIO()
    plt.savefig(img_stream, format="png", dpi=300, bbox_inches="tight")
    img_stream.seek(0)
    plt.close(fig)  # Закрываем график
    return img_stream


# Для воды
def global_water(water_df):
    sns.set_theme(style="darkgrid")

    fig, ax = plt.subplots(figsize=(7, 5))
    new_palette = ["#FF6347", "#4682B4"]

    sns.lineplot(
        data=water_df, x="date", y="water", hue="water_type", palette=new_palette
    )

    plt.xticks(rotation=45)
    plt.xlabel("Дата")
    plt.ylabel("Количество воды, мл")
    plt.title("Глобальный прогресс по воде")
    handles, labels = plt.gca().get_legend_handles_labels()
    new_labels = ["Цель", "Выпито"]
    plt.legend(handles, new_labels, title="Вода", loc="best")

    img_stream = BytesIO()
    plt.savefig(img_stream, format="png", dpi=300, bbox_inches="tight")
    img_stream.seek(0)
    plt.close(fig)  # Закрываем график
    return img_stream
