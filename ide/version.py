from datetime import datetime
from os import path

import yaml
from yaml.loader import SafeLoader


class Version:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self, version: str = "0", timestamp: int = 0):
        self.version = version
        self.timestamp = timestamp
        self.load()

    def load(self):
        version_file_path = path.abspath(
            path.join(
                path.dirname(__file__),
                '..',
                'version_info.yml'
            )
        )
        with open(version_file_path, encoding='utf-8', ) as file_instance:
            data = yaml.load(file_instance, Loader=SafeLoader)
            self.version = str(data['version'])
            self.timestamp = data['timestamp']

    def get_version(self) -> str:
        return self.version

    def get_version_formatted(self) -> str:
        return f'Version number: {self.get_version()}'

    def get_date(self) -> datetime:
        return datetime.utcfromtimestamp(self.timestamp)

    def get_date_formatted(self) -> str:
        date = self.get_date().strftime('%B %d, %Y')
        return f'Version from: {date}'
