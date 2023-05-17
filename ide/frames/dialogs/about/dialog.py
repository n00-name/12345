"""
dialog.py - qt dialog actions describer
uses for displaying "About" window
"""

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QCoreApplication as QtApp

from ide.logs import logger
from ide.version import Version

try:
    from data_ui.about import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports
    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"about.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.about import Ui_Dialog  # pylint: disable=ungrouped-imports


class AboutDialog(QDialog):
    """
    Using for specifying content and interactions in "About" window
    """

    def __init__(self, version_storage: Version) -> None:
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.version_lbl.setText(
            QtApp.translate('Dialog', version_storage.get_version_formatted(), None))
        self.ui.date_lbl.setText(
            QtApp.translate('Dialog', version_storage.get_date_formatted(), None))
        logger.info("Opened about dialog")
        self.ui.ok_btn.clicked.connect(self.close)
