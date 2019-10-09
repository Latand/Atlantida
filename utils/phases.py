import asyncio
import datetime
import logging
from asyncio import sleep
from dataclasses import dataclass
from functools import lru_cache
from typing import List
from aiogram.types.poll import PollOption

from aiogram import Bot
from aiogram.utils.exceptions import PollHasAlreadyBeenClosed
from aiogram.types import Message

from app import _
from utils.database import (load_questions, add_winner_question,
    # delete_questions, questions_to_send,
    # save_sent, load_answers,
    # add_winner_answer, delete_answers, clear_table,
                            get_winner_answers, get_sent, get_chats,
                            get_winner_question_poll,
                            save_poll_question,
                            get_all_polls_questions,
                            clear_table, collect_best_questions, collect_best_answers)


@dataclass
class Phase:
    category: str
    last_chat_run: int = None
    timeout: int = 6 * 60
    current: str = "Questions"
    countdown: datetime = datetime.datetime.now()
    running: bool = False
    QUESTIONS = "Questions"
    ANSWERS = "Answers"
    bot: Bot = None
    language: str = None

    def set_running(self):
        self.running = True
        self.countdown: datetime = datetime.datetime.now()
        self.current: str = "Questions"
        self.bot = Bot.get_current()

    def disable(self):
        self.running = False

    def change_phase(self):
        self.countdown = datetime.datetime.now()

        if self.current == self.QUESTIONS:
            self.current = self.ANSWERS
        else:
            self.current = self.QUESTIONS

    def was_the_last(self, chat_id):
        return chat_id == self.last_chat_run

    def _(self, var):
        return _(var, locale=self.language)

    @property
    def chats(self):
        return get_chats(self.category)

    async def send_to_all(self, *args, **kwargs):
        messages = list()
        for (_, chat, *_) in self.chats:
            messages.append(await self.bot.send_message(chat, *args, **kwargs))
            await sleep(0.1)
        return messages

    async def collect_questions_in_category(self):
        best_questions = collect_best_questions(self.category)
        for question in best_questions:
            id_chat, message_id, text, count = question
            add_winner_question(id_chat, self.category, text, message_id)
            text = f"#Q {text}"

            await self.send_to_all(text=text)

    async def collect_answers_in_category(self):
        best_answers = collect_best_answers(self.category)
        for answer in best_answers:
            id_chat, message_id, text, count = answer
            text = f"#A {text}"

            await self.send_to_all(text=text)

    @property
    def time_left(self):
        now = datetime.datetime.now()
        return ((self.countdown + datetime.timedelta(seconds=self.timeout)) - now).total_seconds()

    async def start_phaser(self):
        logging.info("Phaser started")

        async def questions():
            logging.info(f"ENTERING PHASE QUESTIONS")
            return await self.send_to_all(
                text=f"🏛☀{self.category} находится в режиме ⚡Связи.\n"
                f"Пример создания 🗿Атланта:\n"
                f"1-й 🌩СеансСвязи #В ...ВашВопрос? или #О ...ВашОтвет!\n"
                f"2-й 🌩СеансСвязи Ваши ответы на выбранную 🌀Мысль")

        self.set_running()
        clear_table("questions_voting", self.category)
        messages_to_delete = await questions()
        await sleep(self.timeout)

        # People start sending questions and vote for best question
        ###########
        # Voting for questions
        ###########
        await delete_messages(messages_to_delete)
        await self.collect_questions_in_category()
        self.change_phase()
        await sleep(self.timeout)

        # People in category receive best questions and start answering
        ###########
        # Giving answers and voting for them
        ###########



        self.disable()


@lru_cache()
def get_phase(category):
    return Phase(category=category)


async def delete_messages(messages: List[Message]):
    logging.info(f"Starting to delete notification messages")
    for message in messages:
        try:
            await message.delete()
        except Exception as err:
            logging.error(err)


async def send_to_all(bot, m, category: str = None):
    messages = []
    for id, chat_id, *_ in get_chats(category=category):
        try:
            messages.append(await bot.send_message(chat_id, m, disable_notification=True))
        except Exception as err:
            logging.error(err)
        finally:
            await sleep(0.05)
    return messages
