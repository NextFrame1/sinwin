import traceback
from typing import Any, Dict, Tuple, Union

import aiohttp
from loguru import logger

from app.loader import config


class APIRequest:
	"""
	This class describes an api request.
	"""

	@staticmethod
	async def fetch(
		client: aiohttp.ClientSession, url: str, data: Dict[Any, Any] = {}
	) -> Tuple[Union[Any, bool], int]:
		"""
		Fetch URL with data and ClientSession

		:param      client:  The client
		:type       client:  aiohttp.ClientSession
		:param      url:     The url
		:type       url:     str
		:param      data:    The data
		:type       data:    Dict[Any, Any]

		:returns:   tuple with result and status code
		:rtype:     Tuple[Union[Any, bool], int]
		"""
		url = f'{config.secrets.URL}{url if url.startswith("/") else f"/{url}"}'
		try:
			if data:
				logger.debug(f'Post APIRequest: {url}')
				response = await client.post(
					url=url, json=data, headers={'Content-Type': 'application/json'}
				)
			else:
				logger.debug(f'Get APIRequest: {url}')
				response = await client.get(url)

			result = await response.json()

			if result.get('status', {'success': False}).get('success', False):
				return result, response.status
			else:
				return result, 500
		except aiohttp.ClientError:
			logger.error(f'[aiohttp] {url} error: {traceback.format_exc()}')
			return False, 500
		except Exception:
			logger.error(f'[APIRequest] {url} error: {traceback.format_exc()}')
			return False, 500

	@staticmethod
	async def post(url: str, data: Dict[Any, Any]) -> Tuple[Union[Any, bool], int]:
		"""
		Post request to URL with data

		:param      url:   The url
		:type       url:   str
		:param      data:  The data
		:type       data:  data: Dict[Any, Any]

		:returns:   result and status code
		:rtype:     Tuple[Union[Any, bool], int]
		"""
		async with aiohttp.ClientSession() as session:
			result, status = await APIRequest.fetch(session, url, data)
			return result, status

	@staticmethod
	async def get(url: str) -> Tuple[Union[Any, bool], int]:
		"""
		Get request to URL with data

		:param      url:  The url
		:type       url:  str

		:returns:   result and status code
		:rtype:     Tuple[Union[Any, bool], int]
		"""
		async with aiohttp.ClientSession() as session:
			result, status = await APIRequest.fetch(session, url)

			return result, status
