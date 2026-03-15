import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "7780003419:AAGJGPSRuvy8qbwJyUncl6QTKQnfaacG9IQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# очереди и чаты
waiting_users = []
chats = {}

# пользователи
users = set()
# лимиты
DAILY_LIMIT = 20
user_messages = {}
premium_users = set()

last_reset = datetime.date.today()

# меню
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Найти собеседника")],
        [KeyboardButton(text="➡️ Следующий"), KeyboardButton(text="❌ Стоп")]
    ],
    resize_keyboard=True
)

# кнопка доната
donate_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить VIP", callback_data="buy_vip")]
    ]
)

# сброс лимитов
def reset_limits():
    global last_reset
    today = datetime.date.today()

    if today != last_reset:
        user_messages.clear()
        last_reset = today


# старт
@dp.message(CommandStart())
async def start(message: Message):

    users.add(message.from_user.id)

    await message.answer(
        f"👋 Добро пожаловать в аноним чат\n\n"
        f"👥 Пользователей бота: {len(users)}",
        reply_markup=menu
    )


# поиск собеседника
@dp.message(lambda m: m.text == "🔎 Найти собеседника")
async def search(message: Message):

    user_id = message.from_user.id

    if user_id in chats:
        await message.answer("Вы уже в чате")
        return

    if waiting_users:
        partner = waiting_users.pop(0)

        chats[user_id] = partner
        chats[partner] = user_id

        await bot.send_message(user_id, "✅ Собеседник найден")
        await bot.send_message(partner, "✅ Собеседник найден")

    else:
        waiting_users.append(user_id)
        await message.answer("🔎 Ищу собеседника...")


# следующий собеседник
@dp.message(lambda m: m.text == "➡️ Следующий")
async def next_chat(message: Message):

    user_id = message.from_user.id

    if user_id in chats:

        partner = chats[user_id]

        del chats[user_id]
        del chats[partner]

        await bot.send_message(partner, "❌ Собеседник вышел")

        await search(message)

    else:
        await message.answer("Вы не в чате")


# остановить чат
@dp.message(lambda m: m.text == "❌ Стоп")
async def stop_chat(message: Message):

    user_id = message.from_user.id

    if user_id in chats:

        partner = chats[user_id]

        del chats[user_id]
        del chats[partner]

        await bot.send_message(partner, "❌ Собеседник вышел")
        await message.answer("Чат остановлен")

    else:
        await message.answer("Вы не в чате")


# покупка VIP
@dp.callback_query(lambda c: c.data == "buy_vip")
async def buy_vip(call: types.CallbackQuery):

    premium_users.add(call.from_user.id)

    await call.message.edit_text(
        "💎 VIP активирован!\n\n"
        "Теперь у вас нет лимита сообщений."
    )


# пересылка сообщений
@dp.message()
async def relay(message: Message):

    reset_limits()

    user_id = message.from_user.id

    # проверка лимита
    if user_id not in premium_users:

        count = user_messages.get(user_id, 0)

        if count >= DAILY_LIMIT:

            await message.answer(
                "❌ Вы достигли дневного лимита сообщений.\n\n"
                "Купите VIP чтобы писать без ограничений.",
                reply_markup=donate_kb
            )
            return

        user_messages[user_id] = count + 1

    if user_id in chats:

        partner = chats[user_id]

        try:
            await bot.copy_message(
                partner,
                message.chat.id,
                message.message_id
            )
        except Exception :
            pass

    else:

        await message.answer(
            "Нажмите '🔎 Найти собеседника' чтобы начать чат"
        )


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())