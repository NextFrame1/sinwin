from datetime import datetime, timedelta
from random import randint
from typing import Dict

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from apscheduler.triggers.interval import IntervalTrigger
from dateutil.relativedelta import relativedelta
from loguru import logger
import app.keyboards.menu_inline as inline
from app.api import APIRequest
from app.database.test import users
from app.loader import (
	ACHIEVEMENTS,
	bot,
	config,
	convert_to_human,
	loaded_achievements,
	scheduler,
	user_achievements,
)
from app.utils.algorithms import is_valid_card

only_confirmed = (
	lambda call: users.get(call.from_user.id, {}).get('final', False) is True
	or call.from_user.id in config.secrets.ADMINS_IDS
)  # noqa: E731
message_only_confirmed = (
	lambda message: users.get(message.from_user.id, {}).get('final', False) is True
	or message.from_user.id in config.secrets.ADMINS_IDS
)  # noqa: E731

default_router = Router()
alerts = True

transactions_dict = {}
transactions_schedulded = {}
withdraws_history = {}


LIMITS = {
	'bitcoin': (10650.0, 665000.0),
	'ethereum': (1000.0, 665000.0),
	'tether erc20': (1500.0, 5000000.0),
	'tether trc20': (1500.0, 5000000.0),
	'tether bep20': (1500.0, 5000000.0),
}

last_update_time: Dict[int, datetime] = {}


class CardWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	approved = State()


class SteamWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	approved = State()


class PhonenumberWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	approved = State()


class CryptoWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	address = State()
	limit = State()
	approved = State()


class FKWalletWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	approved = State()


class PiastrixWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	withdraw_card = State()
	approved = State()


class PromoGroup(StatesGroup):
	promocode = State()


class CancelTransaction(StatesGroup):
	transac = State()
	cancel_reason = State()


async def collect_stats(opts: dict):
	result, status = await APIRequest.post('/user/find', {'opts': opts})

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

	users = result['users']

	users_count = len(users)
	users_income = sum([user['income'] for user in users])
	users_notreg_count = len([user for user in users if not user['approved']])
	users_nottopup_count = len(
		[user for user in users if user['balance'] < 500.0 and user['approved']]
	)
	users_gamed_count = len(
		[user for user in users if user['balance'] > 500.0 and user['approved']]
	)

	users_today = [
		user
		for user in users
		if datetime.strptime(user['register_date'], '%Y-%m-%dT%H:%M:%S').date() == today
	]
	users_yesterday = [
		user
		for user in users
		if datetime.strptime(user['register_date'], '%Y-%m-%dT%H:%M:%S').date()
		== yesterday
	]
	users_lastweek = [
		user
		for user in users
		if last_week_start
		<= datetime.strptime(user['register_date'], '%Y-%m-%dT%H:%M:%S').date()
		<= last_week_end
	]
	users_month = [
		user
		for user in users
		if last_month_start
		<= datetime.strptime(user['register_date'], '%Y-%m-%dT%H:%M:%S').date()
		<= last_month_end
	]

	users_today = len(users_today)
	users_yesterday = len(users_yesterday)
	users_lastweek = len(users_lastweek)
	users_month = len(users_month)

	return {
		'users_count': users_count,
		'users_today': users_today,
		'users_yesterday': users_yesterday,
		'users_lastweek': users_lastweek,
		'users_month': users_month,
		'users_notreg_count': users_notreg_count,
		'users_nottopup_count': users_nottopup_count,
		'users_gamed_count': users_gamed_count,
		'users_income': users_income,
	}


