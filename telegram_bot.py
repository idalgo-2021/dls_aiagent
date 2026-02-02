import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from main import agent, config
import os
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

print(BOT_TOKEN)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище истории по chat_id
chat_histories = {}  # {chat_id: [{"role": "user/assistant", "content": "..."}, ...]}


class OrderForm(StatesGroup):
    waiting_for_confirmation = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Я — консультант SneakerHub. Чем могу помочь?\n"
        "Напишите, какие кроссовки ищете, размер, или просто задайте вопрос."
    )


@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_input = message.text.strip()

    if not user_input:
        return

    # Получаем или создаём историю для этого чата
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    history = chat_histories[chat_id]

    # Формируем полный контекст
    full_context = config["system_prompt"] + "\n\nИстория диалога:\n"
    for msg in history:
        role = "Пользователь" if msg["role"] == "user" else "Агент"
        full_context += f"{role}: {msg['content']}\n"
    full_context += f"Пользователь: {user_input}\n"

    try:
        response = await asyncio.to_thread(agent.run, full_context, max_steps=5)
        await message.answer(response)

        # Добавляем в историю
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

        # Ограничиваем историю (чтобы не переполнять контекст)
        if len(history) > 20:
            history = history[-20:]

        chat_histories[chat_id] = history

    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {str(e)}\nПопробуйте ещё раз или напишите менеджеру."
        )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
