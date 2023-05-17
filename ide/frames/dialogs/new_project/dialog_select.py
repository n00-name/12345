from PySide6.QtWidgets import QDialog

from ide.logs import logger
from ide.registry import Registry

try:
    from data_ui.new_project_select_type import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"new_project_select_type.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.new_project_select_type import Ui_Dialog  # pylint: disable=ungrouped-imports


class NewProjectSelectDialog(QDialog):
    RESULT_CREATE = 0
    RESULT_LEAVE = 1

    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.button_box.accepted.connect(self.trigger_accepted)
        self.ui.button_box.rejected.connect(self.trigger_rejected)

        for gen in Registry.project_generators:
            self.ui.listWidget.addItem(gen.__class__.name)

        self.return_code = NewProjectSelectDialog.RESULT_LEAVE
        self.return_gen = None
        logger.info("Opened new project Type selection dialog")

    def trigger_accepted(self) -> None:
        """Utility method. Bound to signal. If OK pressed"""
        if len(self.ui.listWidget.selectedIndexes()) > 0:
            self.return_code = NewProjectSelectDialog.RESULT_CREATE
            self.return_gen = Registry.project_generators[self.ui.listWidget.selectedIndexes()[0].row()]

    def trigger_rejected(self) -> None:
        """Utility method. Bound to signal. If Cancel pressed"""
        self.return_code = NewProjectSelectDialog.RESULT_LEAVE
        self.return_gen = None
        logger.info("Creating project aborted!")
