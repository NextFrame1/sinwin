from typing import Dict


class UsersDebug:
	def __init__(self):
		self._users: Dict[str, Dict[str, str]] = {}

	def add_user(self, user_id: str, params: Dict[str, str]):
		self._users[user_id] = params

	def get_user(self, user_id):
		return self._users.get(user_id)

	def renew_param(self, user_id, param_key: str, param_value: str):
		user = self.get_user(user_id)

		if user is None:
			return None

		user[param_key] = param_value

		self._users[user_id] = user
