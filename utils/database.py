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


def add_question(chat_id, question, message_id, category):
    if sql.select(where="questions", what="COUNT(*)", condition=dict(chat_id=chat_id)) < 10:
        sql.insert(table="questions", chat_id=chat_id, question=question, message_id=message_id,
                   category=category)
        return True
    else:
        return False


def add_answer(chat_id, answer, message_id, poll_id):
    sql.insert(table="answers", chat_id=chat_id, answer=answer, message_id=message_id, poll_id=poll_id)


def load_questions(chat_id):
    return sql.select(where="questions q",
                      what="q.question",
                      condition={"q.chat_id": chat_id}, multiple=True)


def load_answers(category):
    return sql.select(where="answers q, chats c",
                      what="q.chat_id, q.poll_id, q.answer, q.message_id",
                      condition={"q.chat_id": "=c.chat_id",
                                 "c.category": category})


def add_winner_question(chat_id, category, question=None, message_id=None):
    sql.exec_raw("INSERT INTO winner_questions (chat_id, category, question, message_id) "
                 "VALUES (%s, %s, %s, %s)", chat_id, category, question, message_id)


def get_winner_question_poll(chat_id):
    return sql.select(where="winner_questions", what="poll_id", condition=dict(chat_id=chat_id))


def load_winner_questions_in_category(category):
    return sql.select(where="winner_questions", what="question", condition=dict(category=category), multiple=True)


def get_winner_question_category(category):
    return sql.select(where="winner_questions", what="question", condition=dict(category=category))


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


def save_poll_question(chat_id, category, poll_id, page):
    sql.insert(table="category_poll_questions",
               chat_id=chat_id, category=category, poll_id=poll_id, page=page)


def get_all_polls_questions(category):
    return sql.select(where="category_poll_questions", condition=dict(category=category), multiple=True)


def vote_for_question_db(user, chat, category, text, message_id):
    if sql.exec_raw("SELECT COUNT(*) "
                    "FROM questions_voting "
                    "WHERE user=%s AND id_chat=%s AND category=%s", user, chat, category,
                    select=True):
        sql.exec_raw("UPDATE questions_voting "
                     "SET message_id=%s, text=%s "
                     "WHERE user=%s AND category=%s AND id_chat=%s", message_id, text, user, category, chat)
        return "Changed"
    else:
        sql.exec_raw("INSERT INTO questions_voting (text, id_chat, category, user, message_id) "
                     "VALUES (%s, %s, %s, %s, %s)", text, chat, category, user, message_id)
        return "Voted"


def vote_for_answer_db(user, chat, category, text, message_id, q_message_id):
    if sql.exec_raw("SELECT COUNT(*) "
                    "FROM answers_voting "
                    "WHERE user=%s AND id_chat=%s AND category=%s AND q_message_id=%s",
                    user, chat, category, q_message_id,
                    select=True):
        sql.exec_raw("UPDATE answers_voting "
                     "SET message_id=%s, text=%s, q_message_id=%s "
                     "WHERE user=%s AND category=%s AND id_chat=%s",
                     message_id, text, q_message_id, user, category, chat)
        return "Changed"
    else:
        sql.exec_raw("INSERT INTO answers_voting (text, id_chat, category, user, message_id, q_message_id) "
                     "VALUES (%s, %s, %s, %s, %s, %s)", text, chat, category, user, message_id, q_message_id)
        return "Voted"


def collect_best_questions(category):
    rows = sql.exec_raw("SELECT id_chat, message_id, text, COUNT(*) "
                        "FROM questions_voting "
                        "WHERE category='кат' "
                        "GROUP BY id_chat, message_id, text", category, select=True)
    return rows


def collect_best_answers(category):
    rows = sql.exec_raw("SELECT DISTINCT(answers_voting.text) answer, winner_questions.question, COUNT(*) c "
                        "FROM answers_voting, winner_questions "
                        "WHERE answers_voting.category = 'cat' "
                        "  AND winner_questions.message_id=answers_voting.q_message_id "
                        "GROUP BY answers_voting.text, winner_questions.question "
                        "ORDER BY c DESC "
                        "LIMIT 1", category, select=True)
    return rows
