from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import orjson as json
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hermes_langlib.locales import LocaleManager
from hermes_langlib.storage import load_config as i18n_load_config

from app.config import get_config, load_config
from app.database._debug import UsersDebug

DEFAULT_DATA = {
	'topworkers': {
		'first_place': {
			'type': 'uplevel',
			'status': 'профессионал',
		},
		'second_place': {
			'type': 'prize',
			'amount': 30_000.0,
		},
		'third_place': {
			'type': 'prize',
			'amount': 10_000.0,
		},
	},
	'promocodes': {
		'MANYMONEY_DEV': {
			'type': 'prize',
			'amount': 1_000.0,
			'date': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
			'activates': 10000,
			'activations_left': 10000,
		}
	},
}


def humanize_promocode_type(promocode_type: str):
	if promocode_type == 'prize':
		return 'Рубли'
	elif promocode_type == 'status':
		return 'Статус'
	elif promocode_type == 'uplevel':
		return 'Переход на следующий статус'
	elif promocode_type == 'percent':
		return 'Проценты'

	return 'Неизвестно'


def humanize_place(place: str):
	if place == 'first_place':
		return 'первое место'
	elif place == 'second_place':
		return 'второе место'
	elif place == 'third_place':
		return 'третье место'
	else:
		return 'другое место'


def validate_data(data: dict):
	count = 0
	topworkers = data.get('topworkers', {})

	if topworkers.get('first_place', False):
		count += 1
	if topworkers.get('second_place', False):
		count += 1
	if topworkers.get('third_place', False):
		count += 1

	promocodes = data.get('promocodes', None)

	if promocodes is not None:
		count += 1

	if count != 4:
		raise Exception(
			'Fatal Error: Invalid data in data.json file. Please, check and fix it.'
		)


def load_data():
	if not Path('data.json').exists():
		data = DEFAULT_DATA
		with open('data.json', 'wb') as file:
			file.write(json.dumps(data))
	else:
		try:
			with open('data.json', 'rb') as file:
				data = json.loads(file.read())
		except Exception:
			data = DEFAULT_DATA

	validate_data(data)

	return data


sinwin_data = load_data()


def save_data():
	global sinwin_data

	with open('data.json', 'wb') as file:
		file.write(json.dumps(sinwin_data))


ACHIEVEMENTS = {
	'users': [
		100,
		250,
		500,
		750,
		1000,
		2500,
		5000,
		10000,
		15000,
		20000,
		25000,
		30000,
		40000,
		50000,
		75000,
		100000,
		150000,
		200000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		5000000,
	],
	'deposits': [
		10000,
		25000,
		50000,
		100000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		3000000,
		4000000,
		5000000,
		6000000,
		7000000,
		8000000,
		9000000,
		10000000,
		12500000,
		15000000,
		20000000,
		25000000,
		50000000,
		100000000,
		150000000,
		200000000,
		250000000,
		500000000,
		750000000,
		1000000000,
		1500000000,
		2000000000,
		2500000000,
		5000000000,
	],
	'income': [
		5000,
		10000,
		25000,
		50000,
		100000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		3000000,
		4000000,
		5000000,
		6000000,
		7000000,
		8000000,
		9000000,
		10000000,
		12500000,
		15000000,
		20000000,
		25000000,
		50000000,
		100000000,
		150000000,
		200000000,
		250000000,
		500000000,
		750000000,
		1000000000,
		1500000000,
		2000000000,
		2500000000,
		5000000000,
	],
	'first_deposits': [
		25,
		50,
		75,
		100,
		150,
		200,
		250,
		500,
		750,
		1000,
		2500,
		5000,
		10000,
		25000,
		50000,
		100000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		3000000,
		4000000,
		5000000,
		6000000,
		7000000,
		8000000,
		9000000,
		10000000,
		12500000,
		15000000,
		20000000,
		25000000,
		50000000,
		100000000,
		150000000,
		200000000,
		250000000,
		500000000,
		750000000,
		1000000000,
		1500000000,
		2000000000,
		2500000000,
		5000000000,
	],
	'referrals': [
		1,
		2,
		3,
		5,
		7,
		10,
		15,
		20,
		25,
		35,
		50,
		75,
		100,
		150,
		200,
		250,
		500,
		750,
		1000,
		1500,
		2000,
		2500,
		5000,
		10000,
		25000,
	],
	'api': [
		1000,
		5000,
		10000,
		25000,
		50000,
		100000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		3000000,
		4000000,
		5000000,
		6000000,
		7000000,
		8000000,
		9000000,
		10000000,
		12500000,
		15000000,
		20000000,
		25000000,
		50000000,
		100000000,
		150000000,
		200000000,
		250000000,
		500000000,
		750000000,
		1000000000,
		1500000000,
		2000000000,
		2500000000,
		5000000000,
	],
	'signals': [
		100,
		250,
		500,
		750,
		1000,
		2500,
		5000,
		10000,
		25000,
		50000,
		100000,
		250000,
		500000,
		750000,
		1000000,
		1500000,
		2000000,
		2500000,
		3000000,
		4000000,
		5000000,
		6000000,
		7000000,
		8000000,
		9000000,
		10000000,
		12500000,
		15000000,
		20000000,
		25000000,
		50000000,
		100000000,
		150000000,
		200000000,
		250000000,
		500000000,
		750000000,
		1000000000,
		1500000000,
		2000000000,
		2500000000,
		5000000000,
	],
}


def convert_to_human(string: str) -> str:
	data = '{:,}'.format(string).replace(',', ' ')

	return data


scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

config = load_config(get_config('config.ini'))
i18n_config = i18n_load_config('i18n.toml')

locale_manager = LocaleManager(i18n_config, locales=['default.json'])

users_db = UsersDebug()

bot = Bot(token=config.secrets.TOKEN)

dp = Dispatcher(storage=MemoryStorage())

loaded_achievements: Dict[int, Dict[Any, Any]] = {}
user_achievements: Dict[int, Any] = {}
