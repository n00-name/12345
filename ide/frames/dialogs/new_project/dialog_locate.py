import os

from PySide6.QtWidgets import QDialog, QFileDialog

from ide.logs import logger

try:
    from data_ui.new_project_locate import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"new_project_locate.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.new_project_locate import Ui_Dialog  # pylint: disable=ungrouped-imports


class NewProjectLocateDialog(QDialog):
    RESULT_CREATE = 0
    RESULT_LEAVE = 1

    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.project_name_edit.setText("Untitled")
        self.ui.project_path_edit.setText("Untitled")

        self.ui.button_box.accepted.connect(self.trigger_accepted)
        self.ui.button_box.rejected.connect(self.trigger_rejected)

        self.ui.project_name_edit.textEdited.connect(self.trigger_name_edit)
        self.ui.project_path_edit.textEdited.connect(self.trigger_path_edit)
        self.ui.choose_path_btn.clicked.connect(self.trigger_select_path)

        self.return_code = NewProjectLocateDialog.RESULT_LEAVE
        self.return_path = None

        self.name = None

        logger.info("Opened new project Path and Name selection dialog")

    def trigger_select_path(self) -> None:
        """Utility method. Bound to signal"""
        file_path = QFileDialog.getExistingDirectory(self, 'Locate project', os.getcwd())
        if file_path is not None and file_path != "":
            self.ui.project_path_edit.setText(os.path.join(file_path, self.ui.project_name_edit.text()))
            self.trigger_path_edit()

    def trigger_name_edit(self) -> None:
        """Utility method. Bound to signal"""
        path, _ = os.path.split(self.ui.project_path_edit.text())
        self.ui.project_path_edit.setText(os.path.join(path, self.ui.project_name_edit.text()))
        if os.path.exists(self.ui.project_path_edit.text()):
            self.ui.button_box.button()[0].setDisabled(True)
        else:
            self.ui.button_box.buttons()[0].setDisabled(False)

    def trigger_path_edit(self) -> None:
        """Utility method. Bound to signal"""
        _, name = os.path.split(self.ui.project_path_edit.text())
        self.ui.project_name_edit.setText(name)
        self.name = name  # for logging purposes
        if os.path.exists(self.ui.project_path_edit.text()):
            self.ui.button_box.buttons()[0].setDisabled(True)
        else:
            self.ui.button_box.buttons()[0].setDisabled(False)

    def trigger_accepted(self) -> None:
        """Utility method. Bound to signal. If OK pressed"""
        self.return_code = NewProjectLocateDialog.RESULT_CREATE
        self.return_path = self.ui.project_path_edit.text()
        logger.info("Created new project. Path: %s; name: %s.", self.return_path, self.name)

    def trigger_rejected(self) -> None:
        """Utility method. Bound to signal. If Cancel pressed"""
        self.return_code = NewProjectLocateDialog.RESULT_LEAVE
        self.return_path = None
        logger.info("Creating project aborted!")
