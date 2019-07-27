from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types
from config import I18N_DOMAIN, LOCALES_DIR
from utils.database import sql
import logging


def get_lang(chat_id):
    return sql.select(what="language", where="chats", condition={"chat_id": chat_id})


class ACLMiddleware(I18nMiddleware):
    """
    Modified i18n middleware
    """

    async def get_user_locale(self, action, args):
        chat = types.Chat.get_current()
        lang = get_lang(chat.id)
        logging.info(f"Language is {lang}")
        return lang or None


def setup_middleware(dp):
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)

    dp.middleware.setup(i18n)
    return i18n
