from typing import Any

from aiocache import Cache
from loguru import logger

from app.loader import config


def create_cache(
	name: str, namespace: str = "main", subspace: str = None
) -> Cache.REDIS:
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
	if namespace and subspace:
		name = f"{namespace}:{subspace}:{name}"
	elif namespace and subspace is None:
		name = f"{namespace}:{name}"

	try:
		cache = Cache.REDIS(
			endpoint=config.redis.host,
			port=config.redis.port,
			namespace=namespace,
		)
	except Exception as ex:
		logger.error(f"Error when get_cache: {ex}")
		return None, None

	return cache, name


async def get_cache(name: str, namespace: str = "main", subspace: str = None) -> Any:
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
	cache, cachename = create_cache(name, namespace, subspace)
	value = await cache.get(cachename)

	return value


async def set_cache(
	data: Any, name: str, namespace: str = "main", subspace: str = None
):
	cache, cache_key = create_cache(name, namespace, subspace)
	await cache.set(cache_key, data, ttl=-1)
