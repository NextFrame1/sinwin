from datetime import datetime
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
import app.keyboards.menu_inline as inline
from app.loader import bot
from app.utils.fileloader import get_file
from app.database.test import users

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
		'💰️ Баланс: 0 RUB\n', 
		'Всего пользователей: n\nДепозиты за все время: n\nДоход за все время: n\nПервые депозиты за все время: n',
		'Сгенерировано сигналов: n\n', 'Пользователей на этапе регистрации: n\nПользователей на этапе пополнения',
		'Пользователей на этапе игры: n\n', 'Пользователей за сегодня: n\n├ Пользователей за вчера: n\n├ Пользователей за неделю: n',
		'└ Пользователей за месяц: n\n', 
		'Сумма депозитов за сегодня: n\n├ Сумма депозитов за вчера: n\n├ Сумма депозитов за неделю: n', '└ Сумма депозитов за месяц: n\n', 
		'Первые депозиты за сегодня: n\n├ Первые депозиты за вчера: n\n├ Первые депозиты за неделю: n', '└ Первые депозиты за месяц: n\n',
		'Доход за сегодня: n\n├ Доход за вчера: n\n├ Доход за неделю: n', '└ Доход за месяц: n\n'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_statistics_bot_menu())


@default_router.callback_query(F.data == "statistics_mines")
async def statistics_mines_callback(call: CallbackQuery):
	messages = [
		'<b>💣️СТАТИСТИКА ПО  MINES</b>', 
		'<b>ЗА ВСЕ ВРЕМЯ</b>\n',
		'┌ Баланс партнерки: n',
		'├ Пользователей в партнерке всего: n',
		'├ Баланс всех пользователей: n',
		'├ Вывели с партнерки: n',
		f'└ Поставлено на вывод {datetime.now()}: n\n',
		'┌ Всего пользователей по всех ботах: n\n├ Депозиты: n\n├ Доход ботов: n\n├ Первые депозиты: n',
		'└  Сгенерировано сигналов: n\n', 'Пользователей на этапе регистрации: n\n├ Пользователей на этапе пополнения',
		'└ Пользователей на этапе игры: n\n', 'Пользователей за сегодня: n\n├ Пользователей за вчера: n\n├ Пользователей за неделю: n',
		'└ Пользователей за месяц: n\n', 
		'Сумма депозитов за сегодня: n\n├ Сумма депозитов за вчера: n\n├ Сумма депозитов за неделю: n', '└ Сумма депозитов за месяц: n\n', 
		'Первые депозиты за сегодня: n\n├ Первые депозиты за вчера: n\n├ Первые депозиты за неделю: n', '└ Первые депозиты за месяц: n\n',
		'Доход за сегодня: n\n├ Доход за вчера: n\n├ Доход за неделю: n', '└ Доход за месяц: n\n'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_mines_statistics_menu())


@default_router.callback_query(F.data.startswith("referal"))
async def referal_callback(call: CallbackQuery):
	messages = [
		'Помогите своим друзьям стать частью нашей команды и начите зарабатывать вместе!\n',
		'Мы ищем только мотивированных профессионалов, предпочтительно с опытом в арбитраже.\n\n<code>💰️ Условия реферальной программы могут меняться</code>\n\n',
		'<b>Для вас:</b>', 'Вы получите 15 000 рублей если приглашенный вами пользователь дойдет до статуса "Профессионал".\n',
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
		alerts = not alerts

	messages = [
		'🏆️ Ваши Цели:\n', '❌ Пользователей по вашим ссылкам: 100\n❌ Депозиты: 10 000 рублей\n❌ Доход: 5 000 рублей',
		'❌ Первые депозиты: 25', '❌ Количество рефералов: 1', '❌ Сгенерировано сигналов: 250\n'
	]

	messages.append('✅ Уведомления включены\n' if alerts else '❌ Уведомления выключены\n')

	messages.append('Продолжайте в том же духе и достигайте новых высот! 🌟')

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML,
							reply_markup=inline.create_achievements_markup(alerts))


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


@default_router.callback_query(F.data.startswith('admin_'))
async def adminpanel_query_callback(call: CallbackQuery):
	await call.message.edit_text("ЗАГЛУШКА", reply_markup=inline.create_back_markup('showmenu'))


@default_router.callback_query(F.data == 'adminpanel')
async def adminpanel_callback(call: CallbackQuery):
	#└┏ ├「┌
	messages = ['┌ Пользователей в партнерке: 10', '├ Баланс Партнерки: 100 000 рублей', '├ Доход бота: 10 000 000 рублей',
	'├ Баланс всех пользователей: 15 000 500 рублей',
	f'└ Поставлено на вывод {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: 100 000 рублей']

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_adminpanel_markup())


@default_router.callback_query(F.data == 'top_workers')
async def top_workers_callback(call: CallbackQuery):
	#🥇🥈🥉🏅 
	messages = [
				'🏆️ Топ воркеров по доходу за последний месяц\n',
				'<code>🥇 WOT****3156: 1 000 000 рублей</code>',
				'🥈 RNP****6871: 800 000 рублей',
				'🥉 RNP****8165: 700 000 рублей',
				'🏅 WOK****2899: 600 000 рублей',
				'🏅 WOI****9437: 450 000 рублей\n',
				'👽️ Ваша позиция в топе: 10\n',
				'📅 Статистика обнуляется 1 числа каждого месяца.\n',
				'<code>👑 Пользователь, занявший первое место, повышается в статусе, если его текущий статус "Профессионал" или ниже.</code>',
				'<code>💵 Второе и третье места получают премию.</code>\n\n'
				'🚀 Удачи в достижении новых высот!'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_back_markup('showmenu'))


