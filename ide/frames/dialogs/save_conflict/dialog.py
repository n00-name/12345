from PySide6.QtWidgets import QDialog

try:
    from data_ui.dialog_saveconflict import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports
    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"dialog_saveconflict.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.dialog_saveconflict import Ui_Dialog  # pylint: disable=ungrouped-imports


class SaveConflictDialog(QDialog):
    """
    Dialog window which is opened when saving file has conflicts from outside
    """
    RESULT_SAVE = 0
    RESULT_LEAVE = 1

    def __init__(self, editor, editor_version: str, disk_version: str):
        from ide.ui.tabbing import CodeEditorTab

        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.your_code = CodeEditorTab(editor)
        self.your_code.text_edit.setText(editor_version)
        self.ui.verticalLayout.addWidget(self.your_code)

        self.final_code = CodeEditorTab(editor)
        self.ui.verticalLayout_2.addWidget(self.final_code)

        self.disk_code = CodeEditorTab(editor)
        self.disk_code.text_edit.setText(disk_version)
        self.ui.verticalLayout_3.addWidget(self.disk_code)

        self.ui.accept_yours.clicked.connect(lambda: self.final_code.text_edit.setText(editor_version))
        self.ui.accept_disk.clicked.connect(lambda: self.final_code.text_edit.setText(disk_version))
        self.ui.button_box.accepted.connect(self.trigger_accepted)
        self.ui.button_box.rejected.connect(self.trigger_rejected)

        self.return_code = SaveConflictDialog.RESULT_LEAVE
        self.return_text = ""

    def trigger_accepted(self) -> None:
        """Utility method. Bound to signal. If OK pressed"""
        self.return_code = SaveConflictDialog.RESULT_SAVE
        self.return_text = self.final_code.text_edit.toPlainText()

    def trigger_rejected(self) -> None:
        """Utility method. Bound to signal. If Cancel pressed"""
        self.return_code = SaveConflictDialog.RESULT_LEAVE
        self.return_text = None
