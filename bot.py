import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ==== Настройки через переменные окружения ====
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

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

# ==== Комиссия ====
def get_commission_percent(price_rub: float) -> float:
    if price_rub >= 100_000: return 5
    elif price_rub >= 75_000: return 6
    elif price_rub >= 50_000: return 7
    elif price_rub >= 25_000: return 8
    elif price_rub >= 20_000: return 9
    elif price_rub >= 15_000: return 10
    elif price_rub >= 10_000: return 13
    return 15

# ==== /start ====
@dp.message(Command("start"))
async def start_handler(message: Message):
    text = (
        "👋 Привет! Я помогу тебе рассчитать стоимость заказа 😇\n\n"
        "Отправь мне:\n<code>ЦЕНА ВЕС</code>\n\n"
        "Пример: <code>100 2.5</code>"
    )
    await message.answer(text, reply_markup=get_admin_keyboard())

# ==== /set_yuan ====
@dp.message(Command("set_yuan"))
async def set_yuan(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        global yuan_rate
        yuan_rate = float(command.args)
        await message.answer(f"✅ Курс юаня обновлен: {yuan_rate} ₽")
    except:
        await message.answer("❌ Введите число. Пример: /set_yuan 12.3")

# ==== /set_kg ====
@dp.message(Command("set_kg"))
async def set_kg(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        global price_per_kg
        price_per_kg = float(command.args)
        await message.answer(f"✅ Цена за 1 кг обновлена: {price_per_kg} ₽")
    except:
        await message.answer("❌ Введите число. Пример: /set_kg 600")

# ==== Расчет стоимости ====
@dp.message()
async def calculate_handler(message: Message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат")

        price = float(parts[0])
        weight = float(parts[1])
        price_rub = price * yuan_rate
        commission_percent = get_commission_percent(price_rub)
        total = price_rub * (1 + commission_percent / 100) + (weight * price_per_kg)

        result = (
            f"📦 Стоимость заказа:\n\n"
            f"Цена товара: {price} ¥\n"
            f"Вес: {weight} кг\n"
            f"Курс юаня: {yuan_rate} ₽\n"
            f"Комиссия: {commission_percent}%\n"
            f"Доставка: {price_per_kg} ₽/кг\n\n"
            f"<b>Итого: {round(total, 2)} ₽</b>"
        )
        await message.answer(result, reply_markup=get_admin_keyboard())
    except Exception:
        await message.answer("⚠️ Ошибка ввода. Используй формат: <code>цена вес</code>\nПример: <code>200 1.5</code>")

# ==== Запуск с Webhook ====
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

async def main():
    app = web.Application()
    dp.include_router(dp)  # безопасно, если структура расширится
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, on_startup=on_startup, on_shutdown=on_shutdown)
    return app

if __name__ == "__main__":
    web.run_app(main(), port=10000)
