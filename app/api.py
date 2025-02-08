from typing import Any, Dict

import aiohttp
from loguru import logger

from app.loader import config


class APIRequest:
	@staticmethod
	async def fetch(client: aiohttp.ClientSession, url: str, data: Dict[Any, Any] = {}):
		url = f'{config.secrets.URL}{url if url.startswith('/') else f"/{url}"}'
		try:
			if data:
				logger.debug(f"Post APIRequest: {url}")
				response = await client.post(
					url=url, json=data, headers={"Content-Type": "application/json"}
				)
			else:
				logger.debug(f"Get APIRequest: {url}")
				response = await client.get(url)

			result = await response.json()

			return result, response.status
		except aiohttp.ClientError as ex:
			logger.error(f"[aiohttp] {url} error: {ex}")
			return False, 500

	@staticmethod
	async def post(url: str, data: Dict[Any, Any]):
		async with aiohttp.ClientSession() as session:
			data = await APIRequest.fetch(session, url, data)
			return data

	@staticmethod
	async def get(url: str):
		async with aiohttp.ClientSession() as session:
			data = await APIRequest.fetch(session, url)
			return data
