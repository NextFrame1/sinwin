import re
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ContentType, ReplyKeyboardRemove
from aiogram.utils.chat_action import ChatActionSender
import app.keyboards.inline as inline
import app.keyboards.reply as reply
from app.loader import bot

register_router = Router()


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

	:param      name:  The name
	:type       name:  str

	:returns:   validation status
	:rtype:     bool
	"""
	pattern = r'^[A-za-zА-Яа-яЁё\s]+\d{1,3}$'

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
	await message.answer('Вы не зарегистрированы в боте, для продолэения Вам необходимо подать заявку. Это займет менее 5 минут.',
						parse_mode=ParseMode.HTML, reply_markup=inline.create_start_markup())


@register_router.callback_query(F.data == "submit_reg_request")
async def accept_submitted_reg_request_callback(call: CallbackQuery, state: FSMContext):
	await call.message.delete()

	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.answer('Напишите Ваше имя и возраст в формате "Имя Возраст" (пример: Иван 22):')

	await state.set_state(RegUserGroup.name)


@register_router.message(F.text, RegUserGroup.name)
async def capture_user_name(message: Message, state: FSMContext):
	if not validate_name(message.text):
		async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
			await message.answer('Введите в требуемом формате: Имя Возраст\nПример: Иван 22')
		
		await state.set_state(RegUserGroup.name)
	else:
		await state.update_data(name=message.text)

		async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
			await message.answer('Есть ли у вас опыт в арбитраже траффика?',
				reply_markup=inline.create_choice_user_experience_markup())

		await state.set_state(RegUserGroup.experience_status)


@register_router.callback_query(F.data.startswith('set_experience_time'), RegUserGroup.experience_status)
async def set_experience_status(call: CallbackQuery, state: FSMContext):
	await state.update_data(experience_status='Нет/немного' if call.data.startswith('set_experience_time_no') else 'Да')

	if call.data == 'set_experience_time':
		await call.message.delete()

		async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
			await call.message.answer('Сколько месяцев/лет вы занимаетесь арбитражем трафика?\nЕсли нет вашего варианта, напишите в чат.',
				reply_markup=inline.create_choice_user_experience_time_markup())

		await state.set_state(RegUserGroup.experience_time)
		return

	await state.update_data(experience_time=None)

	await call.message.delete()

	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.answer('Вы подключены к партнерке 1 Win?',
			reply_markup=inline.create_referal_connection_markup())

	await state.set_state(RegUserGroup.referal_status)


@register_router.callback_query(F.data.startswith('set_experience_times'), RegUserGroup.experience_time)
async def set_experience_time(call: CallbackQuery, state: FSMContext):
	await call.message.delete()
	if call.data.startswith('set_experience_times_'):
		if call.data == 'set_experience_times_more':
			await state.update_data(experience_time='Больше')
		elif call.data == 'set_experience_times_1month':
			await state.update_data(experience_time='1 месяц')
		elif call.data == 'set_experience_times_2month':
			await state.update_data(experience_time='2 месяца')
		elif call.data == 'set_experience_times_3month':
			await state.update_data(experience_time='3 месяца')
		elif call.data == 'set_experience_times_halfyear':
			await state.update_data(experience_time='Полгода')
		elif call.data == 'set_experience_times_1year':
			await state.update_data(experience_time='1 год')
		elif call.data == 'set_experience_times_2year':
			await state.update_data(experience_time='2 года')

		async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
			await call.message.answer('Вы подключены к партнерке 1 Win?',
				reply_markup=inline.create_referal_connection_markup())
		
		await state.set_state(RegUserGroup.referal_status)


@register_router.message(F.text, RegUserGroup.experience_time)
async def set_experience_time_from_message(message: Message, state: FSMContext):
	await state.update_data(experience_time=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('Вы подключены к партнерке 1 Win?',
			reply_markup=inline.create_referal_connection_markup())

	await state.set_state(RegUserGroup.referal_status)


@register_router.callback_query(F.data.startswith('referal_status'), RegUserGroup.referal_status)
async def set_referal_status_callback(call: CallbackQuery, state: FSMContext):
	await call.message.delete()
	await state.update_data(referal_status=True if F.data == 'referal_status_have' else False)

	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.answer('Что такое УБТ (трафик)?\n\nНапишите что это.')

	await state.set_state(RegUserGroup.ubt_is)


@register_router.message(F.text, RegUserGroup.ubt_is)
async def set_user_ubt_definition_from_message(message: Message, state: FSMContext):
	await state.update_data(ubt_is=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('Работали ли вы с УБТ (трафиком)?',
			reply_markup=inline.create_ubt_markup())

	await state.set_state(RegUserGroup.ubt_status)


@register_router.callback_query(F.data.startswith('use_ubt_'), RegUserGroup.ubt_status)
async def set_ubt_status_callback(call: CallbackQuery, state: FSMContext):
	await call.message.delete()
	await state.update_data(ubt_status='Нет/немного' if call.data.startswith('use_ubt_no') else 'Да')

	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.answer('Из какого вы города?')

	await state.set_state(RegUserGroup.city)


@register_router.message(F.text, RegUserGroup.city)
async def set_city_from_message(message: Message, state: FSMContext):
	await state.update_data(city=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('Откуда вы узнали о нас?')

	await state.set_state(RegUserGroup.you_source)


@register_router.message(F.text, RegUserGroup.you_source)
async def set_source_from_message(message: Message, state: FSMContext):
	await state.update_data(you_source=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('💬 Расскажите нам о себе. Пожалуйста, поделитесь вашими мотивами для присоединения к нашей команде и расскажите немного о своем опыте, достижениях и мотивации.')

	await state.set_state(RegUserGroup.about_you)


@register_router.message(F.text, RegUserGroup.about_you)
async def set_about_you_from_message(message: Message, state: FSMContext):
	await state.update_data(about_you=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('Откуда вы будете привлекать трафик?')

	await state.set_state(RegUserGroup.source_traffic)


@register_router.message(F.text, RegUserGroup.source_traffic)
async def set_source_traffic_from_message(message: Message, state: FSMContext):
	await state.update_data(source_traffic=message.text)

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		await message.answer('Поделитесь номером.\n\n<i>Он останется конфиденциальным и будет использован только в чрезвычайных ситуациях. Ваш номер никому не передается.</i>', 
							parse_mode=ParseMode.HTML,
							reply_markup=reply.create_get_contact_markup())

	await state.set_state(RegUserGroup.number_phone)


@register_router.message(F.content_type == ContentType.CONTACT, RegUserGroup.number_phone)
async def handle_contact(message: Message, state: FSMContext):
	await state.update_data(number_phone=message.contact.phone_number)

	data = await state.get_data()

	messages = [f'✅ Заявка готова к отправке.\n\nИмя, возраст: {data.get("name")}\nГород: {data.get("city")}',
				f'Есть ли у вас опыт в арбитраже трафика: {data.get("experience_status")}']

	if data.get('experience_status') == 'Да':
		messages.append(f'Опыт: {data.get("experience_time")}')

	messages += [f'Вы подключены к партнерке 1Win: {"Да" if data.get("referal_status") else "Нет"}',
				f'Что такое УБТ трафик: {data.get("ubt_is")}',
				f'Опыт в УБТ: {data.get("ubt_status")}',
				f'Источники трафика: {data.get("source_traffic")}',
				f'Откуда вы узнали о нас: {data.get("you_source")}',
				f'О себе: {data.get("about_you")}']

	messages = "\n".join(messages)

	await message.answer(messages, reply_markup=inline.create_final_req())

	await state.clear()


@register_router.callback_query(F.data == 'send_request')
async def send_request_callback(call: CallbackQuery):
	await call.message.delete()
	# await call.message.answer('✅ Ваша заявка успешно отправлена. Ожидайте подтверждения от администрации', reply_markup=ReplyKeyboardRemove())
	await call.message.answer('✅ Администратор принял вашу заявку ✅', reply_markup=inline.get_show_menu_markup())
