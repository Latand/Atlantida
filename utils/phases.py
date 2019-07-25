from dataclasses import dataclass
from asyncio import sleep
import logging
import datetime
from aiogram import Bot
from typing import List
import asyncio
from aiogram.types import Message
from utils.database import (load_questions, add_winner_question,
                            delete_questions, questions_to_send,
                            save_sent, load_answers,
                            add_winner_answer, delete_answers, clear_table,
                            get_winner_answers, get_sent, get_chats)


@dataclass
class Phase:
    timeout: int = 20 * 60
    current: str = "Questions"
    countdown: datetime = datetime.datetime.now()
    running: bool = False
    QUESTIONS = "Questions"
    ANSWERS = "Answers"

    def set_running(self):
        self.running = True
        self.countdown: datetime = datetime.datetime.now()

    def disable(self):
        self.running = False

    def change_phase(self):
        self.countdown = datetime.datetime.now()

        if self.current == self.QUESTIONS:
            self.current = self.ANSWERS
        else:
            self.current = self.QUESTIONS

    @property
    def time_left(self):
        now = datetime.datetime.now()
        return ((self.countdown + datetime.timedelta(seconds=self.timeout)) - now).total_seconds()

    async def start_phaser(self):
        bot = Bot.get_current()
        # await sleep(5)  # Wait until dp loads
        logging.info("Phaser started")
        messages_to_delete = list()

        async def questions():
            clear_table("winner_answers")
            logging.info(f"ENTERING PHASE QUESTIONS")
            clear_table("sent_messages")
            global messages_to_delete
            return await send_to_all(bot, "🏛 🏘 КАТЕГОРИЯ находится в режиме ⚡Связи.\n"
                                          "Пример создания 🗿 #А :\n"
                                          "#В ...ВашВопрос? или #О ...ВашОтвет!")

        async def answers():
            clear_table("winner_questions")
            for category, chats in load_questions():
                best_option = 0, 0, 0
                for chat_id, poll_id, question, message_id in chats:
                    try:
                        poll = await bot.stop_poll(chat_id=chat_id, message_id=poll_id)
                        logging.info(f"{poll.options}")
                        voters_count = poll.options[0].voter_count
                        if voters_count > best_option[0]:
                            best_option = voters_count, chat_id, message_id
                            add_winner_question(chat_id, category, question, message_id, poll_id)
                    except Exception as err:
                        logging.exception(err)
                logging.info(f"category {category} winner: {best_option}")
            delete_questions()
            l_questions_to_send = questions_to_send()
            if not l_questions_to_send:
                self.running = False
                return
            for id_question, chat_id, question in l_questions_to_send:
                try:
                    sent_message = await bot.send_message(chat_id, question)
                    save_sent(id_question, chat_id, sent_message.message_id)

                except Exception as err:
                    logging.exception(err)
                await sleep(0.05)

            # Sleep until users are answering
            await sleep(self.timeout)

            # Load answers
            for category, chats in load_answers():
                for chat_id, poll_id, answer, message_id in chats:
                    try:
                        poll = await bot.stop_poll(chat_id=chat_id, message_id=poll_id)
                        logging.info(f"{poll.options}")

                        voters_count = poll.options[0].voter_count
                        add_winner_answer(chat_id, category, answer, message_id, poll_id, voters_count)
                    except Exception as err:
                        logging.exception(err)
            delete_answers()

            winner_answers = get_winner_answers()
            if winner_answers:
                for chats, text in winner_answers:
                    for (chat,) in chats:
                        try:
                            await bot.send_message(chat, text)

                        except Exception as err:
                            logging.exception(err)

            # Delete messages
            sent_messages = get_sent()
            if sent_messages:
                for chat_id, _, message_id in sent_messages:
                    try:
                        await bot.delete_message(chat_id, message_id)

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


async def delete_messages(messages: List[Message]):
    logging.info(f"Starting to delete notification messages")
    for message in messages:
        try:
            await message.delete()
        except Exception as err:
            logging.error(err)


async def send_to_all(bot, m):
    messages = []
    for id, chat_id, *_ in get_chats():
        try:
            messages.append(await bot.send_message(chat_id, m, disable_notification=True))
        except Exception as err:
            logging.error(err)
        finally:
            await sleep(0.05)
    return messages
