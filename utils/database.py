from Mysql.sql import sql
import logging
from aiogram.types import Message
from typing import List


def clear_table(table, category: str):
    command = f"""DELETE t FROM {table} t 
LEFT JOIN chats c ON c.chat_id = t.chat_id
WHERE c.category = %s
"""
    sql.execute(command, (category,))


def add_chat(chat_id) -> bool:
    exists = sql.select(where="chats", condition={"chat_id": chat_id})
    if not exists:
        logging.info(chat_id)
        sql.insert(table="chats", chat_id=chat_id)
        return False
    else:
        return True


def get_categories(language=None):
    return sql.select(what="DISTINCT category", where="chats",
                      condition=dict(language=language) if language else None,
                      multiple=True)


def get_category(chat_id):
    return sql.select(what="category", where="chats", condition=dict(chat_id=chat_id))


def add_category(chat_id, category, language):
    if sql.select(where="chats", condition={"chat_id": chat_id}):
        sql.update(table="chats", category=category, language=language, condition=dict(chat_id=chat_id))


def add_question(chat_id, question, message_id, poll_id):
    sql.insert(table="questions", chat_id=chat_id, question=question, message_id=message_id, poll_id=poll_id)


def add_answer(chat_id, answer, message_id, poll_id):
    sql.insert(table="answers", chat_id=chat_id, answer=answer, message_id=message_id, poll_id=poll_id)


def load_questions(category):
    return sql.select(where="questions q, chats c",
                      what="q.chat_id, q.poll_id, q.question, q.message_id",
                      condition={"q.chat_id": "=c.chat_id",
                                 "c.category": category})


def load_answers(category):
    return sql.select(where="answers q, chats c",
                      what="q.chat_id, q.poll_id, q.answer, q.message_id",
                      condition={"q.chat_id": "=c.chat_id",
                                 "c.category": category})


def add_winner_question(chat_id, category, question, message_id, poll_id):
    if sql.select(where="winner_questions", condition={"category": category}):
        sql.update(table="winner_questions",
                   chat_id=chat_id, message_id=message_id,
                   question=question, poll_id=poll_id,
                   condition=dict(category=category))
    else:
        sql.insert(table="winner_questions", chat_id=chat_id, message_id=message_id,
                   question=question, poll_id=poll_id,
                   category=category)


def add_winner_answer(chat_id, category, answer, message_id, poll_id, vote_count):
    sql.insert(table="winner_answers", chat_id=chat_id, message_id=message_id,
               answer=answer, poll_id=poll_id,
               category=category, vote_count=vote_count)


def get_chats(category=None):
    if category:
        return sql.select(where="chats",
                          condition=dict(category=category),
                          multiple=True)
    else:
        return sql.select(where="chats", multiple=True)


def get_winner_question(category: str):
    return sql.select(where="winner_questions", what="question", condition=dict(category=category))


def get_winner_question_id(chat_id):
    return sql.select(what="s.message_id", where="winner_questions w, chats, sent_messages s",
                      condition={"chats.category": "=w.category",
                                 "chats.chat_id": chat_id,
                                 "s.chat_id": chat_id,
                                 "w.id": "=s.id_question"})


def get_winner_answers(category):
    answers = sql.select(where="winner_answers",
                         what="answer",
                         order="vote_count DESC",
                         limit=3,
                         multiple=True,
                         condition={"category": category})
    question = get_winner_question(category)
    if question and answers:
        emo = ["☀️", "🌤️", "⛅️"]
        text = f"☁️ {question}\n\n"
        text += "\n".join([f"{emo[num]} {answer}" for num, (answer,) in enumerate(answers)])
        text += "\n\n#А"
        return text


def delete_questions(category):
    clear_table("questions", category)


def delete_answers(category):
    clear_table("answers", category)


def questions_to_send(category):
    return sql.select(where="winner_questions w, chats c",
                      what="w.id, c.chat_id, w.question",
                      condition={"w.category": category,
                                 "c.chat_id": "w.chat_id"})


def save_sent(id_question, chat_id, message_id):
    sql.insert(table="sent_messages", id_question=id_question, chat_id=chat_id, message_id=message_id)


def get_sent(category):
    return sql.select(where="sent_messages s, chats c",
                      condition={"s.chat_id": "c.chat_id",
                                 "c.category": category})


def get_count_for_category(category):
    count_users = sql.select(where="chats", what="SUM(count_users)", condition={"category": category})
    count_chats = sql.select(where="chats", what="COUNT(*)", condition={"category": category})
    return count_chats, count_users


def set_new_lang(chat_id, language):
    sql.update(table="chats", language=language, condition=dict(chat_id=chat_id))


def save_no_phase(messages: List[Message]):
    for message in messages:
        sql.insert(table="no_phase_message", chat_id=message.chat.id, message_id=message.message_id)