@default_router.callback_query(F.data == 'withdraws_history')
async def withdraws_history_callback(call: CallbackQuery):
	#🟢🟡⚪️
	messages = ['🤖 История выводов: 3', '├ 18:07 27.12.2024: 10 000: 💳️ Карта ⚪️',
				'├ 15:07 21.12.2024: 2 000: ⚙️ Steam 🟡',
				'└ 16:27 04.11.2024: 5 000: 📱 Вывод по номеру 🟢\n',
				'🟢 - Вывод произведен, 🟡 - вывод на обработке, ⚪️ - вывод подтверждается.']

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_back_markup('profile'))


@default_router.callback_query(F.data == 'status_levels')
async def status_levels_callback(call: CallbackQuery):
	#❌✅🏆️📊🎯💼💰️
	messages = ['1. Новичок: 35 %\nУсловия для перехода:', '❌ Доход за последний месяц: не менее 50 000 рублей', '✅ Общий доход за все время: не менее 100 000 рублей',
				'✅ Первые депозиты за последний месяц: не менее 100\n',
				'2. Специалист 40 %', '❌ Доход за последний месяц: не менее 150 000 рублей', '✅ Общий доход за все время: не менее 300 000 рублей',
				'✅ Первые депозиты за последний месяц: не менее 200\n',
				'3. Профессионал 45 %', '❌ Доход за последний месяц: не менее 300 000 рублей', 
				'✅ Общий доход за все время: не менее 600 000 рублей',
				'✅ Первые депозиты за последний месяц: не менее 400\n',
				'4. Мастер 50%', '❌ Доход за последний месяц: не менее 500 000 рублей',
				'✅ Общий доход за все время: не менее 1 000 000 рублей',
				'✅ Первые депозиты за последний месяц: не менее 600\n',
				'5. Легенда Суб Партнерство\n', 'Суб партнерство подключается вручную. Пользователь регистрируется в официальной партнерской программе 1 Win через нашу ссылку. Создает свою уникальную ссылку для приглашения, которую мы интегрируем в нашего бота. Пользователь получает от 50% до 60% прибыли через официальную партнерскую программу. Иногда статус "Легенда" подключается вместо статуса "Мастер".\n',
				'<code>Условия перехода могут изменяться</code>'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_back_markup('status'))


@default_router.callback_query(F.data == 'statistics_online')
async def statistics_online_callback(call: CallbackQuery):
	#✨📊💰️🎮️
	messages = [
		'✨ Статистика в реальном времени\n',
		'Следите за всей активностью мнговенно! Нажмите, чтобы перейти в бота @testusername, и получайте:',
		'📊 Уведомления о регистрации новых пользователей.',
		'💰️ Информацию о депозитах.',
		'🎮️ Данные по каждой игре ваших пользователей',
		'\nОбратите внимание: статистика, накопленная ранее, в боте не отображается. Вы сможете отслеживать данные только с момента подключения.'
	]

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_online_statistics_markup())


@default_router.callback_query(F.data == 'status')
async def status_callback(call: CallbackQuery):
	#❌✅🏆️📊🎯💼💰️
	messages = ['🏆️ Ваш текущий статус: Новичок', '🎯 Вы получаете: 35%\n', '📊 Ваш доход за последний месяц: 15 000 RUB',
				'💼 Общий доход: 100 000 RUB', '💰️ Первые депозиты за последний месяц: 100\n',
				'Условия для перехода:', '❌ Доход за последний месяц: не менее 50 000 рублей', '✅ Общий доход за все время: не менее 100 000 рублей',
				'✅ Первые депозиты за последний месяц: не менее 100\n',
				'Продолжайте в том же духе! Чем дольше и лучше вы работаете, тем больше вы зарабатывайте! Переход на новый уровень происходит автоматически каждые 24 часа, если все условия выполнены.',
				'\n<code>Обратите внимание: условия перехода могут меняться.</code>\n', 'Если у вас есть вопросы, напишите в поддержку']

	await call.message.edit_text("\n".join(messages), parse_mode=ParseMode.HTML, reply_markup=inline.create_status_markup())


@default_router.callback_query(F.data == 'profile')
async def profile_callback(call: CallbackQuery):
	#
	messages = [f'<b>Ваш профиль</b>\n\n🆔 Ваш ID: {call.message.from_user.id}',
				'🛡️ Ваш хеш: hash\n',
				'💰️ Баланс: 0 RUB', '⚖️ Статус: новичок', '🎯 Вы получаете: 35%\n',
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
	
	
	await call.message.edit_media(
			InputMediaPhoto(media=photo, caption=message, parse_mode=ParseMode.HTML),
			reply_markup=inline.create_back_markup('withdraw'),
		)

	await state.set_state(CardWithdrawGroup.withdraw_sum)


@default_router.message(F.text, CardWithdrawGroup.withdraw_sum)
async def withdraw_card_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	await message.delete()

	if user.get('final', False):
		await message.answer('💰️ Баланс: 0 RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
						reply_markup=inline.create_back_markup('withdraw_card'))
		await state.clear()


@default_router.message(F.text)
async def text_handler(message: Message):
	user = users.get(message.chat.id, {})
	await message.delete()

	if user.get('final', False):
		await message.answer('🏠️ <b>Приветствуем!</b>\n\nСпасибо, что выбрали SinWin!', parse_mode=ParseMode.HTML,
							reply_markup=inline.create_main_menu_markup())


@default_router.callback_query(F.data == 'withdraw_steam')
async def withdraw_steam_callback(call: CallbackQuery, state: FSMContext):
	photo = get_file("main/steam.jpg")
	message = '💰️ Баланс: 0 RUB\nВывод на аккаунт Steam\nЛимит одного вывода: от 2 000 ₽ до 12 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'
	
	
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
