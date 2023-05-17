"""тестовый код"""
import bisect
import platform
import shutil
from typing import Optional

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QProcess
from PySide6.QtGui import QColor, QSyntaxHighlighter
from PySide6.QtWidgets import QApplication, QPushButton, QTextEdit

from ide.logs import logger


class TerminalHighlighter(QSyntaxHighlighter):
    """
    Class for terminal syntax highlighting

    TODO: ansi colors
    """
    STDIN_COLOR = QColor("Green")
    STDOUT_COLOR = QColor("Gray")
    STDERR_COLOR = QColor("Red")

    def __init__(self, text_edit: "TerminalTextEdit"):
        super().__init__(text_edit.document())
        self.text_edit = text_edit
        self.output_indexes = []

    def highlightBlock(self, text):
        """
        Get's called when some text in file is updated and applies highlighting to it
        """
        block = self.currentBlock()
        while block.text() != text:
            block = block.previous()
        index = bisect.bisect_right(self.output_indexes, block.position(), key=lambda x: x[0]) - 1
        if index == -1:
            return
        right_position = min(block.position() + len(text), self.output_indexes[index][1]) - block.position()
        self.setFormat(0, right_position, self.output_indexes[index][2])
        self.setFormat(right_position, len(text) - right_position, self.STDIN_COLOR)


class TerminalTextEdit(QTextEdit):
    """
    Class making an interactive terminal process inside QTextEdit
    """
    ENCODING = {
        "Windows": "cp866",
        "Linux": "utf-8",
        "Darwin": "utf-8"
        }.get(platform.system())
    ENDL = {
        "Windows": "\r\n",
        "Linux": "\n",
        "Darwin": "\n"
        }.get(platform.system())

    def get_terminal(self):
        terminals = {
            "Windows": [("powershell",), ("cmd",)],
            "Linux": [("bash", "-i")],
            "Darwin": [("bash", "-i")]
            }.get(platform.system(), [])

        for command, *args in terminals:
            if shutil.which(command) is not None:
                logger.info(f"Using {command} located in {shutil.which(command)} as terminal")
                return command, args
        raise LookupError("Terminal was not found")

    def __init__(
        self, parent, *, python_run_command: Optional[str] = None, cwd: Optional[str] = None,
        run_button: Optional[QPushButton] = None
            ):
        super().__init__(parent)
        self.highlighter = TerminalHighlighter(self)
        self.selectionChanged.connect(self.selection_changed)
        self.run_button = run_button

        if platform.system() == "Linux":
            self.highlighter.STDERR_COLOR = QColor(
                "Gray"
                )  # Disable stderr color on linux until we fix a problem twith terminal
        self.blocked_to = -1
        self.command = ""
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.terminate()
        self.is_finished = False
        if cwd:
            self.process.setWorkingDirectory(cwd)
            print(cwd, self.process.workingDirectory())
        if python_run_command:
            exe, *args = python_run_command.split()
            self.process.finished.connect(self.finished)
        else:
            exe, args = self.get_terminal()
        self.process.setProgram(exe)
        self.process.setArguments(args)
        self.process.start()

    def handle_stdout(self):
        """
        Activates when standart output comes from process
        """
        data = self.process.readAllStandardOutput()
        self.add_blocked_text(bytes(data).decode(self.ENCODING))

    def handle_stderr(self):
        """
        Activates when error output comes from process
        """
        data = self.process.readAllStandardError()
        self.add_blocked_text(bytes(data).decode(self.ENCODING),
                              color=self.highlighter.STDERR_COLOR)

    def keyPressEvent(self, event):
        """
        Does some actions to make it more terminal-like

        1. if user is trying to clear or input text in blocked area - ignore event
        2. If event presses arrow when file is in ReadOnly because of selection -
            make it not ReadOnly
        3. If user presses return (enter) - send user input to terminal

        * Resize on ctrl + wheel
        """
        position = self.textCursor().positionInBlock()
        if event.key() == QtCore.Qt.Key_Backspace and position <= self.blocked_to:
            return
        if (event.key() == QtCore.Qt.Key_Delete or event.text()) and position < self.blocked_to:
            return
        if self.isReadOnly() and event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Up,
                                                 QtCore.Qt.Key_Right, QtCore.Qt.Key_Down):
            self.setReadOnly(False)
        if event.key() == QtCore.Qt.Key_Return:
            cursor = self.textCursor()
            cursor.setPosition(len(self.toPlainText()))
            self.command = self.textCursor().block().text()[max(self.blocked_to, 0):]
            self.process.write((self.command + self.ENDL).encode(self.ENCODING))
            self.blocked_to = -1
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier:
            (self.zoomIn if event.angleDelta().y() > 0 else self.zoomOut)()
        else:
            super().wheelEvent(event)

    def add_blocked_text(self, text, color=TerminalHighlighter.STDOUT_COLOR):
        """
        Add text inside textedit, make it readable only, move cursor in the end
        """
        if text.startswith(self.command):
            text = text[len(self.command):]
            self.command = ""
        begin = self.textCursor().position()
        self.insertPlainText(text)
        end = self.textCursor().position()
        if self.highlighter.output_indexes and begin == self.highlighter.output_indexes[-1][1]:
            self.highlighter.output_indexes[-1] = (self.highlighter.output_indexes[-1][0],
                                                   end, color)
        else:
            self.highlighter.output_indexes.append((begin, end, color))
        self.blocked_to = self.textCursor().positionInBlock()
        self.moveCursor(QtGui.QTextCursor.End)
        block = self.document().lastBlock()
        for _ in range(text.count(self.ENDL) + 1):
            self.highlighter.rehighlightBlock(block)
            block = block.previous()

    def selection_changed(self):
        """
        Checks if selection is safe (and changes ReadOnly value)
        """
        cursor = self.textCursor()
        start = cursor.selectionStart()
        self.setReadOnly(start < self.document().lastBlock().position() + self.blocked_to)

    def finished(self):
        self.add_blocked_text(self.ENDL * 2)
        self.add_blocked_text(f"Program finished with exit code {self.process.exitCode()}",
                              color=QColor("orange"))
        self.setReadOnly(True)
        self.is_finished = True
        self.run_button.setEnabled(True)
