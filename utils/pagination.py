from typing import Tuple, Union

from aiogram.utils.callback_data import CallbackData

from utils.database import get_categories, get_count_for_category
from utils.keyboard_maker import InlineKeyboardButton, InlineKeyboardMarkup

page_change = CallbackData("page_change", "action", "current")


def create_pages(page: int = 1, language: str = "ru"):
    data: Union[str, Tuple] = get_categories(language)
    markup = InlineKeyboardMarkup()
    if data:

        categories = data[(page - 1) * 5: page * 5]
        if not categories:
            return

        for num, (category,) in enumerate(categories):
            if not category:
                continue
            text = "{} ({}; {})".format(category, *get_count_for_category(category))
            markup.add(InlineKeyboardButton(text=text, callback_data=category))

    markup.add(
        InlineKeyboardButton(text="<<", callback_data=page_change.new(action="-", current=page)),
        InlineKeyboardButton(text=">>", callback_data=page_change.new(action="+", current=page)),
    )
    return markup