@default_router.callback_query(F.data == 'statistics', only_confirmed)
async def statistics_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	if call.from_user.id in config.secrets.ADMINS_IDS:
		data = await collect_stats({})

		today_firstdeps = len([dep['amount'] for dep in stats['today']['firstdep']])
		yesterday_firstdeps = len(
			[dep['amount'] for dep in stats['yesterday']['firstdep']]
		)
		last_week_firstdeps = len(
			[dep['amount'] for dep in stats['last_week']['firstdep']]
		)
		last_month_firstdeps = len(
			[dep['amount'] for dep in stats['last_month']['firstdep']]
		)

		today_deps = (
			sum([dep['amount'] for dep in stats['today']['dep']]) + sum([dep['amount'] for dep in stats['today']['firstdep']])
		)
		yesterday_deps = (
			sum([dep['amount'] for dep in stats['yesterday']['dep']])
			+ sum([dep['amount'] for dep in stats['yesterday']['firstdep']])
		)
		last_week_deps = (
			sum([dep['amount'] for dep in stats['last_week']['dep']])
			+ sum([dep['amount'] for dep in stats['last_week']['firstdep']])
		)
		last_month_deps = (
			sum([dep['amount'] for dep in stats['last_month']['dep']])
			+ sum([dep['amount'] for dep in stats['last_month']['firstdep']])
		)

		today_income = sum([dep['income'] for dep in stats['today']['income']])
		yesterday_income = sum([dep['income'] for dep in stats['yesterday']['income']])
		last_week_income = sum([dep['income'] for dep in stats['last_week']['income']])
		last_month_income = sum(
			[dep['income'] for dep in stats['last_month']['income']]
		)

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		alltime_firstdeps = (
			today_firstdeps
			+ yesterday_firstdeps
			+ last_week_firstdeps
			+ last_month_firstdeps
		)
		alltime_income = (
			today_income + yesterday_income + last_week_income + last_month_income
		)

		balance, status_code = await APIRequest.get('/base/admin_balance')

		signals_gens = [
			[info[k] for k, _ in info.items()] for _, info in result['signals'].items()
		]
		signals_gens = sum(sum(x) for x in signals_gens)

		api_count = sum([apinum for partnerhash, apinum in result['api_count'].items()])

		messages = [
			'<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>\n',
			f'💰️ Баланс: {balance["balance"]} RUB\n',
			f'Всего пользователей: {data["users_count"]}',
			f'Депозиты за все время: {alltime_deps}',
			f'Доход за все время: {alltime_income}',
			f'Первые депозиты за все время: {alltime_firstdeps}',
			f'API за все время: {api_count}',
			f'Сгенерировано сигналов: {signals_gens}\n',
			f'Пользователей на этапе регистрации: {data["users_notreg_count"]}',
			f'Пользователей на этапе пополнения: {data["users_nottopup_count"]}',
			f'Пользователей на этапе игры: {data["users_gamed_count"]}\n',
			f'Пользователей за сегодня: {data["users_today"]}',
			f'├ Пользователей за вчера: {data["users_yesterday"]}',
			f'├ Пользователей за неделю: {data["users_lastweek"]}',
			f'└ Пользователей за месяц: {data["users_month"]}\n',
			f'Сумма депозитов за сегодня: {today_deps}',
			f'├ Сумма депозитов за вчера: {yesterday_deps}',
			f'├ Сумма депозитов за неделю: {last_week_deps}',
			f'└ Сумма депозитов за месяц: {last_month_deps}\n',
			f'Первые депозиты за сегодня: {today_firstdeps}',
			f'├ Первые депозиты за вчера: {yesterday_firstdeps}',
			f'├ Первые депозиты за неделю: {last_week_firstdeps}',
			f'└ Первые депозиты за месяц: {last_month_firstdeps}\n',
			f'Доход за сегодня: {today_income}',
			f'├ Доход за вчера: {yesterday_income}',
			f'├ Доход за неделю: {last_week_income}',
			f'└ Доход за месяц: {last_month_income}',
		]
	else:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		partner = partners[0]['partners'][-1]

		if not partner['approved']:
			users[call.from_user.id] = users.get(call.from_user.id, {})
			users[call.from_user.id]['final'] = False
			await call.answer('Вы заблокированы')
			return

		opts = {'referal_parent': partner['partner_hash']}

		data = await collect_stats(opts)

		api_count = result['api_count'].get(partner['partner_hash'], 0)

		today_firstdeps = len(
			[
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_firstdeps = len(
			[
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		today_deps = sum(
			[
				dep['amount']
				for dep in stats['today']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		yesterday_deps = sum(
			[
				dep['amount']
				for dep in stats['yesterday']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		last_week_deps = sum(
			[
				dep['amount']
				for dep in stats['last_week']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])
		last_month_deps = sum(
			[
				dep['amount']
				for dep in stats['last_month']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		today_income = sum(
			[
				dep['x']
				for dep in stats['today']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_income = sum(
			[
				dep['x']
				for dep in stats['yesterday']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_income = sum(
			[
				dep['x']
				for dep in stats['last_week']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_income = sum(
			[
				dep['x']
				for dep in stats['last_month']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		alltime_firstdeps = (
			today_firstdeps
			+ yesterday_firstdeps
			+ last_week_firstdeps
			+ last_month_firstdeps
		)
		alltime_income = (
			today_income + yesterday_income + last_week_income + last_month_income
		)

		signals_gens = sum(
			[info[partner['partner_hash']] for _, info in result['signals'].items()]
		)

		messages = [
			'<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>',
			'<code>Пользователи которые запустили бота по вашим ссылкам</code>\n',
			f'💰️ Баланс: {partner["balance"]} RUB\n',
			f'Всего пользователей: {data["users_count"]}',
			f'Депозиты за все время: {alltime_deps}',
			f'Доход за все время: {alltime_income}',
			f'Первые депозиты за все время: {alltime_firstdeps}',
			f'API за все время: {api_count}',
			f'Сгенерировано сигналов: {signals_gens}\n',
			f'Пользователей на этапе регистрации: {data["users_notreg_count"]}',
			f'Пользователей на этапе пополнения: {data["users_nottopup_count"]}',
			f'Пользователей на этапе игры: {data["users_gamed_count"]}\n',
			f'Пользователей за сегодня: {data["users_today"]}',
			f'├ Пользователей за вчера: {data["users_yesterday"]}',
			f'├ Пользователей за неделю: {data["users_lastweek"]}',
			f'└ Пользователей за месяц: {data["users_month"]}\n',
			f'Сумма депозитов за сегодня: {today_deps}',
			f'├ Сумма депозитов за вчера: {yesterday_deps}',
			f'├ Сумма депозитов за неделю: {last_week_deps}',
			f'└ Сумма депозитов за месяц: {last_month_deps}\n',
			f'Первые депозиты за сегодня: {today_firstdeps}',
			f'├ Первые депозиты за вчера: {yesterday_firstdeps}',
			f'├ Первые депозиты за неделю: {last_week_firstdeps}',
			f'└ Первые депозиты за месяц: {last_month_firstdeps}\n',
			f'Доход за сегодня: {today_income}',
			f'├ Доход за вчера: {yesterday_income}',
			f'├ Доход за неделю: {last_week_income}',
			f'└ Доход за месяц: {last_month_income}',
		]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_statistics_bot_menu(),
	)


@default_router.callback_query(F.data == 'statistics_mines', only_confirmed)
async def statistics_mines_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	if call.from_user.id in config.secrets.ADMINS_IDS:
		data = await collect_stats({'game': 'Mines'})

		api_count = sum([apinum for partnerhash, apinum in result['api_count'].items()])

		today_firstdeps = len(
			[
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['game'] == 'Mines'
			]
		)
		yesterday_firstdeps = len(
			[
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['game'] == 'Mines'
			]
		)
		last_week_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['game'] == 'Mines'
			]
		)
		last_month_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['game'] == 'Mines'
			]
		)

		today_deps = sum([
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['game'] == 'Mines'
			]) + sum(
			[dep['amount'] for dep in stats['today']['dep'] if dep['game'] == 'Mines']
		)
		yesterday_deps = sum([
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['game'] == 'Mines'
			]) + sum(
			[
				dep['amount']
				for dep in stats['yesterday']['dep']
				if dep['game'] == 'Mines'
			]
		)
		last_week_deps = sum([
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['game'] == 'Mines'
			]) + sum(
			[
				dep['amount']
				for dep in stats['last_week']['dep']
				if dep['game'] == 'Mines'
			]
		)
		last_month_deps = sum([
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['game'] == 'Mines'
			]) + sum(
			[
				dep['amount']
				for dep in stats['last_month']['dep']
				if dep['game'] == 'Mines'
			]
		)

		today_income = sum(
			[
				dep['income']
				for dep in stats['today']['income']
				if dep['game'] == 'Mines'
			]
		)
		yesterday_income = sum(
			[
				dep['income']
				for dep in stats['yesterday']['income']
				if dep['game'] == 'Mines'
			]
		)
		last_week_income = sum(
			[
				dep['income']
				for dep in stats['last_week']['income']
				if dep['game'] == 'Mines'
			]
		)
		last_month_income = sum(
			[
				dep['income']
				for dep in stats['last_month']['income']
				if dep['game'] == 'Mines'
			]
		)

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		alltime_firstdeps = (
			today_firstdeps
			+ yesterday_firstdeps
			+ last_week_firstdeps
			+ last_month_firstdeps
		)
		alltime_income = (
			today_income + yesterday_income + last_week_income + last_month_income
		)

		signals_gens = [
			[info[k] for k, _ in info.items()]
			for name, info in result['signals'].items()
			if name == 'Mines'
		]
		signals_gens = sum(sum(x) for x in signals_gens)

		balance, status_code = await APIRequest.get('/base/admin_balance')

		messages = [
			'<b>💣️ СТАТИСТИКА ПО MINES</b>\n',
			f'💰️ Баланс: {balance["balance"]} RUB\n',
			f'Всего пользователей: {data["users_count"]}',
			f'Депозиты за все время: {alltime_deps}',
			f'Доход за все время: {alltime_income}',
			f'Первые депозиты за все время: {alltime_firstdeps}',
			f'API за все время: {api_count}',
			f'Сгенерировано сигналов: {signals_gens}\n',
			f'Пользователей на этапе регистрации: {data["users_notreg_count"]}',
			f'Пользователей на этапе пополнения: {data["users_nottopup_count"]}',
			f'Пользователей на этапе игры: {data["users_gamed_count"]}\n',
			f'Пользователей за сегодня: {data["users_today"]}',
			f'├ Пользователей за вчера: {data["users_yesterday"]}',
			f'├ Пользователей за неделю: {data["users_lastweek"]}',
			f'└ Пользователей за месяц: {data["users_month"]}\n',
			f'Сумма депозитов за сегодня: {today_deps}',
			f'├ Сумма депозитов за вчера: {yesterday_deps}',
			f'├ Сумма депозитов за неделю: {last_week_deps}',
			f'└ Сумма депозитов за месяц: {last_month_deps}\n',
			f'Первые депозиты за сегодня: {today_firstdeps}',
			f'├ Первые депозиты за вчера: {yesterday_firstdeps}',
			f'├ Первые депозиты за неделю: {last_week_firstdeps}',
			f'└ Первые депозиты за месяц: {last_month_firstdeps}\n',
			f'Доход за сегодня: {today_income}',
			f'├ Доход за вчера: {yesterday_income}',
			f'├ Доход за неделю: {last_week_income}',
			f'└ Доход за месяц: {last_month_income}',
		]
	else:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		partner = partners[0]['partners'][-1]

		if not partner['approved']:
			print(partner)
			users[call.from_user.id] = users.get(call.from_user.id, {})
			users[call.from_user.id]['final'] = False
			await call.answer('Вы заблокированы')
			return

		opts = {'game': 'Mines', 'referal_parent': partner['partner_hash']}

		data = await collect_stats(opts)

		api_count = result['api_count'].get(partner['partner_hash'], 0)

		today_firstdeps = len(
			[
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_firstdeps = len(
			[
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)

		today_deps = sum([
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]) + sum(
			[
				dep['amount']
				for dep in stats['today']['dep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_deps = sum([
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]) + sum(
			[
				dep['amount']
				for dep in stats['yesterday']['dep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_deps = sum([
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]) + sum(
			[
				dep['amount']
				for dep in stats['last_week']['dep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_deps = sum([
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]) + sum(
			[
				dep['amount']
				for dep in stats['last_month']['dep']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)

		today_income = sum(
			[
				dep['x']
				for dep in stats['today']['income']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_income = sum(
			[
				dep['x']
				for dep in stats['yesterday']['income']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_income = sum(
			[
				dep['x']
				for dep in stats['last_week']['income']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_income = sum(
			[
				dep['x']
				for dep in stats['last_month']['income']
				if dep['game'] == 'Mines'
				and dep['partner_hash'] == partner['partner_hash']
			]
		)

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		alltime_firstdeps = (
			today_firstdeps
			+ yesterday_firstdeps
			+ last_week_firstdeps
			+ last_month_firstdeps
		)
		alltime_income = (
			today_income + yesterday_income + last_week_income + last_month_income
		)

		signals_gens = sum(
			[info[partner['partner_hash']] for _, info in result['signals'].items()]
		)

		messages = [
			'<b>💣️ СТАТИСТИКА ПО MINES</b>',
			'<code>Пользователи которые запустили бота по вашим ссылкам</code>\n',
			f'💰️ Баланс: {partner["balance"]} RUB\n',
			f'Всего пользователей: {data["users_count"]}',
			f'Депозиты за все время: {alltime_deps}',
			f'Доход за все время: {alltime_income}',
			f'Первые депозиты за все время: {alltime_firstdeps}',
			f'API за все время: {api_count}',
			f'Сгенерировано сигналов: {signals_gens}\n',
			f'Пользователей на этапе регистрации: {data["users_notreg_count"]}',
			f'Пользователей на этапе пополнения: {data["users_nottopup_count"]}',
			f'Пользователей на этапе игры: {data["users_gamed_count"]}\n',
			f'Пользователей за сегодня: {data["users_today"]}',
			f'├ Пользователей за вчера: {data["users_yesterday"]}',
			f'├ Пользователей за неделю: {data["users_lastweek"]}',
			f'└ Пользователей за месяц: {data["users_month"]}\n',
			f'Сумма депозитов за сегодня: {today_deps}',
			f'├ Сумма депозитов за вчера: {yesterday_deps}',
			f'├ Сумма депозитов за неделю: {last_week_deps}',
			f'└ Сумма депозитов за месяц: {last_month_deps}\n',
			f'Первые депозиты за сегодня: {today_firstdeps}',
			f'├ Первые депозиты за вчера: {yesterday_firstdeps}',
			f'├ Первые депозиты за неделю: {last_week_firstdeps}',
			f'└ Первые депозиты за месяц: {last_month_firstdeps}\n',
			f'Доход за сегодня: {today_income}',
			f'├ Доход за вчера: {yesterday_income}',
			f'├ Доход за неделю: {last_week_income}',
			f'└ Доход за месяц: {last_month_income}',
		]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_mines_statistics_menu(),
	)


@default_router.callback_query(F.data.startswith('referal'), only_confirmed)
async def referal_callback(call: CallbackQuery):
	if call.from_user.id in config.secrets.ADMINS_IDS:
		messages = [
			'Помогите своим друзьям стать частью нашей команды и начните зарабатывать вместе!\n',
			'Мы ищем только мотивированных профессионалов, предпочтительно с опытом в арбитраже.\n\n<code>💰️ Условия реферальной программы могут меняться</code>\n',
			'<b>Для вас:</b>',
			'Вы получите 15 000 рублей если приглашенный вами пользователь дойдет до статуса "Профессионал".\n',
			'<b>Для вашего друга:</b>',
			'Ваш друг получит статус "Специалист 40%" вместо "Новичок 35%" на протяжении первого месяца работы.\n',
			'Ваша реферальная ссылка: <code>https://t.me/SinWin_work_bot?start={hash}</code>',
		]
	else:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
		messages = [
			'Помогите своим друзьям стать частью нашей команды и начните зарабатывать вместе!\n',
			'Мы ищем только мотивированных профессионалов, предпочтительно с опытом в арбитраже.\n\n<code>💰️ Условия реферальной программы могут меняться</code>\n',
			'<b>Для вас:</b>',
			'Вы получите 15 000 рублей если приглашенный вами пользователь дойдет до статуса "Профессионал".\n',
			'<b>Для вашего друга:</b>',
			'Ваш друг получит статус "Специалист 40%" вместо "Новичок 35%" на протяжении первого месяца работы.\n',
			f'Ваша реферальная ссылка: <code>https://t.me/SinWin_work_bot?start={partner["partner_hash"]}</code>',
		]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_referals_markup(),
	)


@default_router.callback_query(F.data.startswith('about_us'), only_confirmed)
async def about_uscallback(call: CallbackQuery):
	messages = [
		'Следите за нашими новостями и обновлениями на <a href="https://t.me/+W8_28FXJWXIxZTgy">канале SinWin</a>. Там вы найдете свежие новости и важные объявления для нашей команды.\n',
		'Ваше мнение важно для нас! Мы всегда стремимся к совершенству, поэтому будем рады ваши вопросам, предложениям и отзывам.\n',
		'Спасибо, что выбрали SinWin!',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_about_us_markup(),
	)


@default_router.callback_query(F.data.startswith('my_referals'), only_confirmed)
async def referal_answer_callback(call: CallbackQuery):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	try:
		partner = partners[0]['partners'][-1]
	except Exception:
		return

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['partner_hash']}}
	)
	cpartner = cpartners[0]['partners']

	# if rpartner:
	# 	await bot.send_message(chat_id=rpartner['tg_id'], text=f'У вас новый реферал: #{tid}\nВсего рефералов: {len(cpartner)}')

	if len(cpartner) == 0:
		await call.answer('У вас нет рефералов', show_alert=True)
	else:
		items = []

		for cp in cpartner:
			regdate = datetime.strptime(cp['register_date'], '%Y-%m-%dT%H:%M:%S')
			regdate = regdate.strftime('%H:%M %d/%m/%Y')
			items.append(f'{regdate} - {cp["tg_id"]} - {cp["status"]}')

		items = '\n'.join(items)

		await call.message.answer(
			f"""
Вы заработали с рефералов: {partner['ref_income']} рублей  

🏆 Ваши рефералы: {len(cpartner)} Дата - Телеграм id - Статус пользователя

{items}

Ваши достижения впечатляют! Не сбавляйте темп и стремитесь к еще большему успеху.		
""",
			reply_markup=inline.create_referals_markup(),
		)


def check_achievements(
	users_count,
	income,
	deposits_sum,
	first_deposits_count,
	referrals_count,
	signals_count,
):
	achievements = [
		'🏆️ Ваши достижения:\n',
	]

	thresholds = {
		'users_count': ['0'],
		'deposits_sum': ['0'],
		'income': ['0'],
		'first_deposits_count': ['0'],
		'referrals_count': ['0'],
		'signals_count': ['0'],
	}

	for threshold in ACHIEVEMENTS['users']:
		if users_count >= threshold:
			thresholds['users_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS['deposits']:
		if deposits_sum >= threshold:
			thresholds['deposits_sum'].append(convert_to_human(threshold))

	for threshold in ACHIEVEMENTS['income']:
		if income >= threshold:
			thresholds['income'].append(convert_to_human(threshold))

	for threshold in ACHIEVEMENTS['first_deposits']:
		if first_deposits_count >= threshold:
			thresholds['first_deposits_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS['referrals']:
		if referrals_count >= threshold:
			thresholds['referrals_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS['signals']:
		if signals_count >= threshold:
			thresholds['signals_count'].append(str(threshold))

	count = (
		len(thresholds['users_count'])
		+ len(thresholds['referrals_count'])
		+ len(thresholds['signals_count'])
		+ len(thresholds['deposits_sum'])
		+ len(thresholds['income'])
		+ len(thresholds['first_deposits_count'])
		- 6
	)

	achievements.append(
		f'Количество: {count}\n\n✅ Пользователей по Вашим ссылкам: {", ".join(thresholds["users_count"])}\n'
	)
	achievements.append(f'✅ Депозиты: {",".join(thresholds["deposits_sum"])}\n')
	achievements.append(f'✅ Доход: {",".join(thresholds["income"])}\n')
	achievements.append(
		f'✅ Первые депозиты: {",".join(thresholds["first_deposits_count"])}\n'
	)
	achievements.append(f'✅ Рефералы: {",".join(thresholds["referrals_count"])}\n')
	achievements.append(
		f'✅ Сгенерировано сигналов: {",".join(thresholds["signals_count"])}'
	)

	return achievements


def check_achievements_for_reload(
	users_count,
	income,
	deposits_sum,
	first_deposits_count,
	referrals_count,
	signals_count,
):
	thresholds = {
		'users_count': [str(users_count)],
		'deposits_sum': [str(deposits_sum)],
		'income': [str(income)],
		'first_deposits_count': [str(first_deposits_count)],
		'referrals_count': [str(referrals_count)],
		'signals_count': [str(signals_count)],
	}

	for threshold in ACHIEVEMENTS['users']:
		if users_count >= threshold:
			thresholds['users_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS['deposits']:
		if deposits_sum >= threshold:
			thresholds['deposits_sum'].append(convert_to_human(threshold))

	for threshold in ACHIEVEMENTS['income']:
		if income >= threshold:
			thresholds['income'].append(convert_to_human(threshold))

	for threshold in ACHIEVEMENTS['first_deposits']:
		if first_deposits_count >= threshold:
			thresholds['first_deposits_count'].append(str(threshold))

	for threshold in ACHIEVEMENTS['referrals']:
		if referrals_count <= threshold:
			thresholds['referrals_count'].append(str(threshold))
			break

	for threshold in ACHIEVEMENTS['signals']:
		if signals_count < threshold:
			thresholds['signals_count'].append(str(threshold))
			break

	count = (
		len(thresholds['users_count'])
		+ len(thresholds['signals_count'])
		+ len(thresholds['deposits_sum'])
		+ len(thresholds['income'])
		+ len(thresholds['first_deposits_count'])
		+ len(thresholds['referrals_count'])
		- 6
	)

	return {
		'count': count,
		'thresholds': thresholds,
	}


@default_router.callback_query(F.data.startswith('reload_achievs'), only_confirmed)
async def reload_achievs_callback(call: CallbackQuery):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners']

	if last_update_time.get(call.from_user.id) is not None:
		time_difference = datetime.now() - last_update_time.get(call.from_user.id)

		if time_difference.total_seconds() < 60:
			await call.answer('Слишком часто, обновите через минуту')
			return

	last_update_time[call.from_user.id] = datetime.now()

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Вы еще не зарегистрированы в системе')

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	result, code = await APIRequest.get(
		f'/base/achstats?partnerhash={partner["partner_hash"]}'
	)

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['partner_hash']}}
	)
	cpartners = cpartners[0]['partners']

	opts = {'game': 'Mines', 'referal_parent': partner['partner_hash']}
	data = await collect_stats(opts)

	achievements = check_achievements_for_reload(
		data['users_count'],
		result['income'],
		result['deposits_sum'],
		result['first_deposits_count'],
		len(cpartners),
		result['signals_count'],
	)

	count = achievements['count']
	thresholds = achievements['thresholds']

	# thresholds_data = {
	# 	'users_count': ['0'],
	# 	'deposits_sum': ['0'],
	# 	'income': ['0'],
	# 	'first_deposits_count': ['0'],
	# }

	loaded_achievs = loaded_achievements.get(call.from_user.id, {})

	loaded_achievements[call.from_user.id] = achievements

	loaded_count = loaded_achievs.get('count')

	if loaded_count > count:
		loaded_thresholds = loaded_achievs['thresholds']

		users_count = list(
			set(loaded_thresholds['users_count']) - set(thresholds['users_count'])
		)
		deposits_sum = list(
			set(loaded_thresholds['deposits_sum']) - set(thresholds['deposits_sum'])
		)
		income = list(set(loaded_thresholds['income']) - set(thresholds['income']))
		first_deposits_count = list(
			set(loaded_thresholds['first_deposits_count'])
			- set(thresholds['first_deposits_count'])
		)
		referrals_count = list(
			set(loaded_thresholds['referrals_count'])
			- set(thresholds['referrals_count'])
		)
		signals_count = list(
			set(loaded_thresholds['signals_count']) - set(thresholds['signals_count'])
		)

		if users_count:
			for data in users_count:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Пользователи по вашим ссылкам: больше {data}.'
				)

		if deposits_sum:
			for data in deposits_sum:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Депозиты: больше {convert_to_human(data)} рублей.'
				)

		if income:
			for data in income:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Доход: больше {convert_to_human(data)} рублей.'
				)

		if first_deposits_count:
			for data in first_deposits_count:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Количество первых депозитов: больше {data}.'
				)

		if referrals_count:
			for data in referrals_count:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Количество рефералов: больше {data}.'
				)

		if signals_count:
			for data in signals_count:
				await call.message.answer(
					f'Достижение успешно выполнено.\n\n✅ Сгенерировано сигналов: больше {data}.'
				)

		achievements = check_achievements_var2(
			data['users_count'],
			result['income'],
			result['deposits_sum'],
			result['first_deposits_count'],
			len(cpartners),
			result['signals_count'],
		)

		data = user_achievements.get(call.from_user.id, {})
		data['achievements'] = achievements
		user_achievements[call.from_user.id] = data
	else:
		await call.answer('Вы не выполнили ни одного достижения')
	# await call.answer("Обновили список достижений", show_alert=True)


@default_router.callback_query(F.data.startswith('my_achievs'), only_confirmed)
async def my_achievs_callback(call: CallbackQuery):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners']

	messages = []

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Вы еще не зарегистрированы в системе')

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	result, code = await APIRequest.get(
		f'/base/achstats?partnerhash={partner["partner_hash"]}'
	)

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['partner_hash']}}
	)
	cpartners = cpartners[0]['partners']

	opts = {'game': 'Mines', 'referal_parent': partner['partner_hash']}
	data = await collect_stats(opts)

	achievements = check_achievements(
		data['users_count'],
		result['income'],
		result['deposits_sum'],
		result['first_deposits_count'],
		len(cpartners),
		result['signals_count'],
	)

	messages += achievements

	messages.append('\nПродолжайте в том же духе и достигайте новых высот! 🌟')

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('achievements'),
	)

	messages = []


def check_achievements_var2(
	users_count,
	income,
	deposits_sum,
	first_deposits_count,
	referrals_count,
	signals_count,
):
	achievements = [
		'🏆️ Ваши Цели:\n',
	]

	for threshold in ACHIEVEMENTS['users']:
		if users_count >= threshold:
			continue
		elif users_count < threshold:
			achievements.append(f'❌ Пользователей по вашим ссылкам: {threshold}')
			break

	for threshold in ACHIEVEMENTS['deposits']:
		if deposits_sum >= threshold:
			continue
		elif deposits_sum < threshold:
			achievements.append(f'❌ Депозиты: {convert_to_human(threshold)} рублей')
			break

	for threshold in ACHIEVEMENTS['income']:
		if income >= threshold:
			continue
		if income < threshold:
			achievements.append(f'❌ Доход: {convert_to_human(threshold)} рублей')
			break

	for threshold in ACHIEVEMENTS['first_deposits']:
		if first_deposits_count >= threshold:
			continue
		elif first_deposits_count < threshold:
			achievements.append(f'❌ Первые депозиты: {threshold}')
			break

	for threshold in ACHIEVEMENTS['referrals']:
		if referrals_count >= threshold:
			continue
		elif referrals_count < threshold:
			achievements.append(f'❌ Количество рефералов: {threshold}')
			break

	for threshold in ACHIEVEMENTS['signals']:
		if signals_count >= threshold:
			continue
		elif signals_count < threshold:
			achievements.append(f'❌ Сгенерировано сигналов: {threshold}')
			break

	return achievements


@default_router.callback_query(F.data.startswith('achievements'), only_confirmed)
async def achievements_callback(call: CallbackQuery):
	if call.data == 'achievements_false':
		data = user_achievements.get(call.from_user.id, {})
		data['alerts'] = False
		user_achievements[call.from_user.id] = data
	elif call.data == 'achievements_true':
		data = user_achievements.get(call.from_user.id, {})
		data['alerts'] = True
		user_achievements[call.from_user.id] = data

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners']

	messages = []

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Вы еще не зарегистрированы в системе')

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	if user_achievements.get(call.from_user.id, {}).get('achievements', []):
		achievements = user_achievements.get(call.from_user.id, {})

		messages += achievements['achievements']
	else:
		result, code = await APIRequest.get(
			f'/base/achstats?partnerhash={partner["partner_hash"]}'
		)

		cpartners = await APIRequest.post(
			'/partner/find', {'opts': {'referrer_hash': partner['referrer_hash'], "is_referal": True}}
		)
		cpartners = cpartners[0]['partners']

		logger.error(len(cpartners))

		opts = {'game': 'Mines', 'referal_parent': partner['partner_hash']}
		data = await collect_stats(opts)

		achievements = check_achievements_var2(
			data['users_count'],
			result['income'],
			result['deposits_sum'],
			result['first_deposits_count'],
			len(cpartners),
			result['signals_count'],
		)

		loaded_achievements[call.from_user.id] = check_achievements_for_reload(
			data['users_count'],
			result['income'],
			result['deposits_sum'],
			result['first_deposits_count'],
			len(cpartners),
			result['signals_count'],
		)

		messages += achievements

		data = user_achievements.get(call.from_user.id, {})
		data['achievements'] = achievements
		user_achievements[call.from_user.id] = data

	messages += [
		(
			'\n✅ Уведомления включены\n'
			if user_achievements.get(call.from_user.id, {}).get('alerts', True)
			else '\n❌ Уведомления выключены\n'
		),
		'Продолжайте в том же духе и достигайте новых высот! 🌟',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_achievements_markup(
			user_achievements.get(call.from_user.id, {}).get('alerts', True)
		),
	)

	messages = []


@default_router.callback_query(F.data == 'record_creo', only_confirmed)
async def record_creo_callback(call: CallbackQuery):
	messages = [
		'В этих ботах вы можете легко записать креативы:\n',
		'Mines для выбора мин: @iZiMinsBot',
		'Mines для генерации мин: @iZiMin_Bot',
		'Speed Cash: @SPDCashsBot',
		'LuckyJet: @CashJetsBot',
		'Coin Flip: @WinFlipsBot\n',
		'Для правильного взаимодействия с этими ботами, пожалуйста, ознакомьтесь с инструкцией. В ней вы найдете все необходимые шаги для правильной записи креативов.',
	]
	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_record_creo_markup(),
	)


@default_router.callback_query(F.data == 'work', only_confirmed)
async def work_callback(call: CallbackQuery):
	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception:
		messages = [
			'💻️ WORK\n\n<b>ССЫЛКИ НА БОТОВ</b>\nMines - <code>https://t.me/IziMin_test_Bot</code>',
			'Lucky Jet - <code>https://t.me/CashJetBot</code>',
			'Speed Cash - <code>https://t.me/SPDCashBot</code>',
			'Coin Flip - <code>https://t.me/CoinFlipBot</code>',
		]
		await call.message.edit_text(
			'\n'.join(messages),
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_work_markup(),
		)
		return

	partner_hash = partner.get('partner_hash', 'Недоступно')
	messages = [
		f'💻️ WORK\n\n<b>ССЫЛКИ НА БОТОВ</b>\nMines - <code>https://t.me/IziMin_test_Bot?start={partner_hash}</code>',
		f'Lucky Jet - <code>https://t.me/CashJetBot?start={partner_hash}</code>',
		f'Speed Cash - <code>https://t.me/SPDCashBot?start={partner_hash}</code>',
		f'Coin Flip - <code>https://t.me/CoinFlipBot?start={partner_hash}</code>',
	]
	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_work_markup(),
	)


@default_router.callback_query(F.data.startswith('showmenu'), only_confirmed)
async def showmenu_callback(call: CallbackQuery):
	try:
		await call.message.edit_text(
			'🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!',
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_main_menu_markup(call.from_user.id),
		)
	except Exception:
		await call.message.delete()
		await call.message.answer(
			'🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!',
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_main_menu_markup(call.from_user.id),
		)


@default_router.callback_query(F.data.startswith('admin_'), only_confirmed)
async def adminpanel_query_callback(call: CallbackQuery):
	await call.message.edit_text(
		'ЗАГЛУШКА', reply_markup=inline.create_back_markup('showmenu')
	)


@default_router.callback_query(F.data == 'adminpanel')
async def adminpanel_callback(call: CallbackQuery):
	# └┏ ├「┌
	messages = [
		'┌ Пользователей в партнерке: 10',
		'├ Баланс Партнерки: 100 000 рублей',
		'├ Доход бота: 10 000 000 рублей',
		'├ Баланс всех пользователей: 15 000 500 рублей',
		f'└ Поставлено на вывод {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: 100 000 рублей',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_adminpanel_markup(),
	)


@default_router.callback_query(F.data == 'top_workers', only_confirmed)
async def top_workers_callback(call: CallbackQuery):
	# 🥇🥈🥉🏅
	result, code = await APIRequest.get('/base/stats?exclude=1')

	stats = result['data']
	income = (
		stats['last_month']['income']
		+ stats['today']['income']
		+ stats['last_week']['income']
		+ stats['yesterday']['income']
	)

	userp = None
	status = False
	state = 0

	partners = {}

	if call.from_user.id not in config.secrets.ADMINS_IDS:
		result = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		user = result[0]['partners']

		if user:
			user = user[-1]
			userp = user['partner_hash']
		else:
			await call.answer('Вы заблокированы')
			return

	print(income)

	for partner in income:
		partner_hash = partner['partner_hash']
		if userp == partner_hash:
			status = True

		partners[partner_hash] = partner['x']

	partners = dict(sorted(partners.items(), key=lambda item: item[1], reverse=True))

	partners = dict(list(partners.items())[:5])

	if status:
		state = list(partners).index(userp) + 1

	messages = [
		'🏆️ Топ воркеров по доходу за последний месяц',
	]

	for i, (partner_hash, income) in enumerate(partners.items()):
		messages.append('')
		partner_hash = partner_hash[:3] + '****' + partner_hash[7:]

		if i == 0:
			messages.append(f'🥇 {partner_hash}: {income} рублей')
		elif i == 1:
			messages.append(f'🥈 {partner_hash}: {income} рублей')
		elif i == 3:
			messages.append(f'🥉 {partner_hash}: {income} рублей')
		else:
			messages.append(f'🏅 {partner_hash}: {income} рублей')

	if status:
		messages.append(f'👽️ Ваша позиция в топе: {state}\n')
	else:
		messages.append('')

	messages += [
		'📅 Статистика обнуляется 1 числа каждого месяца.\n',
		'<code>👑 Пользователь, занявший первое место, повышается в статусе, если его текущий статус "Профессионал" или ниже.</code>',
		'<code>💵 Второе и третье места получают премию.</code>\n\n'
		'🚀 Удачи в достижении новых высот!',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('showmenu'),
	)


@default_router.callback_query(F.data == 'withdraws_history', only_confirmed)
async def withdraws_history_callback(call: CallbackQuery):
	# 🟢🟡⚪️
	result = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	user = result[0]['partners']

	if not user:
		await call.answer('Вы заблокированы')
		return

	user = user[-1]

	# data = withdraws_history.get(partner_hash, {})
	# data[transaction_id] = {
	# 	'status': '⚪️ Вывод на обработке',
	# 	'type': '💳 Карта',
	# 	'sum': data['withdraw_sum'],
	# 	'date': datetime.now()
	# }
	# withdraws_history[partner_hash] = data

	if not withdraws_history.get(user['partner_hash'], False):
		messages = ['🤖 История выводов: 0']
	else:
		withdraws = withdraws_history.get(user['partner_hash'])
		messages = [f'🤖 История выводов: {len(withdraws)}']

		withdraws = dict(reversed(withdraws.items()))

		for _, data in withdraws.items():
			messages.append(
				f'{data["status"]}\n├ {data["date"].strftime("%H:%M %d-%m-%Y")}: {data["sum"]}: {data["type"]}'
			)

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('profile'),
	)


@default_router.callback_query(F.data == 'statistics_online', only_confirmed)
async def statistics_online_callback(call: CallbackQuery):
	# ✨📊💰️🎮️
	messages = [
		'✨ Статистика в реальном времени\n',
		'Следите за всей активностью мнговенно! Нажмите, чтобы перейти в бота @sinwin_alerts_bot, и получайте:',
		'📊 Уведомления о регистрации новых пользователей.',
		'💰️ Информацию о депозитах.',
		'🎮️ Данные по каждой игре ваших пользователей',
		'\nОбратите внимание: статистика, накопленная ранее, в боте не отображается. Вы сможете отслеживать данные только с момента подключения.',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_online_statistics_markup(),
	)


def get_percent_by_status(status: str) -> float:
	"""
	Gets the percent by status.

	:param		status:	 The status
	:type		status:	 str

	:returns:	The percent by status.
	:rtype:		float
	"""
	status = status.lower()

	match status:
		case 'новичок':
			return 35
		case 'специалист':
			return 40
		case 'профессионал':
			return 45
		case 'мастер':
			return 50
		case 'легенда':
			return 60
		case _:
			return 35


def get_status_conditions(
	status, last_month_income, alltime_income, last_month_firstdeps
) -> tuple:
	if status == 'новичок':
		statuses = {
			'income': True if last_month_income >= 50000.0 else False,
			'total_income': True if alltime_income >= 100000.0 else False,
			'first_deposits': True if last_month_firstdeps >= 100 else False,
		}
	elif status == 'специалист':
		statuses = {
			'income': True if last_month_income >= 150000.0 else False,
			'total_income': True if alltime_income >= 300000.0 else False,
			'first_deposits': True if last_month_firstdeps >= 200 else False,
		}
	elif status == 'профессионал':
		statuses = {
			'income': True if last_month_income >= 300000.0 else False,
			'total_income': True if alltime_income >= 600000.0 else False,
			'first_deposits': True if last_month_firstdeps >= 400 else False,
		}
	elif status == 'мастер':
		statuses = {
			'income': True if last_month_income >= 500000.0 else False,
			'total_income': True if alltime_income >= 1000000.0 else False,
			'first_deposits': True if last_month_firstdeps >= 600 else False,
		}

	statuses_items = {}

	for status_name, status_type in statuses.items():
		statuses_items[status_name] = '✅' if status_type else '❌'

	return statuses_items, not any(val is False for val in statuses.values())


def get_next_level(status):
	if status == 'новичок':
		return 'специалист'

	elif status == 'специалист':
		return 'профессионал'

	elif status == 'профессионал':
		return 'мастер'

	elif status == 'мастер':
		return 'легенда'


@default_router.callback_query(F.data == 'status_levels', only_confirmed)
async def status_levels_callback(call: CallbackQuery):
	if call.from_user.id in config.secrets.ADMINS_IDS:
		await call.answer('Для просмотра условий перехода обратитесь к админпанели')
		return

	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners']

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Доступ запрещен')
		return

	today_firstdeps = len(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_firstdeps = len(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	today_income = sum(
		[
			dep['x']
			for dep in stats['today']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_income = sum(
		[
			dep['x']
			for dep in stats['yesterday']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_income = sum(
		[
			dep['x']
			for dep in stats['last_week']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_income = sum(
		[
			dep['x']
			for dep in stats['last_month']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	other_dates_income = [info for name, info in stats.items() if name == 'income']
	others_income = sum(
		[
			dep['x']
			for dep in other_dates_income
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	alltime_firstdeps = (
		today_firstdeps
		+ yesterday_firstdeps
		+ last_week_firstdeps
		+ last_month_firstdeps
	)
	alltime_income = (
		today_income
		+ yesterday_income
		+ last_week_income
		+ last_month_income
		+ others_income
	)

	last_month_income = (
		today_income + yesterday_income + last_week_income + last_month_income
	)

	statuses1, _ = get_status_conditions(
		'новичок', last_month_income, alltime_income, alltime_firstdeps
	)

	statuses2, _ = get_status_conditions(
		'специалист', last_month_income, alltime_income, alltime_firstdeps
	)

	statuses3, _ = get_status_conditions(
		'профессионал', last_month_income, alltime_income, alltime_firstdeps
	)

	statuses4, _ = get_status_conditions(
		'мастер', last_month_income, alltime_income, alltime_firstdeps
	)

	messages = [
		'1. Новичок: 35 %\nУсловия для перехода:',
		f'{statuses1["income"]} Доход за последний месяц: не менее 50 000 рублей',
		f'{statuses1["total_income"]} Общий доход за все время: не менее 100 000 рублей',
		f'{statuses1["first_deposits"]} Первые депозиты за последний месяц: не менее 100\n',
		'2. Специалист 40 %',
		f'{statuses2["income"]} Доход за последний месяц: не менее 150 000 рублей',
		f'{statuses2["total_income"]} Общий доход за все время: не менее 300 000 рублей',
		f'{statuses2["first_deposits"]} Первые депозиты за последний месяц: не менее 200\n',
		'3. Профессионал 45 %',
		f'{statuses3["income"]} Доход за последний месяц: не менее 300 000 рублей',
		f'{statuses3["total_income"]} Общий доход за все время: не менее 600 000 рублей',
		f'{statuses3["first_deposits"]} Первые депозиты за последний месяц: не менее 400\n',
		'4. Мастер 50%',
		f'{statuses4["income"]} Доход за последний месяц: не менее 500 000 рублей',
		f'{statuses4["total_income"]} Общий доход за все время: не менее 1 000 000 рублей',
		f'{statuses4["first_deposits"]} Первые депозиты за последний месяц: не менее 600\n',
		'5. Легенда Суб Партнерство\n',
		'Суб партнерство подключается вручную. Пользователь регистрируется в официальной партнерской программе 1 Win через нашу ссылку. Создает свою уникальную ссылку для приглашения, которую мы интегрируем в нашего бота. Пользователь получает от 50% до 60% прибыли через официальную партнерскую программу. Иногда статус "Легенда" подключается вместо статуса "Мастер".\n',
		'<code>Условия перехода могут изменяться</code>',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('status'),
	)


@default_router.callback_query(F.data == 'status', only_confirmed)
async def status_callback(call: CallbackQuery):
	# ❌✅🏆️📊🎯💼💰️
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	if call.from_user.id in config.secrets.ADMINS_IDS:
		await call.answer(
			'Для просмотра условий перехода статусов обратитесь к админ-панели.'
		)
		return
	else:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': call.from_user.id}}
		)
		partner = partners[0]['partners']

		if partner:
			partner = partner[-1]
		else:
			await call.answer('Доступ запрещен')
			return

		opts = {'referal_parent': partner['partner_hash']}

		data = await collect_stats(opts)

		api_count = result['api_count'].get(partner['partner_hash'], 0)

		today_firstdeps = len(
			[
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_firstdeps = len(
			[
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_firstdeps = len(
			[
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		today_deps = sum(
			[
				dep['amount']
				for dep in stats['today']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])
	
		yesterday_deps = sum(
			[
				dep['amount']
				for dep in stats['yesterday']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		last_week_deps = sum(
			[
				dep['amount']
				for dep in stats['last_week']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		last_month_deps = sum(
			[
				dep['amount']
				for dep in stats['last_month']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]) + sum([
				dep['amount']
				for dep in stats['last_month']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			])

		today_income = sum(
			[
				dep['x']
				for dep in stats['today']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		yesterday_income = sum(
			[
				dep['x']
				for dep in stats['yesterday']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_week_income = sum(
			[
				dep['x']
				for dep in stats['last_week']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_income = sum(
			[
				dep['x']
				for dep in stats['last_month']['income']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		other_dates_income = [info for name, info in stats.items() if name == 'income']
		others_income = sum(
			[
				dep['x']
				for dep in other_dates_income
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		alltime_firstdeps = (
			today_firstdeps
			+ yesterday_firstdeps
			+ last_week_firstdeps
			+ last_month_firstdeps
		)
		alltime_income = (
			today_income
			+ yesterday_income
			+ last_week_income
			+ last_month_income
			+ others_income
		)

		signals_gens = sum(
			[info[partner['partner_hash']] for _, info in result['signals'].items()]
		)

		last_month_income = today_income + yesterday_income + last_week_income + last_month_income

		last_month_income_str = '{:,}'.format(last_month_income).replace(',', ' ')
		alltime_income_str = '{:,}'.format(alltime_income).replace(',', ' ')

		statuses, may_up = get_status_conditions(
			partner['status'], last_month_income, alltime_income, alltime_firstdeps
		)

		statuses_conditions = {
			'новичок': {
				'last_month_income': convert_to_human(50000),
				'alltime_income': convert_to_human(100000),
				'alltime_firstdeps': convert_to_human(100),
			},
			'специалист': {
				'last_month_income': convert_to_human(150000),
				'alltime_income': convert_to_human(300000),
				'alltime_firstdeps': convert_to_human(200),
			},
			'профессионал': {
				'last_month_income': convert_to_human(300000),
				'alltime_income': convert_to_human(600000),
				'alltime_firstdeps': convert_to_human(400),
			},
			'мастер': {
				'last_month_income': convert_to_human(500000),
				'alltime_income': convert_to_human(1000000),
				'alltime_firstdeps': convert_to_human(600),
			},
		}

		messages = [
			f'🏆️ Ваш текущий статус: {partner["status"]}',
			f'🎯 Вы получаете: {get_percent_by_status(partner["status"])}%\n',
			f'📊 Ваш доход за последний месяц: {last_month_income_str} RUB',
			f'💼 Общий доход: {alltime_income_str} RUB',
			f'💰️ Первые депозиты за последний месяц: {last_month_firstdeps}\n',
			'Условия для перехода:',
			f'{statuses["income"]} Доход за последний месяц: не менее {statuses_conditions[partner["status"]]["last_month_income"]} рублей',
			f'{statuses["total_income"]} Общий доход за все время: не менее {statuses_conditions[partner["status"]]["alltime_income"]} рублей',
			f'{statuses["first_deposits"]} Первые депозиты за последний месяц: не менее {statuses_conditions[partner["status"]]["alltime_firstdeps"]}\n',
			'Продолжайте в том же духе! Чем дольше и лучше вы работаете, тем больше вы зарабатывайте! Переход на новый уровень происходит автоматически каждые 24 часа, если все условия выполнены.',
			'\n<code>Обратите внимание: условия перехода могут меняться.</code>\n',
			'Если у вас есть вопросы, напишите в поддержку',
		]

		if partner['status'] == 'специалист' and partner['is_referal'] and may_up:
			cpartners = await APIRequest.post(
				'/partner/find', {'opts': {'partner_hash': partner['referrer_hash']}}
			)
			cpartner = cpartners[0]['partners'][-1]

			cpartner['ref_income'] += 15000.0
			cpartner['balance'] += 15000.0

			await APIRequest.post('/partner/update', {**cpartner})

			await bot.send_message(
				chat_id=cpartner['tg_id'],
				text=f'Ваш реферал #{call.from_user.id} перешел на статус “Профессионал 45%”\nВам зачислено на баланс 15 000 рублей',
			)

			for admin in config.secrets.ADMINS_IDS:
				await bot.send_message(
					chat_id=admin,
					text=f'Пользователь {call.from_user.username if call.from_user.username is not None else call.from_user.id} перешел со статуса “Специалист 40 %” на статус “Профессионал 45 %”\nПользователь {cpartner["username"] if cpartner["username"] else cpartner["tg_id"]} получил 15 00 рублей',
				)

		if may_up and partner['status'] == 'профессионал':
			await call.message.answer(
				"""
✅ Вы соответствуете условиям для перехода на следующий уровень!

В течение 24 часов администрация подтвердит ваш переход или предложит перейти на статус “Легенда”
Если за 24 часа статус не меняется, напишите в поддержку""",
				reply_markup=inline.create_status_up_master_markup(),
			)
			for admin in config.secrets.ADMINS_IDS:
				try:
					await bot.send_message(
						chat_id=admin,
						text=f"""
Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Хэш: {partner['partner_hash']}
Реферал: {partner['is_referal']}

Пользователь переходит со статуса “Профессионал 45%” на статус “Мастер 50%”

<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>
<code>пользователи которые запустили бота по вашим ссылкам (моно ширфт)</code>

💰️ Баланс: {partner['balance']} RUB

Депозиты за все время: {alltime_deps}
Доход за все время: {alltime_income}
Первые депозиты за все время: {alltime_firstdeps}
API за все время: {api_count}
Сгенерировано сигналов: {signals_gens}

Пользователей на этапе регистрации: {data['users_notreg_count']}
Пользователей на этапе пополнения: {data['users_nottopup_count']}
Пользователей на этапе игры: {data['users_gamed_count']}

Пользователей за сегодня: {data['users_today']}
├ Пользователей за вчера: {data['users_yesterday']}
├ Пользователей за неделю: {data['users_lastweek']}
└ Пользователей за месяц: {data['users_month']}

Сумма депозитов за сегодня: {today_deps}
├ Сумма депозитов за вчера: {yesterday_deps}
├ Сумма депозитов за неделю: {last_week_deps}
└ Сумма депозитов за месяц: {last_month_deps}

Первые депозиты за сегодня: {today_firstdeps}
├ Первые депозиты за вчера: {yesterday_firstdeps}
├ Первые депозиты за неделю: {last_week_firstdeps}
└ Первые депозиты за месяц: {last_month_firstdeps}

Доход за сегодня: {today_income}
├ Доход за вчера: {yesterday_income}
├ Доход за неделю: {last_week_income}
└ Доход за месяц: {last_month_income}
""",
						reply_markup=inline.create_confirm_status_change(
							call.from_user.id
						),
						parse_mode=ParseMode.HTML,
					)
				except Exception:
					await bot.send_message(
						chat_id=admin,
						text=f"""
Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Хэш: {partner['partner_hash']}
Реферал: {partner['is_referal']}

Пользователь переходит со статуса “Профессионал 45%” на статус “Мастер 50%”

<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>
<code>пользователи которые запустили бота по вашим ссылкам (моно ширфт)</code>

💰️ Баланс: {partner['balance']} RUB

Депозиты за все время: {alltime_deps}
Доход за все время: {alltime_income}
Первые депозиты за все время: {alltime_firstdeps}
API за все время: {api_count}
Сгенерировано сигналов: {signals_gens}

Пользователей на этапе регистрации: {data['users_notreg_count']}
Пользователей на этапе пополнения: {data['users_nottopup_count']}
Пользователей на этапе игры: {data['users_gamed_count']}

Пользователей за сегодня: {data['users_today']}
├ Пользователей за вчера: {data['users_yesterday']}
├ Пользователей за неделю: {data['users_lastweek']}
└ Пользователей за месяц: {data['users_month']}

Сумма депозитов за сегодня: {today_deps}
├ Сумма депозитов за вчера: {yesterday_deps}
├ Сумма депозитов за неделю: {last_week_deps}
└ Сумма депозитов за месяц: {last_month_deps}

Первые депозиты за сегодня: {today_firstdeps}
├ Первые депозиты за вчера: {yesterday_firstdeps}
├ Первые депозиты за неделю: {last_week_firstdeps}
└ Первые депозиты за месяц: {last_month_firstdeps}

Доход за сегодня: {today_income}
├ Доход за вчера: {yesterday_income}
├ Доход за неделю: {last_week_income}
└ Доход за месяц: {last_month_income}
""",
						reply_markup=inline.create_confirm_status_change(
							call.from_user.id, withwrite=False
						),
						parse_mode=ParseMode.HTML,
					)
			return
		elif may_up and (
			partner['status'] != 'профессионал'
			and partner['status'] != 'мастер'
			and partner['status'] != 'легенда'
		):
			await call.message.edit_text(
				f"""
✅ Вы соответствуете условиям для перехода на следующий уровень!

Поздравляем! Вы переходите на следующий уровень "{get_next_level(partner['status'])}"!

Процент Вашего дохода теперь: {get_percent_by_status(get_next_level(partner['status']))}%
				""",
				reply_markup=inline.create_status_up_markup(),
			)

			partner['status'] = get_next_level(partner['status'])
			partner['percent'] = get_percent_by_status(partner['status'])

			await APIRequest.post('/partner/update', {**partner})
			return

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_status_markup(),
	)


async def send_message_about_status_change(status: str, userid: int):
	scheduler.remove_job(f'{status}status_{userid}')

	if status == 'confirm':
		await bot.send_message(
			chat_id=userid,
			text="""
✅ Вы соответствуете условиям для перехода на следующий уровень!

Поздравляем! Вы переходите на следующий уровень "Мастер"! Процент Вашего дохода теперь: 50 %	
""",
			reply_markup=inline.create_status_up_markup(),
		)

		partner = await APIRequest.post('/partner/find', {'opts': {'tg_id': userid}})
		partner = partner[0]['partners'][-1]

		partner['status'] = 'мастер'
		partner['percent'] = 50

		await APIRequest.post('/partner/update', {**partner})
	else:
		await bot.send_message(
			chat_id=userid,
			text="""
❌ Ваш запрос на переход на статус “Мастер” отклонен.

Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации.
""",
			reply_markup=inline.create_status_up_rejected_markup(),
		)


@default_router.callback_query(F.data.startswith('confirm_status_change_'))
async def confirm_status_change_user(call: CallbackQuery, scheduler=scheduler):
	userid = int(call.data.replace('confirm_status_change_', ''))
	partners = await APIRequest.post('/partner/find', {'opts': {'tg_id': userid}})
	partner = partners[0]['partners']

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Невозможно найти партнера')
		return

	try:
		scheduler.remove_job(f'confirmstatus_{userid}')
	except Exception:
		pass
	try:
		scheduler.remove_job(f'rejectstatus_{userid}')
	except Exception:
		pass

	scheduler.add_job(
		send_message_about_status_change,
		trigger=IntervalTrigger(seconds=180),
		args=('confirm', userid),
		id=f'confirmstatus_{userid}',
		replace_existing=True,
	)

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""
Ник: {partner['username']}
Хэш: {partner['partner_hash']}
Реферал: {partner['is_referal']}

✅ Пользователь перешел со статуса со статуса “Профессионал 45%” на статус “Мастер 50%”		
""",
			reply_markup=inline.change_status_moving(userid),
		)


@default_router.callback_query(F.data.startswith('reject_status_change_'))
async def reject_status_change_user(call: CallbackQuery, scheduler=scheduler):
	userid = int(call.data.replace('reject_status_change_', ''))
	partners = await APIRequest.post('/partner/find', {'opts': {'tg_id': userid}})
	partner = partners[0]['partners']

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Невозможно найти партнера')
		return

	try:
		scheduler.remove_job(f'confirmstatus_{userid}')
	except Exception:
		pass
	try:
		scheduler.remove_job(f'rejectstatus_{userid}')
	except Exception:
		pass

	scheduler.add_job(
		send_message_about_status_change,
		trigger=IntervalTrigger(seconds=180),
		args=('reject', userid),
		id=f'rejectstatus_{userid}',
		replace_existing=True,
	)

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""
Ник: {partner['username']}
Хэш: {partner['hash']}
Реферал: {partner['is_referal']}

❌ Пользователь  не перешел со статуса со статуса “Профессионал 45%” на статус “Мастер 50%”	
""",
			reply_markup=inline.change_status_moving(userid),
		)


@default_router.callback_query(F.data.startswith('change_status_moving_'))
async def change_status_moving_callback(call: CallbackQuery):
	userid = int(call.data.replace('change_status_moving_', ''))

	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	partners = await APIRequest.post('/partner/find', {'opts': {'tg_id': userid}})
	partner = partners[0]['partners']

	opts = {'referal_parent': partner['partner_hash']}

	data = await collect_stats(opts)

	api_count = len(
		[
			apinum
			for partnerhash, apinum in result['api_count'].items()
			if partnerhash == partner['partner_hash']
		]
	)

	today_firstdeps = len(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_firstdeps = len(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	today_deps = sum([
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]) + sum(
		[
			dep['amount']
			for dep in stats['today']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_deps = sum([
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]) + sum(
		[
			dep['amount']
			for dep in stats['yesterday']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_deps = sum([
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]) + sum(
		[
			dep['amount']
			for dep in stats['last_week']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_deps = sum([
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]) + sum(
		[
			dep['amount']
			for dep in stats['last_month']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	today_income = sum(
		[
			dep['x']
			for dep in stats['today']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_income = sum(
		[
			dep['x']
			for dep in stats['yesterday']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_income = sum(
		[
			dep['x']
			for dep in stats['last_week']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_income = sum(
		[
			dep['x']
			for dep in stats['last_month']['income']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	other_dates_income = [info for name, info in stats.items() if name == 'income']
	others_income = sum(
		[
			dep['x']
			for dep in other_dates_income
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	alltime_firstdeps = (
		today_firstdeps
		+ yesterday_firstdeps
		+ last_week_firstdeps
		+ last_month_firstdeps
	)
	alltime_income = (
		today_income
		+ yesterday_income
		+ last_week_income
		+ last_month_income
		+ others_income
	)

	signals_gens = sum(
		[info[partner['partner_hash']] for _, info in result['signals'].items()]
	)

	statuses, may_up = get_status_conditions(
		partner['status'], last_month_income, alltime_income, last_month_firstdeps
	)

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Невозможно найти партнера')
		return

	for admin in config.secrets.ADMINS_IDS:
		try:
			await bot.send_message(
				chat_id=admin,
				text=f"""
Tg id: {userid}
Ник: {partner['username']}
Хэш: {partner['partner_hash']}
Реферал: {partner['is_referal']}

Пользователь переходит со статуса “Профессионал 45%” на статус “Мастер 50%”

<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>
<code>пользователи которые запустили бота по вашим ссылкам (моно ширфт)</code>

💰️ Баланс: {partner['balance']} RUB

Депозиты за все время: {alltime_deps}
Доход за все время: {alltime_income}
Первые депозиты за все время: {alltime_firstdeps}
API за все время: {api_count}
Сгенерировано сигналов: {signals_gens}

Пользователей на этапе регистрации: {data['users_notreg_count']}
Пользователей на этапе пополнения: {data['users_nottopup_count']}
Пользователей на этапе игры: {data['users_gamed_count']}

Пользователей за сегодня: {data['users_today']}
├ Пользователей за вчера: {data['users_yesterday']}
├ Пользователей за неделю: {data['users_lastweek']}
└ Пользователей за месяц: {data['users_month']}

Сумма депозитов за сегодня: {today_deps}
├ Сумма депозитов за вчера: {yesterday_deps}
├ Сумма депозитов за неделю: {last_week_deps}
└ Сумма депозитов за месяц: {last_month_deps}

Первые депозиты за сегодня: {today_firstdeps}
├ Первые депозиты за вчера: {yesterday_firstdeps}
├ Первые депозиты за неделю: {last_week_firstdeps}
└ Первые депозиты за месяц: {last_month_firstdeps}

Доход за сегодня: {today_income}
├ Доход за вчера: {yesterday_income}
├ Доход за неделю: {last_week_income}
└ Доход за месяц: {last_month_income}
""",
				reply_markup=inline.create_confirm_status_change(call.from_user.id),
				parse_mode=ParseMode.HTML,
			)
		except Exception:
			await bot.send_message(
				chat_id=admin,
				text=f"""
Tg id: {userid}
Ник: {partner['username']}
Хэш: {partner['partner_hash']}
Реферал: {partner['is_referal']}

Пользователь переходит со статуса “Профессионал 45%” на статус “Мастер 50%”

<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>
<code>пользователи которые запустили бота по вашим ссылкам (моно ширфт)</code>

💰️ Баланс: {partner['balance']} RUB

Депозиты за все время: {alltime_deps}
Доход за все время: {alltime_income}
Первые депозиты за все время: {alltime_firstdeps}
API за все время: {api_count}
Сгенерировано сигналов: {signals_gens}

Пользователей на этапе регистрации: {data['users_notreg_count']}
Пользователей на этапе пополнения: {data['users_nottopup_count']}
Пользователей на этапе игры: {data['users_gamed_count']}

Пользователей за сегодня: {data['users_today']}
├ Пользователей за вчера: {data['users_yesterday']}
├ Пользователей за неделю: {data['users_lastweek']}
└ Пользователей за месяц: {data['users_month']}

Сумма депозитов за сегодня: {today_deps}
├ Сумма депозитов за вчера: {yesterday_deps}
├ Сумма депозитов за неделю: {last_week_deps}
└ Сумма депозитов за месяц: {last_month_deps}

Первые депозиты за сегодня: {today_firstdeps}
├ Первые депозиты за вчера: {yesterday_firstdeps}
├ Первые депозиты за неделю: {last_week_firstdeps}
└ Первые депозиты за месяц: {last_month_firstdeps}

Доход за сегодня: {today_income}
├ Доход за вчера: {yesterday_income}
├ Доход за неделю: {last_week_income}
└ Доход за месяц: {last_month_income}
""",
				reply_markup=inline.create_confirm_status_change(
					call.from_user.id, withwrite=False
				),
				parse_mode=ParseMode.HTML,
			)


@default_router.callback_query(F.data == 'profile', only_confirmed)
async def profile_callback(call: CallbackQuery):
	if call.from_user.id in config.secrets.ADMINS_IDS:
		balance, status_code = await APIRequest.get('/base/admin_balance')
		messages = [
			f'<b>Ваш профиль</b>\n\n🆔 Ваш ID: {call.from_user.id}',
			'🛡️ Ваш хеш: admin\n',
			f'💰️ Баланс: {balance["balance"]} RUB',
			'⚖️ Статус: Админ',
			'🏗️ Количество рефералов: 0',
		]

		await call.message.edit_text(
			'\n'.join(messages),
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_profile_markup(),
		)
		return

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	partner_hash = partner.get('partner_hash', 'Недоступно')
	status = partner.get('status', 'новичок')

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['referrer_hash'], "is_referal": True}}
	)
	cpartners = cpartners[0]['partners']

	messages = [
		f'<b>Ваш профиль</b>\n\n🆔 Ваш ID: {call.from_user.id}',
		f'🛡️ Ваш хеш: {partner_hash}\n',
		f'💰️ Баланс: {partner.get("balance", 0.0)} RUB',
		f'⚖️ Статус: {status}',
		f'🎯 Вы получаете: {get_percent_by_status(partner["status"])}%\n',
		f'🏗️ Количество рефералов: {len(cpartners)}',
		f'☯️ Количество дней с нами: {days_difference}',
		# f'Ваша реферальная ссылка на @IziMin_test_Bot: https://t.me/IziMin_test_Bot?start='
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_profile_markup(),
	)


@default_router.callback_query(F.data == 'withdraw', only_confirmed)
async def withdraw_callback(call: CallbackQuery):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners']

	if partner:
		partner = partner[-1]
	else:
		await call.answer('Недоступно получение партнера')
		return

	messages = [
		f'💰️ Баланс: {partner["balance"]} RUB\n',
		'❗️ ВЫВОД СРЕДСТВ ДОСТУПЕН ОДИН РАЗ В НЕДЕЛЮ КАЖДУЮ СРЕДУ ПО МОСКОВСКОМУ ВРЕМЕНИ. К ВЫВОДУ ДОСТУПНА ВСЯ СУММА КОТОРАЯ НАХОДИТСЯ НА БАЛАНСЕ.❗️\n',
		'В редких случаях при больщом доходе со вторника на среду вывести всю сумму получится через неделю. Однако в таких ситуациях вы всегда можете вывести часть средств, оставив небольшой остаток на балансе.\n',
		'Если в течении 24 часов после создания заявки на вывод вы не получите уведомление от бота, пожалуйста, свяжитесь с поддержкой.\n',
		'<b>ЛИМИТЫ НА ВЫВОД СРЕДСТВ</b>\n',
		'💳️ <b>Карта</b>',
		' ∟ VISA, MasterCard: от 2 000 ₽ до 50 000 ₽\n',
		'📱 <b>Вывод по номеру телефона</b>',
		' ∟ VISA, MasterCard, МИР: от 5 000 ₽ до 100 000 ₽\n',
		'⚙️ <b>Steam</b>',
		' ∟ Вывод на аккаунт Steam: от 2 000 ₽ до 12 000 ₽\n',
		'🌸 <b>Piastrix</b>',
		'∟ от 1 800 ₽ до 100 000 ₽\n',
		'👾 <b>FK Wallet</b>',
		'∟ от 1 800 ₽ до 100 000 ₽\n',
		'👑 <b>Крипта</b>',
		'∟ Плавающие лимиты, смотрите при выводе от 1 500 ₽ до 5 000 000 ₽\n',
	]

	try:
		await call.message.edit_text(
			'\n'.join(messages),
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_withdraw_markup(),
		)
	except Exception:
		await call.message.delete()
		await call.message.answer(
			'\n'.join(messages),
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_withdraw_markup(),
		)


@default_router.callback_query(F.data == 'withdraw_crypto', only_confirmed)
async def withdraw_crypto_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()
	messages = [
		'Какую криптовалюту вы хотите использовать для вывода денег?\n',
		'<b>ЛИМИТЫ НА ВЫВОД СРЕДСТВ</b>',
		'Bitcoin - 10 650 ₽ - 665 000 ₽',
		'Ethereum - 1 000 ₽ - 665 000 ₽',
		'Tron - 1 500 ₽ - 665 070 ₽',
		'Tether ERC20 - 1 500 ₽ - 5 000 000 ₽',
		'Tether TRC20 - 1 500 ₽ - 5 000 000 ₽',
		'Tether BEP20 - 1 500 ₽ - 5 000 000 ₽',
		'BNB BEP20 - 1 500 ₽ - 655 070 ₽',
		'Litecoin - 1 500 ₽ - 665 000 ₽',
		'Monero - 1 500 ₽ - 665 070 ₽',
		'Bitcoin Cash - 1 500 ₽ - 665 070 ₽',
		'Dash - 1 500 ₽ - 665 070 ₽',
		'Doge - 1 500 ₽ - 665 070 ₽',
		'Zcash - 1 500 ₽ - 665 070 ₽',
		'Ripple - 1 500 ₽ - 665 070 ₽',
		'Stellar - 1 500 ₽ - 665 070 ₽',
	]

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_crypto_withdraw_markup(),
	)

	await state.set_state(CryptoWithdrawGroup.withdraw_card)


@default_router.callback_query(
	F.data.startswith('crypto_set_withdraw_'),
	CryptoWithdrawGroup.withdraw_card,
	only_confirmed,
)
async def crypto_set_withdraw_type(call: CallbackQuery, state: FSMContext):
	crypto_type = call.data.replace('crypto_set_withdraw_', '').lower()
	limit = LIMITS.get(crypto_type, (1500.0, 665070.0))

	await state.update_data(withdraw_card=crypto_type, limit=limit)

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на криптовалюту {crypto_type.upper()}\n\nВведите адрес вашего криптокошелька: '

	await call.message.edit_text(
		message,
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)
	await state.set_state(CryptoWithdrawGroup.address)

	# message = f"💰️ Баланс: {partner['balance']} RUB\nВывод на криптовалюту {crypto_type.upper()}\nЛимит одного вывода: от {limit[0]} ₽ до {limit[1]} ₽\n\n✍️ Введите сумму которую Вы хотите вывести."

	# image = FSInputFile(path=f"{config.SINWIN_DATA}/main/crupto.jpg")

	# await call.message.edit_media(
	# 	InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
	# 	parse_mode=ParseMode.HTML,
	# 	reply_markup=inline.create_back_markup("withdraw"),
	# )

	# await state.set_state(CryptoWithdrawGroup.withdraw_sum)


@default_router.message(F.text, CryptoWithdrawGroup.address, message_only_confirmed)
async def withdraw_crypto_address(message: Message, state: FSMContext):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': message.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[message.from_user.id] = users.get(message.from_user.id, {})
		users[message.from_user.id]['final'] = False
		await message.answer('Вы заблокированы')
		return

	data = await state.get_data()
	crypto_type = data.get('withdraw_card').lower()
	limit = LIMITS.get(crypto_type, (1500.0, 665070.0))

	messages = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на криптовалюту {crypto_type.upper()} {message.text}\nЛимит одного вывода: от {limit[0]} ₽ до {limit[1]} ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	await state.update_data(address=message.text)
	await state.update_data(withdraw_card=f'{crypto_type.upper()} {message.text}')

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/crupto.jpg')

	await message.answer_photo(
		photo=image,
		caption=messages,
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(CryptoWithdrawGroup.withdraw_sum)


@default_router.message(
	F.text, CryptoWithdrawGroup.withdraw_sum, message_only_confirmed
)
async def withdraw_crypto_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_crypto'),
		)
		return

	data = await state.get_data()

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_crypto'),
			)

		elif sum_to_withdraw > data['limit'][1]:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_crypto'),
			)

		elif sum_to_withdraw < data['limit'][0]:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_crypto'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			data = await state.get_data()
			await message.answer(
				f'Вывод на криптовалюту принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nКриптовалюта: {data.get("withdraw_card")}',
				reply_markup=inline.create_withdraw_continue_markup(withdraw='crypto'),
			)
			await state.set_state(CryptoWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_crypto_withdraw',
	CryptoWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_crypto_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '👑 Крипта',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/crupto.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: 👑 Крипта
Сумма: <code>{data['withdraw_sum']}</code>₽
Криптовалюта: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'crypto'
			),
		)


@default_router.callback_query(F.data == 'withdraw_card', only_confirmed)
async def withdraw_card_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\n💳️ Visa или MasterCard\nЛимит одного вывода: 2 000 ₽ - 50 000 ₽\n\n<code>Вывод средств на карты банков РФ может происходить с задержкой. Чтобы совершать выводы максимально быстро, рекомендуем использовать карту Сбера.</code>\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/card.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(CardWithdrawGroup.withdraw_sum)


@default_router.message(F.text, CardWithdrawGroup.withdraw_sum, message_only_confirmed)
async def withdraw_card_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_card'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_card'),
			)

		elif sum_to_withdraw > 50000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_card'),
			)

		elif sum_to_withdraw < 2000.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_card'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f'Сумма вывода: {sum_to_withdraw} ₽\n\nНапишите номер банковской карты (16 цифр, без пробелов)',
				reply_markup=inline.create_back_markup('withdraw_card'),
			)
			await state.set_state(CardWithdrawGroup.withdraw_card)


@default_router.message(F.text, CardWithdrawGroup.withdraw_card, message_only_confirmed)
async def withdraw_withdraw_card_message(message: Message, state: FSMContext):
	text = message.text
	user = users.get(message.chat.id, {})
	status = is_valid_card(text)

	if status is None:
		# await state.clear()
		user['withdraw_card'] = False
		await message.answer(
			'Ошибка: некорректный номер карты\n\nПожалуйста, введите корректный номер банковской карты, состоящий из 16 цифр, без пробелов.',
			reply_markup=inline.create_back_markup('withdraw_card'),
		)
	elif not status:
		# await state.clear()
		user['withdraw_card'] = False
		await message.answer(
			'Ошибка: некорректный номер карты\n\nВведенный номер карты не прошел проверку. Пожалуйста, проверьте номер и введите корректный номер банковской карты, состоящий из 16 цифр, без пробелов.',
			reply_markup=inline.create_back_markup('withdraw_card'),
		)
	else:
		await state.update_data(withdraw_card=text)
		data = await state.get_data()
		await message.answer(
			f'Номер карты принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nКарта: {text}',
			reply_markup=inline.create_withdraw_continue_markup(),
		)
		await state.set_state(CardWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_card_withdraw',
	CardWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_card_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '💳 Карта',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/card.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: 💳 Карта
Сумма: <code>{data['withdraw_sum']}</code>₽
Карта: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'card'
			),
		)


async def send_message_about_transaction_to_user(
	sum_to_withdraw,
	partner_hash: str,
	transaction_id: int,
	scheduler,
	transactype: str = '💳 Карта',
):
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners[0]['partners'][-1]

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	scheduler.remove_job(f'sendtransac_{transaction_id}')

	if partner['balance'] - int(sum_to_withdraw.replace(' ', '')) < 0.0:
		await bot.send_message(
			chat_id=partner['tg_id'],
			text=f'❌ Ваш вывод был отклонен системой по причине: недостаточно средств на балансе.\n\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nСумма вывода: {sum_to_withdraw}₽',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	partner['balance'] -= int(sum_to_withdraw.replace(' ', ''))

	transactions_schedulded[transaction_id] = False

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '🟢 Вывод произведен',
		'type': transactype,
		'sum': transac['amount'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	await APIRequest.post('/partner/update', {**partner})

	await bot.send_message(
		chat_id=partner['tg_id'],
		text=f'✅Ваш вывод средств успешно обработан и находиться на выплате. Средства должны прийти в течение 24 часов.\n\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nСпасибо за использование нашего сервиса! Если средства не поступят в течение 24 часов, пожалуйста, свяжитесь с поддержкой',
		reply_markup=inline.create_back_markup('profile'),
	)


async def send_message_about_ftransaction_to_user(
	reason,
	sum_to_withdraw,
	partner_hash: str,
	transaction_id: int,
	scheduler,
	transactype: str = '💳 Карта',
):
	# 🟢🟡⚪️
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners[0]['partners'][-1]

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	scheduler.remove_job(f'fsendtransac_{transaction_id}')

	transactions_schedulded[transaction_id] = False

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '🟡 Вывод отклонен',
		'type': transactype,
		'sum': transac['amount'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	reason = f'Причина отказа: {reason}\n' if reason is not None else reason

	await bot.send_message(
		chat_id=partner['tg_id'],
		text=f"""
❌ Ваш запрос на вывод средств был отклонен.

🛡 Ваш хэш: {partner_hash}
🆔 ID Вывода: {transac['preview_id']}
{reason if reason is not None else ''}
Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации.	
""",
		reply_markup=inline.create_support_transac_markup(),
	)


def get_emoji_by_method(method: str) -> str:
	if method == 'card':
		return '💳 Карта'
	elif method == 'steam':
		return '⚙️ Steam'
	elif method == 'crypto':
		return '👑 Крипта'
	elif method == 'phone':
		return '📱 Вывод по номеру'
	elif method == 'piastrix':
		return '🌸 Piastrix'
	elif method == 'fkwallet':
		return '👾 FK Wallet'


@default_router.callback_query(F.data.startswith('badmin_approve_transaction'))
async def admin_approve_transaction(call: CallbackQuery, scheduler=scheduler):
	data = call.data.split('.')
	method = data[-1]
	data = data[0]
	transaction_id = int(data.replace('badmin_approve_transaction', '').split('_')[0])
	await call.answer()

	names = {
		'card': 'Карта',
		'steam': 'Steam логин',
		'crypto': 'Криптовалюта',
		'piastrix': 'Piastrix',
		'fkwallet': 'FK Wallet',
		'phone': 'Номер телефона',
	}

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transaction = transactions[0]['transactions'][-1]

	if transactions_schedulded.get(transaction['id'], False):
		await call.answer(
			f'Транзакция {transaction["preview_id"]} уже обработана другим администратором'
		)
		return

	transaction['approved'] = True

	await APIRequest.post('/transaction/update', {**transaction})

	data = transactions_dict.get(transaction_id, {})
	sum_to_withdraw = f'{data["withdraw_sum"]:,}'.replace(',', ' ')

	try:
		scheduler.remove_job(f'sendtransac_{transaction_id}')
	except Exception:
		pass
	try:
		scheduler.remove_job(f'fsendtransac_{transaction_id}')
	except Exception:
		pass

	scheduler.add_job(
		send_message_about_transaction_to_user,
		trigger=IntervalTrigger(seconds=180),
		args=(
			sum_to_withdraw,
			transaction['partner_hash'],
			transaction_id,
			scheduler,
			get_emoji_by_method(method),
		),
		id=f'sendtransac_{transaction_id}',
		replace_existing=True,
	)

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""✅Вывод средств успешно обработан

🙎‍♂️ Ник: {transaction['username']}
🛡 Хэш: {transaction['partner_hash']}
🆔 ID Вывода: {transaction['preview_id']}

Вывод: {get_emoji_by_method(method)}
Сумма: {sum_to_withdraw}
{names.get(method, 'Данные')}: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.admin_change_transaction(transaction_id),
		)


@default_router.callback_query(F.data.startswith('badmin_disapprove_transaction'))
async def badmin_dispprove_transaction(call: CallbackQuery, state: FSMContext):
	transaction_id = int(
		call.data.replace('badmin_disapprove_transaction', '').split('_')[0]
	)
	admin_id = call.data.split('_')[-1]

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transaction = transactions[0]['transactions'][-1]

	if transactions_schedulded.get(transaction['id'], False):
		await call.answer(
			f'Транзакция {transaction["preview_id"]} уже обработана другим администратором'
		)
		return

	transaction['approved'] = True

	await APIRequest.post('/transaction/update', {**transaction})

	await call.answer()

	await bot.send_message(
		chat_id=admin_id,
		text='Напишите причину отказа',
		reply_markup=inline.create_cancel_reason_markup(transaction_id),
	)
	await state.update_data(transac=transaction)
	await state.set_state(CancelTransaction.cancel_reason)


@default_router.callback_query(
	F.data == 'empty_cancel_reason', CancelTransaction.cancel_reason
)
async def empty_cancel_reason(
	call: CallbackQuery, state: FSMContext, scheduler=scheduler
):
	await state.update_data(cancel_reason=None)

	data = await state.get_data()
	data = data['transac']

	await call.answer()

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': data['id']}}
	)
	transaction = transactions[0]['transactions'][-1]

	transaction['approved'] = False

	await APIRequest.post('/transaction/update', {**transaction})
	sum_to_withdraw = f'{transaction["amount"]:,}'.replace(',', ' ')

	if transactions_schedulded.get(transaction['id'], False):
		await call.answer(
			f'Транзакция {transaction["preview_id"]} уже обработана другим администратором'
		)
		return

	try:
		scheduler.remove_job(f'sendtransac_{transaction["id"]}')
	except Exception:
		pass
	try:
		scheduler.remove_job(f'fsendtransac_{transaction["id"]}')
	except Exception:
		pass

	scheduler.add_job(
		send_message_about_ftransaction_to_user,
		trigger=IntervalTrigger(seconds=180),
		args=(
			None,
			sum_to_withdraw,
			transaction['partner_hash'],
			transaction['id'],
			scheduler,
		),
		id=f'fsendtransac_{transaction["id"]}',
		replace_existing=True,
	)

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""
❌ Вывод средств был отклонен

🙎‍♂️ Ник: {transaction['username']}
🛡 Хэш: {transaction['partner_hash']}
🆔 ID Вывода: {transaction['preview_id']}

Вывод: 💳 Карта
Сумма: {sum_to_withdraw}
Карта: <code>{transaction['withdraw_card']}</code>	
""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.admin_change_transaction(transaction['id']),
		)


@default_router.message(F.text, CancelTransaction.cancel_reason)
async def empty_cancel_reaso_msgn(
	message: Message, state: FSMContext, scheduler=scheduler
):
	await state.update_data(cancel_reason=message.text)

	data = await state.get_data()
	data = data['transac']

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': data['id']}}
	)
	transaction = transactions[0]['transactions'][-1]

	if transactions_schedulded.get(transaction['id'], False):
		await message.answer(
			f'Транзакция {transaction["preview_id"]} уже обработана другим администратором'
		)
		return

	transaction['approved'] = False

	await APIRequest.post('/transaction/update', {**transaction})
	sum_to_withdraw = f'{transaction["amount"]:,}'.replace(',', ' ')

	try:
		scheduler.remove_job(f'sendtransac_{transaction["id"]}')
	except Exception:
		pass
	try:
		scheduler.remove_job(f'fsendtransac_{transaction["id"]}')
	except Exception:
		pass

	scheduler.add_job(
		send_message_about_ftransaction_to_user,
		trigger=IntervalTrigger(seconds=180),
		args=(
			message.text,
			sum_to_withdraw,
			transaction['partner_hash'],
			transaction['id'],
			scheduler,
		),
		id=f'fsendtransac_{transaction["id"]}',
		replace_existing=True,
	)

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""
❌ Вывод средств был отклонен
Причина: {message.text}

🙎‍♂️ Ник: {transaction['username']}
🛡 Хэш: {transaction['partner_hash']}
🆔 ID Вывода: {transaction['preview_id']}

Вывод: 💳 Карта
Сумма: {sum_to_withdraw}
Карта: <code>{transaction['withdraw_card']}</code>
""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.admin_change_transaction(transaction['id']),
		)


@default_router.callback_query(F.data.startswith('change_transaction_status'))
async def change_transaction_status(call: CallbackQuery):
	transaction_id = int(call.data.replace('change_transaction_status', ''))

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transaction = transactions[0]['transactions'][-1]

	if transactions_schedulded.get(transaction['id'], False):
		await call.answer(
			f'Транзакция {transaction["preview_id"]} уже обработана другим администратором'
		)
		return

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': transaction['partner_hash']}}
	)
	partner = partners[0]['partners'][-1]

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_message(
			chat_id=admin,
			text=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {transaction['partner_hash']}
Id Вывода: {transaction['preview_id']}

Вывод: 💳 Карта
Сумма: <code>{transaction['amount']}</code>₽
Карта: <code>{transaction['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'card'
			),
		)


############ STEAM


@default_router.callback_query(F.data == 'withdraw_steam', message_only_confirmed)
async def withdraw_steam_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на аккаунт Steam\nЛимит одного вывода: от 2 000 ₽ до 12 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/steam.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(SteamWithdrawGroup.withdraw_sum)


@default_router.message(F.text, SteamWithdrawGroup.withdraw_sum, message_only_confirmed)
async def withdraw_steam_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_steam'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)

		elif sum_to_withdraw > 12000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)

		elif sum_to_withdraw < 2000.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f"Сумма вывода: {sum_to_withdraw} ₽\n\nУкажите ваш логин аккаунта steam\n\nВы можете узнать ваш Steam login кликнув по <a href='https://store.steampowered.com/account/'>прямой ссылке</a>",
				reply_markup=inline.create_back_markup('withdraw_steam'),
				parse_mode=ParseMode.HTML,
			)
			await state.set_state(SteamWithdrawGroup.withdraw_card)


@default_router.message(
	F.text, SteamWithdrawGroup.withdraw_card, message_only_confirmed
)
async def withdraw_withdraw_steam_message(message: Message, state: FSMContext):
	text = message.text

	await state.update_data(withdraw_card=text)
	data = await state.get_data()
	await message.answer(
		f'Логин Steam принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nSteam: {text}',
		reply_markup=inline.create_withdraw_continue_markup(withdraw='steam'),
	)
	await state.set_state(SteamWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_steam_withdraw',
	SteamWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_steam_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '⚙️ Steam',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/steam.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: ⚙️ Steam
Сумма: <code>{data['withdraw_sum']}</code>₽
Steam логин: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'steam'
			),
		)


############## PHONE NUMBER


@default_router.callback_query(F.data == 'withdraw_phone', message_only_confirmed)
async def withdraw_phone_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод по номеру телефона\nЛимит одного вывода: от 5 000 ₽ до 100 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/telefon.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(PhonenumberWithdrawGroup.withdraw_sum)


@default_router.message(
	F.text, PhonenumberWithdrawGroup.withdraw_sum, message_only_confirmed
)
async def withdraw_phone_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_phone'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_phone'),
			)

		elif sum_to_withdraw > 100000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_phone'),
			)

		elif sum_to_withdraw < 5000.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_phone'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f'Сумма вывода: {sum_to_withdraw} ₽\n\nУкажите ваш номер телефона',
				reply_markup=inline.create_back_markup('withdraw_phone'),
				parse_mode=ParseMode.HTML,
			)
			await state.set_state(PhonenumberWithdrawGroup.withdraw_card)


@default_router.message(
	F.text, PhonenumberWithdrawGroup.withdraw_card, message_only_confirmed
)
async def withdraw_withdraw_phone_message(message: Message, state: FSMContext):
	text = message.text

	await state.update_data(withdraw_card=text)
	data = await state.get_data()
	await message.answer(
		f'Номер телефона принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nНомер телефона: {text}',
		reply_markup=inline.create_withdraw_continue_markup(withdraw='phone'),
	)
	await state.set_state(PhonenumberWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_phone_withdraw',
	PhonenumberWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_phone_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '📱 Вывод по номеру',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/telefon.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: 📱 Вывод по номеру
Сумма: <code>{data['withdraw_sum']}</code>₽
Номер телефона: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'phone'
			),
		)


########## FK Wallet


@default_router.callback_query(F.data == 'withdraw_fkwallet', message_only_confirmed)
async def withdraw_fkwallet_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на FK Wallet\nЛимит одного вывода: от 1 800 ₽ до 100 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/FK.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(FKWalletWithdrawGroup.withdraw_sum)


@default_router.message(
	F.text, FKWalletWithdrawGroup.withdraw_sum, message_only_confirmed
)
async def withdraw_fkwallet_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_fkwallet'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_fkwallet'),
			)

		elif sum_to_withdraw > 100000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_fkwallet'),
			)

		elif sum_to_withdraw < 1800.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_fkwallet'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f'Сумма вывода: {sum_to_withdraw} ₽\n\nУкажите номер аккаунта в формате F12345678',
				reply_markup=inline.create_back_markup('withdraw_fkwallet'),
				parse_mode=ParseMode.HTML,
			)
			await state.set_state(FKWalletWithdrawGroup.withdraw_card)


@default_router.message(
	F.text, FKWalletWithdrawGroup.withdraw_card, message_only_confirmed
)
async def withdraw_withdraw_fkwallet_message(message: Message, state: FSMContext):
	text = message.text

	await state.update_data(withdraw_card=text)
	data = await state.get_data()
	await message.answer(
		f'Номер аккаунта принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nНомер аккаунта: {text}',
		reply_markup=inline.create_withdraw_continue_markup(withdraw='fkwallet'),
	)
	await state.set_state(FKWalletWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_fkwallet_withdraw',
	FKWalletWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_fkwallet_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '👾 FK Wallet',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/FK.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: 👾 FK Wallet
Сумма: <code>{data['withdraw_sum']}</code>₽
Номер аккаунта: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'fkwallet'
			),
		)


########## 🌸 Piastrix


@default_router.callback_query(F.data == 'withdraw_piastrix', message_only_confirmed)
async def withdraw_piastrix_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на Piastrix\nЛимит одного вывода: от 1 800 ₽ до 100 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/piastrix.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(PiastrixWithdrawGroup.withdraw_sum)


@default_router.message(
	F.text, PiastrixWithdrawGroup.withdraw_sum, message_only_confirmed
)
async def withdraw_piastrix_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_piastrix'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_piastrix'),
			)

		elif sum_to_withdraw > 100000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_piastrix'),
			)

		elif sum_to_withdraw < 1800.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_piastrix'),
			)

		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f'Сумма вывода: {sum_to_withdraw} ₽\n\nУкажите номер кошелька или email Piastrix',
				reply_markup=inline.create_back_markup('withdraw_piastrix'),
				parse_mode=ParseMode.HTML,
			)
			await state.set_state(PiastrixWithdrawGroup.withdraw_card)


@default_router.message(
	F.text, PiastrixWithdrawGroup.withdraw_card, message_only_confirmed
)
async def withdraw_withdraw_piastrix_message(message: Message, state: FSMContext):
	text = message.text

	await state.update_data(withdraw_card=text)
	data = await state.get_data()
	await message.answer(
		f'Номер аккаунта принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nНомер кошелька/email: {text}',
		reply_markup=inline.create_withdraw_continue_markup(withdraw='piastrix'),
	)
	await state.set_state(PiastrixWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_piastrix_withdraw',
	PiastrixWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_piastrix_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%d%m%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '🌸 Piastrix',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/piastrix.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: 🌸 Piastrix
Сумма: <code>{data['withdraw_sum']}</code>₽
Номер аккаунта: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'piastrix'
			),
		)


############################################
############## DEFAULT ROUTER ##############
###########################################


@default_router.message(F.text)
async def text_handler(message: Message):
	user = users.get(message.chat.id, {})
	await message.delete()

	if user.get('final', False):
		await message.answer(
			'🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!',
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_main_menu_markup(message.from_user.id),
		)
		return
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': message.from_user.id}}
	)
	partner = partners[0]['partners']

	if partner:
		partner = partner[-1]

		if not partner['approved']:
			await message.answer(
				'Вы не зарегистрированы в боте, для продолжения Вам необходимо подать заявку. Это займет менее 5 минут.',
				parse_mode=ParseMode.HTML,
				reply_markup=inline.create_start_markup(),
			)
