from PySide6.QtWidgets import QDialog
from ide.logs import logger

try:
    from data_ui.new_project_setup import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports
    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"new_project_setup.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.new_project_setup import Ui_Dialog  # pylint: disable=ungrouped-imports

from ide.ui.forms import FormTab  # pylint: disable=ungrouped-imports


class NewProjectSetupDialog(QDialog):
    RESULT_CREATE = 0
    RESULT_LEAVE = 1

    def __init__(self, forms: list):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.button_box.accepted.connect(self.trigger_accepted)
        self.ui.button_box.rejected.connect(self.trigger_rejected)

        self.form_tabs = {}
        self.forms = forms
        for form in self.forms:
            self.form_tabs[form.id] = FormTab(form)
            self.ui.tabs.addTab(self.form_tabs[form.id], "")
            self.ui.tabs.setTabText(self.ui.tabs.count() - 1, form.name)

        self.return_code = NewProjectSetupDialog.RESULT_LEAVE
        self.return_data = None
        logger.info("Opened new project Interpreter selection dialog")

    def trigger_accepted(self) -> None:
        """Utility method. Bound to signal. If OK pressed"""
        sections = {}
        for form_id, tab in self.form_tabs.items():
            sections[form_id] = tab.form.to_dict()
        self.return_code = NewProjectSetupDialog.RESULT_CREATE
        self.return_data = sections

    def trigger_rejected(self) -> None:
        """Utility method. Bound to signal. If Cancel pressed"""
        self.return_code = NewProjectSetupDialog.RESULT_LEAVE
        self.return_data = None
        logger.info("Creating project aborted!")
