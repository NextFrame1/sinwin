import random
import string
from collections import Counter
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import app.keyboards.admin_inline as inline
from app.api import APIRequest
from app.loader import humanize_place, humanize_promocode_type, save_data, sinwin_data

admin_router = Router()

deleted_promocodes = {}


def generate_random_promocode() -> str:
	length = 16
	characters = string.ascii_letters + string.digits  # Содержит буквы и цифры
	promocode = ''.join(random.choice(characters) for _ in range(length))

	while promocode in sinwin_data['promocodes']:
		promocode = ''.join(random.choice(characters) for _ in range(length))

	return promocode


class CreateRublesPromocodeGroup(StatesGroup):
	promocode_name = State()


class CreateStatusPromocodeGroup(StatesGroup):
	promocode_name = State()


class CreatePercentPromocodeGroup(StatesGroup):
	promocode_name = State()


################################################################################
################################### Промокоды ##################################
################################################################################


@admin_router.callback_query(F.data == 'admin_promocodes')
async def admin_promocodes_callback(call: CallbackQuery):
	await call.answer.edit_text(
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
	elif status == 7:
		return 'специалист'
	elif status == 8:
		return 'профессионал'


@admin_router.message(F.text, CreateStatusPromocodeGroup.promocode_name)
async def create_promocode_status_by_name(message: Message, state: FSMContext):
	await state.update_data(promocode_name=message.text)
	data = message.text.split(' ')

	if len(data) < 3:
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if data[0] in sinwin_data['promocodes']:
		await message.answer(
			'❌Такой промокод уже существует',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if not data[1].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return
	else:
		if int(data[1]) > 8:
			await message.answer(
				'❌Введено в неправильном формате',
				reply_markup=inline.create_back_markup('admin_promocodes'),
			)
			return

	if not data[2].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if data[0] == 'Random':
		name = generate_random_promocode()
	else:
		name = data[0]

	status = get_status_by_digit(data[1])

	date = datetime.now()
	promocode = {
		'type': 'status',
		'date': date,
		'activates': data[2],
		'activated_count': data[2],
	}

	status_type = 'uplevel' if data[1] not in ['6', '7', '8'] else 'status'

	promocode[status_type] = status

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
		return

	if data[0] in sinwin_data['promocodes']:
		await message.answer(
			'❌Такой промокод уже существует',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if not data[1].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if not data[2].isdigit():
		await message.answer(
			'❌Введено в неправильном формате',
			reply_markup=inline.create_back_markup('admin_promocodes'),
		)
		return

	if data[0] == 'Random':
		name = generate_random_promocode()
	else:
		name = data[0]

	date = datetime.now()
	promocode = {
		'type': 'prize',
		'amount': float(data[1]),
		'date': date,
		'activates': data[2],
		'activated_count': data[2],
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


@admin_router.callback_query(F.data.startswith('delete_promocode_'))
async def delete_promocode_by_name(call: CallbackQuery):
	promocode_name = call.data.split('_')[1]

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

	await call.message.answer(
		f"""
❌ Промокод УДАЛЕН
Промокод: <code>{promocode_name}</code>
Промокод на: {humanize_promocode_type(promocode['type'])}
""",
		reply_markup=inline.create_deleted_markup(),
	)


@admin_router.callback_query(F.data == 'show_created_promocodes')
async def show_created_promocodes_callback(call: CallbackQuery):
	promocodes = sinwin_data['promocodes']

	for promocode_name, promocode in promocodes.items():
		await call.message.answer(
			f"""
✅Промокод создан: {promocode['date'].strftime('%d.%m.%Y %H:%M:%S')}

Промокод: <code>{promocode_name}</code>
Количество активаций: {promocode['activates']}
Осталось активации: {promocode['activations_left']}
Промокод на: {humanize_promocode_type(promocode['type'])}	
""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.delete_promocode_markup(promocode_name),
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


@admin_router.callback_query(F.data == 'admin_top_workers_by_deps')
async def admin_top_workers_by_deps_callback(call: CallbackQuery):
	result, code = await APIRequest.get('/base/stats?exclude=1')

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

	alltime_deps = (
		deps_last_month + others_deps + firstdeps_last_month + others_firstdeps
	)
	last_month_deps = deps_last_month + firstdeps_last_month

	partners_last_month = {}
	partners_alltime = {}

	# Last Month
	for partner in last_month_deps:
		partner_hash = partner['partner_hash']

		partners_last_month[partner_hash] = partner['x']

	# All time
	for partner in alltime_deps:
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

	sorted_partners = sorted(partners, key=lambda x: x['referrals_count'], reverse=True)
	sorted_partners = sorted_partners[:10]

	partners_alltime_messages = []

	for index, partner in enumerate(sorted_partners):
		partner_hash = partner['partner_hash']
		count = partner['referrals_count']
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

	result, code = await APIRequest.get('/base/stats?exclude=1')

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

	for id_partner, count in top_10:
		partner_hash = id_partner

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
