from aiogram.types import BotCommand, BotCommandScopeDefault


async def setup_default_commands(bot):
	"""
	Setup default bot commands

	:param		bot:  Bot
	:type		bot:  bot
	"""
	commands = [BotCommand(command="start", description="Старт")]

	await bot.set_my_commands(commands, BotCommandScopeDefault())
