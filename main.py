from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN =
'5000569519:AAFwYjm5pK3rP3ZY-n0BNsk_jDsJTZSB64E /test'


bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

def main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎂 Ввести код", callback_data="enter_code"))
    keyboard.add(InlineKeyboardButton("💰 Мой баланс", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("🎁 Вывод", callback_data="withdraw"))
    return keyboard

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Добро пожаловать! Выберите действие:", reply_markup=main_keyboard())

if name == '__main__':
    executor.start_polling(dp, skip_updates=True)
