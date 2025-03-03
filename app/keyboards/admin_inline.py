from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_markup(callback: str = 'adminpanel'):
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=callback))

	builder.adjust(1)

	return builder.as_markup()


def get_admin_top_workers_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Топ по Приглашениям', callback_data='admin_top_workers_by_users'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Топ по Депозитам', callback_data='admin_top_workers_by_deps'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Изменить условия вознаграждения',
			callback_data='admin_top_workers_change',
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


def get_change_bonus_for_place():
	keyboard = [
		[
			InlineKeyboardButton(text='1', callback_data='change_bonus_for_place_1'),
			InlineKeyboardButton(text='2', callback_data='change_bonus_for_place_2'),
			InlineKeyboardButton(text='3', callback_data='change_bonus_for_place_3'),
		],
		[
			InlineKeyboardButton(
				text='Отключить все бонусы',
				callback_data='disable_all_bonuses_for_places',
			)
		],
		[InlineKeyboardButton(text='🔙 Назад', callback_data='admin_top_workers')],
	]

	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_change_places_bonus(place: str):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Следующий статус до Специалист 40 %',
			callback_data=f'admin_place_set_type_to_specialist.{place}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Следующий статус до Профессионал 45 %',
			callback_data=f'admin_place_set_type_to_professional.{place}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Следующий статус до Мастер 50 %',
			callback_data=f'admin_place_set_type_to_master.{place}',
		)
	)

	builder.row(
		InlineKeyboardButton(
			text='50 000 рублей', callback_data=f'admin_place_set_type_to_50000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='45 000 рублей', callback_data=f'admin_place_set_type_to_45000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='40 000 рублей', callback_data=f'admin_place_set_type_to_40000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='35 000 рублей', callback_data=f'admin_place_set_type_to_35000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='30 000 рублей', callback_data=f'admin_place_set_type_to_30000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='25 000 рублей', callback_data=f'admin_place_set_type_to_25000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='20 000 рублей', callback_data=f'admin_place_set_type_to_20000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='15 000 рублей', callback_data=f'admin_place_set_type_to_15000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='10 000 рублей', callback_data=f'admin_place_set_type_to_10000.{place}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='5 000 рублей', callback_data=f'admin_place_set_type_to_5000.{place}'
		)
	)

	builder.row(
		InlineKeyboardButton(text='🔙 Назад', callback_data='admin_top_workers')
	)

	builder.adjust(1)

	return builder.as_markup()
