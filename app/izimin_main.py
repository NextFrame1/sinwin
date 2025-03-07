import asyncio
import platform
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app import handlers, utils
from app.api import APIRequest
from app.keyboards.inline import create_registration_markup, create_single_signal_markup
from app.loader import alerts, alerts_en, bot, config, dp, scheduleded_users, users_db
from app.utils.fileloader import get_file


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler

    async def __call__(self, handler, event, data):
        data["apscheduler"] = self.scheduler
        return await handler(event, data)


async def send_register_process_message(user_id, data):
    photo = get_file("reg.jpg", users_db.get_user_language(user_id))
    try:
        await data["message"].delete()
    except Exception:
        pass
    await bot.send_photo(
        chat_id=user_id,
        photo=photo,
        caption=(
            alerts["reg"]
            if users_db.get_user_language(user_id) == "RU_RU"
            else alerts_en["reg"]
        ),
        reply_markup=create_registration_markup(user_id, "start_income"),
    )


async def send_topup_process_message(user_id, data):
    photo2 = get_file("dep.jpg", users_db.get_user_language(user_id))
    await bot.send_photo(
        chat_id=user_id,
        photo=photo2,
        caption=(
            alerts["topup"]
            if users_db.get_user_language(user_id) == "RU_RU"
            else alerts_en["topup"]
        ),
        reply_markup=create_registration_markup(
            user_id, "change_life", "register_passed"
        ),
    )


async def send_signal_message(user_id, data, alert: str = "newsignal"):
    photo = get_file("gen.jpg", users_db.get_user_language(user_id))
    try:
        await data["message"].delete()
    except Exception:
        pass
    await bot.send_photo(
        chat_id=user_id,
        photo=photo,
        caption=(
            alerts[alert]
            if users_db.get_user_language(user_id) == "RU_RU"
            else alerts_en[alert]
        ),
        reply_markup=create_single_signal_markup(user_id),
    )


async def check_inactive_users():
    for user_id, data in scheduleded_users.items():
        time_difference = datetime.now() - data["date"]

        print(data["status"], time_difference, data.get("first", False))

        if data.get("first", False):
            if data["status"] == "register_process" and time_difference >= timedelta(
                hours=10
            ):
                await send_register_process_message(user_id, data)
            elif data["status"] == "topup_process" and time_difference >= timedelta(
                hours=10
            ):
                await send_topup_process_message(user_id, data)
            elif (
                data["status"] == "signal"
                and time_difference >= timedelta(hours=12)
                and data.get("signal15", False)
            ):
                await send_signal_message(user_id, data, "newsignal12")
            elif (
                data["status"] == "signal"
                and time_difference >= timedelta(minutes=15)
                and not data.get("signal15", False)
            ):
                await send_signal_message(user_id, data)
                data["signal15"] = True
            else:
                continue

            data["date"] = datetime.now()
        else:
            status = True
            if data["status"] == "register_process" and time_difference >= timedelta(
                minutes=44
            ):
                await send_register_process_message(user_id, data)
            elif data["status"] == "topup_process" and time_difference >= timedelta(
                minutes=44
            ):
                await send_topup_process_message(user_id, data)
            elif data["status"] == "signal" and time_difference >= timedelta(minutes=1):
                await send_signal_message(user_id, data)
            else:
                status = False

            data["first"] = status
            data["date"] = datetime.now()


async def total_messaging():
    for user_id, data in scheduleded_users.items():
        time_difference = datetime.now() - data["date"]

        if time_difference >= timedelta(hours=23):
            photo = get_file("gen.jpg", users_db.get_user_language(user_id))
            try:
                await data["message"].delete()
            except Exception:
                pass
            await bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=alerts["inactive24"],
                reply_markup=create_registration_markup(
                    user_id, "change_life", "homeprofile"
                ),
            )


async def on_startup() -> None:
    uname = platform.uname()

    system = f"Система: {uname.system} {uname.release}; Node: {uname.node}"

    await utils.setup_default_commands(bot)

    for admin_id in config.secrets.ADMINS_IDS:
        await bot.send_message(chat_id=admin_id, text=f"Бот был запущен в: {system}")


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(check_inactive_users, "interval", minutes=1)
    scheduler.add_job(total_messaging, "cron", hour=15, minute=0)

    dp.update.middleware(SchedulerMiddleware(scheduler=scheduler))

    scheduler.start()

    utils.setup_logger("INFO", ["sqlalchemy.engine", "aiogram.bot.api"])

    conn_ok, _ = await APIRequest.get("/base/info")
    if not conn_ok:
        logger.error("Fatal error: API dont connected")
        exit()

    dp.include_routers(handlers.commands_router)
    dp.include_routers(handlers.admin_router)

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
