from aiogram.types import Message

from app.loader import config


def check_is_admin(message: Message) -> bool:
	if message.chat.id in config.secrets.ADMINS_IDS:
		return True
	else:
		return False
