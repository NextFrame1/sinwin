from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_start_markup():
	builder = InlineKeyboardBuilder()

	builder.row(
		InlineKeyboardButton(
			text="✍️ Оставить заявку", callback_data="submit_reg_request"
		)
	)  # accept_submitted_reg_request_callback

	builder.adjust(1)

	return builder.as_markup()


def create_choice_user_experience_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text="Да", callback_data="1set_experience_time"))
	builder.row(
		InlineKeyboardButton(text="Нет", callback_data="1set_experience_time_no")
	)
	builder.row(
		InlineKeyboardButton(text="Немного", callback_data="1set_experience_time_none")
	)

	builder.adjust(2)

	return builder.as_markup()


def create_choice_user_experience_time_markup():
	inline_kb_list = [
		[
			InlineKeyboardButton(
				text="1 месяц", callback_data="set_experience_times_1month"
			),
			InlineKeyboardButton(
				text="2 месяца", callback_data="set_experience_times_2month"
			),
		],
		[
			InlineKeyboardButton(
				text="3 месяца", callback_data="set_experience_times_3month"
			),
			InlineKeyboardButton(
				text="Полгода", callback_data="set_experience_times_halfyear"
			),
		],
		[
			InlineKeyboardButton(
				text="Год", callback_data="set_experience_times_1year"
			),
			InlineKeyboardButton(
				text="2 года", callback_data="set_experience_times_2year"
			),
			InlineKeyboardButton(
				text="Больше", callback_data="set_experience_times_more"
			),
		],
	]

	return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def create_referal_connection_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text="Да", callback_data="referal_status_not"))
	builder.row(InlineKeyboardButton(text="Нет", callback_data="referal_status_have"))

	builder.adjust(2)

	return builder.as_markup()


def create_final_req():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text="✈️ Отправить", callback_data="send_request"))
	builder.row(
		InlineKeyboardButton(
			text="↪️ Поменять ответы", callback_data="submit_reg_request"
		)
	)

	builder.adjust(2)

	return builder.as_markup()


def get_show_menu_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text="💻️ Показать меню", callback_data="showmenu"))

	builder.adjust(1)

	return builder.as_markup()


def create_ubt_markup():
	builder = InlineKeyboardBuilder()

	builder.row(InlineKeyboardButton(text="Да", callback_data="use_ubt_yes"))
	builder.row(InlineKeyboardButton(text="Нет", callback_data="use_ubt_no"))
	builder.row(InlineKeyboardButton(text="Немного", callback_data="use_ubt_none"))

	builder.adjust(2)

	return builder.as_markup()
