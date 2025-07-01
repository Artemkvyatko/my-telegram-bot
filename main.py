import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = '5000569519:AAFwYjm5pK3rP3ZY-n0BNsk_jDsJTZSB64E /test'
OWNER_ID = 5000569519
ADMIN_USERNAME = '@neozz'

bot = Bot(token=API_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    activations_left INTEGER,
    reward INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS used_codes (
    user_id INTEGER,
    code TEXT,
    PRIMARY KEY (user_id, code)
)
''')
conn.commit()

def main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎂 Ввести код", callback_data="enter_code"))
    keyboard.add(InlineKeyboardButton("💰 Мой баланс", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("🎁 Вывод", callback_data="withdraw"))
    return keyboard

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    await message.answer("👋 Добро пожаловать! Выберите действие:", reply_markup=main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'balance')
async def check_balance(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Пользователь"
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    balance = result[0] if result else 0
    await bot.send_message(user_id, f"💼 <b>{username}</b>, Ваш баланс тортов: <b>{balance} 🎂</b>")

@dp.callback_query_handler(lambda c: c.data == 'enter_code')
async def ask_code(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите промокод в формате:\n<b>КОД: ваш_код</b>")

@dp.message_handler(lambda message: message.text and message.text.startswith('КОД:'))
async def redeem_code(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    code = message.text.replace('КОД:', '').strip()

    cursor.execute("SELECT activations_left, reward FROM promo_codes WHERE code = ?", (code,))
    result = cursor.fetchone()

    if not result:
        await message.answer("❌ Неверный промокод.")
        return

    activations_left, reward = result

    if activations_left <= 0:
        await message.answer("❌ Этот промокод больше не активен.")
        return

    cursor.execute("SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?", (user_id, code))
    if cursor.fetchone():
        await message.answer("❗ Вы уже использовали этот промокод.")
        return

    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    cursor.execute("UPDATE promo_codes SET activations_left = activations_left - 1 WHERE code = ?", (code,))
    cursor.execute("INSERT INTO used_codes (user_id, code) VALUES (?, ?)", (user_id, code))
    conn.commit()

    await message.answer(f"🎉 Успешно! Вы получили <b>{reward}</b> торт(а/ов) 🎂")

@dp.callback_query_handler(lambda c: c.data == 'withdraw')
async def handle_withdraw(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    if not username:
        await bot.send_message(user_id, "❌ Для вывода необходимо установить юзернейм в Telegram.")
        return

    cursor.
execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    balance = result[0] if result else 0

    if balance < 1:
        await bot.send_message(user_id, "❗ Вывод доступен только при балансе от 1 торта.")
        return

    cursor.execute("UPDATE users SET balance = balance - 1 WHERE user_id = ?", (user_id,))
    conn.commit()

    await bot.send_message(user_id, f"{username}, ваша заявка на вывод торта отправлена администратору ({ADMIN_USERNAME})")
    await bot.send_message(OWNER_ID, f"<b>{username}</b> отправил(-а) заявку на вывод торта 🎂")

class CreateCodeState(StatesGroup):
    code = State()
    activations = State()
    reward = State()

@dp.message_handler(commands=['code'])
async def create_code(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer("Введите название промокода:")
    await CreateCodeState.code.set()

@dp.message_handler(state=CreateCodeState.code)
async def set_code_name(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await message.answer("Сколько активаций для этого кода?")
    await CreateCodeState.activations.set()

@dp.message_handler(state=CreateCodeState.activations)
async def set_code_activations(message: types.Message, state: FSMContext):
    await state.update_data(activations=int(message.text.strip()))
    await message.answer("Сколько тортов будет начисляться за активацию?")
    await CreateCodeState.reward.set()

@dp.message_handler(state=CreateCodeState.reward)
async def finish_code_creation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    activations = data['activations']
    reward = int(message.text.strip())

    cursor.execute("INSERT OR REPLACE INTO promo_codes (code, activations_left, reward) VALUES (?, ?, ?)",
                   (code, activations, reward))
    conn.commit()

    await message.answer(f"✅ Промокод <b>{code}</b> создан!\n🔁 Активаций: {activations}\n🎂 Награда: {reward} торт(а/ов)")
    await state.finish()

if name == '__main__':
    print("Бот запущен")
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        print(f"Ошибка при запуске: {e}")