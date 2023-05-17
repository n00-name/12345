import os

import yaml
from ide.logs import logger

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class ConfigField:
    def __init__(self, data_type: type, data: object):
        self.type = data_type
        self.data = data
        self.default = data

    def load(self, data: object):
        if data is not None:
            self.data = self.type(data)
        else:
            self.data = None

    def save(self) -> object:
        return self.data


class BoolField(ConfigField):
    def __init__(self, data: bool):
        super().__init__(bool, data)


class IntField(ConfigField):
    def __init__(self, data: int):
        super().__init__(int, data)


class FloatField(ConfigField):
    def __init__(self, data: float):
        super().__init__(float, data)


class StringField(ConfigField):
    def __init__(self, data: str):
        super().__init__(str, data)


class ListField(ConfigField):
    def __init__(self, data: list):
        super().__init__(list, data)

    def load(self, data: object):
        assert isinstance(data, (list, tuple))
        if data is not None:
            self.data = list(data)
        else:
            self.data = None


class DictField(ConfigField):
    def __init__(self, data: dict):
        super().__init__(dict, data)

    def load(self, data: object):
        if data is not None:
            if isinstance(data, dict):
                self.data = data
            else:
                self.data = data.__dict__
        else:
            self.data = None


class ConfigSection(dict):
    def __init__(self, **fields):
        super().__init__()
        self.__dict__["fields"] = fields

    @property
    def __dict__(self):
        return self

    def __getattr__(self, item):
        return self.__dict__["fields"][item].data

    def __setattr__(self, key, value):
        self.__dict__["fields"][key].load(value)

    def load(self, data: dict):
        for field_name, field in self.__dict__["fields"].items():
            if isinstance(field, ConfigField):
                if field_name in data:
                    field.load(data[field_name])
                else:
                    field.load(field.default)

    def save(self) -> dict:
        data = {}
        for field_name, field in self.__dict__["fields"].items():
            if isinstance(field, ConfigField):
                data[field_name] = field.save()
        return data


class Config:
    """
    Represents global IDE configuration
    """

    class Mode:
        UNKNOWN = -1
        LIGHT = 0
        PROJECT = 1

    last_state = ConfigSection(
        last_mode=IntField(Mode.UNKNOWN),
        last_project=StringField(None),
        last_opened=ListField([]),
        opened_index=IntField(0)
    )

    misc = ConfigSection(
        recent_files=ListField([])
    )

    editor = ConfigSection(
        use_default_font=BoolField(True),
        font_size=IntField(16),
        font_name=StringField("Consolas"),
    )

    appearance = ConfigSection(
        theme=StringField("qt-auto"),
        scheme=StringField("qt-auto")
    )

    run = ConfigSection(
        in_ide=BoolField(True),
        terminal_choice=StringField("xfce4-terminal")
    )

    plugins = ConfigSection(
        enabled=ListField([])
    )

    @staticmethod
    def get_sections() -> dict[str, ConfigSection]:
        sections = {}
        for name, attr in Config.__dict__.items():
            if isinstance(attr, ConfigSection):
                sections[name] = attr
        return sections

    @staticmethod
    def save(file_path: str) -> None:
        """
        Saves global config to given file
        :param str file_path: path to config file
        """
        config = {}
        sections = Config.get_sections()
        for section_name, section in sections.items():
            config[section_name] = section.save()
        with open(file_path, "w", encoding='utf-8') as config_file:
            config_file.write(yaml.dump(config, Dumper=Dumper, default_flow_style=False))
        logger.info("Saved global config to %s", file_path)

    @staticmethod
    def load(file_path: str):
        """
        Loads global config from given file
        :param str file_path: path to config file
        """
        if not os.path.exists(file_path):
            Config.save(file_path)
        with open(file_path, "r", encoding='utf-8') as config_file:
            config = yaml.load(config_file.read(), Loader=Loader)
        sections = Config.get_sections()
        for section_name, section in sections.items():
            if section_name in config:
                section.load(config[section_name])
        logger.info("Loaded global config from %s", file_path)
        return Config  # for backwards compatibility
