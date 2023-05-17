from jedi.api.classes import Completion
from PySide6 import QtWidgets
from PySide6.QtCore import QEvent
from PySide6.QtGui import QAction, QIcon, QKeyEvent, Qt

from .base_menu import BaseMenu


class AutocompleteMenu(BaseMenu):
    def generate_actions(self):
        self.data: list[Completion]
        for complete in self.data[:5]:
            action = QAction(complete.name_with_symbols, self)
            action.setToolTip(
                complete.description + "\n\n" + (complete.docstring(raw=True) or "No docstring found...")
            )
            action.triggered.connect(self.choose_action)
            action.setIcon(QIcon(f"images/icons/{complete.type}"))
            self.addAction(action)
            self.mapping[complete.name_with_symbols] = complete

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Ignore these keys
        if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_CapsLock):
            self.parent().keyPressEvent(event)
            return

        # Autocompletion menu navigation
        if event.key() == Qt.Key_Down or event.key() == Qt.Key_Up:
            if QtWidgets.QApplication.keyboardModifiers() & Qt.ControlModifier:  # Ctrl + arrow to move caret
                self.hide()
                # Remove ctrl modifier from event
                self.parent().keyPressEvent(QKeyEvent(QEvent.KeyPress, event.key(), Qt.NoModifier))
                return
            super().keyPressEvent(event)
            return

        # Complete word (tab key will do it too)
        if event.key() in (Qt.Key_Return, Qt.Key_Tab, Qt.Key_Enter):
            super().keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.KeyboardModifiers()))
            return

        # Ctrl+. to complete word and insert a dot
        if event.key() == Qt.Key_Period and QtWidgets.QApplication.keyboardModifiers() & Qt.ControlModifier:
            super().keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.KeyboardModifiers()))
            # Remove ctrl modifier from event
            self.parent().keyPressEvent(QKeyEvent(QEvent.KeyPress, event.key(), Qt.NoModifier, "."))
            return

        self.parent().setFocus()
        self.parent().keyPressEvent(event)

    def choose_action(self):
        self.parent().insertPlainText(self.mapping[self.sender().text()].complete)
        if self.mapping[self.sender().text()].type == "function":
            self.parent().insertPlainText("()")
            self.parent().keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.KeyboardModifiers()))
