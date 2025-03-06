from typing import Any

from aiocache import Cache
from loguru import logger

from app.loader import config


async def create_cache(namespace: str = 'main') -> Cache.REDIS:
	"""
	Gets the cache.

	:param		name:			The name
	:type		name:			str
	:param		namespace:		The namespace
	:type		namespace:		str
	:param		subspace:		The subspace
	:type		subspace:		str

	:returns:	The cache.
	:rtype:		redis cache

	:raises		HTTPException:	error connect to redis cache server
	"""
	try:
		cache = Cache.REDIS(
			endpoint=config.redis.host,
			port=config.redis.port,
			namespace=namespace,
		)
	except Exception as ex:
		logger.error(f'Error when get_cache: {ex}')
		return None, None

	return cache


async def get_cache(name: str, namespace: str = 'main') -> Any:
	"""
	Gets the cached value by name.

	:param		name:		The name
	:type		name:		str
	:param		namespace:	The namespace
	:type		namespace:	str
	:param		subspace:	The subspace
	:type		subspace:	str

	:returns:	The cached value by name.
	:rtype:		Any
	"""
	try:
		cachename = f'{namespace}:{name}'
		cache = await create_cache(namespace)
		value = await cache.get(cachename)
	except Exception as ex:
		logger.error(f'Exception thrown at get_cache ({cachename}): {ex}')
		return {}

	return value


async def set_cache(data: Any, name: str, namespace: str = 'main'):
	"""
	Sets the cache.

	:param      data:       The data
	:type       data:       Any
	:param      name:       The name
	:type       name:       str
	:param      namespace:  The namespace
	:type       namespace:  str
	"""
	cache_key = f'{namespace}:{name}'
	cache = await create_cache(namespace)
	await cache.set(cache_key, data)
