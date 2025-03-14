import random
import string
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message
from dateutil.relativedelta import relativedelta
from loguru import logger

import app.keyboards.admin_inline as inline
from app.api import APIRequest
from app.loader import (
	bot,
	convert_to_human,
	humanize_place,
	humanize_promocode_type,
	save_data,
	sinwin_data,
)

admin_router = Router()

deleted_promocodes = {}


def generate_random_promocode() -> str:
	length = 16
	characters = string.ascii_letters + string.digits  # Содержит буквы и цифры
	promocode = ''.join(random.choice(characters) for _ in range(length))

	while promocode in sinwin_data['promocodes']:
		promocode = ''.join(random.choice(characters) for _ in range(length))

	return promocode


def generate_excel_file(data: List[Dict[str, Any]]):
	df = pd.DataFrame.from_dict(data)

	# Сохраняем DataFrame в Excel-файл
	file_name = f'{datetime.now().strftime("%Y%m%d")}_output.xlsx'
	df.to_excel(file_name, index=False)

	with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
		df.to_excel(writer, index=False, sheet_name='Partners')
		ws = writer.sheets['Partners']

		for word in list('CDEFGHIJKLMNOPQRSTUVWXYZ'):
			ws.column_dimensions[word].width = 15

		ws.column_dimensions['B'].width = 30
		ws.column_dimensions['AA'].width = 20
		ws.column_dimensions['AB'].width = 20
		ws.column_dimensions['AC'].width = 20
		ws.column_dimensions['AD'].width = 20
		ws.column_dimensions['AE'].width = 20
		ws.column_dimensions['AF'].width = 20
		ws.column_dimensions['AG'].width = 20
		ws.column_dimensions['AH'].width = 20
		ws.column_dimensions['AI'].width = 20

		writer.book.save(file_name)
	return file_name


class CreateRublesPromocodeGroup(StatesGroup):
	promocode_name = State()


class CreateStatusPromocodeGroup(StatesGroup):
	promocode_name = State()


class CreatePercentPromocodeGroup(StatesGroup):
	promocode_name = State()


class ChangeBalance(StatesGroup):
	new_balance = State()


class ChangeRevsharePercent(StatesGroup):
	new_revshare = State()


class GetInfoAboutPartner(StatesGroup):
	partner_key = State()


class ChangePercentIncome(StatesGroup):
	new_percent = State()
	partner_hash = State()
	show_changed_percent = State()


class ChangePartnerBalance(StatesGroup):
	new_balance = State()
	partner_hash = State()


class GiveWithdraw(StatesGroup):
	partner_hash = State()
	withdraw_time = State()


################################################################################
############################# Информация о партнере ############################
################################################################################


@admin_router.callback_query(F.data == 'admin_info_about_partner')
async def admin_info_partner(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		"""Напишите что-то одно:
├ Телеграм id
├ Телеграм Ник
└ Хеш партнера""",
		reply_markup=inline.create_admin_info_by_user_markup(),
	)
	await state.set_state(GetInfoAboutPartner.partner_key)


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


