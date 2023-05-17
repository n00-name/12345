import os
from typing import List

from PySide6.QtWidgets import QWidgetAction, QInputDialog
from ide.utils import files
from ide.logs import logger


class DeleteFilesAction(QWidgetAction):
    def __init__(self, context_files: List[str], editor):
        super().__init__(editor)
        self.editor = editor
        self.files = context_files
        self.triggered.connect(self.trigger_action)
        self.setText("Delete")

    def trigger_action(self) -> None:
        """Utility method. Bound to signal"""
        for file in self.files:
            logger.info("Deleting file %s", file)
            os.remove(file)
        self.editor.refresh_file_tree()


class DeleteFileAction(QWidgetAction):
    def __init__(self, context_file: str, editor):
        super().__init__(editor)
        self.editor = editor
        self.file = context_file
        self.triggered.connect(self.trigger_action)
        self.setText("Delete")

    def trigger_action(self) -> None:
        """Utility method. Bound to signal"""
        logger.info("Deleting file %s", self.file)
        files.remove(self.file)
        self.editor.refresh_file_tree()


class NewFileAction(QWidgetAction):
    def __init__(self, context_file: str, editor):
        super().__init__(editor)
        self.editor = editor
        self.file = context_file
        self.triggered.connect(self.trigger_action)
        self.setText("New File")

    def trigger_action(self) -> None:
        """Utility method. Bound to signal"""
        name, check = QInputDialog.getText(self.editor, "New File", "Enter new file name")
        if check:
            target_file = os.path.join(self.file, name)
            logger.info("Creating new file %s", target_file)
            files.mkfile(target_file)
            self.editor.refresh_file_tree()


class NewFolderAction(QWidgetAction):
    def __init__(self, context_file: str, editor):
        super().__init__(editor)
        self.editor = editor
        self.file = context_file
        self.triggered.connect(self.trigger_action)
        self.setText("New Directory")

    def trigger_action(self) -> None:
        """Utility method. Bound to signal"""
        name, check = QInputDialog.getText(self.editor, "New Directory", "Enter new directory name")
        if check:
            target_file = os.path.join(self.file, name)
            logger.info("Creating new directory %s", name)
            files.mkdir(target_file)
            self.editor.refresh_file_tree()
