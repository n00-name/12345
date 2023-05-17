import os

from PySide6.QtWidgets import QMainWindow, QFileDialog, QListWidgetItem

from ide.frames.editor.window import EditorWindow
from ide.logs import logger

try:
    from data_ui.welcome import Ui_MainWindow
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"welcome.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.welcome import Ui_MainWindow  # pylint: disable=ungrouped-imports


class WelcomeWindow(QMainWindow):
    """Welcome window"""

    def __init__(self, app: "Application"):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.app = app
        self.ui.version_label.setText("v" + self.app.version.version)

        if self.app.config.last_state.last_project is None:
            self.ui.restore_project_btn.setDisabled(True)

        self.ui.open_btn.clicked.connect(self.trigger_file_opening)
        self.ui.close_btn.clicked.connect(self.trigger_closing)
        self.ui.restore_btn.clicked.connect(self.trigger_restore_last)
        self.ui.recent_files.itemDoubleClicked.connect(self.trigger_last_file_opening)
        self.ui.restore_project_btn.clicked.connect(self.trigger_last_project)
        self.ui.open_project_btn.clicked.connect(self.trigger_project_opening)
        self.ui.new_project_btn.clicked.connect(self.trigger_new_project)

        self.add_recent_files()

    def trigger_file_opening(self) -> None:
        """Utility method. Bound to signal"""
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd())
        logger.info("Opening file %s", file_path)
        if file_path is not None and file_path != "":
            editor = EditorWindow(self.app, project=None, do_restore_last=False)
            editor.show()
            editor.open_file(file_path)
            self.app.editors.append(editor)
            self.close()

    def trigger_last_file_opening(self, item: QListWidgetItem) -> None:
        """Utility method. Bound to signal"""
        editor = EditorWindow(self.app, project=None, do_restore_last=False)
        editor.show()
        editor.open_file(item.text())
        self.app.editors.append(editor)
        self.close()

    def trigger_closing(self) -> None:
        """Utility method. Bound to signal"""
        self.close()

    def trigger_restore_last(self) -> None:
        """Utility method. Bound to signal"""
        editor = EditorWindow(self.app, project=None)
        editor.show()
        self.app.editors.append(editor)
        self.close()

    def trigger_project_opening(self) -> None:
        """Utility method. Bound to signal"""
        file_path = QFileDialog.getExistingDirectory(self, 'Open project', os.getcwd())
        logger.info("Opening project %s", file_path)
        if file_path is not None and file_path != "":
            editor = EditorWindow(self.app, project=file_path)
            editor.show()
            self.app.editors.append(editor)
            self.close()

    def trigger_last_project(self) -> None:
        """Utility method. Bound to signal"""
        editor = EditorWindow(self.app, project=self.app.config.last_state.last_project)
        logger.info("Opening project %s", self.app.config.last_state.last_project)
        editor.show()
        self.app.editors.append(editor)
        self.close()

    def trigger_new_project(self) -> None:
        """Utility method. Bound to signal"""
        from ide.frames.dialogs.new_project import new_project_setup_sequence
        result, _ = new_project_setup_sequence.create_new_project()
        if result is not None:
            self.close()

    def add_recent_files(self):
        """
        Adds all recent files to list widget
        """
        self.ui.recent_files.addItems(self.app.config.misc.recent_files)
