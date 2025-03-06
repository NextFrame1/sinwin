import os

from aiogram.types import FSInputFile

from app.loader import config


def get_file(filename: str) -> FSInputFile:
	"""
	Gets the file.

	:param		filename:  The filename
	:type		filename:  str
	:param		language:  The language
	:type		language:  str

	:returns:	The file.
	:rtype:		FSInputFile
	"""
	filepath = get_localized_image(filename)
	file = FSInputFile(path=filepath)
	return file


def get_localized_image(filename: str) -> str:
	"""
	Gets the localized image filename.

	:param		filename:  The filename
	:type		filename:  str
	:param		language:  The language
	:type		language:  str

	:returns:	The localized image.
	:rtype:		str
	"""

	return os.path.join(config.SINWIN_DATA, filename)
