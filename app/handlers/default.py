import re
from hashlib import sha256
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.chat_action import ChatActionSender
import app.keyboards.menu_inline as inline
from app.loader import bot
from app.utils.fileloader import get_file

default_router = Router()
alerts = True


class CardWithdrawGroup(StatesGroup):
	withdraw_sum = State()
	card_number = State()


class SteamWidthDrawGroup(StatesGroup):
	withdraw_sum = State()
	steam_login = State()


class PromoGroup(StatesGroup):
	promocode = State()


@default_router.callback_query(F.data == "statistics")
async def statistics_callback(call: CallbackQuery):
	messages = [
		'<b>СТАТИСТИКА ПО ВСЕМ БОТАМ</b>', '<code>Пользователи которые запустили бота по вашим ссылкам</code>\n',
		'💰️ Баланс: 0 RUB\n', 'Всего пользователей: n\nДепозиты за все время: n\nДоход за все время: n\nПервые депозиты за все время: n',
		'Сгенерировано сигналов: n\n', 'Пользователей на этапе регистрации: n\nПользователей на этапе пополнения',
		'Пользователей на этапе игры: n\n', 'Пользователей за сегодня: n\n├ Пользователей за вчера: n\n├ Пользователей за неделю: n',
		'└ Пользователей за месяц: n\n', 
		'Сумма депозитов за сегодня: n\n├ Сумма депозитов за вчера: n\n├ Сумма депозитов за неделю: n', '└ Сумма депозитов за месяц: n\n', 
		'Первые депозиты за сегодня: n\n├ Первые депозиты за вчера: n\n├ Первые депозиты за неделю: n', '└ Первые депозиты за месяц: n\n',
		'Доход за сегодня: n\n├ Доход за вчера: n\n├ Доход за неделю: n', '└ Доход за месяц: n\n'
	]

	await call.message.answer("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_statistics_bot_menu())


@default_router.callback_query(F.data.startswith("referal"))
async def referal_callback(call: CallbackQuery):
	messages = [
		'Помогите своим друзьям стать частью нашей команды и нанчите зарабатывать вместе!\n',
		'Мы ищем только мотивированных профессионалов, предпочтительно с опытом в арбитраже.\n<code>💰️ Условия реферальной программы могут меняться</code>\n',
		'<b>Для вас:</b>', 'Вы получите 15 000 рублей если приглашенный вами пользователь дойдет до статуса "Профессионал".',
		'<b>Для вашего друга:</b>', 'Ваш друг получит статус "Специалист 40%" вместо "Новичок 35%" на протяжении первого месяца работы.\n',
		'Ваша реферальная ссылка: <code>https://t.me/SinWinBot?start={hash}</code>'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_referals_markup())


@default_router.callback_query(F.data.startswith("about_us"))
async def about_uscallback(call: CallbackQuery):
	messages = [
		'Следите за нашими новостями и обновлениями на <a href="https://t.me/+W8_28FXJWXIxZTgy">канале SinWin</a>. Там вы найдете свежие новости и важные объявления для нашей команды.\n',
		'Ваше мнение важно для нас! Мы всегда стремимся к совершенству, поэтому будем рады ваши вопросам, предложениям и отзывам.\n',
		'Спасибо, что выбрали SinWin!'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_about_us_markup())

@default_router.callback_query(F.data.startswith("my_referals"))
async def referal_answer_callback(call: CallbackQuery):
	await call.answer('У вас нет рефералов', show_alert=True)


@default_router.callback_query(F.data.startswith("reload_achievs"))
async def reload_achievs_callback(call: CallbackQuery):
	await call.answer('Вы не выполнили не одного достижения', show_alert=True)


@default_router.callback_query(F.data.startswith("my_achievs"))
async def my_achievs_callback(call: CallbackQuery):
	messages = [
		'🏆️ Ваши достижения\n', 'Количество: 4\n', '✅ Пользователей по Вашим ссыькам: 100, 250\n',
		'✅ Депозиты: 10 000, 25 000, 50 000 рублей\n', '✅ Доход: 5 000, 10 000, 25 000 рублей\n',
		'✅ Первые депозиты: 25, 50, 75, 100, 150\n', 'Топ Воркеров:\n', '🥇 1 место за декабрь 2024\n',
		'Продолжайте в том же духе и достигайте новых высот! 🌟'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_back_markup('achievements'))


@default_router.callback_query(F.data.startswith("achievements"))
async def achievements_callback(call: CallbackQuery):
	global alerts

	if call.data == 'achievements_false':
		alerts = False

	messages = [
		'🏆️ Ваши Цели:\n', '❌ Пользователей по вашим ссылкам: 100\n❌ Депозиты: 10 000 рублей\n❌ Доход: 5 000 рублей',
		'❌ Первые депозиты: 25', '❌ Количество рефералов: 1', '❌ Сгенерировано сигналов: 250\n'
	]

	messages.append('✅ Уведомления включены\n' if alerts else '❌ Уведомления выключены\n')

	messages.append('Продолжайте в том же духе и достигайте новых высот! 🌟')

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_achievements_markup())