@admin_router.callback_query(F.data.startswith('admin_info_by_user'))
async def admin_info_by_user(call: CallbackQuery):
	partner_hash = call.data.replace('admin_info_by_user', '')
	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partners = partners['partners']
	partner = partners[-1]

	user_id = partner['tg_id']
	partner_hash = partner['partner_hash']
	status = partner['status']
	additional_percent = partner['additional_percent']
	username = partner['username']

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['partner_hash']}}
	)
	cpartners = cpartners[0]['partners']

	cpartners_items = []

	for cp in cpartners:
		regdate = datetime.strptime(cp['register_date'], '%Y-%m-%dT%H:%M:%S')
		regdate = regdate.strftime('%H:%M %d/%m/%Y')
		cpartners_items.append(
			f'├ {regdate}:{cp["tg_id"]}:{cp["status"]}:{cp["username"]}:{cp["status"]}:{cp["total_income"]} рублей'
		)

	cpartners_items = '\n'.join(cpartners_items)

	transactions, status = await APIRequest.post(
		'/transaction/find', {'opts': {'partner_hash': partner_hash}}
	)

	transactions = transactions['transactions']

	transactions_items = []

	for transac in transactions:
		regdate = datetime.strptime(
			transac['register_date'], '%Y-%m-%dT%H:%M:%S'
		).strftime('%H:%M %d/%m/%Y')
		withdraw_sum = transac['amount']
		transaction_type = transac['transaction_type']
		transactions_items.append(f'├ {regdate}:{withdraw_sum}:{transaction_type}')

	transactions_items = '\n'.join(transactions_items)

	opts = {'referal_parent': partner['partner_hash']}

	data = await collect_stats(opts)

	result, code = await APIRequest.get('/base/stats')
	stats = result['data']

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
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	yesterday_deps = sum(
		[
			dep['amount']
			for dep in stats['yesterday']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	last_week_deps = sum(
		[
			dep['amount']
			for dep in stats['last_week']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_deps = sum(
		[
			dep['amount']
			for dep in stats['last_month']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
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

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len(
		[
			dep['x']
			for dep in other_dates_firstdep
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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

	showed_percent = (
		partner['showed_percent']
		if partner['showed_percent'] != 'default'
		else get_percent_by_status(partner['status'])
		+ partner['additional_percent'] * 100
	)

	logger.debug(
		f'showed_percent: {showed_percent}     {partner["additional_percent"] * 100}      {get_percent_by_status(partner["status"])}'
	)

	await call.message.edit_text(
		f"""
СТАТИСТИКА ПО ВСЕМ БОТАМ

💰 Баланс: {partner['balance']} RUB

🆔 ID пользователя: {user_id}
├ 🤖Ник пользователя: {username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
├ 🎯 Пользователь получает : {get_percent_by_status(partner['status']) + additional_percent * 100}% / {partner['showed_percent']}%
└ ☯️ Количество дней с нами: {days_difference}

🏗 Количество рефералов: {len(cpartners)}
├ Дата:Tg_id:Ник:Статус:Доход за все время
{cpartners_items}

🤖 История выводов: n
├ Дата:Сумма вывода:Наименование вывода
{transactions_items}

Всего пользователей: {data['users_count']}
├ Депозиты за все время: {alltime_deps}
├ Доход за все время: {alltime_income}

Первые депозиты за все время: {alltime_firstdeps}
├ Api за все время: {api_count}
└ Сгенерировано сигналов: {signals_gens}

┌ Пользователей на этапе регистрации: {data['users_notreg_count']}
├ Пользователей на этапе пополнения: {data['users_nottopup_count']}
└ Пользователей на этапе игры: {data['users_gamed_count']}

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
		reply_markup=inline.create_partner_interactions_markup(partner['partner_hash']),
	)


@admin_router.message(F.text, GetInfoAboutPartner.partner_key)
async def get_partner_by_key_message(message: Message, state: FSMContext):
	await state.update_data(partner_key=message.text)

	partner_key = message.text

	partners = []

	if partner_key.isdigit():
		result, status = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': int(partner_key)}}
		)

		partners = result['partners']

	if len(partners) < 1:
		result, status = await APIRequest.post(
			'/partner/find', {'opts': {'username': partner_key}}
		)

		partners = result['partners']

	if len(partners) < 1:
		result, status = await APIRequest.post(
			'/partner/find', {'opts': {'partner_hash': partner_key}}
		)

		partners = result['partners']

	if len(partners) == 0:
		await message.answer(
			"""
Я не понял кого вы хотите найти

Напишите что-то одно:
├ Телеграм id
├ Телеграм Ник
└ Хеш партнера""",
			reply_markup=inline.create_admin_info_by_user_markup(),
		)
		await state.set_state(GetInfoAboutPartner.partner_key)
		return

	partner = partners[-1]

	user_id = partner['tg_id']
	partner_hash = partner['partner_hash']
	status = partner['status']
	additional_percent = partner['additional_percent']
	username = partner['username']

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	cpartners = await APIRequest.post(
		'/partner/find', {'opts': {'referrer_hash': partner['partner_hash']}}
	)
	cpartners = cpartners[0]['partners']

	cpartners_items = []

	for cp in cpartners:
		regdate = datetime.strptime(cp['register_date'], '%Y-%m-%dT%H:%M:%S')
		regdate = regdate.strftime('%H:%M %d/%m/%Y')
		cpartners_items.append(
			f'├ {regdate}:{cp["tg_id"]}:{cp["status"]}:{cp["username"]}:{cp["status"]}:{cp["total_income"]} рублей'
		)

	cpartners_items = '\n'.join(cpartners_items)

	transactions, status = await APIRequest.post(
		'/transaction/find', {'opts': {'partner_hash': partner_hash}}
	)

	transactions = transactions['transactions']

	transactions_items = []

	for transac in transactions:
		regdate = datetime.strptime(
			transac['register_date'], '%Y-%m-%dT%H:%M:%S'
		).strftime('%H:%M %d/%m/%Y')
		withdraw_sum = transac['amount']
		transaction_type = transac['transaction_type']
		transactions_items.append(f'├ {regdate}:{withdraw_sum}:{transaction_type}')

	transactions_items = '\n'.join(transactions_items)

	opts = {'referal_parent': partner['partner_hash']}

	data = await collect_stats(opts)

	result, code = await APIRequest.get('/base/stats')
	stats = result['data']

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
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	yesterday_deps = sum(
		[
			dep['amount']
			for dep in stats['yesterday']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	last_week_deps = sum(
		[
			dep['amount']
			for dep in stats['last_week']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_deps = sum(
		[
			dep['amount']
			for dep in stats['last_month']['dep']
			if dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
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

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len(
		[
			dep['x']
			for dep in other_dates_firstdep
			if dep['partner_hash'] == partner['partner_hash']
		]
	)

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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

	showed_percent = (
		partner['showed_percent']
		if partner['showed_percent'] != 'default'
		else get_percent_by_status(partner['status'])
		+ partner['additional_percent'] * 100
	)

	logger.debug(
		f'showed_percent: {showed_percent}     {partner["additional_percent"] * 100}      {get_percent_by_status(partner["status"])}'
	)

	await message.answer(
		f"""
СТАТИСТИКА ПО ВСЕМ БОТАМ

💰 Баланс: {partner['balance']} RUB

🆔 ID пользователя: {user_id}
├ 🤖Ник пользователя: {username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
├ 🎯 Пользователь получает : {get_percent_by_status(partner['status']) + additional_percent * 100}% / {partner['showed_percent']}%
└ ☯️ Количество дней с нами: {days_difference}

🏗 Количество рефералов: {len(cpartners)}
├ Дата:Tg_id:Ник:Статус:Доход за все время
{cpartners_items}

🤖 История выводов: n
├ Дата:Сумма вывода:Наименование вывода
{transactions_items}

Всего пользователей: {data['users_count']}
├ Депозиты за все время: {alltime_deps}
├ Доход за все время: {alltime_income}

Первые депозиты за все время: {alltime_firstdeps}
├ Api за все время: {api_count}
└ Сгенерировано сигналов: {signals_gens}

┌ Пользователей на этапе регистрации: {data['users_notreg_count']}
├ Пользователей на этапе пополнения: {data['users_nottopup_count']}
└ Пользователей на этапе игры: {data['users_gamed_count']}

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
		reply_markup=inline.create_partner_interactions_markup(partner['partner_hash']),
	)


@admin_router.callback_query(F.data.startswith('admin_set_percent_income_to_partner_'))
async def admin_set_percent_income_to_partner_callback(
	call: CallbackQuery, state: FSMContext
):
	partner_hash = call.data.replace('admin_set_percent_income_to_partner_', '')

	# partners, code = await APIRequest.post('/partner/find', {'opts': {'partner_hash': partner_hash}})
	# partner = partners['partners'][-1]

	await call.message.edit_text(
		"""Напишите какой процент для этого пользователя сделать или выберите из инлайт кнопок.

Процент от дохода 1 Win Максимум 60 %""",
		reply_markup=inline.create_percent_input_markup(partner_hash),
	)

	await state.update_data(partner_hash=partner_hash)
	await state.set_state(ChangePercentIncome.new_percent)


@admin_router.callback_query(
	F.data.startswith('admin_change_percent_income_to_percent_'),
	ChangePercentIncome.new_percent,
)
async def admin_change_percent_income_to_percent_callback(
	call: CallbackQuery, state: FSMContext
):
	percent = call.data.split('.')[-1]
	partner_hash = call.data.split('.')[0].replace(
		'admin_change_percent_income_to_percent_', ''
	)

	await call.message.edit_text(
		f'Отображать измененный процент ({percent}%) у пользователя?',
		reply_markup=inline.create_yes_no_markup_for_income_percent(partner_hash),
	)

	await state.update_data(new_percent=str(percent))
	await state.set_state(ChangePercentIncome.show_changed_percent)


@admin_router.callback_query(
	F.data.startswith('admin_change_percent_income_to_percent_'),
	ChangePercentIncome.new_percent,
)
async def admin_change_percent_income_to_percent_msg(
	message: Message, state: FSMContext
):
	percent = message.text

	if not percent.isdigit():
		await message.answer('Ошибка! Введите число!')
		await state.set_state(ChangePercentIncome.new_percent)
		return
	else:
		percent = str(percent)

	await message.answer(
		f'Отображать измененный процент ({percent}%) у пользователя?',
		reply_markup=inline.create_yes_no_markup_for_income_percent(),
	)

	await state.update_data(new_percent=percent)
	await state.set_state(ChangePercentIncome.show_changed_percent)


@admin_router.callback_query(
	F.data == 'admin_percent_income_disapprove',
	ChangePercentIncome.show_changed_percent,
)
async def admin_percent_income_disapprove_callback(
	call: CallbackQuery, state: FSMContext
):
	await state.update_data(show_changed_percent=False)
	data = await state.get_data()
	partner_hash = data['partner_hash']
	percent = data['new_percent']

	partners, result = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['showed_percent'] = str(
		get_percent_by_status(partner['status']) + partner['additional_percent'] * 100
	)
	partner['additional_percent'] = (
		int(percent) - get_percent_by_status(partner['status'])
	) / 100

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Поменял процент дохода для пользователя

Пользователь получает : {percent}%
Пользователь видит: Нет

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}""",
		reply_markup=inline.get_markup_back_and_cancel_perc_inc(partner_hash),
	)


@admin_router.callback_query(
	F.data == 'admin_percent_income_approve', ChangePercentIncome.show_changed_percent
)
async def admin_percent_income_approve_callback(call: CallbackQuery, state: FSMContext):
	await state.update_data(show_changed_percent=False)
	data = await state.get_data()
	partner_hash = data['partner_hash']
	percent = data['new_percent']

	partners, result = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['showed_percent'] = 'default'
	partner['additional_percent'] = (
		int(percent) - get_percent_by_status(partner['status'])
	) / 100

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Поменял процент дохода для пользователя

Пользователь получает : {percent}%
Пользователь видит: Да

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}""",
		reply_markup=inline.get_markup_back_and_cancel_perc_inc(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_change_status_'))
async def admin_change_status_callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_change_status_', '')

	await call.message.edit_text(
		'Выберите какой статус сделать для этого пользователя.',
		reply_markup=inline.create_change_status_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_set_status_'))
async def admin_set_status_callback(call: CallbackQuery):
	status = call.data.split('.')[-1]
	data = call.data.split('.')[0]
	partner_hash = data.replace('admin_set_status_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	partner['status'] = status

	partner['additional_percent'] = 0.0

	partner['showed_percent'] = 'default'

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f'Статус пользователя изменен: {status}',
		reply_markup=inline.get_markup_back_and_cancel_status(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_change_balance_'))
async def admin_change_balance_callback(call: CallbackQuery, state: FSMContext):
	partner_hash = call.data.replace('admin_change_balance_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']} рублей

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}

Напишите в чат какой баланс делать для пользователя?

Поставить на паузу - заморозить счет чтобы любые доходы и расходы не зачислялись на баланс
""",
		reply_markup=inline.create_admin_balance_change_markup(partner_hash),
	)

	await state.update_data(partner_hash=partner_hash)
	await state.set_state(ChangePartnerBalance.new_balance)


@admin_router.callback_query(
	F.data.startswith('admin_freeze_partner_'), ChangePartnerBalance.new_balance
)
async def admin_freeze_partner_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	partner_hash = call.data.replace('admin_freeze_partner_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['is_freezed'] = True

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']} рублей

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}

Напишите в чат какой баланс делать для пользователя?

Снять с паузы - разморозить счет чтобы любые доходы и расходы зачислялись на баланс
""",
		reply_markup=inline.create_admin_balance_change_markup_defreeze(partner_hash),
	)

	await state.set_state(ChangePartnerBalance.new_balance)


@admin_router.callback_query(
	F.data.startswith('admin_defreeze_partner_'), ChangePartnerBalance.new_balance
)
async def admin_defreeze_partner_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	partner_hash = call.data.replace('admin_defreeze_partner_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['is_freezed'] = False

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']} рублей

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}

Напишите в чат какой баланс делать для пользователя?

Поставить на паузу - заморозить счет чтобы любые доходы и расходы не зачислялись на баланс
""",
		reply_markup=inline.create_admin_balance_change_markup_defreeze(partner_hash),
	)

	await state.set_state(ChangePartnerBalance.new_balance)


@admin_router.message(F.text, ChangePartnerBalance.new_balance)
async def set_new_balance_message(message: Message, state: FSMContext):
	new_balance = message.text

	data = await state.get_data()
	partner_hash = data['partner_hash']

	if not new_balance.isdigit():
		await message.answer(
			'Введите число',
			reply_markup=inline.create_admin_balance_change_markup(partner_hash),
		)
		await state.set_state(ChangePartnerBalance.new_balance)
		return
	else:
		new_balance = int(new_balance)

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	await message.answer(
		f"""Сделать для пользователя
	
🆔 ID пользователя: (тут тг id пользователя){username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}

Сейчас баланс пользователя: {partner['balance']}
Баланс который станет: {new_balance}""",
		reply_markup=inline.create_ok_or_cancel_balance_markup(
			partner_hash, new_balance
		),
	)
	await state.clear()


@admin_router.callback_query(F.data.startswith('admin_totally_change_balance_'))
async def admin_totally_change_balance_callback(call: CallbackQuery):
	new_balance = call.data.split('.')[-1]
	partner_hash = call.data.split('.')[0].replace('admin_totally_change_balance_', '')
	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['balance'] = int(new_balance)

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Баланс пользователя: {new_balance}
	
🆔 ID пользователя: (тут тг id пользователя){username}
├ 🛡 Хэш: {partner['partner_hash']}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}""",
		reply_markup=inline.create_back_admin_info_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_block_user_'))
async def admin_block_user_callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_block_user_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']}

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner['partner_hash']}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}

Заблокировать - пользователь будет заблокирован, он больше не сможет пользоваться ботом""",
		reply_markup=inline.create_block_user_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_totally_block_'))
async def admin_totally_block_callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_totally_block_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['approved'] = False
	# users[partner["tg_id"]] = users.get(partner["tg_id"], {})
	# users[partner["tg_id"]]['final'] = False

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']}

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner['partner_hash']}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}""",
		reply_markup=inline.create_unblock_user_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_totally_unblock_'))
async def admin_totally_unblock__callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_totally_unblock_', '')

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	partner['approved'] = True
	# users[partner["tg_id"]] = users.get(partner["tg_id"], {})
	# users[partner["tg_id"]]['final'] = True

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Баланс пользователя: {partner['balance']}

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner['partner_hash']}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}""",
		reply_markup=inline.create_block_user_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('admin_give_withdraw_'))
async def admin_give_withdraw_callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_give_withdraw_', '')

	await call.message.edit_text(
		'Выберите на какой период дать возможность вывести средства?',
		reply_markup=inline.create_withdraw_period_markup(partner_hash),
	)


@admin_router.callback_query(F.data.startswith('set_withdraw_period_'))
async def set_withdraw_period_callback(call: CallbackQuery):
	period = call.data.split('.')[-1]
	partner_hash = call.data.split('.')[0].replace('set_withdraw_period_', '')

	period_timedelta = timedelta(minutes=30)

	if period == '1h':
		period = '1 час'
		period_timedelta = timedelta(hours=1)
	elif period == '2h':
		period = '2 часа'
		period_timedelta = timedelta(hours=2)
	elif period == '3h':
		period = '3 часа'
		period_timedelta = timedelta(hours=3)
	elif period == '6h':
		period = '6 часов'
		period_timedelta = timedelta(hours=6)
	elif period == '12h':
		period = '12 часов'
		period_timedelta = timedelta(hours=12)
	elif period == '1d':
		period = '1 день'
		period_timedelta = timedelta(days=1)
	elif period == '2d':
		period = '2 дня'
		period_timedelta = timedelta(days=2)
	elif period == '3d':
		period = '3 дня'
		period_timedelta = timedelta(days=3)

	partners, code = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partner = partners['partners'][-1]

	username = (
		f'\n├ 🤖Ник пользователя: {partner["username"]}'
		if partner['username'] is not None
		else ''
	)

	reg_date = datetime.fromisoformat(partner.get('register_date'))
	cur_date = datetime.now()
	difference = cur_date - reg_date
	days_difference = max(difference.days, 1)

	date = datetime.now() + period_timedelta
	partner['time_to_withdraw'] = date.strftime('%Y-%m-%d %H:%M:%S')

	await APIRequest.post('/partner/update', {**partner})

	await call.message.edit_text(
		f"""Выдал пользователю права на вывод
Период действия: {period}

🆔 ID пользователя: {partner['tg_id']}{username}
├ 🛡 Хэш: {partner_hash}
├ ⚖️ Статус: {partner['status']}
└ ☯️ Количество дней с нами: {days_difference}
""",
		reply_markup=inline.create_admin_give_withdraw_callback_back(partner_hash),
	)

	await bot.send_message(
		chat_id=partner['tg_id'],
		text=f'Вам доступен вывод средств в течение {period}',
		reply_markup=inline.create_profile_partner_markup(),
	)


###############################################################
######################## ИЗМЕНИТЬ МЕНЮ ########################
###############################################################


@admin_router.callback_query(F.data == 'admin_main_settings')
async def admin_main_settings(call: CallbackQuery):
	result, status = await APIRequest.get('/base/admin_balance_and_revshare')

	balance = result['balance']
	revshare_percent = result['revshare']

	await call.message.edit_text(
		text=f"""Выберите из списка
	
Баланс Партнерки: {convert_to_human(balance)} рублей
RevShare: {int(revshare_percent * 100)}%""",
		reply_markup=inline.admin_main_settings_menu(),
	)


@admin_router.callback_query(F.data == 'change_revshare_percent')
async def change_revshare_percent(call: CallbackQuery, state: FSMContext):
	result, status = await APIRequest.get('/base/admin_balance_and_revshare')

	balance = result['balance']
	revshare_percent = result['revshare']

	await call.message.edit_text(
		f"""Напишите какой процент у вас в партнерском аккаунте 1Win.

Текущий баланс партнерки: {convert_to_human(balance)}
Текущий RevShare: {int(revshare_percent * 100)}%""",
		reply_markup=inline.create_back_markup('admin_main_settings'),
	)

	await state.set_state(ChangeRevsharePercent.new_revshare)


@admin_router.message(F.text, ChangeRevsharePercent.new_revshare)
async def change_revshare_percent_message(message: Message, state: FSMContext):
	await state.update_data(new_revshare=message.text)
	new_revshare = message.text

	if not new_revshare.isdigit():
		await message.answer(
			f'Некорректный ввод: {new_revshare} не число',
			reply_markup=inline.create_back_markup('change_revshare_percent'),
		)
		await state.set_state(ChangeRevsharePercent.new_revshare)
		return

	new_revshare = int(new_revshare)

	if new_revshare >= 100:
		await message.answer(
			f'Некорректный ввод: {new_revshare} больше или равен 100',
			reply_markup=inline.create_back_markup('change_revshare_percent'),
		)
		await state.set_state(ChangeRevsharePercent.new_revshare)
		return

	new_revshare = int(new_revshare) / 100

	result, status = await APIRequest.get('/base/admin_balance_and_revshare')

	revshare_percent = result['revshare']

	await message.answer(
		f"""Вы хотите поменять процент дохода по RevShare на {int(new_revshare * 100)}%?

Чем больше процент, тем меньше получают партнеры.

Текущий RevShare: {int(revshare_percent * 100)}%""",
		reply_markup=inline.create_approve_revshare_change_markup(new_revshare),
	)

	await state.clear()


@admin_router.callback_query(F.data.startswith('revshare_approve_revshare_change_'))
async def approve_revshare_change_callback(call: CallbackQuery):
	new_revshare = float(call.data.replace('revshare_approve_revshare_change_', ''))

	result, status = await APIRequest.get(
		f'/base/set_revshare?revshare_perc={new_revshare}'
	)

	await call.message.edit_text(
		f'Текущий процент по RevShare изменен\nПроцент партнерки: {int(new_revshare * 100)}%',
		reply_markup=inline.create_back_markup('admin_main_settings'),
	)


@admin_router.callback_query(F.data == 'change_partner_balance')
async def change_partner_balance_callback(call: CallbackQuery, state: FSMContext):
	result, status = await APIRequest.get('/base/admin_balance_and_revshare')

	balance = result['balance']

	await call.message.edit_text(
		f'Напишите текущий баланс в партнерском аккаунте 1Win.\n\nТекущий баланс партнерки: {convert_to_human(balance)} рублей',
		reply_markup=inline.create_back_markup('admin_main_settings'),
	)

	await state.set_state(ChangeBalance.new_balance)


@admin_router.message(F.text, ChangeBalance.new_balance)
async def change_partner_balance_message_callback(message: Message, state: FSMContext):
	await state.update_data(new_balance=message.text)
	new_balance = message.text

	if not new_balance.isdigit():
		await message.answer(
			f'Некорректный ввод: {new_balance} не число',
			reply_markup=inline.create_back_markup('change_partner_balance'),
		)
		await state.set_state(ChangeBalance.new_balance)
		return

	new_balance = float(new_balance)

	result, status = await APIRequest.get('/base/admin_balance_and_revshare')

	balance = result['balance']

	await message.answer(
		f"""Вы хотите сделать баланс партнерки {convert_to_human(new_balance)} рублей?

Текущий баланс партнерки: {convert_to_human(balance)} рублей""",
		reply_markup=inline.create_approve_balance_change_markup(new_balance),
	)

	await state.clear()


@admin_router.callback_query(F.data.startswith('balance_approve_balance_change_'))
async def approve_balance_change_new_balance(call: CallbackQuery):
	new_balance = float(call.data.replace('balance_approve_balance_change_', ''))

	result, status = await APIRequest.get(
		f'/base/set_admin_balance?balance_set={new_balance}'
	)

	balance = result['balance']

	await call.message.edit_text(
		f'Текущий баланс партнерки изменен\nБаланс партнерки: {balance}',
		reply_markup=inline.create_back_markup('admin_main_settings'),
	)


@admin_router.callback_query(F.data == 'change_bot_links')
async def change_bot_links(call: CallbackQuery):
	await call.message.edit_text(
		'Выберите бота в которых вы хотите поменять ссылки',
		reply_markup=inline.create_bot_links_menu(),
	)


@admin_router.callback_query(F.data.startswith('change_links_in_bot_'))
async def change_links_in_bot_by_name(call: CallbackQuery):
	bot_name = call.data.replace('change_links_in_bot_', '')

	if bot_name == 'mines':
		bot_name = '💣 Mines'
		url = 'https://t.me/IziMin_test_Bot'
	elif bot_name == 'luckyjet':
		bot_name = '🚀 Lucky Jet'
		url = 'https://t.me/CashJetBot'
	elif bot_name == 'speedcash':
		bot_name = '🚗 Speed Cash'
		url = 'https://t.me/SPDCashBot'
	elif bot_name == 'coinflip':
		bot_name = '🎲 Coin Flip'
		url = 'https://t.me/CoinFlipBot'
	else:
		bot_name = '💣 Mines'
		url = 'https://t.me/IziMin_test_Bot'

	await call.message.edit_text(
		f'Для того, чтобы задать ссылки для бота {bot_name} зайдите в диалог <a href="{url}">с ним</a> и перейдите в админ-панель бота.',
		reply_markup=inline.create_bot_link_menu(bot_name, url),
		parse_mode=ParseMode.HTML,
	)


@admin_router.callback_query(F.data == 'admin_all_partners_1win')
async def admin_all_partners_1win_callback(call: CallbackQuery):
	partners, result = await APIRequest.post('/partner/get', {'index': None})

	partners = partners['partners']

	partners_message = []
	total_balance = 0
	approved_partners = 0

	for i, partner in enumerate(partners):
		partners_message.append(
			f'{i + 1}) {partner["tg_id"]}:{partner["username"]}:{partner["partner_hash"]}:{partner["status"]}:{partner["balance"]}'
		)
		total_balance += partner['balance']

		if partner['approved']:
			approved_partners += 1

	partners_message = '\n'.join(partners_message)

	(
		await call.message.edit_text(
			f"""
Количество партнеров: {approved_partners}

Баланс всех пользователей: {total_balance}

tg_id:Ник:Хеш:Статус:Баланс
{partners_message}
""",
			reply_markup=inline.admin_send_partners_excel(),
		),
	)


@admin_router.callback_query(F.data.startswith('admin_get_info_by_partner_mines_'))
async def admin_get_info_by_partner_mines_callback(call: CallbackQuery):
	partner_hash = call.data.replace('admin_get_info_by_partner_mines_', '')

	partners, result = await APIRequest.post(
		'/partner/find', {'opts': {'partner_hash': partner_hash}}
	)
	partners = partners['partners']

	partner = partners[-1]

	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	opts = {'game': 'Mines', 'referal_parent': partner['partner_hash']}

	data = await collect_stats(opts)

	api_count = result['api_count'].get(partner['partner_hash'], 0)

	today_firstdeps = len(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_firstdeps = len(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)

	today_deps = sum(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['today']['dep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_deps = sum(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['yesterday']['dep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_deps = sum(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['last_week']['dep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_deps = sum(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['last_month']['dep']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)

	today_income = sum(
		[
			dep['x']
			for dep in stats['today']['income']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	yesterday_income = sum(
		[
			dep['x']
			for dep in stats['yesterday']['income']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_week_income = sum(
		[
			dep['x']
			for dep in stats['last_week']['income']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)
	last_month_income = sum(
		[
			dep['x']
			for dep in stats['last_month']['income']
			if dep['game'] == 'Mines' and dep['partner_hash'] == partner['partner_hash']
		]
	)

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len(
		[
			dep['x']
			for dep in other_dates_firstdep
			if dep['partner_hash'] == partner['partner_hash'] and dep['game'] == 'Mines'
		]
	)

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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
		reply_markup=inline.create_back_admin_info_markup(partner_hash),
	)


@admin_router.callback_query(F.data == 'send_partners_excel')
async def send_partners_excel_callback(call: CallbackQuery):
	await call.message.edit_text(
		'Отправляем Excel-файл с информацией о партнерах... Ожидайте, это может занять некоторое время.',
		reply_markup=inline.create_back_markup('adminpanel'),
	)

	partners, result = await APIRequest.post('/partner/get', {'index': -1})
	partners = partners['partners']

	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	result_data = []

	for i, partner in enumerate(partners):
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
			]
		) + sum(
			[
				dep['amount']
				for dep in stats['today']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		yesterday_deps = sum(
			[
				dep['amount']
				for dep in stats['yesterday']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		) + sum(
			[
				dep['amount']
				for dep in stats['yesterday']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		last_week_deps = sum(
			[
				dep['amount']
				for dep in stats['last_week']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		) + sum(
			[
				dep['amount']
				for dep in stats['last_week']['firstdep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		)
		last_month_deps = sum(
			[
				dep['amount']
				for dep in stats['last_month']['dep']
				if dep['partner_hash'] == partner['partner_hash']
			]
		) + sum(
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

		alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
		other_dates_firstdep = [
			info for name, info in stats.items() if name == 'firstdep'
		]
		others_firstdep = len(
			[
				dep['x']
				for dep in other_dates_firstdep
				if dep['partner_hash'] == partner['partner_hash']
			]
		)

		alltime_firstdeps = (
			others_firstdep
			+ today_firstdeps
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

		result_data.append(
			{
				'id': str(partner['id']),
				'partner_hash': str(partner['partner_hash']),
				'api_count': str(api_count),
				'today_firstdeps': str(today_firstdeps),
				'yesterday_firstdeps': str(yesterday_firstdeps),
				'last_week_firstdeps': str(last_week_firstdeps),
				'last_month_firstdeps': str(last_month_firstdeps),
				'today_deps': str(today_deps),
				'yesterday_deps': str(yesterday_deps),
				'last_week_deps': str(last_week_deps),
				'last_month_deps': str(last_month_deps),
				'alltime_deps': str(alltime_deps),
				'alltime_firstdeps': str(alltime_firstdeps),
				'today_income': str(today_income),
				'yesterday_income': str(yesterday_income),
				'last_week_income': str(last_week_income),
				'last_month_income': str(last_month_income),
				'alltime_income': str(alltime_income),
				'signals_gens': str(signals_gens),
				'tg_id': str(partner['tg_id']),
				'username': str(partner['username']),
				'status': str(partner['status']),
				'additional_percent': str(partner['additional_percent']),
				'register_date': str(partner['register_date']),
				'referals_count': str(partner['referals_count']),
				'ref_income': str(partner['ref_income']),
				'age': str(partner['ref_income']),
				'referrer_hash': str(partner['ref_income']),
				'approved': str(partner['ref_income']),
				'is_referal': str(partner['is_referal']),
				'arbitration_experience': str(partner['arbitration_experience']),
				'fullname': str(partner['fullname']),
				'number_phone': str(partner['number_phone']),
				'experience_time': str(partner['experience_time']),
				'balance': str(partner['balance']),
				'showed_percent': str(partner['showed_percent']),
				'is_freezed': str(partner['is_freezed']),
				'last_withdraw_date': str(partner['last_withdraw_date']),
				'total_income': str(partner['total_income']),
			}
		)

	filename = generate_excel_file(result_data)

	efile = FSInputFile(path=filename)
	await call.message.answer_document(
		document=efile,
		caption='Результат в виде Excel-файла',
		reply_markup=inline.back_markup(),
	)


################################################################################
################################## Статистика ##################################
################################################################################


@admin_router.callback_query(F.data == 'admin_statistics')
async def admin_statistics_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	data = await collect_stats({})

	today_firstdeps = len([dep['amount'] for dep in stats['today']['firstdep']])
	yesterday_firstdeps = len([dep['amount'] for dep in stats['yesterday']['firstdep']])
	last_week_firstdeps = len([dep['amount'] for dep in stats['last_week']['firstdep']])
	last_month_firstdeps = len(
		[dep['amount'] for dep in stats['last_month']['firstdep']]
	)

	today_deps = sum([dep['amount'] for dep in stats['today']['dep']]) + sum(
		[dep['amount'] for dep in stats['today']['firstdep']]
	)
	yesterday_deps = sum([dep['amount'] for dep in stats['yesterday']['dep']]) + sum(
		[dep['amount'] for dep in stats['yesterday']['firstdep']]
	)
	last_week_deps = sum([dep['amount'] for dep in stats['last_week']['dep']]) + sum(
		[dep['amount'] for dep in stats['last_week']['firstdep']]
	)
	last_month_deps = sum([dep['amount'] for dep in stats['last_month']['dep']]) + sum(
		[dep['amount'] for dep in stats['last_month']['firstdep']]
	)

	today_income = sum([dep['income'] for dep in stats['today']['income']])
	yesterday_income = sum([dep['income'] for dep in stats['yesterday']['income']])
	last_week_income = sum([dep['income'] for dep in stats['last_week']['income']])
	last_month_income = sum([dep['income'] for dep in stats['last_month']['income']])

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len([dep['x'] for dep in other_dates_firstdep])

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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

	await call.message.edit_text('\n'.join(messages), parse_mode=ParseMode.HTML)


################################################################################
################################### Промокоды ##################################
################################################################################


@admin_router.callback_query(F.data == 'admin_promocodes')
async def admin_promocodes_callback(call: CallbackQuery):
	await call.message.edit_text(
		"""
Выберете на что вы хотите создать промокод?

Промокод на:
1) Рубли
2) Статус
3) Прибавить процент
""",
		reply_markup=inline.create_admin_promocodes_markup(),
	)


@admin_router.callback_query(F.data == 'create_promocode_rubles')
async def create_promocode_rub_callback(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		"""
Напишите: Название / на какую сумму хотите создать промокод / на какое количество использований

Название <code>Random</code> - случайное название

Пример: FREE 5000 1

Промокод FREE, на 5000 рублей, 1 активация
""",
		reply_markup=inline.create_admin_promocode_markup(),
		parse_mode=ParseMode.HTML,
	)
	await state.set_state(CreateRublesPromocodeGroup.promocode_name)


@admin_router.callback_query(F.data == 'create_promocode_percent')
async def create_promocode_percent(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		"""
Напишите на сколько процентов хотите сделать промокод?

Напишите: Название / Процент / количество использований

Название <code>Random</code> - случайное название

Пример: FREE 5 1
Промокод FREE, на прибавку 5 % к заработку, 1 активация
""",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_admin_promocode_markup(),
	)
	await state.set_state(CreatePercentPromocodeGroup.promocode_name)


@admin_router.message(F.text, CreatePercentPromocodeGroup.promocode_name)
async def create_percent_promocode_state(message: Message, state: FSMContext):
	await state.update_data(promocode_name=message.text)
	data = message.text.split(' ')

	if len(data) < 3:
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreatePercentPromocodeGroup.promocode_name)
		return

	if data[0] in sinwin_data['promocodes']:
		await message.answer(
			'❌Такой промокод уже существует',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreatePercentPromocodeGroup.promocode_name)
		return

	if not data[1].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreatePercentPromocodeGroup.promocode_name)
		return
	else:
		if int(data[1]) > 99:
			await message.answer(
				'❌Введено в неправильном формате',
				reply_markup=inline.create_back_markup('admin_promocodes'),
			)
			await state.set_state(CreatePercentPromocodeGroup.promocode_name)
			return

	if not data[2].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreatePercentPromocodeGroup.promocode_name)
		return

	if data[0] == 'Random':
		name = generate_random_promocode()
	else:
		name = data[0]

	date = datetime.now()
	promocode = {
		'type': 'percent',
		'percent': int(data[1]),
		'date': date.strftime('%d.%m.%Y %H:%M:%S'),
		'activates': data[2],
		'activations_left': int(data[2]),
	}

	sinwin_data['promocodes'][name] = promocode

	save_data()

	await message.answer(
		f"""✅Промокод создан: {date.strftime('%d.%m.%Y %H:%M:%S')}

Промокод: <code>{name}</code>
Количество активаций: {data[2]}
Осталось активации: {data[2]}
Промокод на: процент {data[1]}%""",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.delete_promocode_markup(name),
	)

	await state.clear()


@admin_router.callback_query(F.data == 'create_promocode_status')
async def create_promocode_status_callback(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		"""
Напишите на какой статус хотите создать промокод

1. Новичок 35 %
2. Специалист 40 %
3. Профессионал 45 %
4. Мастер 50 %
5. Легенда Суб Партнерство

6. Переход на следующий статус до Специалист 40 %
7. Переход на следующий статус до Профессионал 45 %
8. Переход на следующий статус до Мастер 50 %

Если статус пользователя совпадает с промокодом, бот НЕ присваивает ему новый статус. (моно шрифтом)

Напишите: Название / Номер промокода / количество использований

Название <code>Random</code> - случайное название

Пример: FREE 1 1
Промокод FREE, на статус Новичок 35 % , 1 активация
""",
		reply_markup=inline.create_admin_promocode_markup(),
		parse_mode=ParseMode.HTML,
	)
	await state.set_state(CreateStatusPromocodeGroup.promocode_name)


def get_status_by_digit(status: str):
	status = int(status)

	if status == 1:
		return 'новичок'
	elif status == 2:
		return 'специалист'
	elif status == 3:
		return 'профессионал'
	elif status == 4:
		return 'мастер'
	elif status == 5:
		return 'легенда'
	elif status == 6:
		return 'специалист'
	elif status == 7:
		return 'профессионал'
	elif status == 8:
		return 'мастер'


@admin_router.message(F.text, CreateStatusPromocodeGroup.promocode_name)
async def create_promocode_status_by_name(message: Message, state: FSMContext):
	await state.update_data(promocode_name=message.text)
	data = message.text.split(' ')

	if len(data) < 3:
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateStatusPromocodeGroup.promocode_name)
		return

	if data[0] in sinwin_data['promocodes']:
		await message.answer(
			'❌Такой промокод уже существует',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateStatusPromocodeGroup.promocode_name)
		return

	if not data[1].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateStatusPromocodeGroup.promocode_name)
		return
	else:
		if int(data[1]) > 8:
			await message.answer(
				'❌Введено в неправильном формате',
				reply_markup=inline.create_back_markup('admin_promocodes'),
			)
			return
			await state.set_state(CreateStatusPromocodeGroup.promocode_name)

	if not data[2].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateStatusPromocodeGroup.promocode_name)
		return

	if data[0] == 'Random':
		name = generate_random_promocode()
	else:
		name = data[0]

	status = get_status_by_digit(data[1])

	date = datetime.now()
	status_type = 'status' if data[1].strip() in ['6', '7', '8'] else 'uplevel'
	promocode = {
		'type': 'status',
		'date': date.strftime('%d.%m.%Y %H:%M:%S'),
		'status_type': status_type,
		'data': status.lower(),
		'activates': data[2],
		'activations_left': int(data[2]),
	}

	sinwin_data['promocodes'][name] = promocode

	save_data()

	await message.answer(
		f"""✅Промокод создан: {date.strftime('%d.%m.%Y %H:%M:%S')}

Промокод: <code>{name}</code>
Количество активаций: {data[2]}
Осталось активации: {data[2]}
Промокод на: {'Повышение статуса' if status_type == 'uplevel' else 'Статус'}""",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.delete_promocode_markup(name),
	)

	await state.clear()


@admin_router.message(F.text, CreateRublesPromocodeGroup.promocode_name)
async def create_promocode_rubles_by_name(message: Message, state: FSMContext):
	await state.update_data(promocode_name=message.text)
	data = message.text.split(' ')

	if len(data) < 3:
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateRublesPromocodeGroup.promocode_name)
		return

	if data[0] in sinwin_data['promocodes']:
		await message.answer(
			'❌Такой промокод уже существует',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateRublesPromocodeGroup.promocode_name)
		return

	if not data[1].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateRublesPromocodeGroup.promocode_name)
		return

	if not data[2].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		await state.set_state(CreateRublesPromocodeGroup.promocode_name)
		return

	if data[0] == 'Random':
		name = generate_random_promocode()
	else:
		name = data[0]

	date = datetime.now()
	promocode = {
		'type': 'prize',
		'amount': float(data[1]),
		'date': date.strftime('%d.%m.%Y %H:%M:%S'),
		'activates': data[2],
		'activations_left': int(data[2]),
	}

	sinwin_data['promocodes'][name] = promocode

	save_data()

	await message.answer(
		f"""✅Промокод создан: {date.strftime('%d.%m.%Y %H:%M:%S')}

Промокод: <code>{name}</code>
Количество активаций: {data[2]}
Осталось активации: {data[2]}
Промокод на: Рубли""",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.delete_promocode_markup(name),
	)

	await state.clear()


@admin_router.callback_query(F.data.startswith('reborn_promocode_'))
async def reborn_promocode_by_name_callback(call: CallbackQuery):
	promocode_name = call.data.split('_')[1]

	promocode = deleted_promocodes.get(promocode_name, False)
	date = promocode.get('date', datetime.now().strftime('%d.%m.%Y %H:%M:%S'))

	sinwin_data['promocodes'][promocode_name] = promocode

	save_data()

	await call.message.edit_text(
		f"""✅Промокод создан: {date}

Промокод: <code>{promocode_name}</code>
Количество активаций: {promocode['activates']}
Осталось активации: {promocode['activations_left']}
Промокод на: {humanize_promocode_type(promocode['type'])}""",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.delete_promocode_markup(promocode_name),
	)


@admin_router.callback_query(F.data.startswith('delete_promocode_'))
async def delete_promocode_by_name(call: CallbackQuery):
	promocode_name = call.data.replace('delete_promocode_', '')

	promocode = sinwin_data['promocodes'].get(promocode_name, False)

	if not promocode:
		await call.answer(f'Промокод "{promocode_name}" не найден')
		return

	try:
		del sinwin_data['promocodes'][promocode_name]
	except Exception as ex:
		await call.answer(
			f'Ошибка при удалении промокода "{promocode_name}": {str(ex)}'
		)
		return

	save_data()

	deleted_promocodes[promocode_name] = promocode

	await call.message.answer(
		f"""
❌ Промокод УДАЛЕН
Промокод: <code>{promocode_name}</code>
Промокод на: {humanize_promocode_type(promocode['type'])}
""",
		reply_markup=inline.create_deleted_markup(promocode_name),
		parse_mode=ParseMode.HTML,
	)


@admin_router.callback_query(F.data == 'show_created_promocodes')
async def show_created_promocodes_callback(call: CallbackQuery):
	promocodes = sinwin_data['promocodes']

	for promocode_name, promocode in promocodes.items():
		await call.message.answer(
			f"""
✅Промокод создан: {promocode['date']}

Промокод: <code>{promocode_name}</code>
Количество активаций: {promocode['activates']}
Осталось активации: {promocode['activations_left']}
Промокод на: {humanize_promocode_type(promocode['type'])}	
""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.delete_promocode_markup(promocode_name),
		)


################################################################################
################################## Статистика ##################################
################################################################################


@admin_router.callback_query(F.data == 'admin_statistics_panel_partners')
async def admin_statistics_panel_partners_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	data = await collect_stats({})

	today_firstdeps = len([dep['amount'] for dep in stats['today']['firstdep']])
	yesterday_firstdeps = len(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)
	last_week_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)
	last_month_firstdeps = len(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)

	today_deps = sum(
		[
			dep['amount']
			for dep in stats['today']['dep']
			if dep['partner_hash'] != 'self'
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['today']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)
	yesterday_deps = sum(
		[
			dep['amount']
			for dep in stats['yesterday']['dep']
			if dep['partner_hash'] != 'self'
		]
	) + sum(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)
	last_week_deps = sum([dep['amount'] for dep in stats['last_week']['dep']]) + sum(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)
	last_month_deps = sum([dep['amount'] for dep in stats['last_month']['dep']]) + sum(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['partner_hash'] != 'self'
		]
	)

	today_income = sum(
		[
			dep['income']
			for dep in stats['today']['income']
			if dep['partner_hash'] != 'self'
		]
	)
	yesterday_income = sum(
		[
			dep['income']
			for dep in stats['yesterday']['income']
			if dep['partner_hash'] != 'self'
		]
	)
	last_week_income = sum(
		[
			dep['income']
			for dep in stats['last_week']['income']
			if dep['partner_hash'] != 'self'
		]
	)
	last_month_income = sum(
		[
			dep['income']
			for dep in stats['last_month']['income']
			if dep['partner_hash'] != 'self'
		]
	)

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len([dep['x'] for dep in other_dates_firstdep])

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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

	partners = await APIRequest.post('/partner/find', {'opts': {'approved': True}})
	partners = partners[0]['partners']

	total_balance = sum([partner['balance'] for partner in partners])

	transactions, status = await APIRequest.post(
		'/transaction/find', {'opts': {'approved': True}}
	)

	transactions = transactions['transactions']

	transac_total_balance = []

	for transac in transactions:
		regdate = datetime.strptime(
			transac['register_date'], '%Y-%m-%dT%H:%M:%S'
		).date()
		curr_date = datetime.now().date()

		if regdate == curr_date:
			transac_total_balance.append(transac['amount'])

	transac_total_balance = sum(transac_total_balance)

	await call.message.edit_text(
		f"""
┌ Баланс Партнерки: {balance}
├ Пользователей в партнерки всего: {len(partners)}
├ Баланс всех пользователей: {total_balance}
└ Поставлено на вывод ({datetime.now().strftme('%Y/%m/%d %H:%M')}): {transac_total_balance}

┌ Доход ботов: {alltime_income}
├ Первые депозиты: {alltime_firstdeps}
├ Api: {api_count}
└ Сгенерировано сигналов: {signals_gens}

Доход ботов за сегодня: {today_income}
├ Доход ботов за вчера: (n
├ Доход ботов за неделю: n
└ Доход ботов за месяц: n

Пользователей в партнерки за сегодня: n
├ Пользователей в партнерки за вчера: n
├ Пользователей в партнерки за неделю: n
└ Пользователей в партнерки за месяц: n

Баланс всех пользователей за сегодня: n
├ Баланс всех пользователей за вчера: n
├ Баланс всех пользователей за неделю: n
└ Баланс всех пользователей за месяц: n
"""
	)


