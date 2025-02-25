from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hermes_langlib.locales import LocaleManager
from hermes_langlib.storage import load_config as i18n_load_config

from app.config import get_config, load_config
from app.database._debug import UsersDebug

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

config = load_config(get_config('config.ini'))
i18n_config = i18n_load_config('i18n.toml')

locale_manager = LocaleManager(i18n_config, locales=['default.json'])

users_db = UsersDebug()

bot = Bot(token=config.secrets.TOKEN)

dp = Dispatcher(storage=MemoryStorage())
