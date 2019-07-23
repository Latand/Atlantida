import asyncio
from aiogram import executor


async def on_startup(dp):
    await asyncio.sleep(5)


if __name__ == '__main__':
    from handlers.group_chats import dp
    from handlers.private_chat import dp

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
