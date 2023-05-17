import jedi
from jedi.api.classes import Name
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTextEdit

from ide.ui.contextmenus.jedi import AutocompleteMenu, ReferencesMenu


class TextEdit(QTextEdit):
    """Overwrites certain methods from QTextEdit"""

    autocompletion_ignore_keys = (
        Qt.Key_Space,
        Qt.Key_Down,
        Qt.Key_Up,
        Qt.Key_Left,
        Qt.Key_Right,
        Qt.Key_Backspace,
        Qt.Key_Enter,
        Qt.Key_Return,
        Qt.Key_Shift,
        Qt.Key_Control,
        Qt.Key_Alt,
        Qt.Key_CapsLock,
        Qt.Key_Comma,
    )

    def __init__(self, editor):
        super().__init__()
        self.editor = editor

    def keyPressEvent(self, event):
        """Overwrites keyPressEvent for tab key. Replaces tab with 4 spaces.
        Supports auto indentation"""
        if event.key() == Qt.Key_Tab:
            cursor_pos = self.textCursor().position() - 1

            if cursor_pos >= 0:
                text = self.toPlainText()

                space_count = 0

                char = text[cursor_pos]
                i = cursor_pos
                while i >= 0 and char != "\n":
                    if char == " ":
                        space_count += 1
                    else:
                        # Some text detected to the left of the cursor, add default 4 spaces
                        space_count = 0
                        break

                    i -= 1
                    char = text[i]

                if space_count == 0:
                    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.KeyboardModifiers(), "    ")
                else:
                    space_count = (space_count // 4 + 1) * 4 - space_count
                    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.KeyboardModifiers(), " " * space_count)

            else:
                event = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.KeyboardModifiers(), "    ")

        # Auto indentation
        elif event.key() == Qt.Key_Return:
            cursor_pos = self.textCursor().position() - 1

            if cursor_pos >= 0:
                text = self.toPlainText()

                char = text[cursor_pos]
                i = cursor_pos
                while i >= 0 and char == " ":
                    i -= 1
                    char = text[i]

                space_count = 0

                i = cursor_pos
                char = text[i]
                while i >= 0 and char != "\n":
                    if char == " ":
                        space_count += 1
                    else:
                        space_count = 0

                    i -= 1
                    char = text[i]

                if text[cursor_pos] == ":":
                    space_count += 4

                super().keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.KeyboardModifiers(), ""))
                event = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.KeyboardModifiers(), " " * space_count)

        # Remove indentation layers automatically
        elif event.key() == Qt.Key_Backspace:
            cursor_pos = self.textCursor().position() - 1

            if cursor_pos >= 0:
                text = self.toPlainText()

                space_count = 0

                i = cursor_pos
                char = text[i]
                while i >= 0 and char != "\n":
                    if char == " ":
                        space_count += 1
                    else:
                        space_count = 0  # Some text detected to the left of the cursor, don't multiply backspaces
                        break

                    i -= 1
                    char = text[i]

                if space_count != 0 and space_count % 4 == 0:
                    for _ in range(3):
                        super().keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Backspace, Qt.NoModifier))

        super().keyPressEvent(event)

        if event.key() not in self.autocompletion_ignore_keys:
            script = jedi.Script(
                code=self.toPlainText(),
                project=jedi.Project(self.editor.project.root)
            )
            completions = script.complete(
                self.textCursor().blockNumber() + 1,
                self.textCursor().positionInBlock()
            )
            if completions:
                AutocompleteMenu(self, completions).show()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers & QtCore.Qt.ControlModifier:
            cursor = self.cursorForPosition(event.pos())
            script = jedi.Script(
                code=self.toPlainText(),
                project=jedi.Project(self.editor.project.root)
            )
            if modifiers & QtCore.Qt.AltModifier:
                references = script.get_references(
                    cursor.blockNumber() + 1,
                    cursor.positionInBlock(),
                    include_builtins=False
                )
                ReferencesMenu(self, references).show()
            else:
                gotos = script.goto(
                    cursor.blockNumber() + 1,
                    cursor.positionInBlock(),
                    follow_imports=True
                )
                if gotos:
                    goto: Name = gotos[0]
                    if goto.module_path:
                        self.editor.open_file(str(goto.module_path))
                    tab_index = self.editor.ui.workspace_tabs.currentIndex()
                    opened_tab = list(self.editor.opened_workspace_tabs.values())[tab_index]
                    cursor = opened_tab.text_edit.textCursor()
                    cursor.setPosition(0)
                    opened_tab.text_edit.setTextCursor(cursor)
                    opened_tab.text_edit.find(goto.description)
