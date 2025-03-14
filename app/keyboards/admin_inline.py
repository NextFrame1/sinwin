from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_admin_promocode_markup():
	keyboard = [
		[
			InlineKeyboardButton(
				text='Созданные промокоды', callback_data='show_created_promocodes'
			),
		],
		[InlineKeyboardButton(text='🔙 Назад', callback_data='admin_promocodes')],
	]

	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_back_markup(callback: str = 'showmenu'):
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=callback))

	builder.adjust(1)

	return builder.as_markup()


def create_deleted_markup(promocode_name):
	keyboard = [
		[
			InlineKeyboardButton(
				text='❌ Восстановить',
				callback_data=f'reborn_promocode_{promocode_name}',
			),
		],
		[InlineKeyboardButton(text='🔙 Назад', callback_data='admin_promocodes')],
	]

	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def delete_promocode_markup(promocode_name):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Удалить', callback_data=f'delete_promocode_{promocode_name}'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_promocodes'))

	builder.adjust(1)

	return builder.as_markup()


def create_approve_revshare_change_markup(new_revshare: float):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Ок', callback_data=f'revshare_approve_revshare_change_{new_revshare}'
		),
	)
	builder.row(
		InlineKeyboardButton(text='Отмена', callback_data='change_revshare_percent')
	)

	builder.adjust(1)

	return builder.as_markup()


def create_approve_balance_change_markup(new_balance: float):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Ок', callback_data=f'balance_approve_balance_change_{new_balance}'
		),
	)
	builder.row(
		InlineKeyboardButton(text='Отмена', callback_data='change_partner_balance')
	)

	builder.adjust(1)

	return builder.as_markup()


def admin_main_settings_menu():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Изменить баланс партнерки', callback_data='change_partner_balance'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='Поменять процент RevShare', callback_data='change_revshare_percent'
		),
	)
	builder.row(
		InlineKeyboardButton(text='Поменять ссылки', callback_data='change_bot_links')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


def create_bot_link_menu(bot_name: str, url: str):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(text=bot_name, url=url),
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='change_bot_links'))

	builder.adjust(1)

	return builder.as_markup()


def create_percent_input_markup(partner_hash: str):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='5',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.5',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='10',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.10',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='15',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.15',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='20',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.20',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='25',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.25',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='30',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.30',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='35',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.35',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='40',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.40',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='45',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.45',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='50',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.50',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='55',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.55',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='60',
			callback_data=f'admin_change_percent_income_to_percent_{partner_hash}.60',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		)
	)

	builder.adjust(6)

	return builder.as_markup()


def get_markup_back_and_cancel_status(partner_hash):
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def get_markup_back_and_cancel_perc_inc(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Отмена',
			callback_data=f'admin_set_percent_income_to_partner_{partner_hash}',
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_admin_statistics_panel_menu():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='💣 Mines', callback_data='admin_statistics_panel_mines'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🚀 Lucky Jet', callback_data='admin_statistics_panel_luckyjet'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🚗 Speed Cash', callback_data='admin_statistics_panel_speedcash'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🎲 Coin Flip', callback_data='admin_statistics_panel_coinflip'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='За другой период',
			callback_data='admin_statistics_panel_choose_period',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Статистика партнеров', callback_data='admin_statistics_panel_partners'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


def create_admin_statistics_panel_menu_game():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='За другой период',
			callback_data='admin_statistics_panel_choose_period.Mines',
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_statistics'))

	builder.adjust(1)

	return builder.as_markup()


def create_yes_no_markup_for_income_percent(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Нет', callback_data='admin_percent_income_disapprove'
		),
	)
	builder.row(
		InlineKeyboardButton(text='Да', callback_data='admin_percent_income_approve'),
	)
	builder.row(
		InlineKeyboardButton(
			text='Отмена',
			callback_data=f'admin_set_percent_income_to_partner_{partner_hash}',
		),
	)

	builder.adjust(2)

	return builder.as_markup()


def create_admin_info_by_user_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Все партнеры', callback_data='admin_all_partners_1win'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


