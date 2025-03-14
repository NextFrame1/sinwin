from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.loader import config


def create_start_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='✍️ Оставить заявку', callback_data='submit_reg_request'
		)
	)  # accept_submitted_reg_request_callback

	builder.adjust(1)

	return builder.as_markup()


def create_main_menu_markup(userid):
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='💻️ Профиль', callback_data='profile'))
	builder.row(InlineKeyboardButton(text='📈 Статистика', callback_data='statistics'))
	builder.row(InlineKeyboardButton(text='👉️ Work', callback_data='work'))
	builder.row(
		InlineKeyboardButton(text='💎 Достижения', callback_data='achievements')
	)
	builder.row(
		InlineKeyboardButton(
			text='📝 Мануал',
			url='https://telegra.ph/manual-kak-nachat-rabotu-i-uspeshno-prodvigat-kreativy-08-19',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='🤔 В чем суть работы?',
			url='https://telegra.ph/V-chem-sut-raboty-08-19',
		)
	)
	builder.row(
		InlineKeyboardButton(text='📊 Топ воркеров', callback_data='top_workers')
	)
	builder.row(InlineKeyboardButton(text='🙎‍♂️ Рефка', callback_data='referal'))
	builder.row(InlineKeyboardButton(text='🔮 Статус', callback_data='status'))
	builder.row(InlineKeyboardButton(text='🔥 О нас', callback_data='about_us'))

	if userid in config.secrets.ADMINS_IDS:
		builder.row(InlineKeyboardButton(text='⭐️ Админка', callback_data='adminpanel'))

	builder.adjust(2)

	return builder.as_markup()


def create_adminpanel_markup():
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(
			text='Подключить Суб Партнерство', callback_data='admin_connect_subpartner'
		)
	)
	builder.row(
		InlineKeyboardButton(text='Топ воркеров', callback_data='admin_top_workers')
	)
	builder.row(
		InlineKeyboardButton(text='Промокоды', callback_data='admin_promocodes')
	)
	builder.row(
		InlineKeyboardButton(text='Статистика', callback_data='admin_statistics')
	)
	builder.row(
		InlineKeyboardButton(
			text='Информация по человеку', callback_data='admin_info_about_partner'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Все партнеры Sin Win', callback_data='admin_all_partners_1win'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Общие настройки', callback_data='admin_main_settings'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='Изменить меню бота', callback_data='admin_change_bot_menu'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(1)

	return builder.as_markup()


def create_status_markup():
	builder = InlineKeyboardBuilder()
	builder.row(InlineKeyboardButton(text='📊 Уровни', callback_data='status_levels'))
	builder.row(
		InlineKeyboardButton(text='👨‍🦱 Поддержка', url='https://t.me/HelpSinWin')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(2)

	return builder.as_markup()


def create_referals_markup():
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(text='👪️ Мои рефералы', callback_data='my_referals')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(1)

	return builder.as_markup()


def create_about_us_markup():
	keyboard = [
		[
			InlineKeyboardButton(text='👨‍🦱 Поддержка', url='https://t.me/HelpSinWin'),
			InlineKeyboardButton(text='💎 Канал', url='https://t.me/+W8_28FXJWXIxZTgy'),
		],
		[
			InlineKeyboardButton(
				text='💬 Предложить улучшение', url='https://t.me/HelpSinWin'
			)
		],
		[InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu')],
	]

	return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_record_creo_markup():
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(
			text='📄 Инструкция',
			url='https://telegra.ph/polnoe-rukovodstvo-po-sozdaniyu-kreativnyh-video-s-ispolzo%20vaniem-nashih-botov-08-16',
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='work'))

	builder.adjust(1)

	return builder.as_markup()


def create_achievements_update_markup(alerts: bool):
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(text='🎯 Новые цели', callback_data='achievements')
	)
	builder.row(
		InlineKeyboardButton(text='🏆️ Мои достижения', callback_data='my_achievs')
	)

	builder.adjust(1)

	return builder.as_markup()


def create_achievements_markup(alerts: bool):
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(text='🔄 Обновить', callback_data='reload_achievs')
	)
	builder.row(
		InlineKeyboardButton(text='🏆️ Мои достижения', callback_data='my_achievs')
	)
	if alerts:
		builder.row(
			InlineKeyboardButton(
				text='❌ Выключить уведомления', callback_data='achievements_false'
			)
		)
	else:
		builder.row(
			InlineKeyboardButton(
				text='✅ Включить уведомления', callback_data='achievements_true'
			)
		)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(1)

	return builder.as_markup()


def create_work_markup():
	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(text='🎬️ Запись Крео', callback_data='record_creo')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(1)

	return builder.as_markup()


def create_online_statistics_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(text='Подключиться', url='https://t.me/sinwin_alerts_bot')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='statistics'))

	builder.adjust(1)

	return builder.as_markup()


def create_mines_statistics_menu():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='statistics'))

	builder.adjust(1)

	return builder.as_markup()


