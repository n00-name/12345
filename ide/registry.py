from ide.expansion.file_types import FileType
from ide.expansion.project import ProjectGenerator
from ide.expansion.theme import Theme


class Registry:
    """Contains all registered dataclasses"""
    file_types: list[FileType] = []
    themes: list[Theme] = []
    run_profile_types: list = []
    project_generators: list[ProjectGenerator] = []

    @staticmethod
    def find_file_types(file_path: str) -> list[FileType]:
        """
        Finds all file types that are applicable to file by given path.
        Note: it sorts it automatically based on order of registration.
        Last registered file type will come first.
        :param str file_path: file to resolve
        """
        applicable = []
        for file_type in reversed(Registry.file_types):
            if file_type.applies(file_path):
                applicable.append(file_type)
        return applicable

    @staticmethod
    def get_project_generator(uid: str) -> None | ProjectGenerator:
        """
        Get registered project generator by id
        :param str uid: identifier
        :return: registered object with given id or None if not found
        """
        for gen in Registry.project_generators:
            if gen.id == uid:
                return gen
        return None

    @staticmethod
    def get_file_type(uid: str) -> None | FileType:
        """
        Get registered file type by id
        :param str uid: identifier
        :return: registered object with given id or None if not found
        """
        for file_type in Registry.file_types:
            if file_type.id == uid:
                return file_type
        return None

    @staticmethod
    def get_theme(uid: str) -> None | Theme:
        """
        Get registered theme by id
        :param str uid: identifier
        :return: registered object with given id or None if not found
        """
        for theme in Registry.themes:
            if theme.id == uid:
                return theme
        return None

    @staticmethod
    def get_run_profile_type(uid: str) -> None | object:
        """
        Get registered run profile type by id
        :param str uid: identifier
        :return: registered object with given id or None if not found
        """
        for run_profile_type in Registry.run_profile_types:
            if run_profile_type.id == uid:
                return run_profile_type
        return None

    @staticmethod
    def register(obj: FileType | Theme | ProjectGenerator) -> None:
        """
        Register object
        :param obj: object
        """
        if isinstance(obj, FileType):
            if obj not in Registry.file_types:
                Registry.file_types.append(obj)
        elif isinstance(obj, Theme):
            if obj not in Registry.themes:
                Registry.themes.append(obj)
        elif isinstance(obj, ProjectGenerator):
            if obj not in Registry.project_generators:
                Registry.project_generators.append(obj)
