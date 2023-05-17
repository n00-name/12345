from PySide6.QtWidgets import QDialog

from ide.expansion.run_profiles import RunProfile
from ide.logs import logger

try:
    from data_ui.run_profile import Ui_Dialog
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"run_profile.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.run_profile import Ui_Dialog  # pylint: disable=ungrouped-imports


class RunProfilesDialog(QDialog):
    def __init__(self, editor, project):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.editor = editor
        self.project = project
        self.profiles: list[RunProfile] = project.run_profiles[::]

        self.refresh_profiles()
        self.trigger_profile_selection()

        self.ui.remove_btn.setDisabled(True)
        self.ui.copy_btn.setDisabled(True)

        self.ui.profile_list.clicked.connect(self.trigger_profile_selection)
        self.ui.add_btn.clicked.connect(self.trigger_profile_add)
        self.ui.remove_btn.clicked.connect(self.trigger_profile_remove)
        self.ui.copy_btn.clicked.connect(self.trigger_profile_copy)
        self.ui.env_edit.textChanged.connect(self.trigger_profile_edit)
        self.ui.name_edit.textEdited.connect(self.trigger_profile_edit)
        self.ui.cmd_edit.textEdited.connect(self.trigger_profile_edit)
        self.ui.separate_flag.stateChanged.connect(self.trigger_profile_edit)
        self.ui.button_box.accepted.connect(self.trigger_accepted)
        self.ui.button_box.rejected.connect(self.trigger_rejected)

        logger.info("Opened run profiles list")

        # Do not trigger profile edit until profile selection finishes
        self.profile_edit_mute = False

    def refresh_profiles(self) -> None:
        """Refreshes the run profiles list"""
        sel = self.ui.profile_list.selectedIndexes()[0] \
            if len(self.ui.profile_list.selectedIndexes()) == 1 else None
        self.ui.profile_list.clear()
        for profile in self.profiles:
            self.ui.profile_list.addItem(profile.name)
        if sel is not None:
            self.ui.profile_list.setCurrentIndex(sel)

    def trigger_profile_selection(self) -> None:
        """Utility method. Bound to signal"""
        if len(self.ui.profile_list.selectedIndexes()) == 1:
            self.ui.tabWidget.setVisible(True)
            index = self.ui.profile_list.selectedIndexes()[0]
            profile: RunProfile = self.profiles[index.row()]

            self.profile_edit_mute = True

            self.ui.cmd_edit.setText(profile.command)
            self.ui.name_edit.setText(profile.name)
            self.ui.env_edit.setPlainText(profile.envs)
            self.ui.separate_flag.setChecked(profile.open_in_separate_terminal)
            self.ui.profile_list.setCurrentIndex(index)

            self.profile_edit_mute = False

            self.ui.remove_btn.setDisabled(False)
            self.ui.copy_btn.setDisabled(False)
        else:
            self.ui.tabWidget.setVisible(False)
            self.ui.remove_btn.setDisabled(True)
            self.ui.copy_btn.setDisabled(True)

    def trigger_profile_edit(self) -> None:
        """Utility method. Bound to signal"""

        if not self.profile_edit_mute:
            profile: RunProfile = self.profiles[self.ui.profile_list.selectedIndexes()[0].row()]
            profile.name = self.ui.name_edit.text()
            profile.command = self.ui.cmd_edit.text()
            profile.envs = self.ui.env_edit.toPlainText()
            profile.open_in_separate_terminal = self.ui.separate_flag.isChecked()
            index = self.ui.profile_list.selectedIndexes()[0]
            self.ui.profile_list.takeItem(index.row())
            self.ui.profile_list.insertItem(index.row(), profile.name)
            self.ui.profile_list.setCurrentIndex(index)

    def trigger_profile_add(self) -> None:
        """Utility method. Bound to signal"""
        self.profiles.append(RunProfile("Untitled", "", "", False))
        self.refresh_profiles()

    def trigger_profile_copy(self) -> None:
        """Utility method. Bound to signal"""
        if len(self.ui.profile_list.selectedIndexes()) == 1:
            profile: RunProfile = self.profiles[self.ui.profile_list.selectedIndexes()[0].row()]
            self.profiles.append(RunProfile(profile.name,
                                            profile.command,
                                            profile.envs,
                                            profile.open_in_separate_terminal))
            self.refresh_profiles()

    def trigger_profile_remove(self) -> None:
        """Utility method. Bound to signal"""
        if len(self.ui.profile_list.selectedIndexes()) == 1:
            del self.profiles[self.ui.profile_list.selectedIndexes()[0].row()]
            self.refresh_profiles()
            self.trigger_profile_selection()

    def trigger_accepted(self) -> None:
        """Utility method. Bound to signal. If OK pressed"""
        self.project.run_profiles = self.profiles
        self.project.save_config()
        self.editor.refresh_run_profiles()

    def trigger_rejected(self) -> None:
        """Utility method. Bound to signal. If Cancel pressed"""