@admin_router.callback_query(F.data == 'admin_statistics')
async def admin_statistics_callback_panel(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	data = await collect_stats({})

	today_firstdeps = len([dep['amount'] for dep in stats['today']['firstdep']])
	yesterday_firstdeps = len([dep['amount'] for dep in stats['yesterday']['firstdep']])
	last_week_firstdeps = len([dep['amount'] for dep in stats['last_week']['firstdep']])
	last_month_firstdeps = len(
		[dep['amount'] for dep in stats['last_month']['firstdep']]
	)

	today_deps = sum([dep['amount'] for dep in stats['today']['dep']]) + sum(
		[dep['amount'] for dep in stats['today']['firstdep']]
	)
	yesterday_deps = sum([dep['amount'] for dep in stats['yesterday']['dep']]) + sum(
		[dep['amount'] for dep in stats['yesterday']['firstdep']]
	)
	last_week_deps = sum([dep['amount'] for dep in stats['last_week']['dep']]) + sum(
		[dep['amount'] for dep in stats['last_week']['firstdep']]
	)
	last_month_deps = sum([dep['amount'] for dep in stats['last_month']['dep']]) + sum(
		[dep['amount'] for dep in stats['last_month']['firstdep']]
	)

	today_income = sum([dep['income'] for dep in stats['today']['income']])
	yesterday_income = sum([dep['income'] for dep in stats['yesterday']['income']])
	last_week_income = sum([dep['income'] for dep in stats['last_week']['income']])
	last_month_income = sum([dep['income'] for dep in stats['last_month']['income']])

	alltime_deps = today_deps + yesterday_deps + last_week_deps + last_month_deps
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len([dep['x'] for dep in other_dates_firstdep])

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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
		'<b>ЗА ВСЕ ВРЕМЯ</b>',
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

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_admin_statistics_panel_menu(),
	)


