import re

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ContentType, Message, ReplyKeyboardRemove
from loguru import logger

import app.keyboards.inline as inline
import app.keyboards.menu_inline as inlinem
import app.keyboards.reply as reply
from app.api import APIRequest
from app.loader import config, bot
from app.database.redis import set_cache
from app.database.test import users
from datetime import datetime

register_router = Router()

forms = {}


class RegUserGroup(StatesGroup):
	name = State()
	experience_status = State()
	experience_time = State()
	referal_status = State()
	ubt_is = State()
	ubt_status = State()
	city = State()
	you_source = State()
	about_you = State()
	source_traffic = State()
	number_phone = State()


def validate_name(name: str) -> bool:
	"""
	Validate name by regular expression

	:param		name:  The name
	:type		name:  str

	:returns:	validation status
	:rtype:		bool
	"""
	pattern = r"^[A-za-zА-Яа-яЁё\s]+\d{1,3}$"

	if re.match(pattern, name):
		return True
	else:
		return False


@register_router.message(Command("start"))
async def cmd_start(message: Message):
	"""
	Command /start

	:param		message:  The message
	:type		message:  Message
	"""
	partners = await APIRequest.post("/partner/find", {"opts": {"tg_id": message.from_user.id}})
	partner = None if len(partners[0]['partners']) < 1 else partners[0]['partners'][-1]
	users[message.from_user.id] = {"final": False, "count": 0}

	print(partner)

	if users.get(message.from_user.id) is not None or partner is not None or message.from_user.id in config.secrets.ADMINS_IDS:
		if users.get(message.from_user.id, {}).get("final", False) and partner is not None:
			await message.answer(
				"🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!",
				parse_mode=ParseMode.HTML,
				reply_markup=inlinem.create_main_menu_markup(),
			)
			return

	await message.answer(
		"Вы не зарегистрированы в боте, для продолжения Вам необходимо подать заявку. Это займет менее 5 минут.",
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_start_markup(),
	)


@register_router.callback_query(F.data == "submit_reg_request")
async def accept_submitted_reg_request_callback(call: CallbackQuery, state: FSMContext):
	count = users.get(call.from_user.id, {}).get('count', 1)
	users[call.from_user.id]['count'] = 1 + count

	await call.message.edit_text(
		'Напишите Ваше имя и возраст в формате "Имя Возраст" (пример: Иван 22):'
	)

	await state.set_state(RegUserGroup.name)


@register_router.message(F.text, RegUserGroup.name)
async def capture_user_name(message: Message, state: FSMContext):
	if not validate_name(message.text):
		await message.answer(
			"Введите в требуемом формате: Имя Возраст\nПример: Иван 22"
		)

		await state.set_state(RegUserGroup.name)
	else:
		await state.update_data(name=message.text)

		await message.answer(
			"Есть ли у вас опыт в арбитраже траффика?",
			reply_markup=inline.create_choice_user_experience_markup(),
		)

		await state.set_state(RegUserGroup.experience_status)


@register_router.callback_query(
	F.data.startswith("1set_experience_time"), RegUserGroup.experience_status
)
async def set_experience_status(call: CallbackQuery, state: FSMContext):
	await state.update_data(
		experience_status=(
			"Нет/немного" if call.data.startswith("1set_experience_time_no") else "Да"
		)
	)
	if call.data == "1set_experience_time":
		await call.message.edit_text(
			"Сколько месяцев/лет вы занимаетесь арбитражем трафика?\nЕсли нет вашего варианта, напишите в чат.",
			reply_markup=inline.create_choice_user_experience_time_markup(),
		)

		await state.set_state(RegUserGroup.experience_time)
		return

	await state.update_data(experience_time=None)

	await call.message.edit_text(
		"Вы подключены к партнерке 1 Win?",
		reply_markup=inline.create_referal_connection_markup(),
	)

	await state.set_state(RegUserGroup.referal_status)


@register_router.callback_query(
	F.data.startswith("set_experience_times_"), RegUserGroup.experience_time
)
async def set_experience_time(call: CallbackQuery, state: FSMContext):
	if call.data.startswith("set_experience_times_"):
		if call.data == "set_experience_times_more":
			await state.update_data(experience_time="Больше")
		elif call.data == "set_experience_times_1month":
			await state.update_data(experience_time="1 месяц")
		elif call.data == "set_experience_times_2month":
			await state.update_data(experience_time="2 месяца")
		elif call.data == "set_experience_times_3month":
			await state.update_data(experience_time="3 месяца")
		elif call.data == "set_experience_times_halfyear":
			await state.update_data(experience_time="Полгода")
		elif call.data == "set_experience_times_1year":
			await state.update_data(experience_time="1 год")
		elif call.data == "set_experience_times_2year":
			await state.update_data(experience_time="2 года")

		try:
			await call.message.edit_text(
				"Вы подключены к партнерке 1 Win?",
				reply_markup=inline.create_referal_connection_markup(),
			)
		except:
			await call.message.delete()
			await call.message.answer(
				"Вы подключены к партнерке 1 Win?",
				reply_markup=inline.create_referal_connection_markup(),
			)

		await state.set_state(RegUserGroup.referal_status)


