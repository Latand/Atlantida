from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from app import dp, logging, _
from utils.database import add_category
from utils.filters import IsPrivate
from utils.pagination import create_pages, page_change
from utils.states import Registration
from aiogram.utils.callback_data import CallbackData

language_callback = CallbackData("language", "code")


@dp.callback_query_handler(IsPrivate(), language_callback.filter(), state=Registration.Language)
async def choose_language(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    language = callback_data.get("code")
    markup = create_pages(language=language)
    await state.update_data(language=language)
    text = _("Язык {language} был установлен.\n").format(language=language)
    text += _("Создайте расположение Вашего 🏡чата/канала или выберите из предложенного списка:\n")
    text += _("\n\n"
              "Нажмите /cancel для отмены.")

    await call.message.edit_text(text, reply_markup=markup)
    await Registration.next()


@dp.message_handler(IsPrivate(), state=Registration.WaitForCategory)
async def category_text(message: types.Message, state: FSMContext):
    category = message.text
    if len(category) > 50:
        return await message.answer(_("Слишком длинное название"))
    data = await state.get_data()
    await state.finish()
    chat = data.get("chat_id")
    language = data.get("language")
    add_category(chat, category, language)
    await message.answer(_("🏛 Вы расположились в 🏘 {category}. "
                           "Для изменения расположения 🏡 введите команду connect в Вашем 🏡канале/чате\n"
                           ).format(category=category))


@dp.callback_query_handler(IsPrivate(), page_change.filter(), state=Registration.WaitForCategory)
async def page_change_call(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    action = callback_data.get("action")
    current_page = int(callback_data.get("current"))

    data = await state.get_data()
    language = data.get("language")
    new_page = {
        "+": current_page + 1,
        "-": current_page - 1
    }[action]

    markup = create_pages(new_page, language)
    if not markup:
        new_page_text = _("Следующей") if action == "+" else _("Предыдущей")
        await call.answer(_("{new_page_text} страницы не существует").format(new_page_text=new_page_text))

    else:
        await call.message.edit_reply_markup(markup)


@dp.callback_query_handler(IsPrivate(), state=Registration.WaitForCategory)
async def category_call(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    category = call.data
    data = await state.get_data()
    await state.finish()

    chat = data.get("chat_id")
    language = data.get("language")
    add_category(chat, category, language)

    await call.message.answer(_("🏛 Поздравляем! ⚡️Связь с 🏘 {category} установлена!\n").format(
        category=category))
