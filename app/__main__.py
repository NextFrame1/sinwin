import asyncio
import platform
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from aiogram import BaseMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app import handlers, utils
from app.api import APIRequest
from app.loader import bot, config, dp, scheduler, loaded_achievements, ACHIEVEMENTS, convert_to_human, user_achievements


class SchedulerMiddleware(BaseMiddleware):
	def __init__(self, scheduler: AsyncIOScheduler):
		self.scheduler = scheduler

	async def __call__(self, handler, event, data):
		data['apscheduler'] = self.scheduler
		return await handler(event, data)


async def on_startup() -> None:
	uname = platform.uname()

	system = f'Система:\n + {uname.system} {uname.release}\n + Node: {uname.node}'

	await utils.setup_default_commands(bot)

	for admin_id in config.secrets.ADMINS_IDS:
		await bot.send_message(chat_id=admin_id, text=f'Бот был запущен в: {system}')


async def collect_stats(opts: dict):
	result, status = await APIRequest.post("/user/find", {"opts": opts})

	# if opts.get('game', False):
	# result_incomes, status2 = await APIRequest.get(f"/base/incomes?game={opts['game']}")
	# incomes = result_incomes["income_stat"]
	# postbacks = result_incomes["postbacks_stat"]

	today = datetime.now().date()
	yesterday = today - timedelta(days=1)
	last_week_start = today - timedelta(days=today.weekday() + 7)
	last_week_end = last_week_start + timedelta(days=6)
	last_month_start = today - relativedelta(months=1)
	last_month_end = last_month_start + relativedelta(day=31)

	users = result["users"]

	users_count = len(users)
	users_income = sum([user["income"] for user in users])
	users_notreg_count = len([user for user in users if not user["approved"]])
	users_nottopup_count = len(
		[user for user in users if user["balance"] < 500.0 and user["approved"]]
	)
	users_gamed_count = len(
		[user for user in users if user["balance"] > 500.0 and user["approved"]]
	)

	users_today = [
		user
		for user in users
		if datetime.strptime(user["register_date"], "%Y-%m-%dT%H:%M:%S").date() == today
	]
	users_yesterday = [
		user
		for user in users
		if datetime.strptime(user["register_date"], "%Y-%m-%dT%H:%M:%S").date()
		== yesterday
	]
	users_lastweek = [
		user
		for user in users
		if last_week_start
		<= datetime.strptime(user["register_date"], "%Y-%m-%dT%H:%M:%S").date()
		<= last_week_end
	]
	users_month = [
		user
		for user in users
		if last_month_start
		<= datetime.strptime(user["register_date"], "%Y-%m-%dT%H:%M:%S").date()
		<= last_month_end
	]

	users_today = len(users_today)
	users_yesterday = len(users_yesterday)
	users_lastweek = len(users_lastweek)
	users_month = len(users_month)

	return {
		"users_count": users_count,
		"users_today": users_today,
		"users_yesterday": users_yesterday,
		"users_lastweek": users_lastweek,
		"users_month": users_month,
		"users_notreg_count": users_notreg_count,
		"users_nottopup_count": users_nottopup_count,
		"users_gamed_count": users_gamed_count,
		"users_income": users_income,
	}


