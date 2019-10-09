import asyncio

from aiogram import types
from aiogram.dispatcher import filters
from aiogram.dispatcher.filters import Text

from app import dp, bot, logging, _
from utils.database import (add_question, add_answer,
                            get_winner_question_id, get_category,
                            save_no_phase, vote_for_question_db, vote_for_answer_db)
from utils.filters import IsGroup, AskedQuestion, AnsweredQuestionPhase, AnsweredQuestionNoPhase, AskedQuestionAnswer
from utils.keyboard_maker import ListOfButtons
from utils.phases import send_to_all, get_phase

from aiogram.utils.callback_data import CallbackData

language_callback = CallbackData("language", "code")


# Start phase with specified time
@dp.message_handler(IsGroup(), filters.RegexpCommandsFilter(regexp_commands=['call ([0-9]*)']))
async def register_chat(message: types.Message, regexp_command):
    chat_id = message.chat.id
    category = get_category(chat_id)
    if not category:
        return await message.answer(_("Чат не подключен, нажмите /connect"))
    timeout = int(regexp_command.group(1))
    phase = get_phase(category)

    if phase.running:
        a = _("#В(Вопрос) или #О(Ответ)") if phase.current == phase.QUESTIONS else _("#О(Ответ) или #В(Вопрос)")
        return await message.answer(
            _("🏛Ваш 🏠дом {category} принимает {a}, пожалуйста дождитесь окончания 🌩СеансаСвязи").format(
                category=category,
                a=a))
    elif 0 < timeout < 12:
        if not phase.was_the_last(chat_id):
            phase.timeout = timeout * 60
            phase.last_chat_run = chat_id
            await message.answer(_("🏛 ⚡️Связь с {category} установлена").format(category=category))
            asyncio.ensure_future(phase.start_phaser())
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
    if not category:
        return await message.answer(_("Чат не подключен, нажмите /connect"))

    phase = get_phase(category)
    if not phase.was_the_last(chat_id) and not phase.running:
        phase.last_chat_run = chat_id
        await message.answer(_("🏛 ⚡️Связь с {category} установлена").format(category=category))
        asyncio.ensure_future(phase.start_phaser())
    else:
        await message.answer(_("🏛 Приносим извинения за временные неудобства. \n"
                               "Ваш 🏡чат/канал недавно запускал 🌩СеансСвязи ожидайте Ваш 🌀Порядок через ⚡️1 "))


@dp.message_handler(AskedQuestionAnswer())
async def asked_question_answer(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)
    phase = get_phase(category)

    if phase.running:
        return
    prefix_1, prefix_2 = message.text[:2]

    def get_tag(prefix):
        return _("Ответ" if prefix == "." else "Вопрос")

    tag = f"#" + get_tag(prefix_1) + get_tag(prefix_2)
    text = "\n".join([message.text, tag])
    await send_to_all(bot, text, category=category)


@dp.message_handler(AnsweredQuestionNoPhase())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)
    phase = get_phase(category)

    if phase.running:
        return

    *question, last_tag = message.reply_to_message.text.splitlines()
    question = "\n".join(question)
    if message.text.startswith(".") or message.text.startswith("?"):
        prefix_a, answer = message.text[0], message.text[1:]
    else:
        prefix_a = "."
        answer = message.text

    def extract_tag(tag):
        return "." if _("Ответ") in tag else "?"

    prefix_q = extract_tag(last_tag)

    def get_tag(prefix):
        return _("Ответ" if prefix == "." else "Вопрос")

    tag = f"{prefix_q}{prefix_a} #" + get_tag(prefix_q) + get_tag(prefix_a)
    text = "".join([question, "\n", answer, "\n\n", tag])
    await send_to_all(bot, text, category=category)


@dp.message_handler(AskedQuestion())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)

    phase = get_phase(category)
    if phase.running:
        if phase.current == "Questions":
            await message.reply(_("🏛 Создать 🗿Атланта в {category}? \n{time} мин").format(
                category=category,
                time=phase.time_left // 60
            ),
                reply_markup=ListOfButtons(
                    text=[_("⚡️ Создать!")],
                    callback=["vote_q"],
                ).inline_keyboard)

        else:
            a = _("#В(Вопросы) или #О(Ответы)") if phase.current == phase.QUESTIONS else _("ответы к этой 🌀Мысли")
            text = _("🏛Ваш 🏠дом {category} принимает {a}, следующий 🌩СеансСвязи через {time} мин\n").format(
                time=phase.time_left // 60,
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
        if message.text.startswith("."):
            await send_to_all(bot, message.text[2:], category=category)
            return

        def get_tag(prefix):
            return _("Ответ" if prefix == "." else "Вопрос")

        tag = get_tag(message.text[0])

        question = "\n".join([message.text[1:], f"#{tag}"])
        messages_sent = await send_to_all(bot, question, category=category)
        save_no_phase(messages_sent)


@dp.message_handler(AnsweredQuestionPhase())
async def asked_question(message: types.Message):
    chat_id = message.chat.id
    category = get_category(chat_id)

    phase = get_phase(category)
    if phase.running:
        if phase.current == "Answers":
            await message.reply(_("🏛 Создать 🗿Атланта в {category}? \n{time} мин").format(
                category=category,
                time=phase.time_left // 60
            ),
                reply_markup=ListOfButtons(
                    text=[_("⚡️ Создать!")],
                    callback=[f"vote_a {message.reply_to_message.message_id}"],
                ).inline_keyboard)

        else:
            a = _("#В(Вопросы) или #О(Ответы)") if phase.current == phase.QUESTIONS else _("ответы к этой 🌀Мысли")

            text = _("🏛Ваш 🏠дом {category} принимает {a} \n время для подачи заявок - {time} мин\n").format(
                time=phase.time_left // 60,
                category=category,
                a=a
            )
            await message.answer(text)
    else:
        await message.answer(
            _("🏛 Для начала 🌩СеансаСвязи в {category} введите команду /call").format(category=category))


@dp.callback_query_handler(Text(contains="vote"))
async def vote_for_question(call: types.CallbackQuery):
    chat = call.message.chat.id
    category = get_category(chat_id=chat)
    phase = get_phase(category)

    user = call.from_user.id
    message_id = call.message.message_id
    owner = call.message.reply_to_message.from_user.id
    text = call.message.reply_to_message.text
    if owner == user:
        return await call.answer(_("Вы не можете голосовать за свою Мысль"), show_alert=True)

    if phase.running:
        if phase.current == "Questions" and "q" in call.data:
            result = vote_for_question_db(user, chat, category, text, message_id)
        elif phase.current == "Answers" and "a" in call.data:
            q_message_id = call.data.split()[-1]
            result = vote_for_answer_db(user, chat, category, text, message_id, q_message_id)
        else:
            await call.message.edit_reply_markup()
            await call.answer(_("🏛Ваш 🏠дом {category} ОТВЕЧАЕТ на следующую 🌀Мысль").format(category=category))
            return
        await call.answer(_("Вы отдали свой голос за эту Мысль"), show_alert=True)

    else:
        await call.message.edit_reply_markup()

        # Убрать кнопку