@default_router.callback_query(F.data == "record_creo")
async def record_creo_callback(call: CallbackQuery):
	messages = [
		'В этих ботах вы можете легко записать креативы:\n', 'Mines для выбора мин: @iZiMinsBot',
		'Mines для генерации мин: @iZiMin_Bot', 'Speed Cash: @SPDCashsBot', 'LuckyJet: @CashJetsBot',
		'Coin Flip: @WinFlipsBot\n', 'Для правильного взаимодействия с этими ботами, пожалуйста, ознакомьтесь с инструкцией. В ней вы найдете все необходимые шаги для правильной записи креативов.'
	]
	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_record_creo_markup())


@default_router.callback_query(F.data == "work")
async def work_callback(call: CallbackQuery):
	messages = [
		'💻️ WORK\n\n<b>ССЫЛКИ НА БОТОВ</b>\nMines - <code>https://t.me/IziMinBot?start={hash}</code>',
		'Lucky Jet - <code>https://t.me/CashJetBot?start={hash}</code>',
		'Speed Cash - <code>https://t.me/SPDCashBot?start={hash}</code>',
		'Coin Flip - <code>https://t.me/CoinFlipBot?start={hash}</code>'
	]
	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_work_markup())


@default_router.callback_query(F.data.startswith("showmenu"))
async def showmenu_callback(call: CallbackQuery):
	if call.data == 'showmenu_after_reg':
		await call.message.delete()
		await call.message.answer('🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!', parse_mode=ParseMode.HTML,
							reply_markup=inline.create_main_menu_markup())
	else:
		await call.message.edit_text('🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!', parse_mode=ParseMode.HTML,
							reply_markup=inline.create_main_menu_markup())


@default_router.callback_query(F.data == 'withdraws_history')
async def withdraws_history_callback(call: CallbackQuery):
	messages = ['🤖 История выводов: 3', '├ 18:07 27.12.2024: 10 000: 💳️ Карта',
				'├ 15:07 21.12.2024: 2 000: ⚙️ Steam',
				'└ 16:27 04.11.2024: 5 000: 📱 Вывод по номеру']

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_back_markup('profile'))


@default_router.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery):
	#
	messages = [f'<b>Ваш профиль</b>\n\n🆔 Ваш ID: {call.message.from_user.id}',
				'🛡️ Ваш хеш: hash',
				'💰️ Баланс: 0 RUB', '⚖️ Статус: новичок', '🎯 Вы получаете: 35%',
				'🏗️ Количество рефералов: 0', '☯️ Количество дней с нами: 1 месяц']

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_profile_markup())


