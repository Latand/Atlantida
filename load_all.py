import asyncio
from aiogram import executor
from utils.database import get_chats, sql
from app import bot
import logging


async def update_numbers():
    logging.info("Started updating numbers")
    while True:
        for chat in get_chats():
            if not chat:
                continue
            try:
                count_users = await (await bot.get_chat(chat[1])).get_members_count()
            except Exception as err:
                logging.exception(err)
                await asyncio.sleep(1)
                continue
            logging.info(f"Counted {count_users} users in chat {chat[1]}")
            await asyncio.sleep(1)
            sql.update(table="chats",
                       count_users=count_users,
                       condition={"chat_id": chat[1]})

        await asyncio.sleep(60 * 60 * 20)


async def on_startup(dp):
    await asyncio.sleep(5)
    asyncio.ensure_future(update_numbers())


if __name__ == '__main__':
    from handlers.group.phases_handler import dp
    from handlers.group.registration import dp
    from handlers.private.registration import dp
    from handlers.private.other import dp

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
