from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, bot, logging, _
from utils.database import add_chat
from utils.filters import IsGroup
from utils.keyboard_maker import ListOfButtons
from utils.states import Registration

from aiogram.utils.callback_data import CallbackData

language_callback = CallbackData("language", "code")


@dp.message_handler(IsGroup(), commands=["connect"])
async def register_chat(message: types.Message):
    chat_id = message.from_user.id
    admins = await message.chat.get_administrators()
    for admin in admins:
        if chat_id == admin.user.id:
            await message.reply(_("🏡 Добро пожаловать Домой!\n"
                                  "🏛 Перейдите пожалуйста в ЛС и укажите Ваше расположение\n"))
            exists = add_chat(message.chat.id)

            if exists:
                text = _("🏛 Ваше расположение уже было зарегистрировано. "
                         "Создайте новое расположение Вашего 🏡чата/канала\n"
                         "Для этого выберите язык чата из списка")
            else:
                text = _("🏛 Поздравляем! Ваш 🏡чат/канал ⚡️связан с ☀️Атлантидой. "
                         "Создайте расположение Вашего 🏡чата/канала\n"
                         "Для этого выберите язык чата из списка")

            language_keyboard = ListOfButtons(
                text=["English", "Русский", "Українська"],
                callback=[language_callback.new(code="en"),
                          language_callback.new(code="ru"),
                          language_callback.new(code="uk")]
            ).inline_keyboard

            await bot.send_message(chat_id, text,
                                   reply_markup=language_keyboard)
            await dp.current_state(chat=chat_id, user=chat_id).set_state(Registration.Language)
            await dp.current_state(chat=chat_id, user=chat_id).update_data(chat_id=message.chat.id)
            break
    else:
        await message.answer(_("🏛 Приносим извинения за временные неудобства. \n"
                               "В данный момент принимаются только администраторы чатов/каналов"))
        logging.info("User is not an admin")


@dp.message_handler(IsGroup())
async def other(message: types.Message, state: FSMContext):
    state = await state.get_state()
    # logging.info(f"what? %s %s", message.text, state)
