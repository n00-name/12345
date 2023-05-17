"""
This module implements an Integrated Development Environment (IDE) application
that allows users to create and edit source code files. The IDE supports various
programming languages and provides a range of features to enhance productivity.

The application class `Application` is the main entry point for the IDE. It loads
plugins, registers file types, and runs the application.
"""

import os.path
import sys
from typing import Optional

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

from ide.expansion.file_types import GenericFile, GenericFolder, GenericLink, \
    PythonFile, CppFile, TxtFile, ImageFile, VideoFile
from ide.expansion.theme import Theme, QTAutoTheme, LightTheme, DarkTheme
from ide.logs import logger
from ide.configuration.config import Config
from ide.frames.editor.window import EditorWindow
from ide.frames.welcome.window import WelcomeWindow
from ide.registry import Registry
from ide.expansion.project import EmptyProjectGenerator, PythonProjectGenerator
from ide.expansion.plugins import PluginLoader, GlobalPlugin, PluginAdapter
from ide.version import Version


class Application(QApplication):
    """
    Represents the IDE application
    """

    def __init__(self, argv):
        super().__init__(argv)
        self.config = {}
        font_id = QFontDatabase.addApplicationFont(":/fonts/fonts/JetBrainsMono-2.304/"
                                                   "fonts/ttf/JetBrainsMonoNL-Regular.ttf")
        self.default_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.default_font = None

        self.editors: list[EditorWindow] = []
        self.welcome: Optional[WelcomeWindow] = None
        self.current_theme: Optional[Theme] = None
        self.plugins: list[PluginAdapter] = []
        self.ide_path = os.path.abspath("")

        self.config = Config.load("config.yml")
        self.version = Version()
        self.register_core()
        self.load_plugins()

    def register_core(self) -> None:
        """
        Register all application dataclasses
        """
        Registry.register(GenericFile())
        Registry.register(GenericFolder())
        Registry.register(GenericLink())
        Registry.register(PythonFile())
        Registry.register(CppFile())
        Registry.register(TxtFile())
        Registry.register(ImageFile())
        Registry.register(VideoFile())
        Registry.register(QTAutoTheme())
        Registry.register(LightTheme())
        Registry.register(DarkTheme())
        Registry.register(EmptyProjectGenerator())
        Registry.register(PythonProjectGenerator())

    def load_plugins(self) -> None:
        """
        Loads all plugins
        """
        if not os.path.exists("plugins"):
            return
        for plugin_name in self.config.plugins.enabled:
            if not os.path.exists(os.path.join("plugins", plugin_name, "__init__.py")):
                continue
            adapter = PluginLoader.load_plugin(plugin_name,
                                               os.path.join("plugins", plugin_name))
            if isinstance(adapter.plugin, GlobalPlugin):
                adapter.plugin.on_enable()
            for filetype in adapter.plugin.provided_filetypes():
                Registry.register(filetype)
            for generator in adapter.plugin.provided_generators():
                Registry.register(generator)
            for theme in adapter.plugin.provided_themes():
                Registry.register(theme)
            self.plugins.append(adapter)

    def run(self) -> None:
        """
        Run the application
        """
        self.config = Config.load(os.path.join(self.ide_path, "config.yml"))

        self.default_font = QFont(self.default_font_family, self.config.editor.font_size - 6)
        if self.config.editor.use_default_font:
            self.setFont(self.default_font)

        self.current_theme = Registry.get_theme(self.config.appearance.theme)
        if self.current_theme is None:
            logger.error("Theme %s not found", self.config.appearance.theme)
        self.current_theme.on_apply()

        if self.config.last_state.last_mode == Config.Mode.UNKNOWN:
            window = WelcomeWindow(self)
            window.show()
            logger.info("Opened welcome window")
            self.welcome = window
        elif self.config.last_state.last_mode == Config.Mode.LIGHT:
            window = EditorWindow(self, project=None)
            window.show()
            logger.info("Opened project window in light mode")
        elif self.config.last_state.last_mode == Config.Mode.PROJECT:
            if self.config.last_state.last_project is not None:
                window = EditorWindow(self, self.config.last_state.last_project)
                window.show()
                logger.info("Opened project window at %s project", self.config.last_state.last_project)
                self.editors.append(window)
            else:
                raise ValueError("last_state.last_mode in config.yml")

        return_code = self.exec()
        self.config.save(os.path.join(self.ide_path, "config.yml"))
        logger.critical("Closing Application")
        sys.exit(return_code)
