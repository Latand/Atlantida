from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, logging
from utils.database import add_category
from utils.filters import IsPrivate
from utils.pagination import create_pages, page_change
from utils.states import Registration


@dp.message_handler(IsPrivate(), commands=["start"])
async def start(message: types.Message):
    text = "🏛 Чтобы наладить ⚡️связь в ☀️Атлантиде - добавьте бота администратором в чат/канал и напишите в нём команду " \
           "/connect"
    await message.answer(text)


@dp.message_handler(IsPrivate(), commands=["cancel"], state=Registration.WaitForCategory)
async def no_state_text(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Готово")


@dp.message_handler(IsPrivate(), state=Registration.WaitForCategory)
async def category_text(message: types.Message, state: FSMContext):
    category = message.text
    data = await state.get_data()
    await state.finish()
    chat = data.get("chat_id")
    add_category(chat, category)
    await message.answer(f"🏛 Вы расположились в 🏘 {category}. Для изменения расположения 🏡 введите команду connect в Вашем 🏡канале/чате")


@dp.callback_query_handler(IsPrivate(), page_change.filter(), state=Registration.WaitForCategory)
async def page_change_call(call: types.CallbackQuery, callback_data: dict):
    action = callback_data.get("action")
    current_page = int(callback_data.get("current"))

    new_page = {
        "+": current_page + 1,
        "-": current_page - 1
    }[action]

    markup = create_pages(new_page)
    if not markup:
        new_page_text = "Следующей" if action == "+" else "Предыдущей"
        await call.answer(f"{new_page_text} страницы не существует")

    else:
        await call.message.edit_reply_markup(markup)


@dp.callback_query_handler(IsPrivate(), state=Registration.WaitForCategory)
async def category_call(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()

    category = call.data
    data = await state.get_data()
    await state.finish()
    chat = data.get("chat_id")
    add_category(chat, category)
    await call.message.answer(f"🏛 Поздравляем! ⚡️Связь с 🏘 {category} установлена!")


@dp.callback_query_handler(IsPrivate())
async def no_state_call(call: types.CallbackQuery, state: FSMContext):
    logging.info(f"{state}")
    await call.message.edit_reply_markup()
    
    category = call.data
    data = await state.get_data()
    await state.finish()
    chat = data.get("chat_id")
    add_category(chat, category)
    await call.message.answer(f"🏛 У Вас уже есть расположение в 🏘 {category} Вы всегда можете изменить его указав в нужном 🏡 чате/канале команду"
                              "/connect")


@dp.message_handler(IsPrivate(), commands=["register"])
async def no_state_text(message: types.Message, state: FSMContext):
    await message.answer("🏛 Да не здесь же, а в группе! 🌞")


@dp.message_handler(IsPrivate())
async def no_state_text(message: types.Message, state: FSMContext):
    logging.info(f"{state}")
