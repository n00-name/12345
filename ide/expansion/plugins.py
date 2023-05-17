import importlib.util
import os.path
from dataclasses import dataclass
from ide.expansion.file_types import FileType
from ide.expansion.project import ProjectGenerator
from ide.expansion.theme import Theme


class AbstractPlugin:
    def on_load(self, *args, **kwargs) -> None:
        """Called when plugin is loaded"""

    def on_enable(self, *args, **kwargs) -> None:
        """Called when plugin is enabled"""

    def on_disable(self, *args, **kwargs) -> None:
        """Called when plugin is disabled"""

    def provided_filetypes(self) -> list[FileType]:
        """Returns a list of provided filetypes"""
        return []

    def provided_generators(self) -> list[ProjectGenerator]:
        """Returns a list of provided project generators"""
        return []

    def provided_themes(self) -> list[Theme]:
        """Returns a list of provided themes"""
        return []


class GlobalPlugin(AbstractPlugin):
    """Represents a plugin"""


class EditorPlugin(AbstractPlugin):
    """Represents a plugin"""

    def on_enable(self, editor) -> None:
        """
        Called when plugin is enabled
        :param editor: target editor
        """

    def on_disable(self, editor) -> None:
        """
        Called when plugin is disabled
        :param editor: target editor
        """
        return None


@dataclass
class PluginAdapter:
    plugin: AbstractPlugin
    manifest: dict


class PluginLoader:
    @staticmethod
    def load_plugin(plugin_name: str, plugin_path: str) -> PluginAdapter:
        spec = importlib.util.spec_from_file_location(
            plugin_name,
            os.path.join(plugin_path, "__init__.py"),
            submodule_search_locations=[plugin_path]
        )
        bundle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bundle)
        manifest = getattr(bundle, "manifest")
        plugin_class = manifest["plugin_class"]
        plugin = plugin_class()
        plugin.on_load()
        return PluginAdapter(plugin, manifest)
