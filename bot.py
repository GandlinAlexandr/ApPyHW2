import asyncio
from aiogram import Bot, Dispatcher, types
from config import TOKEN
from handlers import router
from aiogram.types import BotCommand

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())