def create_statistics_bot_menu(menu: str = 'showmenu'):
	builder = InlineKeyboardBuilder()
	builder.row(InlineKeyboardButton(text='💣️ Mines', callback_data='statistics_mines'))
	builder.row(
		InlineKeyboardButton(text='🚀 Lucky Jet', callback_data='statistics_luckyjet')
	)
	builder.row(
		InlineKeyboardButton(text='🚗 Speed Cash', callback_data='statistics_speedcash')
	)
	builder.row(
		InlineKeyboardButton(text='🎲 Coin Flip', callback_data='statistics_coinflip')
	)
	builder.row(
		InlineKeyboardButton(
			text='Статистика онлайн', callback_data='statistics_online'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=menu))

	builder.adjust(1)

	return builder.as_markup()


def create_profile_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='💳️ Вывод Средств', callback_data='withdraw'))
	builder.row(
		InlineKeyboardButton(
			text='🤖 История выводов', callback_data='withdraws_history'
		)
	)
	builder.row(
		InlineKeyboardButton(text='🧩 Ввести промокод', callback_data='enter_promo')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='showmenu'))

	builder.adjust(1)

	return builder.as_markup()


def create_withdraw_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='💳️ Карта', callback_data='withdraw_card'))
	builder.row(
		InlineKeyboardButton(text='📱 Вывод по номеру', callback_data='withdraw_phone')
	)
	builder.row(
		InlineKeyboardButton(text='🌸 Piastrix', callback_data='withdraw_piastrix')
	)
	builder.row(
		InlineKeyboardButton(text='👾 FK Wallet', callback_data='withdraw_fkwallet')
	)
	builder.row(InlineKeyboardButton(text='👑 Крипта', callback_data='withdraw_crypto'))
	builder.row(InlineKeyboardButton(text='⚙️ Steam', callback_data='withdraw_steam'))
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='profile'))

	builder.adjust(2)

	return builder.as_markup()


def create_crypto_withdraw_markup():
	builder = InlineKeyboardBuilder()

	cryptocurrs = [
		'Bitcoin',
		'Ethereum',
		'Tron',
		'Tether ERC20',
		'Tether TRC20',
		'Tether BEP20',
		'BNB BEP20',
		'Litecoin',
		'Monero',
		'Bitcoin Cash',
		'Dash',
		'Doge',
		'Zcash',
		'Ripple',
		'Stellar',
	]

	for crypto in cryptocurrs:
		builder.row(
			InlineKeyboardButton(
				text=crypto, callback_data=f'crypto_set_withdraw_{crypto}'
			)
		)

	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='withdraw'))

	builder.adjust(3)

	return builder.as_markup()


def admin_change_transaction(transaction_id):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Изменить', callback_data=f'change_transaction_status{transaction_id}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_cancel_reason_markup(transaction_id):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Изменить', callback_data=f'change_transaction_status{transaction_id}'
		)
	)
	builder.row(
		InlineKeyboardButton(text='Не писать', callback_data='empty_cancel_reason')
	)

	builder.adjust(1)

	return builder.as_markup()


def create_admin_transaction_menu(transaction_id, admin_id, method: str = 'card'):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='✅ Подтвердить',
			callback_data=f'badmin_approve_transaction{transaction_id}.{method}',
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='❌ Отклонить',
			callback_data=f'badmin_disapprove_transaction{transaction_id}_{admin_id}.{method}',
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_withdraw_continue_markup(callback: str = 'showmenu', withdraw: str = 'card'):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='✅ Подтвердить', callback_data=f'user_approve_{withdraw}_withdraw'
		)
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=callback))

	builder.adjust(1)

	return builder.as_markup()


def create_status_up_master_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔮 Статус', callback_data='status'))
	builder.row(
		InlineKeyboardButton(text='👨‍🦱 Поддержка', url='https://t.me/HelpSinWin')
	)
	builder.row(InlineKeyboardButton(text='🏠 Главное меню', callback_data='profile'))

	builder.adjust(1)

	return builder.as_markup()


def change_status_moving(userid):
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text='Изменить', callback_data=f'change_status_moving_{userid}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_confirm_status_change(user_id, withwrite=True):
	# tg://user?id=
	builder = InlineKeyboardBuilder()

	if withwrite:
		builder.row(
			InlineKeyboardButton(text='💬 Написать', url=f'tg://user?id={user_id}')
		)

	builder.row(
		InlineKeyboardButton(
			text='✅ Подтвердить', callback_data=f'confirm_status_change_{user_id}'
		)
	)
	builder.row(
		InlineKeyboardButton(
			text='❌ Отклонить', callback_data=f'reject_status_change_{user_id}'
		)
	)

	builder.adjust(1)

	return builder.as_markup()


def create_status_up_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔮 Статус', callback_data='status'))

	builder.row(InlineKeyboardButton(text='🏠 Главное меню', callback_data='profile'))

	builder.adjust(1)

	return builder.as_markup()


def create_support_transac_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(text='👨‍🦱 Поддержка', url='https://t.me/HelpSinWin')
	)
	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='profile'))

	builder.adjust(1)

	return builder.as_markup()


def create_achiev_get_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(text='🎯 Новые цели', callback_data='achievements')
	)
	builder.row(
		InlineKeyboardButton(text='🏆 Мои достижения', callback_data='my_achievs')
	)

	builder.adjust(1)

	return builder.as_markup()


def create_back_markup(callback: str = 'showmenu'):
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=callback))

	builder.adjust(1)

	return builder.as_markup()
