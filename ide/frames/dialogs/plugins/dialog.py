import os

from PySide6.QtWidgets import QDialog

from ide.logs import logger

try:
    from data_ui.plugins import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"plugins.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.plugins import Ui_Dialog  # pylint: disable=ungrouped-imports

from ide.expansion.plugins import PluginLoader  # pylint: disable=ungrouped-imports


class PluginsDialog(QDialog):
    """
    Dialog window which is opened when saving file has conflicts from outside
    """

    def __init__(self, editor):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.editor = editor
        self.selected = None
        self.selected_enabled = False
        self.do_enable = True

        self.ui.close_btn.clicked.connect(self.trigger_closed)
        self.ui.available_list.itemClicked.connect(self.trigger_available_clicked)
        self.ui.installed_list.itemClicked.connect(self.trigger_installed_clicked)
        self.ui.install_btn.clicked.connect(self.trigger_install_plugin)

        logger.info("Opened plugin installation dialog")

        self.refill_list()
        self.update_sidebar()

    def refill_list(self):
        self.ui.installed_list.clear()
        self.ui.available_list.clear()
        for plugin in self.editor.app.config.plugins.enabled:
            self.ui.installed_list.addItem(plugin)
        for plugin in os.listdir("plugins"):
            if os.path.exists(os.path.join("plugins", plugin, "__init__.py")):
                if plugin not in self.editor.app.config.plugins.enabled:
                    self.ui.available_list.addItem(plugin)

    def update_sidebar(self):
        if self.selected is None:
            self.ui.sidebar.setVisible(False)
        elif self.selected_enabled:
            self.ui.sidebar.setVisible(True)
            self.ui.install_btn.setText("Disable")
            self.do_enable = False
            plugin_adapter = PluginLoader.load_plugin(self.selected, os.path.join("plugins", self.selected))
            self.ui.plugin_name_lbl.setText(plugin_adapter.manifest["name"])
            self.ui.plugin_desc_lbl.setText(plugin_adapter.manifest["description"])
        elif not self.selected_enabled:
            self.ui.sidebar.setVisible(True)
            self.ui.install_btn.setText("Enable")
            self.do_enable = True
            plugin_adapter = PluginLoader.load_plugin(self.selected, os.path.join("plugins", self.selected))
            self.ui.plugin_name_lbl.setText(plugin_adapter.manifest["name"])
            self.ui.plugin_desc_lbl.setText(plugin_adapter.manifest["description"])

    def trigger_closed(self) -> None:
        """Utility method. Bound to signal"""
        self.close()

    def trigger_installed_clicked(self) -> None:
        """Utility method. Bound to signal"""
        if len(self.ui.installed_list.selectedItems()) == 1:
            self.selected_enabled = True
            self.selected = self.ui.installed_list.selectedItems()[0].text()
            self.update_sidebar()

    def trigger_available_clicked(self) -> None:
        """Utility method. Bound to signal"""
        if len(self.ui.available_list.selectedItems()) == 1:
            self.selected_enabled = False
            self.selected = self.ui.available_list.selectedItems()[0].text()
            self.update_sidebar()

    def trigger_install_plugin(self) -> None:
        """Utility method. Bound to signal"""
        if self.do_enable:
            self.editor.app.config.plugins.enabled.append(self.selected)
        else:
            self.editor.app.config.plugins.enabled.remove(self.selected)
        self.selected = None
        self.refill_list()
        self.update_sidebar()
