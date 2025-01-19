import requests
from config import WEATHER_API_KEY, FOOD_API_KEY, FOOD_ID
import random

# Получение температуры в городе в текущее время
def get_weather(city):
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(weather_url)
        if response.status_code == 200:
            return response.json()["main"]
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
    return {}

# Получение данных о пище
def get_food_data(product_name):
    food_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": FOOD_ID,
        "x-app-key": FOOD_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"query": "100 grams of " + product_name}
    response = requests.post(food_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка в получении информации о еде: {response.status_code}")
        return None

# Получение данных об активности
def get_exercise_data(exercise, weight_kg, height_cm, age):
    training_url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    headers = {
        "x-app-id": FOOD_ID,
        "x-app-key": FOOD_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "query": exercise,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "age": age
    }
    response = requests.post(training_url, headers=headers, json=data)

    if response.status_code == 200 and len(response.json()['exercises']) != 0:
        return response.json().get("exercises", [])
    else:
        print(f"Ошибка в получении информации о тренировке: {response.status_code}")
        return None

# Получение списка продуктов с низким калоражем
def get_low_calorie():
    food_url = "https://trackapi.nutritionix.com/v2/search/instant/"
    headers = {
        "x-app-id": FOOD_ID,
        "x-app-key": FOOD_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"query": "low calorie"}
    response = requests.post(food_url, headers=headers, json=data)
    if response.status_code == 200:
        food_items = response.json().get("common", [])
        recommendations = random.sample(food_items, k=min(3, len(food_items)))
        recommendations_output = [item['food_name'] for item in recommendations]
        return recommendations_output
    else:
        print(f"Ошибка в получении информации о еде: {response.status_code}")
        return None