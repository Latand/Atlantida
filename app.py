import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(token=TOKEN, loop=loop, parse_mode="HTML")
storage = MemoryStorage()
# storage = RedisStorage2(host="172.22.0.1")
dp = Dispatcher(bot, storage=storage)

