from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, bot, logging

from utils.filters import IsGroup, AskedQuestion, AnsweredQuestion
from utils.pagination import create_pages
from utils.states import Registration
from utils.phases import Phase
import asyncio
from utils.database import add_chat, add_question, add_answer, get_winner_question_id

p: Phase = None


@dp.message_handler(IsGroup(), commands=["Atlantide"])
async def register_chat(message: types.Message):
    chat_id = message.from_user.id
    global p
    if p and p.running:
        a = "вопросы" if p.current == p.QUESTIONS else "ответы"
        return await message.answer(f"☀️Атлантида принимает {a}, дождитесь окончания до того, чтобы задать новый вопрос")
    p = Phase()
    await message.answer("🏡Добро пожаловать домой")
    asyncio.ensure_future(p.start_phaser())


@dp.message_handler(IsGroup(), commands=["register"])
async def register_chat(message: types.Message):
    chat_id = message.from_user.id
    admins = await message.chat.get_administrators()
    for admin in admins:
        if chat_id == admin.user.id:
            await message.reply("Написал в лс.")
            exists = add_chat(message.chat.id)
            markup = create_pages()

            if exists:
                text = "Чат уже был зарегистрирован. Введите категорию или выберите из списка, чтобы изменить"
            else:
                text = "Чат зарегистрирован. Введите категорию или выберите из списка:"
            text += "\n\n" \
                    "Или нажмите /cancel чтобы отменить."
            await bot.send_message(chat_id, text,
                                   reply_markup=markup)
            await dp.current_state(chat=chat_id, user=chat_id).set_state(Registration.WaitForCategory)
            await dp.current_state(chat=chat_id, user=chat_id).update_data(chat_id=message.chat.id)
            break
    else:
        logging.info("User is not an admin")


@dp.message_handler(AskedQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    if p and p.running:
        if p.current == "Questions":
            question = message.text[3:]
            poll = await bot.send_poll(
                chat_id=message.chat.id,
                reply_to_message_id=message.message_id,
                question=f"Задавать вопрос ☀️Атлантиде?\n"
                f"⏱ {p.time_left//60} мин",
                options=["Да! ✊Задавать!", "☁️"],
                disable_notification=True)

            add_question(chat_id, question, message.message_id, poll.message_id)
        else:
            a = "вопросы" if p.current == p.QUESTIONS else "ответы"
            text = f"☀️Атлантида принимает {a}, надо подождать еще {p.time_left//60} мин\n"
            q_id = get_winner_question_id(chat_id)
            logging.info(f"QUID {q_id}")
            reply = None
            if q_id:
                text += f"Отвечаем на этот вопрос"
                reply = q_id
            await bot.send_message(chat_id, text, reply_to_message_id=reply)
    else:
        await message.answer("☀️Атлантида не запущена, нажмите /ask_all, чтобы начать")


@dp.message_handler(AnsweredQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    if p and p.running:
        if p.current == "Answers":
            answer = message.text

            poll = await bot.send_poll(
                chat_id=message.chat.id,
                reply_to_message_id=message.message_id,
                question=f"Отправлять ответ ☀️Атлантиде? \n{p.time_left//60} мин",
                options=["Да! ✊Отправлять!", "☁️"],
                disable_notification=True)

            add_answer(chat_id, answer, message.message_id, poll.message_id)
        else:
            a = "вопросы" if p.current == p.QUESTIONS else "ответы"
            text = f"☀️Атлантида принимает {a}, надо подождать еще {p.time_left//60} мин\n"
            await message.answer(text)
    else:
        await message.answer("☀️Атлантида не запущена, нажмите /ask_all, чтобы начать")


@dp.message_handler(IsGroup())
async def other(message: types.Message, state: FSMContext):
    state = await state.get_state()
    logging.info(f"what? %s %s", message.text, state)
