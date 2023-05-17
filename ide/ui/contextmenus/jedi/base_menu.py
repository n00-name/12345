from PySide6.QtCore import QPoint
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QMenu, QTextEdit


class BaseMenu(QMenu):
    def __init__(self, parent: QTextEdit, data: list):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid #000;")
        self.setFixedWidth(470)
        self.data = data
        self.mapping = {}
        self.generate_actions()
        screen_pos_rect = parent.mapToGlobal(QPoint(0, 0))
        cursor_rect = parent.cursorRect()
        self.setActiveAction(self.actions()[0])
        self.move(screen_pos_rect.x() + cursor_rect.x(), screen_pos_rect.y() + cursor_rect.bottom())
        self.setFocus()
        self.setToolTipsVisible(True)

    def generate_actions(self):
        raise NotImplementedError

    def choose_action(self):
        raise NotImplementedError

    def focusOutEvent(
                self,
                event: QKeyEvent  # pylint: disable=unused-argument
            ):
        self.close()