def check_achievements_for_reload(users_count, income, deposits_sum, first_deposits_count, referrals_count, signals_count):
	thresholds = {
		'users_count': [str(users_count)],
		'deposits_sum': [str(deposits_sum)],
		'income': [str(income)],
		'first_deposits_count': [str(first_deposits_count)],
		'referrals_count': [str(referrals_count)],
		'signals_count': [str(signals_count)],
	}

	for threshold in ACHIEVEMENTS["users"]:
		if users_count >= threshold:
			thresholds['users_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS["deposits"]:
		if deposits_sum >= threshold:
			thresholds['deposits_sum'].append(convert_to_human(threshold))
	
	for threshold in ACHIEVEMENTS["income"]:
		if income >= threshold:
			thresholds['income'].append(convert_to_human(threshold))

	for threshold in ACHIEVEMENTS["first_deposits"]:
		if first_deposits_count >= threshold:
			thresholds['first_deposits_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS["referrals"]:
		if referrals_count<= threshold:
			thresholds['referrals_count'].append(str(threshold))
			break

	for threshold in ACHIEVEMENTS["signals"]:
		if signals_count < threshold:
			thresholds['signals_count'].append(str(threshold))
			break
	
	count = len(thresholds["users_count"]) + len(thresholds["signals_count"]) + len(thresholds["deposits_sum"]) + len(thresholds["income"]) + len(thresholds["first_deposits_count"]) + len(thresholds["referrals_count"]) - 6

	return {
		'count': count,
		'thresholds': thresholds,
	}


async def achievs_alerts():
	for userid, data in loaded_achievements.items():
		if not user_achievements.get(userid, {}).get('alerts', True):
			continue

		partners = await APIRequest.post(
			"/partner/find", {"opts": {"tg_id": userid, "approved": True}}
		)
		partner = partners[0]["partners"]
	
		if partner:
			partner = partner[-1]
		else:
			continue

		result, code = await APIRequest.get(f"/base/achstats?partnerhash={partner["partner_hash"]}")

		cpartners = await APIRequest.post(
			"/partner/find", {"opts": {"referrer_hash": partner["partner_hash"]}}
		)
		cpartners = cpartners[0]["partners"]

		opts = {"game": "Mines", "referal_parent": partner["partner_hash"]}
		data = await collect_stats(opts)

		achievements = check_achievements_for_reload(data['users_count'], result['income'], result['deposits_sum'], result['first_deposits_count'])

		count = achievements['count']
		thresholds = achievements['thresholds']

		# thresholds_data = {
		# 	'users_count': ['0'],
		# 	'deposits_sum': ['0'],
		# 	'income': ['0'],
		# 	'first_deposits_count': ['0'],
		# }

		loaded_achievs = loaded_achievements.get(userid, {})

		loaded_achievements[userid] = achievements

		loaded_count = loaded_achievs.get('count')

		if loaded_count > count:
			loaded_thresholds = loaded_achievs['thresholds']

			users_count = list(set(loaded_thresholds['users_count']) - set(thresholds['users_count']))
			deposits_sum = list(set(loaded_thresholds['deposits_sum']) - set(thresholds['deposits_sum']))
			income = list(set(loaded_thresholds['income']) - set(thresholds['income']))
			first_deposits_count = list(set(loaded_thresholds['first_deposits_count']) - set(thresholds['first_deposits_count']))
			referrals_count = list(set(loaded_thresholds['referrals_count']) - set(thresholds['referrals_count']))
			signals_count = list(set(loaded_thresholds['signals_count']) - set(thresholds['signals_count']))

			if users_count:
				for data in users_count:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Пользователи по вашим ссылкам: больше {data}.')

			if deposits_sum:
				for data in deposits_sum:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Депозиты: больше {convert_to_human(data)} рублей.')

			if income:
				for data in income:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Доход: больше {convert_to_human(data)} рублей.')
			
			if first_deposits_count:
				for data in first_deposits_count:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Количество первых депозитов: больше {data}.')
			
			if referrals_count:
				for data in referrals_count:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Количество рефералов: больше {data}.')

			if signals_count:
				for data in signals_count:
					await bot.send_message(chat_id=userid, text=f'Достижение успешно выполнено.\n\n✅ Сгенерировано сигналов: больше {data}.')


async def main():
	conn_ok = await APIRequest.get('/base/info')
	if not conn_ok:
		logger.error('Fatal error: API dont connected')
		exit()

	utils.setup_logger('INFO', ['sqlalchemy.engine', 'aiogram.bot.api'])

	dp.include_routers(handlers.register_router)
	dp.include_routers(handlers.default_router)

	scheduler.add_job(achievs_alerts, "cron", hour=12, minute=0)

	scheduler.start()

	dp.update.middleware(SchedulerMiddleware(scheduler=scheduler))

	dp.startup.register(on_startup)

	try:
		logger.info('Start polling...')
		await bot.delete_webhook(drop_pending_updates=True)
		await dp.start_polling(bot, on_startup=on_startup)
	finally:
		logger.info('Close bot session...')
		await bot.session.close()


if __name__ == '__main__':
	asyncio.run(main())
