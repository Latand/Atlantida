from typing import Tuple, Union

from aiogram.utils.callback_data import CallbackData

from utils.database import get_categories
from utils.keyboard_maker import InlineKeyboardButton, InlineKeyboardMarkup

page_change = CallbackData("page_change", "action", "current")


def create_pages(page: int = 1):
    data: Union[str, Tuple] = get_categories()
    if data:
        markup = InlineKeyboardMarkup()

        categories = data[(page - 1) * 5: page * 5]
        if not categories:
            return

        for num, (category,) in enumerate(categories):
            if not category:
                continue
            markup.add(InlineKeyboardButton(text=category, callback_data=category))

        markup.add(
            InlineKeyboardButton(text="<<", callback_data=page_change.new(action="-", current=page)),
            InlineKeyboardButton(text=">>", callback_data=page_change.new(action="+", current=page)),
        )
        return markup
