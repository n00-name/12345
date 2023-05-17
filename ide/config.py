"""Модуль, содержащий класс AppConfig"""

from ide.configuration.config import Config


class AppConfig:
    """Класс, представляющий конфигурацию приложения"""

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.__config = Config.load("config.yml")
        self.appearance = self.__config.appearance

    def __del__(self):
        self.__config.save("config.yml")