@admin_router.callback_query(F.data == 'admin_statistics_panel_mines')
async def admin_statistics_panel_mines_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	data = await collect_stats({'game': 'Mines'})

	api_count = sum([apinum for partnerhash, apinum in result['api_count'].items()])

	today_firstdeps = len(
		[dep['amount'] for dep in stats['today']['firstdep'] if dep['game'] == 'Mines']
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

	today_deps = sum(
		[dep['amount'] for dep in stats['today']['firstdep'] if dep['game'] == 'Mines']
	) + sum([dep['amount'] for dep in stats['today']['dep'] if dep['game'] == 'Mines'])
	yesterday_deps = sum(
		[
			dep['amount']
			for dep in stats['yesterday']['firstdep']
			if dep['game'] == 'Mines'
		]
	) + sum(
		[dep['amount'] for dep in stats['yesterday']['dep'] if dep['game'] == 'Mines']
	)
	last_week_deps = sum(
		[
			dep['amount']
			for dep in stats['last_week']['firstdep']
			if dep['game'] == 'Mines'
		]
	) + sum(
		[dep['amount'] for dep in stats['last_week']['dep'] if dep['game'] == 'Mines']
	)
	last_month_deps = sum(
		[
			dep['amount']
			for dep in stats['last_month']['firstdep']
			if dep['game'] == 'Mines'
		]
	) + sum(
		[dep['amount'] for dep in stats['last_month']['dep'] if dep['game'] == 'Mines']
	)

	today_income = sum(
		[dep['income'] for dep in stats['today']['income'] if dep['game'] == 'Mines']
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
	other_dates_firstdep = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdep = len(
		[dep['x'] for dep in other_dates_firstdep if dep['game'] == 'Mines']
	)

	alltime_firstdeps = (
		others_firstdep
		+ today_firstdeps
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
		'<b>ЗА ВСЕ ВРЕМЯ</b>',
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

	await call.message.edit_text(
		'\n'.join(messages),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_admin_statistics_panel_menu_game(),
	)


################################################################################
################################# Топ воркеров #################################
################################################################################


@admin_router.callback_query(F.data == 'admin_top_workers')
async def admin_top_workers_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats?exclude=1')

	stats = result['data']
	income_last_month = (
		stats['last_month']['income']
		+ stats['today']['income']
		+ stats['last_week']['income']
		+ stats['yesterday']['income']
	)
	other_dates_income = [info for name, info in stats.items() if name == 'income']
	others_income = [dep for dep in other_dates_income]
	alltime_income = income_last_month + others_income

	partners_last_month = {}
	partners_alltime = {}

	# Last Month
	for partner in income_last_month:
		partner_hash = partner['partner_hash']

		partners_last_month[partner_hash] = partner['x']

	# All time
	for partner in alltime_income:
		partner_hash = partner['partner_hash']

		partners_alltime[partner_hash] = partner['x']

	partners_last_month = dict(
		sorted(partners_last_month.items(), key=lambda item: item[1], reverse=True)
	)
	partners_last_month = dict(list(partners_last_month.items())[:10])

	partners_alltime = dict(
		sorted(partners_alltime.items(), key=lambda item: item[1], reverse=True)
	)
	partners_alltime = dict(list(partners_alltime.items())[:10])

	# Calculate top 10 workers by income last month

	partners_last_month_messages = []

	for i, (partner_hash, income) in enumerate(partners_last_month.items()):
		if i == 0:
			partners_last_month_messages.append(f'🥇 {partner_hash}: {income} рублей')
		elif i == 1:
			partners_last_month_messages.append(f'🥈 {partner_hash}: {income} рублей')
		elif i == 3:
			partners_last_month_messages.append(f'🥉 {partner_hash}: {income} рублей')
		else:
			partners_last_month_messages.append(f'🏅 {partner_hash}: {income} рублей')

	partners_last_month_messages = '\n'.join(partners_last_month_messages)

	# Calculate top 10 workers by income all time

	partners_alltime_messages = []

	for i, (partner_hash, income) in enumerate(partners_alltime.items()):
		if i == 0:
			partners_alltime_messages.append(f'🥇 {partner_hash}: {income} рублей')
		elif i == 1:
			partners_alltime_messages.append(f'🥈 {partner_hash}: {income} рублей')
		elif i == 3:
			partners_alltime_messages.append(f'🥉 {partner_hash}: {income} рублей')
		else:
			partners_alltime_messages.append(f'🏅 {partner_hash}: {income} рублей')

	partners_alltime_messages = '\n'.join(partners_alltime_messages)

	# Print Message
	await call.message.edit_text(
		f"""🏆 Топ воркеров по доходу за последний месяц

{partners_last_month_messages}

🏆 Топ воркеров по доходу за все время

{partners_alltime_messages}""",
		reply_markup=inline.get_admin_top_workers_markup(),
	)


@admin_router.callback_query(F.data == 'admin_top_workers')
async def admin_top_workers_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats?exclude=1')

	stats = result['data']
	income_last_month = (
		stats['last_month']['income']
		+ stats['today']['income']
		+ stats['last_week']['income']
		+ stats['yesterday']['income']
	)
	other_dates_income = [info for name, info in stats.items() if name == 'income']
	others_income = [dep for dep in other_dates_income]
	alltime_income = income_last_month + others_income

	partners_last_month = {}
	partners_alltime = {}

	# Last Month
	for partner in income_last_month:
		partner_hash = partner['partner_hash']

		partners_last_month[partner_hash] = partner['x']

	# All time
	for partner in alltime_income:
		partner_hash = partner['partner_hash']

		partners_alltime[partner_hash] = partner['x']

	partners_last_month = dict(
		sorted(partners_last_month.items(), key=lambda item: item[1], reverse=True)
	)
	partners_last_month = dict(list(partners_last_month.items())[:10])

	partners_alltime = dict(
		sorted(partners_alltime.items(), key=lambda item: item[1], reverse=True)
	)
	partners_alltime = dict(list(partners_alltime.items())[:10])

	# Calculate top 10 workers by income last month

	partners_last_month_messages = []

	for i, (partner_hash, income) in enumerate(partners_last_month.items()):
		if i == 0:
			partners_last_month_messages.append(f'🥇 {partner_hash}: {income} рублей')
		elif i == 1:
			partners_last_month_messages.append(f'🥈 {partner_hash}: {income} рублей')
		elif i == 3:
			partners_last_month_messages.append(f'🥉 {partner_hash}: {income} рублей')
		else:
			partners_last_month_messages.append(f'🏅 {partner_hash}: {income} рублей')

	partners_last_month_messages = '\n'.join(partners_last_month_messages)

	# Calculate top 10 workers by income all time

	partners_alltime_messages = []

	for i, (partner_hash, income) in enumerate(partners_alltime.items()):
		if i == 0:
			partners_alltime_messages.append(f'🥇 {partner_hash}: {income} рублей')
		elif i == 1:
			partners_alltime_messages.append(f'🥈 {partner_hash}: {income} рублей')
		elif i == 3:
			partners_alltime_messages.append(f'🥉 {partner_hash}: {income} рублей')
		else:
			partners_alltime_messages.append(f'🏅 {partner_hash}: {income} рублей')

	partners_alltime_messages = '\n'.join(partners_alltime_messages)

	# Print Message
	await call.message.edit_text(
		f"""🏆 Топ воркеров по доходу за последний месяц

{partners_last_month_messages}

🏆 Топ воркеров по доходу за все время

{partners_alltime_messages}""",
		reply_markup=inline.get_admin_top_workers_markup(),
	)


@admin_router.callback_query(F.data == 'admin_top_workers_by_deps')
async def admin_top_workers_by_deps_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	deps_last_month = (
		stats['last_month']['dep']
		+ stats['today']['dep']
		+ stats['last_week']['dep']
		+ stats['yesterday']['dep']
	)
	other_dates_deps = [info for name, info in stats.items() if name == 'dep']
	others_deps = [dep for dep in other_dates_deps]

	firstdeps_last_month = (
		stats['last_month']['firstdep']
		+ stats['today']['firstdep']
		+ stats['last_week']['firstdep']
		+ stats['yesterday']['firstdep']
	)
	other_dates_firstdeps = [info for name, info in stats.items() if name == 'firstdep']
	others_firstdeps = [firstdep for firstdep in other_dates_firstdeps]

	logger.debug(f'{firstdeps_last_month}    {deps_last_month}')

	alltime_deps = (
		deps_last_month + others_deps + firstdeps_last_month + others_firstdeps
	)
	last_month_deps = deps_last_month + firstdeps_last_month

	partners_last_month = {}
	partners_alltime = {}

	# Last Month
	for partner in last_month_deps:
		partner_hash = partner['partner_hash']

		if partners_last_month.get(partner_hash) is not None:
			partners_last_month[partner_hash] += partner['amount']
		else:
			partners_last_month[partner_hash] = partner['amount']

	# All time
	for partner in alltime_deps:
		partner_hash = partner['partner_hash']

		if partners_alltime.get(partner_hash) is not None:
			partners_alltime[partner_hash] += partner['amount']
		else:
			partners_alltime[partner_hash] = partner['amount']

	partners_last_month = dict(
		sorted(partners_last_month.items(), key=lambda item: item[1], reverse=True)
	)
	partners_last_month = dict(list(partners_last_month.items())[:10])

	partners_alltime = dict(
		sorted(partners_alltime.items(), key=lambda item: item[1], reverse=True)
	)
	partners_alltime = dict(list(partners_alltime.items())[:10])

	# Calculate top 10 workers by deps last month

	partners_last_month_messages = []

	for i, (partner_hash, amount) in enumerate(partners_last_month.items()):
		if i == 0:
			partners_last_month_messages.append(f'🥇 {partner_hash}: {amount} рублей')
		elif i == 1:
			partners_last_month_messages.append(f'🥈 {partner_hash}: {amount} рублей')
		elif i == 3:
			partners_last_month_messages.append(f'🥉 {partner_hash}: {amount} рублей')
		else:
			partners_last_month_messages.append(f'🏅 {partner_hash}: {amount} рублей')

	partners_last_month_messages = '\n'.join(partners_last_month_messages)

	# Calculate top 10 workers by deps all time

	partners_alltime_messages = []

	for i, (partner_hash, amount) in enumerate(partners_alltime.items()):
		if i == 0:
			partners_alltime_messages.append(f'🥇 {partner_hash}: {amount} рублей')
		elif i == 1:
			partners_alltime_messages.append(f'🥈 {partner_hash}: {amount} рублей')
		elif i == 3:
			partners_alltime_messages.append(f'🥉 {partner_hash}: {amount} рублей')
		else:
			partners_alltime_messages.append(f'🏅 {partner_hash}: {amount} рублей')

	partners_alltime_messages = '\n'.join(partners_alltime_messages)

	# Print Message
	await call.message.edit_text(
		f"""🏆 Топ воркеров по депозитам за последний месяц

{partners_last_month_messages}

🏆 Топ воркеров по депозитам за все время

{partners_alltime_messages}""",
		reply_markup=inline.back_markup('admin_top_workers'),
	)


@admin_router.callback_query(F.data == 'admin_top_workers_by_users')
async def admin_top_workers_by_users_callback(call: CallbackQuery):
	result, status = await APIRequest.post(
		'/partner/find', {'opts': {'approved': True}}
	)

	if status != 200:
		await call.answer(
			f'Ошибка получения списка пользователей: status code={status}; message={result["status"]["message"]}'
		)
		return

	partners = result['partners']

	sorted_partners = sorted(partners, key=lambda x: x['referals_count'], reverse=True)
	sorted_partners = sorted_partners[:10]

	partners_alltime_messages = []

	for index, partner in enumerate(sorted_partners):
		partner_hash = partner['partner_hash']
		count = partner['referals_count']
		if index == 0:
			partners_alltime_messages.append(
				f'🥇 {partner_hash}: {count} пользователей'
			)
		elif index == 1:
			partners_alltime_messages.append(
				f'🥈 {partner_hash}: {count} пользователей'
			)
		elif index == 3:
			partners_alltime_messages.append(
				f'🥉 {partner_hash}: {count} пользователей'
			)
		else:
			partners_alltime_messages.append(
				f'🏅 {partner_hash}: {count} пользователей'
			)

	result, code = await APIRequest.get('/base/stats')

	stats = result['data']

	last_month_users = [
		reg['partner_hash']
		for reg in stats['last_month']['registr']
		if reg['partner_hash'] != 'self'
	]
	last_week_users = [
		reg['partner_hash']
		for reg in stats['last_week']['registr']
		if reg['partner_hash'] != 'self'
	]
	yesterday_users = [
		reg['partner_hash']
		for reg in stats['yesterday']['registr']
		if reg['partner_hash'] != 'self'
	]
	today_users = [
		reg['partner_hash']
		for reg in stats['today']['registr']
		if reg['partner_hash'] != 'self'
	]

	last_month_users = (
		last_month_users + last_week_users + yesterday_users + today_users
	)
	counter = Counter(last_month_users)
	top_10 = counter.most_common(10)

	partners_last_month_messages = []

	for index, (id_partner, count) in enumerate(top_10):
		partner_hash = id_partner

		if index == 0:
			partners_last_month_messages.append(
				f'🥇 {partner_hash}: {count} пользователей'
			)
		elif index == 1:
			partners_last_month_messages.append(
				f'🥈 {partner_hash}: {count} пользователей'
			)
		elif index == 2:  # Здесь должно быть 2, вместо 3
			partners_last_month_messages.append(
				f'🥉 {partner_hash}: {count} пользователей'
			)
		else:
			partners_last_month_messages.append(
				f'🏅 {partner_hash}: {count} пользователей'
			)

	partners_last_month_messages = '\n'.join(partners_last_month_messages)
	partners_alltime_messages = '\n'.join(partners_alltime_messages)

	await call.message.edit_text(
		f"""🏆 Топ воркеров по приглашенным пользователям за последний месяц

{partners_last_month_messages}

🏆 Топ воркеров по приглашенным пользователям за все время

{partners_alltime_messages}""",
		reply_markup=inline.back_markup('admin_top_workers'),
	)


@admin_router.callback_query(F.data == 'admin_top_workers_change')
async def admin_top_workers_change_callback(call: CallbackQuery):
	data = sinwin_data['topworkers']

	if data['first_place']['type'] is not None:
		firstplace = (
			f'Следующий статус до {data["first_place"]["status"]}'
			if data['first_place']['type'] == 'uplevel'
			else f'Премия {data["first_place"]["amount"]} рублей'
		)
	else:
		firstplace = 'Ничего'

	if data['second_place']['type'] is not None:
		secondplace = (
			f'Следующий статус до {data["second_place"]["status"]}'
			if data['second_place']['type'] == 'uplevel'
			else f'Премия {data["second_place"]["amount"]} рублей'
		)
	else:
		secondplace = 'Ничего'

	if data['third_place']['type'] is not None:
		thirdplace = (
			f'Следующий статус до {data["third_place"]["status"]}'
			if data['third_place']['type'] == 'uplevel'
			else f'Премия {data["third_place"]["amount"]} рублей'
		)
	else:
		thirdplace = 'Ничего'

	message = f"""Статистика обнуляется 1 числа каждого месяца

Сейчас
Первое место - {firstplace}
Второе место - {secondplace}
Третье место - {thirdplace}

За какое место поменять бонус?"""

	await call.message.edit_text(
		message, reply_markup=inline.get_change_bonus_for_place()
	)


@admin_router.callback_query(F.data.startswith('admin_place_set_type_to_'))
async def admin_place_set_type_to_place_callback(call: CallbackQuery):
	calldata = call.data.split('.')
	place = calldata[-1]
	place_type = calldata[0].replace('admin_place_set_type_to_', '')

	data_place = {}

	if place_type.isdigit():
		data_place['type'] = 'prize'
		data_place['amount'] = int(place_type)
	else:
		data_place['type'] = 'uplevel'
		data_place['status'] = place_type

	sinwin_data['topworkers'][place] = data_place
	data = sinwin_data['topworkers']

	if data['first_place']['type'] is not None:
		firstplace = (
			f'Следующий статус до {data["first_place"]["status"]}'
			if data['first_place']['type'] == 'uplevel'
			else f'Премия {data["first_place"]["amount"]} рублей'
		)
	else:
		firstplace = 'Ничего'

	if data['second_place']['type'] is not None:
		secondplace = (
			f'Следующий статус до {data["second_place"]["status"]}'
			if data['second_place']['type'] == 'uplevel'
			else f'Премия {data["second_place"]["amount"]} рублей'
		)
	else:
		secondplace = 'Ничего'

	if data['third_place']['type'] is not None:
		thirdplace = (
			f'Следующий статус до {data["third_place"]["status"]}'
			if data['third_place']['type'] == 'uplevel'
			else f'Премия {data["third_place"]["amount"]} рублей'
		)
	else:
		thirdplace = 'Ничего'

	save_data()

	message = f"""Статистика обнуляется 1 числа каждого месяца

Сейчас
Первое место - {firstplace}
Второе место - {secondplace}
Третье место - {thirdplace}

За какое место поменять бонус?"""

	await call.message.edit_text(
		message, reply_markup=inline.get_change_bonus_for_place()
	)


@admin_router.callback_query(F.data.startswith('change_bonus_for_place_'))
async def change_bonus_for_place_num_callback(call: CallbackQuery):
	place = call.data.replace('change_bonus_for_place_', '')

	if place == '1':
		place = 'first_place'
	elif place == '2':
		place = 'second_place'
	elif place == '3':
		place = 'third_place'

	# sinwin_data['topworkers'] = {
	# 	'first_place': {'type': None, 'amount': 0},
	# 	'second_place': {'type': None, 'amount': 0},
	# 	'third_place': {'type': None, 'amount': 0},
	# }

	# save_data()

	data = sinwin_data['topworkers']

	if data['first_place']['type'] is not None:
		firstplace = (
			f'Следующий статус до {data["first_place"]["status"]}'
			if data['first_place']['type'] == 'uplevel'
			else f'Премия {data["first_place"]["amount"]} рублей'
		)
	else:
		firstplace = 'Ничего'

	if data['second_place']['type'] is not None:
		secondplace = (
			f'Следующий статус до {data["second_place"]["status"]}'
			if data['second_place']['type'] == 'uplevel'
			else f'Премия {data["second_place"]["amount"]} рублей'
		)
	else:
		secondplace = 'Ничего'

	if data['third_place']['type'] is not None:
		thirdplace = (
			f'Следующий статус до {data["third_place"]["status"]}'
			if data['third_place']['type'] == 'uplevel'
			else f'Премия {data["third_place"]["amount"]} рублей'
		)
	else:
		thirdplace = 'Ничего'

	await call.message.edit_text(
		f"""Выберете что хотите давать за {humanize_place(place)} место (сейчас: {firstplace})

Второе место - {secondplace}
Третье место - {thirdplace}""",
		reply_markup=inline.get_change_places_bonus(place),
	)


@admin_router.callback_query(F.data == 'disable_all_bonuses_for_places')
async def disable_all_bonuses_for_places_callback(call: CallbackQuery):
	data = sinwin_data['topworkers'] = {
		'first_place': {'type': None, 'amount': 0},
		'second_place': {'type': None, 'amount': 0},
		'third_place': {'type': None, 'amount': 0},
	}

	save_data()

	data = sinwin_data['topworkers']

	if data['first_place']['type'] is not None:
		firstplace = (
			f'Следующий статус до {data["first_place"]["status"]}'
			if data['first_place']['type'] == 'uplevel'
			else f'Премия {data["first_place"]["amount"]} рублей'
		)
	else:
		firstplace = 'Ничего'

	if data['second_place']['type'] is not None:
		secondplace = (
			f'Следующий статус до {data["second_place"]["status"]}'
			if data['second_place']['type'] == 'uplevel'
			else f'Премия {data["second_place"]["amount"]} рублей'
		)
	else:
		secondplace = 'Ничего'

	if data['third_place']['type'] is not None:
		thirdplace = (
			f'Следующий статус до {data["third_place"]["status"]}'
			if data['third_place']['type'] == 'uplevel'
			else f'Премия {data["third_place"]["amount"]} рублей'
		)
	else:
		thirdplace = 'Ничего'

	message = f"""Статистика обнуляется 1 числа каждого месяца

Сейчас
Первое место - {firstplace}
Второе место - {secondplace}
Третье место - {thirdplace}

За какое место поменять бонус?"""

	await call.message.edit_text(
		message, reply_markup=inline.get_change_bonus_for_place()
	)
