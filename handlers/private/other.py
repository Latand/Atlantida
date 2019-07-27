from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, logging, _
from utils.filters import IsPrivate


@dp.message_handler(IsPrivate(), commands=["start"])
async def start(message: types.Message):
    text = _("🏛 Чтобы наладить ⚡️связь в ☀️Атлантиде - "
             "добавьте бота администратором в чат/канал и напишите в нём команду "
             "/connect")
    await message.answer(text)


@dp.message_handler(IsPrivate(), commands=["cancel"], state="*")
async def no_state_text(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(_("Готово"))


@dp.callback_query_handler(IsPrivate())
async def no_state_call(call: types.CallbackQuery, state: FSMContext):
    logging.info(f"{state}")
    await call.message.edit_reply_markup()
    await call.message.answer(_("🏛 У Вас уже есть расположение в ☀️Атлантиде."
                                "Вы всегда можете изменить его указав в нужном 🏡 чате/канале команду"
                                "/connect\n"))


@dp.message_handler(IsPrivate(), commands=["register"])
async def no_state_text(message: types.Message, state: FSMContext):
    await message.answer(_("🏛 Да не здесь же, а в группе! 🌞"))


@dp.message_handler(IsPrivate())
async def no_state_text(message: types.Message, state: FSMContext):
    logging.info(f"{state}")
