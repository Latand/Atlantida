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
                            clear_table)


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

    async def send_poll_questions_in_chat(self):
        """
        Sends polls to all chats in the category with 10 questions (each 10 from the specific chat)
        """
        clear_table("winner_questions", self.category)
        for (_, chat, *_) in self.chats:
            questions = load_questions(chat)
            if questions:
                if len(questions) > 1:
                    poll_to_check = await self.bot.send_poll(
                        chat_id=chat,
                        question=self._("Какой вопрос задать Атлантиде?"),
                        options=[option[:97] + "..." for (option,) in questions],
                        disable_notification=False,
                        reply_to_message_id=None
                    )
                    add_winner_question(chat,
                                        self.category,
                                        poll_id=poll_to_check.message_id,
                                        message_id=poll_to_check.message_id)
                    await asyncio.sleep(0.1)

    async def _check_questions_best_in_chat(self):
        """
        Collects one best question in every chat from the category and adds to "winner_questions" table
        :returns: List of best questions
        :rtype: `list[str]`
        """
        questions = list()
        for (_, chat, *_) in self.chats:
            poll_id = get_winner_question_poll(chat)
            if poll_id:
                try:
                    poll = await self.bot.stop_poll(chat, message_id=poll_id)
                    best_question = sorted(poll.options, key=lambda p: p.voter_count, reverse=True)[0].text
                    questions.append(best_question)
                except PollHasAlreadyBeenClosed:
                    logging.info(f"POLL {chat}:{poll_id} has been closed")
            else:
                question = load_questions(chat)
                if question:
                    questions.append(question[0][0])
        return questions

    async def send_poll_questions_in_category(self):
        """
        Sends polls to all chats in the category with all best questions
        saves to db table `category_poll_questions`
        """
        clear_table("category_poll_questions", category=self.category)
        questions = await self._check_questions_best_in_chat()
        logging.info(f"BEST QUESTIONS IN CATEGORY {questions}")
        number_of_polls = len(questions) // 10 + 1
        if questions:
            for (_, chat, *_) in self.chats:
                for poll_n in range(number_of_polls):
                    index_from = poll_n * 10
                    index_to = (poll_n + 1) * 10
                    questions_in_poll = questions[index_from: index_to]
                    options = [option[:97] + "..." for option in questions_in_poll]
                    logging.info(f"OPTIONS = {options}")
                    poll_to_check = await self.bot.send_poll(
                        chat_id=chat,
                        question=self._("Какой вопрос задать Атлантиде?"),
                        options=options,
                        disable_notification=False,
                        reply_to_message_id=None
                    )
                    save_poll_question(chat_id=chat, category=self.category, poll_id=poll_to_check.message_id,
                                       page=poll_n)
                    await asyncio.sleep(1)

    async def check_poll_questions_in_category(self):
        """
        Checks all polls in all chats in category
        :return: Best question
        :rtype: `str`
        """

        def sum_poll_options(first: List[PollOption], second: List[PollOption]) -> List[PollOption]:
            new_options = list()
            for num, poll_option in enumerate(first):
                poll_option.voter_count += second[num].voter_count
                new_options.append(poll_option)
            return new_options

        def best_question(poll_options: List[PollOption]) -> str:
            return max(poll_options, key=lambda x: x.voter_count).text

        questions = dict()
        all_polls = get_all_polls_questions(self.category)
        if all_polls:
            logging.info(f"all polls {all_polls}")
            for poll in all_polls:
                chat_id, category, poll_id, page = poll
                try:
                    stopped_poll = await self.bot.stop_poll(chat_id, message_id=poll_id)
                    if page not in questions:
                        questions = {page: stopped_poll.options}
                    else:
                        questions[page] = sum_poll_options(questions[page], stopped_poll.options)

                    logging.info(f"NEW POLL OPTIONS {questions[page][0].text, questions[page][0].voter_count}")
                except PollHasAlreadyBeenClosed:
                    logging.error(f"Poll {chat_id}: {poll_id} has already been closed")
            question_options = list()
            for page in sorted(questions.keys()):
                question_options.extend(questions[page])

            return best_question(question_options)

    async def send_best_question_to_all(self):
        best_question = await self.check_poll_questions_in_category()
        if best_question:
            text = f"Победил вопрос: {best_question}"
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
        clear_table("questions", self.category)
        messages_to_delete = await questions()
        # People start sending questions

        await sleep(self.timeout)
        await delete_messages(messages_to_delete)
        await self.send_poll_questions_in_chat()
        # People in chat vote for best question

        await sleep(self.timeout)
        await self.send_poll_questions_in_category()
        # People in category vote for best question

        await sleep(self.timeout)
        await self.send_best_question_to_all()
        # People in category receive best questions and start answering

        await sleep(self.timeout)
        self.change_phase()

        # TODO

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
