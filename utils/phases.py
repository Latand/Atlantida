from dataclasses import dataclass
from asyncio import sleep
import logging
import datetime
from aiogram import Bot
from typing import List
import asyncio
from functools import lru_cache
from aiogram.types import Message
from utils.database import (load_questions, add_winner_question,
                            delete_questions, questions_to_send,
                            save_sent, load_answers,
                            add_winner_answer, delete_answers, clear_table,
                            get_winner_answers, get_sent, get_chats)


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

    @property
    def chats(self):
        return get_chats(self.category)

    # async def send_poll_questions(self):
    #     chats = self.chats


    @property
    def time_left(self):
        now = datetime.datetime.now()
        return ((self.countdown + datetime.timedelta(seconds=self.timeout)) - now).total_seconds()

    async def start_phaser(self):
        logging.info("Phaser started")
        messages_to_delete = list()

        async def questions():
            clear_table("winner_answers", self.category)
            logging.info(f"ENTERING PHASE QUESTIONS")
            clear_table("sent_messages", self.category)
            global messages_to_delete
            return await send_to_all(self.bot, "🏛☀️Атлантида находится в режиме ⚡Связи.\n"
                                          "Пример создания 🗿Атланта:\n"
                                          "1-й 🌩СеансСвязи #В ...ВашВопрос? или #О ...ВашОтвет!\n"
                                          "2-й 🌩СеансСвязи Ваши ответы на выбранную 🌀Мысль",
                                     category=self.category)

        async def answers():
            clear_table("winner_questions", self.category)
            chats = load_questions(self.category)
            logging.info(f"Loaded Questions {chats}")
            best_option = 0, 0, 0
            for chat_id, poll_id, question, message_id in chats:
                try:
                    poll = await self.bot.stop_poll(chat_id=chat_id, message_id=poll_id)
                    voters_count = poll.options[0].voter_count
                    if voters_count > best_option[0]:
                        best_option = voters_count, chat_id, message_id
                        add_winner_question(chat_id, self.category, question, message_id, poll_id)
                except Exception as err:
                    logging.exception(err)

            logging.info(f"category {self.category} winner: {best_option}")
            delete_questions(self.category)
            load_questions_to_send = questions_to_send(self.category)
            logging.info(f"Loaded Questions to send {load_questions_to_send}")

            if not load_questions_to_send:
                self.running = False
                return
            for id_question, chat_id, question in load_questions_to_send:
                try:
                    text = f"☁️ {question}"
                    sent_message = await self.bot.send_message(chat_id, text)
                    save_sent(id_question, chat_id, sent_message.message_id)

                except Exception as err:
                    logging.exception(err)
                await sleep(0.05)

            # Sleep until users are answering
            await sleep(self.timeout)

            # Load answers
            loaded_answers = load_answers(self.category)
            logging.info(f"Loaded answers {loaded_answers}")
            for chat_id, poll_id, answer, message_id in loaded_answers:
                try:
                    poll = await self.bot.stop_poll(chat_id=chat_id, message_id=poll_id)
                    logging.info(f"{poll.options}")

                    voters_count = poll.options[0].voter_count
                    add_winner_answer(chat_id, self.category, answer, message_id, poll_id, voters_count)
                except Exception as err:
                    logging.exception(err)
            delete_answers(self.category)

            text = get_winner_answers(self.category)
            logging.info(f"Loaded winner answers {loaded_answers}")

            if text:
                logging.info(f"Chats = {self.chats}")
                for (chat,) in self.chats:
                    try:
                        await self.bot.send_message(chat, text)

                    except Exception as err:
                        logging.exception(err)

            # Delete messages
            sent_messages = get_sent(self.category)
            if sent_messages:
                for chat_id, _, message_id in sent_messages:
                    try:
                        await self.bot.delete_message(chat_id, message_id)

                    except Exception as err:
                        logging.exception(err)
                    await sleep(0.05)

        self.set_running()
        messages_to_delete = await questions()
        await sleep(self.timeout)
        self.change_phase()
        await delete_messages(messages_to_delete)
        await answers()
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
