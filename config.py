import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
FOOD_API_KEY = os.getenv("FOOD_API_KEY")
FOOD_ID = os.getenv("FOOD_ID")