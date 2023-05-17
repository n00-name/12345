from jedi.api.classes import Name
from PySide6.QtGui import QAction, QKeyEvent, Qt, QTextCursor

from .base_menu import BaseMenu


class ReferencesMenu(BaseMenu):
    def generate_actions(self):
        self.data: list[Name]
        for reference in self.data[:10]:
            action = QAction(reference.get_line_code(), self)
            action.setToolTip(
                f"In file {reference.module_path or reference.module_name}\n"
                f"Line: {reference.line}, Column: {reference.column}"
            )
            action.triggered.connect(self.choose_action)
            self.addAction(action)
            self.mapping[reference.get_line_code()] = reference

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down, Qt.Key_Up):
            super().keyPressEvent(event)
            return
        self.parent().setFocus()
        self.parent().keyPressEvent(event)

    def choose_action(self):
        goto: Name = self.mapping[self.sender().text()]

        if goto.module_path:
            self.parent().editor.open_file(str(goto.module_path))
        tab_index = self.parent().editor.ui.workspace_tabs.currentIndex()
        opened_tab = list(self.parent().editor.opened_workspace_tabs.values())[tab_index]
        cursor = opened_tab.text_edit.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QTextCursor.Down, n=goto.line - 1)
        opened_tab.text_edit.setTextCursor(cursor)
        opened_tab.text_edit.find(self.sender().text().rstrip("\n"))
