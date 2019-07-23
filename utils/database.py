from Mysql.sql import sql
import logging


def clear_table(table):
    sql.delete(table=table)


def add_chat(chat_id) -> bool:
    exists = sql.select(where="chats", condition={"chat_id": chat_id})
    if not exists:
        logging.info(chat_id)
        sql.insert(table="chats", chat_id=chat_id)
        return False
    else:
        return True


def get_categories():
    return sql.select(what="DISTINCT category", where="chats", multiple=True)


def add_category(chat_id, category):
    if sql.select(where="chats", condition={"chat_id": chat_id}):
        sql.update(table="chats", category=category, condition=dict(chat_id=chat_id))


def add_question(chat_id, question, message_id, poll_id):
    sql.insert(table="questions", chat_id=chat_id, question=question, message_id=message_id, poll_id=poll_id)


def add_answer(chat_id, answer, message_id, poll_id):
    sql.insert(table="answers", chat_id=chat_id, answer=answer, message_id=message_id, poll_id=poll_id)


def load_questions():
    categories = sql.select(where="questions q, chats c",
                            what="DISTINCT c.category",
                            condition={"q.chat_id": "=c.chat_id"},
                            multiple=True)
    data = []
    if categories:
        for (category,) in categories:
            chats = sql.select(where="questions q, chats c",
                               what="q.chat_id, q.poll_id, q.question, q.message_id",
                               condition={"q.chat_id": "=c.chat_id",
                                          "c.category": category})
            data.append([category, chats])
    logging.info(str(data))
    return data


def load_answers():
    categories = sql.select(where="answers q, chats c",
                            what="DISTINCT c.category",
                            condition={"q.chat_id": "=c.chat_id"},
                            multiple=True)
    data = []
    if categories:
        for (category,) in categories:
            chats = sql.select(where="answers q, chats c",
                               what="q.chat_id, q.poll_id, q.answer, q.message_id",
                               condition={"q.chat_id": "=c.chat_id",
                                          "c.category": category})
            data.append([category, chats])
    logging.info("ANSWERS:")
    logging.info(str(data))
    return data


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
                          what="chat_id",
                          condition=dict(category=category),
                          multiple=True)
    else:
        return sql.select(where="chats")


def get_winner_question(category: str):
    return sql.select(where="winner_questions", what="question", condition=dict(category=category))


def get_winner_question_id(chat_id):
    return sql.select(what="s.message_id", where="winner_questions w, chats, sent_messages s",
                      condition={"chats.category": "=w.category",
                                 "chats.chat_id": chat_id,
                                 "s.chat_id": chat_id,
                                 "w.id": "=s.id_question"})


def get_winner_answers():
    categories = get_categories()
    data = []
    for (category,) in categories:
        answers = sql.select(where="winner_answers",
                             what="answer",
                             order="vote_count DESC",
                             limit=3,
                             multiple=True)
        question = get_winner_question(category)
        if question and answers:
            emo = ["☀️", "🌤️", "⛅️"]
            text = f"☁️ {question}\n\n"
            text += "\n".join([f"{emo[num]} {answer}" for num, (answer,) in enumerate(answers)])
            text += "\n\n#О"
            chats = get_chats(category)
            logging.info(f"Chats for winners {chats}")
            data.append([chats, text])
    return data


def delete_questions():
    clear_table("questions")


def delete_answers():
    clear_table("answers")


def questions_to_send():
    return sql.select(where="winner_questions w, chats c",
                      what="w.id, c.chat_id, w.question",
                      condition={"w.category": "=c.category"})


def save_sent(id_question, chat_id, message_id):
    sql.insert(table="sent_messages", id_question=id_question, chat_id=chat_id, message_id=message_id)


def get_sent():
    return sql.select(where="sent_messages")
