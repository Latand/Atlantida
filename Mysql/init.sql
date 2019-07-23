USE db;
create table IF NOT EXISTS chats
(
    id       int auto_increment                     not null,
    chat_id  BIGINT                                 not null,
    date     timestamp    default CURRENT_TIMESTAMP not null,
    category VARCHAR(100) DEFAULT NULL,

    primary key (id, chat_id)
) COLLATE utf8mb4_general_ci;

create table IF NOT EXISTS questions
(
    id       int auto_increment                     not null,
    chat_id  BIGINT                                 not null,
    question TEXT NOT NULL,
    message_id BIGINT NOT NULL,
    poll_id BIGINT NOT NULL,
    date     timestamp    default CURRENT_TIMESTAMP not null,

    primary key (id, chat_id, message_id)
) COLLATE utf8mb4_general_ci;


create table IF NOT EXISTS winner_questions
(
    id       int auto_increment                     not null,
    chat_id  BIGINT                                 not null,
    category VARCHAR(1000),
    question TEXT NOT NULL,
    message_id BIGINT NOT NULL,
    poll_id BIGINT NOT NULL,
    date     timestamp    default CURRENT_TIMESTAMP not null,

    primary key (id, chat_id, message_id)
) COLLATE utf8mb4_general_ci;

create table sent_messages
(
    chat_id     bigint not null,
    id_question int    not null,
    message_id  int    not null
);


create table IF NOT EXISTS answers
(
    id       int auto_increment                     not null,
    chat_id  BIGINT                                 not null,
    answer TEXT NOT NULL,
    message_id BIGINT NOT NULL,
    poll_id BIGINT NOT NULL,
    date     timestamp    default CURRENT_TIMESTAMP not null,

    primary key (id, chat_id, message_id)
) COLLATE utf8mb4_general_ci;


create table IF NOT EXISTS winner_answers
(
    id       int auto_increment                     not null,
    chat_id  BIGINT                                 not null,
    category VARCHAR(1000),
    answer TEXT NOT NULL,
    message_id BIGINT NOT NULL,
    poll_id BIGINT NOT NULL,
    vote_count int not null,
    date     timestamp    default CURRENT_TIMESTAMP not null,

    primary key (id, chat_id, message_id)
) COLLATE utf8mb4_general_ci;

