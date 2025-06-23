import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Update
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")  # <-- Переменная среды Render
ADMIN_ID = int(os.getenv("ADMIN_ID", "7887944708"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "poizonbuyers_admin")

yuan_rate = 12
price_per_kg = 600

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать админу 💬", url=f"https://t.me/{ADMIN_USERNAME}")]]
    )

def get_commission_percent(price_rub: float) -> float:
    if price_rub >= 100_000: return 5
    elif price_rub >= 75_000: return 6
    elif price_rub >= 50_000: return 7
    elif price_rub >= 25_000: return 8
    elif price_rub >= 20_000: return 9
    elif price_rub >= 15_000: return 10
    elif price_rub >= 10_000: return 13
    else: return 15

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Отправь <code>цена вес</code>\nПример: <code>200 1.5</code>",
        reply_markup=get_admin_keyboard()
    )

@dp.message(Command("set_yuan"))
async def set_yuan(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    global yuan_rate
    try:
        yuan_rate = float(command.args)
        await message.answer(f"✅ Курс обновлён: {yuan_rate} ₽")
    except:
        await message.answer("❌ Пример: /set_yuan 12.3")

@dp.message(Command("set_kg"))
async def set_kg(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    global price_per_kg
    try:
        price_per_kg = float(command.args)
        await message.answer(f"✅ Цена за 1 кг: {price_per_kg} ₽")
    except:
        await message.answer("❌ Пример: /set_kg 600")

@dp.message()
async def calculate(message: Message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат")

        price = float(parts[0])
        weight = float(parts[1])
        price_rub = price * yuan_rate
        commission = get_commission_percent(price_rub)
        total = price_rub * (1 + commission / 100) + weight * price_per_kg

        await message.answer(
            f"📦 Стоимость заказа:\n"
            f"Цена: {price} ¥\n"
            f"Вес: {weight} кг\n"
            f"Курс: {yuan_rate} ₽\n"
            f"Комиссия: {commission}%\n"
            f"Доставка: {price_per_kg} ₽/кг\n\n"
            f"<b>Итого: {round(total, 2)} ₽</b>",
            reply_markup=get_admin_keyboard()
        )
    except:
        await message.answer("⚠️ Используй формат: <code>цена вес</code>")

# ==== HTTP-сервер для Webhook ====
async def handle(request):
    body = await request.json()
    update = Update.model_validate(body)
    await dp.feed_update(bot, update)
    return web.Response()

async def main():
    app = web.Application()
    app.router.add_post("/", handle)

    webhook_url = os.getenv("WEBHOOK_URL")  # ← Render URL (https://...onrender.com/)
    await bot.set_webhook(webhook_url)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000")))
    await site.start()
    print(f"✅ Webhook запущен на {webhook_url}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
