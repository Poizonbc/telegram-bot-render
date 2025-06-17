import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject

# ==== Настройки ====
TOKEN = "8165411625:AAE7anqzTtCAr99OVQfxX-ytYYbHbVUCqOk"  # ← Вставь свой токен
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

# ==== Функция определения комиссии ====
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
        return 15  # по умолчанию

# ==== Команда /start ====
@dp.message(Command("start"))
async def start_handler(message: Message):
    text = (
        "👋 Привет! Я помогу тебе рассчитать стоимость заказа 😇\n\n"
        "Отправь мне:\n<code>ЦЕНА ВЕС</code>\n\n"
        "Пример: <code>100 2.5</code>"
    )
    await message.answer(text, reply_markup=get_admin_keyboard())

# ==== Команды для изменения курса и стоимости за кг (только для админа) ====
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

# ==== Расчёт стоимости ====
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

# ==== Запуск ====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
