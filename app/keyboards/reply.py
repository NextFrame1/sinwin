from aiogram.utils.keyboard import ReplyKeyboardBuilder


def create_main_rk():
	"""
	Gets the main rkb.

	:returns:	The main rkb.
	:rtype:		keyboard as markup
	"""
	builder = ReplyKeyboardBuilder()

	buttons = ["Создать пост", "Контент-план", "Все посты", "Каналы"]

	for button in buttons:
		builder.button(text=button)

	builder.adjust(4, 4)
	return builder.as_markup(resize_keyboard=True)


def create_get_contact_markup():
	builder = ReplyKeyboardBuilder()

	builder.button(text="Поделиться номером", request_contact=True)

	return builder.as_markup(resize_keyboard=True)
