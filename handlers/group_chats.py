from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, bot, logging

from utils.filters import IsGroup, AskedQuestion, AnsweredQuestion
from utils.pagination import create_pages
from utils.states import Registration
from utils.phases import Phase
import asyncio
from utils.database import add_chat, add_question, add_answer, get_winner_question_id

from aiogram.dispatcher import filters

p: Phase = None


@dp.message_handler(IsGroup(), filters.RegexpCommandsFilter(regexp_commands=['Atlantide ([0-9]*)']))
async def register_chat(message: types.Message, regexp_command):
    chat_id = message.from_user.id
    global p
    if p and p.running:
        a = "вопросы" if p.current == p.QUESTIONS else "ответы"
        return await message.answer(
            f"🏛 КАТЕГОРИЯ принимает {a}, дождитесь окончания сеанса связи")
    timeout = int(regexp_command.group(1))
    if 1 < timeout < 180:
        p = Phase(timeout=timeout * 60)
        await message.answer("🏛 Связь с КАТЕГОРИЯ установлена")
        asyncio.ensure_future(p.start_phaser())
    else:
        await message.answer("🏛 Просим у Вас прощения, но в данный момент длительность сеанса связи находится в диапазоне от 2х до 180 минут (3 Часа).")


@dp.message_handler(IsGroup(), commands=["Atlantide"])
async def register_chat(message: types.Message):
    await message.answer("🏛 Для связи с КАТЕГОРИЯ введите /Atlantide 10\n"
                         "Где 10 - время одного сеанса в минутах .")


@dp.message_handler(IsGroup(), commands=["register"])
async def register_chat(message: types.Message):
    chat_id = message.from_user.id
    admins = await message.chat.get_administrators()
    for admin in admins:
        if chat_id == admin.user.id:
            await message.reply("🏡 Добро пожаловать Домой!\n"
                                "🏛 Перейдите в ЛС для выбора Вашего расположения")
            exists = add_chat(message.chat.id)
            markup = create_pages()

            if exists:
                text = "🏛 Ваше расположение уже было зарегистрировано. Создайте новое расположение Вашего чата или выберите из предложенного списка"
            else:
                text = "🏛 Поздравляем! Ваш чат связан с ☀️Атлантидой. Создайте новое расположение Вашего чата или выберите из предложенного списка:"
            text += "\n\n" \
                    "Нажмите /cancel для отмены."
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
                question=f"🏛 Отправить вопрос в КАТЕГОРИЯ ?\n" 
                f"⏱ {p.time_left // 60} мин",
                options=["✊Отправлять!", "☁️"],
                disable_notification=True)

            add_question(chat_id, question, message.message_id, poll.message_id)
        else:
            a = "вопросы" if p.current == p.QUESTIONS else "ответы к этому вопросу"
            text = f"КАТЕГОРИЯ принимает {a}, ожидайте следующего сеанса через {p.time_left // 60} мин\n"
            q_id = get_winner_question_id(chat_id)
            logging.info(f"QUID {q_id}")
            reply = None
            if q_id:
                text += f" КАТЕГОРИЯ отвечает на этот вопрос"
                reply = q_id
            await bot.send_message(chat_id, text, reply_to_message_id=reply)
    else:
        await message.answer("🏛 Для начала сеанса связи с КАТЕГОРИЯ введите команду /Atlantide")


@dp.message_handler(AnsweredQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    if p and p.running:
        if p.current == "Answers":
            answer = message.text

            poll = await bot.send_poll(
                chat_id=message.chat.id,
                reply_to_message_id=message.message_id,
                question=f"🏛 Отправить ответ в КАТЕГОРИЯ? \n{p.time_left // 60} мин",
                options=["✊ Отправлять!", "☁️"],
                disable_notification=True)

            add_answer(chat_id, answer, message.message_id, poll.message_id)
        else:
            a = "вопросы" if p.current == p.QUESTIONS else "ответы к этому вопросу"
            text = f"🏛 Ваша КАТЕГОРИЯ принимает {a}, время до окончания сеанса {p.time_left // 60} мин\n"
            await message.answer(text)
    else:
        await message.answer("🏛 Для начала сеанса связи с КАТЕГОРИЯ введите команду /Atlantide")


@dp.message_handler(IsGroup())
async def other(message: types.Message, state: FSMContext):
    state = await state.get_state()
    logging.info(f"what? %s %s", message.text, state)
