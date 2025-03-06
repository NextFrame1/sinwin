@default_router.callback_query(F.data == 'withdraw_steam', message_only_confirmed)
async def withdraw_steam_callback(call: CallbackQuery, state: FSMContext):
	await state.clear()

	users[call.message.chat.id] = {
		'final': True,
		'withdraw_card': True,
	}

	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]

	if not partner['approved']:
		print(partner)
		users[call.from_user.id] = users.get(call.from_user.id, {})
		users[call.from_user.id]['final'] = False
		await call.answer('Вы заблокированы')
		return

	message = f'💰️ Баланс: {partner["balance"]} RUB\nВывод на аккаунт Steam\nЛимит одного вывода: от 2 000 ₽ до 12 000 ₽\n\n✍️ Введите сумму которую Вы хотите вывести.'

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/steam.jpg')

	await call.message.edit_media(
		InputMediaPhoto(media=image, caption=message, parse_mode=ParseMode.HTML),
		parse_mode=ParseMode.HTML,
		reply_markup=inline.create_back_markup('withdraw'),
	)

	await state.set_state(SteamWithdrawGroup.withdraw_sum)


@default_router.message(F.text, SteamWithdrawGroup.withdraw_sum, message_only_confirmed)
async def withdraw_steam_message(message: Message, state: FSMContext):
	user = users.get(message.chat.id, {})

	try:
		partners = await APIRequest.post(
			'/partner/find', {'opts': {'tg_id': message.from_user.id}}
		)
		partner = partners[0]['partners'][-1]
	except Exception as ex:
		await message.answer(
			f'Произошла ошибка: {ex}',
			reply_markup=inline.create_back_markup('profile'),
		)
		return

	try:
		sum_to_withdraw = int(message.text)
	except Exception:
		await message.answer(
			'Ошибка: некорректный ввод\n\nПожалуйста, введите корректную сумму для вывода, используя только цифры.',
			reply_markup=inline.create_back_markup('withdraw_steam'),
		)
		await state.clear()
		return

	if user.get('final', False) and user.get('withdraw_card', False):
		if partner['balance'] < sum_to_withdraw:
			await message.answer(
				f'💰️ Баланс: {partner["balance"]} RUB\n\nОшибка: недостаточно средств. У вас недостаточно средств на балансе для выполнения этой операции.\n\nПожалуйста, проверьте ваш баланс и введите сумму, которая не превышает доступные средства.',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)
			await state.clear()
			user['withdraw_card'] = False
		elif sum_to_withdraw > 12000.0:
			await message.answer(
				f'Ошибка: сумма превышает лимит\n\nСумма {sum_to_withdraw} превышает максимально допустимую для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам:',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)
			await state.clear()
			user['withdraw_card'] = False
		elif sum_to_withdraw < 2000.0:
			await message.answer(
				f'Ошибка: сумма слишком мала\n\nСумма {sum_to_withdraw} меньше минимально допустимой для выбранного метода вывода.\n\nПожалуйста, введите сумму, соответствующую указанным лимитам.',
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)
			await state.clear()
			user['withdraw_card'] = False
		else:
			await state.update_data(withdraw_sum=sum_to_withdraw)
			await message.answer(
				f"Сумма вывода: {sum_to_withdraw} ₽\n\nУкажите ваш логин аккаунта steam\n\nВы можете узнать ваш Steam login кликнув по <a href='https://store.steampowered.com/account/'>прямой ссылке</a>",
				reply_markup=inline.create_back_markup('withdraw_steam'),
			)
			await state.set_state(SteamWithdrawGroup.withdraw_card)


@default_router.message(
	F.text, SteamWithdrawGroup.withdraw_card, message_only_confirmed
)
async def withdraw_withdraw_steam_message(message: Message, state: FSMContext):
	text = message.text

	await state.update_data(withdraw_card=text)
	data = await state.get_data()
	await message.answer(
		f'Логин Steam принят.\n\nПожалуйста, подтвердите вывод средств. Сумма: {data.get("withdraw_sum")} ₽\n\nSteam: {text}',
		reply_markup=inline.create_withdraw_continue_markup(withdraw='steam'),
	)
	await state.set_state(SteamWithdrawGroup.approved)


@default_router.callback_query(
	F.data == 'user_approve_steam_withdraw',
	SteamWithdrawGroup.approved,
	message_only_confirmed,
)
async def user_approve_steam_withdraw(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = users.get(call.message.chat.id, {})
	user['withdraw_card'] = False
	partners = await APIRequest.post(
		'/partner/find', {'opts': {'tg_id': call.from_user.id}}
	)
	partner = partners[0]['partners'][-1]
	await state.clear()

	partner_hash = partner.get('partner_hash', 'Недоступно')

	result, status = await APIRequest.post(
		'/transaction/create',
		data={
			'partner_hash': partner_hash,
			'username': str(call.from_user.username),
			'amount': data['withdraw_sum'],
			'withdraw_card': data['withdraw_card'],
			'approved': False,
			'preview_id': int(
				f'{datetime.now().strftime("%Y%m%d%H%M%S")}{randint(1000, 9999)}'
			),
		},
	)

	if status != 200:
		await call.answer(f'ошибка: {status}')
		return

	transaction_id = result.get('transaction_id', 0)

	transactions = await APIRequest.post(
		'/transaction/find', {'opts': {'id': transaction_id}}
	)
	transac = transactions[0]['transactions'][-1]

	await call.message.edit_text(
		f'Ваш запрос на вывод средств поставлен в очередь.\n🛡 Ваш хэш: {partner_hash}\n🆔 ID Вывода: {transac["preview_id"]}\n\nВ течение 24 часов бот уведомит вас о статусе вывода. Если за это время вы не получите уведомление, пожалуйста, обратитесь в поддержку.',
		reply_markup=inline.create_back_markup('profile'),
	)

	tdata = withdraws_history.get(partner_hash, {})
	tdata[transac['preview_id']] = {
		'status': '⚪️ Вывод на обработке',
		'type': '⚙️ Steam',
		'sum': data['withdraw_sum'],
		'date': datetime.now(),
	}
	withdraws_history[partner_hash] = tdata

	transactions_dict[transaction_id] = data

	image = FSInputFile(path=f'{config.SINWIN_DATA}/main/steam.jpg')

	for admin in config.secrets.ADMINS_IDS:
		await bot.send_photo(
			chat_id=admin,
			photo=image,
			caption=f"""Tg id: {call.from_user.id}
Ник: {call.from_user.username}
Реферал: {partner['is_referal']}
Хэш: {partner_hash}
Id Вывода: {transac['preview_id']}

Вывод: ⚙️ Steam
Сумма: <code>{data['withdraw_sum']}</code>₽
Steam логин: <code>{data['withdraw_card']}</code>""",
			parse_mode=ParseMode.HTML,
			reply_markup=inline.create_admin_transaction_menu(
				transaction_id, admin, 'steam'
			),
		)