@register_router.message(F.text, RegUserGroup.experience_time)
async def set_experience_time_from_message(message: Message, state: FSMContext):
	await state.update_data(experience_time=message.text)

	await message.edit_text(
		"Вы подключены к партнерке 1 Win?",
		reply_markup=inline.create_referal_connection_markup(),
	)

	await state.set_state(RegUserGroup.referal_status)


@register_router.callback_query(
	F.data.startswith("referal_status"), RegUserGroup.referal_status
)
async def set_referal_status_callback(call: CallbackQuery, state: FSMContext):
	await state.update_data(
		referal_status=True if F.data == "referal_status_have" else False
	)

	await call.message.edit_text("Что такое УБТ (трафик)?\n\nНапишите что это.")

	await state.set_state(RegUserGroup.ubt_is)


@register_router.message(F.text, RegUserGroup.ubt_is)
async def set_user_ubt_definition_from_message(message: Message, state: FSMContext):
	await state.update_data(ubt_is=message.text)

	await message.answer(
		"Работали ли вы с УБТ (трафиком)?", reply_markup=inline.create_ubt_markup()
	)

	await state.set_state(RegUserGroup.ubt_status)


@register_router.callback_query(F.data.startswith("use_ubt_"), RegUserGroup.ubt_status)
async def set_ubt_status_callback(call: CallbackQuery, state: FSMContext):
	await call.message.delete()
	await state.update_data(
		ubt_status="Нет/немного" if call.data.startswith("use_ubt_no") else "Да"
	)

	await call.message.answer("Из какого вы города?")

	await state.set_state(RegUserGroup.city)


@register_router.message(F.text, RegUserGroup.city)
async def set_city_from_message(message: Message, state: FSMContext):
	await state.update_data(city=message.text)

	await message.answer("Откуда вы узнали о нас?")

	await state.set_state(RegUserGroup.you_source)


@register_router.message(F.text, RegUserGroup.you_source)
async def set_source_from_message(message: Message, state: FSMContext):
	await state.update_data(you_source=message.text)

	await message.answer(
		"💬 Расскажите нам о себе. Пожалуйста, поделитесь вашими мотивами для присоединения к нашей команде и расскажите немного о своем опыте, достижениях и мотивации."
	)

	await state.set_state(RegUserGroup.about_you)


@register_router.message(F.text, RegUserGroup.about_you)
async def set_about_you_from_message(message: Message, state: FSMContext):
	await state.update_data(about_you=message.text)

	await message.answer("Откуда вы будете привлекать трафик?")

	await state.set_state(RegUserGroup.source_traffic)


@register_router.message(F.text, RegUserGroup.source_traffic)
async def set_source_traffic_from_message(message: Message, state: FSMContext):
	await state.update_data(source_traffic=message.text)

	await message.answer(
		"Поделитесь номером.\n\n<i>Он останется конфиденциальным и будет использован только в чрезвычайных ситуациях. Ваш номер никому не передается.</i>",
		parse_mode=ParseMode.HTML,
		reply_markup=reply.create_get_contact_markup(),
	)

	await state.set_state(RegUserGroup.number_phone)


@register_router.message(
	F.content_type == ContentType.CONTACT, RegUserGroup.number_phone
)
async def handle_contact(message: Message, state: FSMContext):
	await state.update_data(number_phone=message.contact.phone_number)

	data = await state.get_data()

	messages = [
		f'✅ Заявка готова к отправке.\n\nИмя, возраст: {data.get("name")}\nГород: {data.get("city")}',
		f'Есть ли у вас опыт в арбитраже трафика: {data.get("experience_status")}',
	]

	if data.get("experience_status") == "Да":
		messages.append(f'Опыт: {data.get("experience_time")}')

	messages += [
		f'Вы подключены к партнерке 1Win: {"Да" if data.get("referal_status") else "Нет"}',
		f'Что такое УБТ трафик: {data.get("ubt_is")}',
		f'Опыт в УБТ: {data.get("ubt_status")}',
		f'Источники трафика: {data.get("source_traffic")}',
		f'Откуда вы узнали о нас: {data.get("you_source")}',
		f'О себе: {data.get("about_you")}',
	]

	messages = "\n".join(messages)

	await message.answer(messages, reply_markup=inline.create_final_req())

	users[message.from_user.id] = {"final": False, "data": data, "count": users[message.from_user.id].get('count', 1)}

	await state.clear()


