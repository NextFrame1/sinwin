#!/usr/bin/python3
import json
from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Union

import toml
import yaml


@dataclass
class Secrets:
	"""
	This dataclass describes secrets params.
	"""

	TOKEN: str
	ADMINS_IDS: list = field(default_factory=list)
	SECRET_KEY: str = 'Ant1ehbiPu'
	URL: str = '127.0.0.1:8000'


@dataclass
class RedisConfig:
	host: str
	port: int


@dataclass
class Database:
	"""
	This class describes a database.
	"""

	NAME: str
	USER: str
	PASSWORD: str
	HOST: str


@dataclass
class Config:
	"""
	This class describes a configuration.
	"""

	database: Database
	secrets: Secrets
	redis: RedisConfig
	ALL_MEDIA_DIR: str
	SINWIN_DATA: str


def get_config(config_path: str) -> str:
	"""
	Gets the configuration.

	:param		config_path:		The configuration path
	:type		config_path:		str

	:returns:	The configuration.
	:rtype:		str

	:raises		FileNotFoundError:	If configuration file is don't exists
	"""
	ext = config_path.split('.')[-1]
	config_path = Path(config_path)

	if not config_path.exists():
		raise FileNotFoundError(f"Configuration file {config_path} don't exists")

	if ext == 'ini':
		config = ConfigParser()
		config.read(config_path)
	elif ext == 'yaml':
		with open(config_path, 'r') as fh:
			config = yaml.load(fh, Loader=yaml.FullLoader)
	elif ext == 'toml':
		with open(config_path, 'r') as fh:
			config = toml.loads(fh)
	elif ext == 'json':
		with open(config_path, 'r') as fh:
			config = json.load(fh)

	return config


def load_config(config: dict) -> Tuple[Config, Union[Database, Secrets]]:
	"""
	Loads a configuration.

	:param		config:	 The configuration
	:type		config:	 dict

	:returns:	Config tuple
	:rtype:		Tuple[Config, Union[Database, Secrets]]
	"""

	return Config(
		ALL_MEDIA_DIR=config['DATA']['ALL_MEDIA_DIR'],
		SINWIN_DATA=config['DATA']['SINWIN_DATA'],
		database=Database(
			NAME=config['DATABASE']['NAME'],
			USER=config['DATABASE']['USER'],
			PASSWORD=config['DATABASE']['PASSWORD'],
			HOST=config['DATABASE']['HOST'],
		),
		secrets=Secrets(
			URL=config['SECRETS']['URL'],
			TOKEN=config['SECRETS']['TOKEN'],
			ADMINS_IDS=[
				int(admin_id) for admin_id in config['SECRETS']['ADMINS_IDS'].split(' ')
			],
		),
		redis=RedisConfig(host=config['REDIS']['host'], port=config['REDIS']['port']),
	)