@default_router.callback_query(F.data == 'withdraw')
async def withdraw_callback(call: CallbackQuery):
	messages = [
		'💰️ Баланс: 0 RUB\n',
		'❗️ ВЫВОД СРЕДСТВ ДОСТУПЕН ОДИН РАЗ В НЕДЕЛЮ КАЖДУЮ СРЕДУ ПО МОСКОВСКОМУ ВРЕМЕНИ. К ВЫВОДУ ДОСТУПНА ВСЯ СУММА КОТОРАЯ НАХОДИТСЯ НА БАЛАНСЕ.❗️\n',
		'В редких случаях при больщом доходе со вторника на среду вывести всю сумму получится через неделю. Однако в таких ситуациях вы всегда можете вывести часть средств, оставив небольшой остаток на балансе.\n',
		'Если в течении 24 часов после создания заявки на вывод вы не получите уведомление от бота, пожалуйста, свяжитесь с поддержкой.\n',
		'<b>ЛИМИТЫ НА ВЫВОД СРЕДСТВ</b>\n',
		'💳️ <b>Карта</b>', ' ∟ VISA, MasterCard: от 2 000 ₽ до 50 000 ₽\n',
		'📱 <b>Вывод по номеру телефона</b>', ' ∟ VISA, MasterCard, МИР: от 5 000 ₽ до 100 000 ₽\n',
		'⚙️ <b>Steam</b>', ' ∟ Вывод на аккаунт Steam: от 2 000 ₽ до 12 000 ₽\n',
		'🌸 <b>Piastrix</b>', '∟ от 1 800 ₽ до 100 000 ₽\n',
		'👾 <b>FK Wallet</b>', '∟ от 1 800 ₽ до 100 000 ₽\n',
		'👑 <b>Крипта</b>', '∟ Плавающие лимиты, смотрите при выводе от 1 500 ₽ до 5 000 000 ₽\n',
	]

	try:
		await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_withdraw_markup())
	except Exception:
		await call.message.delete()
		await call.message.answer("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_withdraw_markup())


@default_router.callback_query(F.data == 'withdraw_crypto')
async def withdraw_crypto_callback(call: CallbackQuery):
	messages = [
		'Какую криптовалюту вы хотите использовать для вывода денег?\n',
		'<b>ЛИМИТЫ НА ВЫВОД СРЕДСТВ</b>',
		'Bitcoin - 10 650 ₽ - 665 000 ₽',
		'Ethereum - 1 000 ₽ - 665 000 ₽',
		'Tron - 1 500 ₽ - 665 070 ₽',
		'Tether ERC20 - 1 500 ₽ - 5 000 000 ₽',
		'Tether TRC20 - 1 500 ₽ - 5 000 000 ₽',
		'Tether BEP20 - 1 500 ₽ - 5 000 000 ₽',
		'BNB ERC20 - 1 500 ₽ - 655 070 ₽',
		'Litecoin - 1 500 ₽ - 665 000 ₽',
		'Monero - 1 500 ₽ - 665 070 ₽',
		'Bitcoin Cash - 1 500 ₽ - 665 070 ₽',
		'Dash - 1 500 ₽ - 665 070 ₽',
		'Doge - 1 500 ₽ - 665 070 ₽',
		'Zcash - 1 500 ₽ - 665 070 ₽',
		'Ripple - 1 500 ₽ - 665 070 ₽',
		'Stellar - 1 500 ₽ - 665 070 ₽',
	]
	photo = get_file("main/crupto.jpg")

	await call.message.edit_media(
			InputMediaPhoto(media=photo, caption="\n".join(messages), parse_mode=ParseMode.HTML),
			reply_markup=inline.create_crypto_withdraw_markup(),
		)


@default_router.callback_query(F.data == 'withdraw_card')
async def withdraw_card_callback(call: CallbackQuery, state: FSMContext):
	photo = get_file("main/card.jpg")
	message = '💰️ Баланс: 0 RUB\n💳️ Visa или MasterCard\nЛимит одного вывода: 2 000 ₽ - 50 000 ₽\n\n<code>Вывод средств на карты банков РФ может происходить с задержкой. Чтобы совершать выводы максимально быстро, рекомендуем использовать карту Сбера.</code>\n\n✍️ Введите сумму которую Вы хотите вывести.'
	
	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.edit_media(
			InputMediaPhoto(media=photo, caption=message, parse_mode=ParseMode.HTML),
			reply_markup=inline.create_back_markup('withdraw'),
		)

	await state.set_state(CardWithdrawGroup.withdraw_sum)


@default_router.message(F.text, CardWithdrawGroup.withdraw_sum)
async def withdraw_card_message(message: Message, state: FSMContext):
	await message.delete()
	await message.answer('💰️ Баланс: 0 RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
						reply_markup=inline.create_back_markup('withdraw_card'))

	await state.clear()


@default_router.callback_query(F.data == 'withdraw_steam')
async def withdraw_steam_callback(call: CallbackQuery, state: FSMContext):
	photo = get_file("main/steam.jpg")
	message = '💰️ Баланс: 0 RUB\nВывод на аккаунт Steam\nЛимит одного вывода: от 2 000 ₽ до 12 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'
	
	async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
		await call.message.edit_media(
			InputMediaPhoto(media=photo, caption=message, parse_mode=ParseMode.HTML),
			reply_markup=inline.create_back_markup('withdraw'),
		)

	await state.set_state(SteamWidthDrawGroup.withdraw_sum)


@default_router.message(F.text, SteamWidthDrawGroup.withdraw_sum)
async def withdraw_steam_message(message: Message, state: FSMContext):
	await message.answer('💰️ Баланс: 0 RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
						reply_markup=inline.create_back_markup('withdraw'))

	await state.clear()