@register_router.callback_query(F.data.startswith('approve_'))
async def approve_user(call: CallbackQuery):
	await call.answer()
	tid = int(call.data.replace('approve_', ''))
	try:
		if users.get(tid, {}).get('final', False):
			return

		users_data = users.get(tid, {})
		data = users_data.get('data', {})

		data_creation = {
			"number_phone": str(data.get("number_phone")),
			"fullname": " ".join(data.get("name").split(" ")[:-1]),
			"arbitration_experience": 1 if data.get("experience_status") == "Да" else 0,
			"is_referal": 0,
			"experience_time": (
				data.get("experience_time")
				if data.get("experience_status") == "Да"
				else "Отстутствует"
			),
			"age": int("".join(data.get("name").split(" ")[1:])),
			"tg_id": str(tid),
			"approved": 1
		}

		users[tid]["final"] = True
		data = users[tid].get("data", {})

		result, status_code = await APIRequest.post("/partner/create", data_creation)

		if not result or status_code != 200:
			logger.error(
				f"Error when reg partner (tg_id: {tid}). Result of API: {result}"
			)
			await bot.send_message(chat_id=tid, text="❌ Ошибка на стороне нашего сервера при регистрации. Попробуйте позже.")
			return

		await set_cache(result, tid, "sinwin_partners")

		await bot.send_message(chat_id=tid, text="✅ Администратор принял вашу заявку ✅",
			reply_markup=inline.get_show_menu_markup(),
		)
	except Exception as ex:
		for admin in config.secrets.ADMINS_IDS:
			await bot.send_message(chat_id=admin, text=f"❌Ошибка при подтверждении {tid}. Возможно, пользователь уже подтвержден другим админом. Лог: {ex}",
				reply_markup=inline.get_show_menu_markup(),
			)
	else:
		for admin in config.secrets.ADMINS_IDS:
			await bot.send_message(chat_id=admin, text=f"✅ <code>{tid}</code> теперь один из нас!",parse_mode=ParseMode.HTML, 
				reply_markup=inline.view_form(tid),
			)


@register_router.callback_query(F.data.startswith('resend_form_'))
async def resend_form_user(call: CallbackQuery):
	await call.answer()
	tid = int(call.data.replace('resend_form_', ''))

	form = forms.get(tid, [])

	await call.message.answer(text="\n".join(form), parse_mode=ParseMode.HTML, 
								reply_markup=inline.get_approve_menu(tid))


@register_router.callback_query(F.data.startswith('disapprove_'))
async def disapprove_user(call: CallbackQuery):
	tid = int(call.data.replace('disapprove_', ''))
	await call.answer()

	partners = await APIRequest.post("/partner/find", {"opts": {"tg_id": str(tid)}})
	partner = partners[0]['partners']

	if partner:
		users[tid] = users.get(tid, {})
		users[tid]['final'] = False

	try:
		users[tid] = users.get(tid, {})
		users[tid]['final'] = False

		await bot.send_message(chat_id=tid, text="❌ Администратор отклонил вашу заявку ❌", reply_markup=inline.choice_new_answers())
	except Exception as ex:
		for admin in config.secrets.ADMINS_IDS:
			await bot.send_message(chat_id=admin, text=f"❌Ошибка при отклонении {tid}. Возможно, пользователь уже отклонен другим админом. Лог: {ex}",
				reply_markup=inline.get_show_menu_markup(),
			)
	else:
		for admin in config.secrets.ADMINS_IDS:
			await bot.send_message(chat_id=admin, text=f"❌ Заявка <code>{tid}</code> отклонена!",parse_mode=ParseMode.HTML, 
				reply_markup=inline.view_form(tid),
			)


@register_router.callback_query(F.data == "send_request")
async def send_request_callback(call: CallbackQuery):
	users_data = users.get(call.from_user.id, {})
	data = users_data.get('data', {})

	await call.answer()

	for admin_id in config.secrets.ADMINS_IDS:
		form = [
			f"Анкета: @{call.from_user.username}",
			f'Telegram ID: {call.from_user.id}',
			f'Телефон: <code>{data.get("number_phone")}</code>',
			'Рефка: {username_ref}, {hash_ref}',
			f'Попытка регистрации: {users_data.get("count", 1)}',
			'Пользовался уже ботами: нет\n',

			f'Имя, возраст: {data.get("name")}',
			f'Город: {data.get("city")}',
			f'Есть ли у вас опыт в арбитраже трафика: {data.get("experience_status")}',
		]

		if data.get("experience_status") == "Да":
			form.append(f'Опыт: {data.get("experience_time")}')

		mark = '✅' if data.get("ubt_is").lower() == 'условно бесплатный трафик' or data.get("ubt_is").lower() == 'условно бесплатный' else '❌'

		form += [
			f'Вы подключены к партнерке 1Win: {"Да" if data.get("referal_status") else "Нет"}',
			f'{mark} Что такое УБТ трафик: {data.get("ubt_is")}',
			f'Опыт в УБТ: {data.get("ubt_status")}',
			f'Источники трафика: {data.get("source_traffic")}',
			f'Откуда вы узнали о нас: {data.get("you_source")}',
			f'О себе: {data.get("about_you")}',

			f'\n{datetime.now().strftime("%H:%M %d.%m.%Y")}'
		]

		forms[call.from_user.id] = form

		await bot.send_message(chat_id=admin_id, text="\n".join(form), parse_mode=ParseMode.HTML, 
								reply_markup=inline.get_approve_menu(call.from_user.id))

	await call.message.answer(text='✅ Ваша заявка успешно отправлена. Ожидайте подтверждения от администрации', reply_markup=ReplyKeyboardRemove())
