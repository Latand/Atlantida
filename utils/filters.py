from dataclasses import dataclass

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types.chat import ChatType
import logging
from utils.database import sql


@dataclass
class IsGroup(BoundFilter):

    async def check(self, message: types.Message):
        return ChatType.is_channel(message.chat) or ChatType.is_group_or_super_group(message.chat)


@dataclass
class AskedQuestion(BoundFilter):

    async def check(self, message: types.Message):
        logging.info(message.text)
        text = message.text.lower()
        if text.startswith("#в ") or text.startswith("#о "):
            if ChatType.is_channel(message.chat) or ChatType.is_group_or_super_group(message.chat):
                return bool(sql.select(where="chats", condition=dict(chat_id=message.chat.id)))


@dataclass
class AnsweredQuestionPhase(BoundFilter):

    async def check(self, message: types.Message):
        if ChatType.is_channel(message.chat) or ChatType.is_group_or_super_group(message.chat):
            rp = message.reply_to_message
            if rp:
                rp = rp.message_id
                chat_id = message.chat.id
                return bool(sql.select(where="sent_messages", condition=dict(chat_id=chat_id, message_id=rp)))


@dataclass
class AnsweredQuestionNoPhase(BoundFilter):

    async def check(self, message: types.Message):
        if ChatType.is_channel(message.chat) or ChatType.is_group_or_super_group(message.chat):
            rp = message.reply_to_message
            if rp:
                rp = rp.message_id
                chat_id = message.chat.id
                return bool(sql.select(where="no_phase_message", condition=dict(chat_id=chat_id, message_id=rp)))


@dataclass
class IsPrivate(BoundFilter):

    async def check(self, message: types.Message):
        if isinstance(message, types.CallbackQuery):
            message = message.message

        return ChatType.is_private(message.chat)
