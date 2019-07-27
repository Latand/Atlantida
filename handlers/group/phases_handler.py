import asyncio

from aiogram import types
from aiogram.dispatcher import filters

from app import dp, bot, logging, _
from utils.database import (add_question, add_answer,
                            get_winner_question_id, get_category)
from utils.filters import IsGroup, AskedQuestion, AnsweredQuestion
from utils.phases import Phase

from aiogram.utils.callback_data import CallbackData

language_callback = CallbackData("language", "code")

p: Phase = None


# Start phase with specified time
@dp.message_handler(IsGroup(), filters.RegexpCommandsFilter(regexp_commands=['call ([0-9]*)']))
async def register_chat(message: types.Message, regexp_command):
    chat_id = message.chat.id
    global p
    category = get_category(chat_id)

    if p and p.running:
        a = _("#В(Вопрос) или #О(Ответ)") if p.current == p.QUESTIONS else _("#О(Ответ) или #В(Вопрос)")
        return await message.answer(
            _("🏛Ваш 🏠дом {category} принимает {a}, пожалуйста дождитесь окончания 🌩СеансаСвязи").format(
                category=category,
                a=a))
    timeout = int(regexp_command.group(1))
    if 1 < timeout < 12:
        if not p or not p.was_the_last(chat_id):
            p = Phase(timeout=timeout * 60, last_chat_run=chat_id)
            await message.answer(_("🏛 ⚡️Связь с {category} установлена").format(category=category))
            asyncio.ensure_future(p.start_phaser())
        else:
            await message.answer(_("🏛 Приносим извинения за временные неудобства. \n"
                                   "Ваш 🏡чат/канал недавно запускал 🌩СеансСвязи ожидайте Ваш 🌀Порядок через ⚡️1 "))
    else:
        await message.answer(
            _("🏛 Приносим извинения за временные неудобства. "
              "В данный момент длительность 🌩СеансаСвязи ограничена от 2х до 12 минут."))


# Start phase with unspecified time
@dp.message_handler(IsGroup(), commands=["call"])
async def register_chat(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)
    global p

    if not p or not p.was_the_last(chat_id):
        p = Phase(last_chat_run=chat_id)
        await message.answer(_("🏛 ⚡️Связь с {category} установлена").format(category=category))
        asyncio.ensure_future(p.start_phaser())
    else:
        await message.answer(_("🏛 Приносим извинения за временные неудобства. \n"
                               "Ваш 🏡чат/канал недавно запускал 🌩СеансСвязи ожидайте Ваш 🌀Порядок через ⚡️1 "))


@dp.message_handler(AskedQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)
    if p and p.running:
        if p.current == "Questions":
            question = message.text[3:]
            poll = await bot.send_poll(
                chat_id=message.chat.id,
                reply_to_message_id=message.message_id,
                question=_("🏛 Создать 🗿Атланта в {category}?\n"
                           "⏱ {time} мин").format(time=p.time_left // 60,
                                                  category=category),
                options=["⚡ Создать!", "☁️"],
                disable_notification=True)

            add_question(chat_id, question, message.message_id, poll.message_id)
        else:
            a = _("#В(Вопросы) или #О(Ответы)") if p.current == p.QUESTIONS else _("ответы к этой 🌀Мысли")
            text = _("🏛Ваш 🏠дом {category} принимает {a}, следующий 🌩СеансСвязи через {time} мин\n").format(
                time=p.time_left // 60,
                category=category,
                a=a
            )
            q_id = get_winner_question_id(chat_id)
            reply = None
            if q_id:
                text += _("🏛Ваш 🏠дом {category} ОТВЕЧАЕТ на следующую 🌀Мысль").format(category=category)
                reply = q_id
            await bot.send_message(chat_id, text, reply_to_message_id=reply)
    else:
        await message.answer(
            _("🏛 Для начала 🌩СеансаСвязи в {category} введите команду /call").format(category=category))


@dp.message_handler(AnsweredQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)
    if p and p.running:
        if p.current == "Answers":
            answer = message.text

            poll = await bot.send_poll(
                chat_id=message.chat.id,
                reply_to_message_id=message.message_id,
                question=_("🏛 Создать 🗿Атланта в {category}? \n{time} мин").format(
                    category=category,
                    time=p.time_left // 60),
                options=[_("⚡️ Создать!"), "☁️"],
                disable_notification=True)

            add_answer(chat_id, answer, message.message_id, poll.message_id)
        else:
            a = _("#В(Вопросы) или #О(Ответы)") if p.current == p.QUESTIONS else _("ответы к этой 🌀Мысли")

            text = _("🏛Ваш 🏠дом {category} принимает {a} \n время для подачи заявок - {time} мин\n").format(
                time=p.time_left // 60,
                category=category,
                a=a
            )
            await message.answer(text)
    else:
        await message.answer(
            _("🏛 Для начала 🌩СеансаСвязи в {category} введите команду /call").format(category=category))
