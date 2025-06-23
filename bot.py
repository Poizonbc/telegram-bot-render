import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiohttp import web
import os

# ==== Настройки ====
TOKEN = os.getenv("BOT_TOKEN")  # ← Токен через переменные среды
ADMIN_ID = 7887944708
ADMIN_USERNAME = "poizonbuyers_admin"

# ==== Начальные значения ====
yuan_rate = 12
price_per_kg = 600

# ==== Инициализация ====
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ==== Кнопка "Написать админу" ====
def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать админу 💬", url=f"https://t.me/{ADMIN_USERNAME}")]
        ]
    )

# ==== Функция комиссии ====
def get_commission_percent(price_rub: float) -> float:
    if price_rub >= 100_000:
        return 5
    elif price_rub >= 75_000:
        return 6
    elif price_rub >= 50_000:
        return 7
    elif price_rub >= 25_000:
        return 8
    elif price_rub >= 20_000:
        return 9
    elif price_rub >= 15_000:
        return 10
    elif price_rub >= 10_000:
        return 13
    else:
        return 15

# ==== Хэндлеры ====
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Я помогу тебе рассчитать стоимость заказа 😇\n\n"
        "Отправь мне: <code>ЦЕНА ВЕС</code>\nПример: <code>100 2.5</code>",
        reply_markup=get_admin_keyboard()
    )

@dp.message(Command("set_yuan"))
async def set_yuan(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    global yuan_rate
    try:
        yuan_rate = float(command.args)
        await message.answer(f"✅ Курс юаня обновлён: {yuan_rate} ₽")
    except:
        await message.answer("❌ Введите число. Пример: /set_yuan 12.3")

@dp.message(Command("set_kg"))
async def set_kg(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    global price_per_kg
    try:
        price_per_kg = float(command.args)
        await message.answer(f"✅ Цена за 1 кг обновлена: {price_per_kg} ₽")
    except:
        await message.answer("❌ Введите число. Пример: /set_kg 600")

@dp.message()
async def calculate_handler(message: Message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError
        price = float(parts[0])
        weight = float(parts[1])
        price_rub = price * yuan_rate
        commission = get_commission_percent(price_rub)
        total = price_rub * (1 + commission / 100) + weight * price_per_kg

        result = (
            f"📦 Стоимость заказа:\n\n"
            f"Цена товара: {price} ¥\n"
            f"Вес: {weight} кг\n"
            f"Курс юаня: {yuan_rate} ₽\n"
            f"Комиссия: {commission}%\n"
            f"Доставка: {price_per_kg} ₽/кг\n\n"
            f"<b>Итого: {round(total, 2)} ₽</b>"
        )
        await message.answer(result, reply_markup=get_admin_keyboard())
    except:
        await message.answer("⚠️ Ошибка ввода. Используй формат: <code>цена вес</code>\nПример: <code>200 1.5</code>")

# ==== Webhook + aiohttp ====
async def on_startup(app: web.Application):
    webhook_url = os.getenv("WEBHOOK_URL")
    await bot.set_webhook(webhook_url)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()

async def main():
    app = web.Application()
    app["bot"] = bot
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(dp)  # Важно: не дублировать!
    app.router.add_post("/", dp.as_handler())
    return app

if __name__ == "__main__":
    web.run_app(main(), port=10000)
