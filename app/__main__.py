import asyncio
import platform

from loguru import logger

from app import handlers, utils
from app.api import APIRequest
from app.loader import bot, config, dp, scheduler

from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class SchedulerMiddleware(BaseMiddleware):
	def __init__(self, scheduler: AsyncIOScheduler):
		self.scheduler = scheduler

	async def __call__(self, handler, event, data):
		data["apscheduler"] = self.scheduler
		return await handler(event, data)


async def on_startup() -> None:
	uname = platform.uname()

	system = f"Система:\n + {uname.system} {uname.release}\n + Node: {uname.node}"

	await utils.setup_default_commands(bot)

	for admin_id in config.secrets.ADMINS_IDS:
		await bot.send_message(chat_id=admin_id, text=f"Бот был запущен в: {system}")


async def main():
	conn_ok = await APIRequest.get("/base/info")
	if not conn_ok:
		logger.error("Fatal error: API dont connected")
		exit()

	utils.setup_logger("INFO", ["sqlalchemy.engine", "aiogram.bot.api"])

	dp.include_routers(handlers.register_router)
	dp.include_routers(handlers.default_router)

	scheduler.start()

	dp.update.middleware(SchedulerMiddleware(scheduler=scheduler))

	dp.startup.register(on_startup)

	try:
		logger.info("Start polling...")
		await bot.delete_webhook(drop_pending_updates=True)
		await dp.start_polling(bot, on_startup=on_startup)
	finally:
		logger.info("Close bot session...")
		await bot.session.close()


if __name__ == "__main__":
	asyncio.run(main())
