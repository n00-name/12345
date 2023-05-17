import os.path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTextOption
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from ide.logs import logger

from ide.expansion.highlighting import Highlighter
from ide.expansion.overwritten_qtextedit import TextEdit
from ide.frames.dialogs.save_conflict.dialog import SaveConflictDialog
from ide.ui.line_numbers import NumberGutter


class AbstractWorkspaceTab(QWidget):
    """Base class for all workspace tabs"""

    def __init__(self, identifier):
        super().__init__()
        self.identifier = identifier


class CodeEditorTab(AbstractWorkspaceTab):
    """Represents an opened code editor tab"""

    def __init__(self, identifier, editor):
        super().__init__(identifier)
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.text_edit = TextEdit(editor)
        if editor.app.config.editor.use_default_font:
            self.text_edit.setStyleSheet(f"font-family: \"{editor.app.default_font_family}\"; "
                                         f"font-size: {editor.app.config.editor.font_size}px;")
        else:
            self.text_edit.setStyleSheet(f"font-family: \"{editor.app.config.editor.font_name}\"; "
                                         f"font-size: {editor.app.config.editor.font_size}px;")
        self.text_edit.installEventFilter(self)
        self.text_edit.viewport().installEventFilter(self)
        self.gutter = NumberGutter(editor, self.text_edit)
        self.h_layout.addWidget(self.gutter)
        self.h_layout.addWidget(self.text_edit)

        self.highlighter = Highlighter(self.text_edit, editor.syntax_formatter, "python3")
        self.editor = editor

        self.last_saved_text = None

        option = QTextOption()
        option.setFlags(QTextOption.ShowTabsAndSpaces)
        self.text_edit.document().setDefaultTextOption(option)

    def eventFilter(self, obj, event):
        """Utility method. Updates gutter when needed"""
        if obj in (self.text_edit, self.text_edit.viewport()):
            self.gutter.update()
            return False
        return super().eventFilter(obj, event)

    def set_area_text(self, text: str) -> None:
        """
        Wrapper for `self.text_edit.setText(str)`.
        Also saves text (required for conflict resolving)
        :param str text: text
        """
        self.text_edit.setText(text)
        self.last_saved_text = text

    def save(self) -> None:
        """
        Save code in file under `self.identifier` path.
        If file was modified by another software
        then will ask what to save
        """
        logger.info("Saving file under %s path", self.identifier)
        present_saved_text = None
        if os.path.exists(self.identifier):
            with open(self.identifier, "r", encoding='utf-8') as file:
                present_saved_text = file.read()

        has_conflict = False
        if present_saved_text is not None and self.last_saved_text is not None:
            has_conflict = self.last_saved_text != present_saved_text

        if has_conflict:
            logger.warning("Found save conflicts! Opening save conflicts dialog.")
            conflict_dialog = SaveConflictDialog(self.editor,
                                                 self.text_edit.toPlainText(),
                                                 present_saved_text)
            conflict_dialog.exec()
            print(conflict_dialog.return_code)
            if conflict_dialog.return_code == SaveConflictDialog.RESULT_SAVE:
                with open(self.identifier, "w", encoding='utf-8') as file:
                    file.write(conflict_dialog.return_text)
                print(conflict_dialog.return_text)
                self.set_area_text(conflict_dialog.return_text)
        else:
            with open(self.identifier, "w", encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
            self.last_saved_text = self.text_edit.toPlainText()


class ImageEditorTab(AbstractWorkspaceTab):
    def __init__(self, identifier):
        super().__init__(identifier)
        self.h_layout = QHBoxLayout(self)
        self.label = QLabel(self)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setPixmap(QPixmap(self.identifier).scaled(self.size(), Qt.KeepAspectRatio))
        self.h_layout.addWidget(self.label)
        self.setLayout(self.h_layout)

    def resizeEvent(
                self,
                event  # pylint: disable=unused-argument
            ):
        """
        Changes image size when window size is changed
        """
        self.label.setPixmap(QPixmap(self.identifier).scaled(self.size(), Qt.KeepAspectRatio))