def create_change_status_markup(partner_hash: str):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Новичок 35%', callback_data=f'admin_set_status_{partner_hash}.новичок'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Специалист 40%',
			callback_data=f'admin_set_status_{partner_hash}.специалист',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Профессионал 45%',
			callback_data=f'admin_set_status_{partner_hash}.профессионал',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Мастер 50%', callback_data=f'admin_set_status_{partner_hash}.мастер'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Легенда Суб Партнерство',
			callback_data=f'admin_set_status_{partner_hash}.легенда',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_partner_interactions_markup(partner_hash: str):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='💣 Mines',
			callback_data=f'admin_get_info_by_partner_mines_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🚀 Lucky Jet',
			callback_data=f'admin_get_info_by_partner_luckyjet_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🚗 Speed Cash',
			callback_data=f'admin_get_info_by_partner_speedcash_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🎲 Coin Flip',
			callback_data=f'admin_get_info_by_partner_coinflip_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Изменить процент дохода',
			callback_data=f'admin_set_percent_income_to_partner_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Изменить статус', callback_data=f'admin_change_status_{partner_hash}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Изменить баланс', callback_data=f'admin_change_balance_{partner_hash}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Дать возможность вывода',
			callback_data=f'admin_give_withdraw_{partner_hash}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Заблокировать', callback_data=f'admin_block_user_{partner_hash}'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


def create_withdraw_period_markup(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='30 минут', callback_data=f'set_withdraw_period_{partner_hash}.30m'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='1 час', callback_data=f'set_withdraw_period_{partner_hash}.1h'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='2 часа', callback_data=f'set_withdraw_period_{partner_hash}.2h'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='3 часа', callback_data=f'set_withdraw_period_{partner_hash}.3h'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='6 часов', callback_data=f'set_withdraw_period_{partner_hash}.6h'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='12 часов', callback_data=f'set_withdraw_period_{partner_hash}.12h'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='1 сутки', callback_data=f'set_withdraw_period_{partner_hash}.1d'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='2 дня', callback_data=f'set_withdraw_period_{partner_hash}.2d'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='3 дня', callback_data=f'set_withdraw_period_{partner_hash}.3d'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_profile_partner_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='💳️ Вывод Средств', callback_data='withdraw'))

	builder.adjust(1)

	return builder.as_markup()


def create_admin_give_withdraw_callback_back(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Отмена', callback_data=f'admin_give_withdraw_{partner_hash}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_block_user_markup(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Заблокировать', callback_data=f'admin_totally_block_{partner_hash}'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_unblock_user_markup(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Разблокировать', callback_data=f'admin_totally_unblock_{partner_hash}'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_admin_balance_change_markup(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Поставить на паузу',
			callback_data=f'admin_freeze_partner_{partner_hash}',
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_back_admin_info_markup(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_ok_or_cancel_balance_markup(partner_hash, new_balance):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Да',
			callback_data=f'admin_totally_change_balance_{partner_hash}.{new_balance}',
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='Отмена', callback_data=f'admin_change_balance_{partner_hash}'
		),
	)

	builder.adjust(2)

	return builder.as_markup()


def create_admin_balance_change_markup_defreeze(partner_hash):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Снять с паузы', callback_data=f'admin_defreeze_partner_{partner_hash}'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🔙 Назад', callback_data=f'admin_info_by_user{partner_hash}'
		),
	)

	builder.adjust(1)

	return builder.as_markup()


def create_bot_links_menu():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='💣 Mines', callback_data='change_links_in_bot_mines'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🚀 Lucky Jet', callback_data='change_links_in_bot_luckyjet'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🚗 Speed Cash', callback_data='change_links_in_bot_speedcash'
		),
	)
	builder.row(
		InlineKeyboardButton(
			text='🎲 Coin Flip', callback_data='change_links_in_bot_coinflip'
		),
	)
	builder.row(
		InlineKeyboardButton(text='🔙 Назад', callback_data='admin_main_settings')
	)

	builder.adjust(1)

	return builder.as_markup()


def create_admin_promocodes_markup():
	keyboard = [
		[
			InlineKeyboardButton(text='1', callback_data='create_promocode_rubles'),
			InlineKeyboardButton(text='2', callback_data='create_promocode_status'),
			InlineKeyboardButton(text='3', callback_data='create_promocode_percent'),
		],
		[
			InlineKeyboardButton(
				text='Созданные промокоды', callback_data='show_created_promocodes'
			),
		],
		[InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel')],
	]

	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_send_partners_excel():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(text='Прислать отчет', callback_data='send_partners_excel')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='adminpanel'))

	builder.adjust(1)

	return builder.as_markup()


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
			callback_data=f'admin_place_set_type_to_специалист.{place}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Следующий статус до Профессионал 45 %',
			callback_data=f'admin_place_set_type_to_профессионал.{place}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Следующий статус до Мастер 50 %',
			callback_data=f'admin_place_set_type_to_мастер.{place}',
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
