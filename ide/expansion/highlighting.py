import bisect
import time

from pygments import highlight as pyghighlight
from pygments.formatter import Formatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_all_styles, get_style_by_name
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox, \
    QFormLayout, QGridLayout, QLabel, QPushButton, QScrollArea, QTextEdit, QWidget

from ide.logs import logger
from .highlighting_labels import labels


def highlight(text, lexer, formatter):
    if text == highlight.CACHE["text"] and highlight.CACHE["style"] == str(CustomStyle.styles):
        return highlight.CACHE["result"]
    highlight.CACHE = {"text": text, "style": str(CustomStyle.styles), "result": pyghighlight(text, lexer, formatter)}
    return highlight.CACHE["result"]


highlight.CACHE = {"text": None, "style": None, "result": None}


def hex2QColor(color: str) -> QColor:
    """
    Converts color from hex format to QColor
    """
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return QColor(red, green, blue)


class FormatBlock:
    def __init__(self, position, style, length):
        self.position = position
        self.style = style
        self.length = length

    def __lt__(self, value):
        return self.position < value

    def __gt__(self, value):
        return self.position > value

    def __repr__(self):
        return f"FormatBlock({self.position}, {self.style}, {self.length})"


class QFormatter(Formatter):
    """
    Class for working with highlight styles
    """

    def __init__(self, app):
        Formatter.__init__(self)
        self.styles = {}
        self.data = []
        self.brackets = (None, None)
        if app.config.appearance.scheme == "qt-auto":
            if app.current_theme.is_dark:
                CustomStyle.get_style_by_name("monokai")
            else:
                CustomStyle.get_style_by_name("emacs")
        else:
            CustomStyle.get_style_by_name(app.config.appearance.scheme)
        self.get_style()

    def get_style(self):
        """
        Converts data from Customstyle class and converts it to PySide QTextCharFormat representation
        """
        self.styles = {}
        for token, style in CustomStyle.styles.items():
            text_format = QTextCharFormat()
            if style['color']:
                text_format.setForeground(hex2QColor(style['color']))
            if style['bgcolor']:
                text_format.setBackground(hex2QColor(style['bgcolor']))
            if style['bold']:
                text_format.setFontWeight(QFont.Bold)
            if style['italic']:
                text_format.setFontItalic(True)
            if style['underline']:
                text_format.setFontUnderline(True)
            self.styles[token] = text_format

    def format(self, token_source, outfile):
        """
        Function that creates list containing style for each symbol from source string
        """
        pos = 0
        self.data = []

        for token, string in token_source:
            count = string.count("\n")
            for part in string.split("\n"):
                if count:
                    part += "\n"
                    count -= 1
                self.data.append(FormatBlock(pos, self.styles[token], len(part)))
                pos += len(part)

            # Now each symbol's style is recalculated and stored. It can be optimized:
            # 1. You can store not each symbol, but groups of symbols. As token_source gives. Not so hard.
            # ^^ Done. 13sec -> 9sec = x1.3 speedup
            # 2. Highlight not whole file. Highlighter works only with current line really, but without
            # formatting the whole file
            #    something can be lost. For example multiline strings highlighting. Ideas needed.
        self.data.append(FormatBlock(pos, None, 0))


class Highlighter(QSyntaxHighlighter):
    """
    Class for syntax highlighting
    """

    def __init__(self, text_edit: QTextEdit, formatter: QFormatter, language: str):
        self.text_edit = text_edit
        QSyntaxHighlighter.__init__(self, text_edit.document())
        self.lexer = get_lexer_by_name(language)
        self.formatter = formatter
        self.source_keyPressEvent = self.text_edit.keyPressEvent
        self.text_edit.keyPressEvent = self.custom_keyPressEvent
        self.source_mousePressEvent = self.text_edit.mousePressEvent
        self.text_edit.mousePressEvent = self.custom_mousePressEvent

    def custom_mousePressEvent(self, event: QEvent):
        self.source_mousePressEvent(event)
        self.check_brackets()

    def custom_keyPressEvent(self, event: QEvent):
        self.source_keyPressEvent(event)
        self.check_brackets()
        if event.key() in (Qt.Key_QuoteDbl, 39):  # 39 = single quote
            cursor = self.text_edit.textCursor()
            text = cursor.block().text()
            pos = cursor.positionInBlock()
            part = text[pos - 3:pos]
            if part in ("'''", '"""'):
                self.rehighlight()
        elif event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            cursor = self.text_edit.textCursor()
            text = cursor.block().text()
            pos = cursor.positionInBlock()
            if pos != 0 and text[pos - 1] in ("'", '"'):
                self.rehighlight()

    def highlightBlock(self, text):
        """
        Get's called when some text in file is updated and applies highlighting to it
        """
        block = self.currentBlock()
        position = block.position()
        end = position + block.length()
        text = self.document().toPlainText()
        highlight(text, self.lexer, self.formatter)
        data = self.formatter.data
        index = bisect.bisect(data, position) - 1
        while data[index].position < end and data[index].style is not None:
            self.setFormat(data[index].position - position, data[index].length, data[index].style)
            index += 1
        for bracket_pos in self.formatter.brackets:
            if not bracket_pos:
                continue
            block_right = self.currentBlock().position() + self.currentBlock().length()
            if self.currentBlock().position() <= bracket_pos < block_right:
                text_format = QTextCharFormat()
                text_format.setBackground(QColor(["orange", "red"][self.formatter.brackets.count(None) == 1]))
                self.setFormat(bracket_pos - position, 1, text_format)

    def rehighlight(self):
        start = time.perf_counter()
        highlight.CACHE["style"] = None
        super().rehighlight()
        logger.info(f"Full rehighlight took {time.perf_counter() - start:.2f}sec")

    def check_brackets(self):
        """
        Check brackets near the cursor and apply highlighting on them if there are any

        Checking order:
        .( -> ). -> (. -> .)
        where . is cursor position
        """
        text = self.text_edit.toPlainText()
        pos = self.text_edit.textCursor().position()
        current_text = text[pos - 1:pos + 1].ljust(2, " ")
        if "(" not in current_text and ")" not in current_text:
            positions = self.formatter.brackets
            self.formatter.brackets = (None, None)
            self.run_bracketblocks_rehighlight(positions)
            return
        if current_text[1] == "(":
            self.formatter.brackets = (pos, self.find_bracket(text, pos, 1))
        elif current_text[0] == ")":
            self.formatter.brackets = (self.find_bracket(text, pos - 1, -1), pos - 1)
        elif current_text[0] == "(":
            self.formatter.brackets = (pos - 1, self.find_bracket(text, pos - 1, 1))
        elif current_text[1] == ")":
            self.formatter.brackets = (self.find_bracket(text, pos, -1), pos)

        self.run_bracketblocks_rehighlight(self.formatter.brackets)

    def run_bracketblocks_rehighlight(self, positions):
        positions = [x for x in positions if x is not None]
        if not positions:
            return
        block = self.text_edit.document().firstBlock()
        while True:
            for bracket_pos in positions:
                if block.position() <= bracket_pos < block.position() + block.length():
                    self.rehighlightBlock(block)
            if block == self.text_edit.document().lastBlock():
                break
            block = block.next()

    def find_bracket(self, text, index, step):
        """
        Go right through the text and return closing bracket position

        Step is 1 to find closing bracket and -1 to find opening bracket
        """
        brackets = 0
        while 0 <= index < len(text):
            brackets += {"(": 1, ")": -1}.get(text[index], 0)
            if brackets == 0:
                return index
            index += step


class ColorListWidget(QWidget):
    """
    Widget for color settings dialog (Code -> Colors)
    """

    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.styling = {}
        for index, (token, color) in enumerate(CustomStyle.styles.items()):
            foreground_button = QPushButton(self)
            foreground_button.clicked.connect(self.ask_color)
            background_button = QPushButton(self)
            background_button.clicked.connect(self.ask_color)
            bold = QCheckBox("Bold", self)
            italic = QCheckBox("Italic", self)
            underline = QCheckBox("Underline", self)
            self.styling[token] = {
                "foreground_button": foreground_button,
                "background_button": background_button,
                "bold": bold,
                "italic": italic,
                "underline": underline
            }
            label = QLabel(labels[token])
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, index, 0)
            layout.addWidget(foreground_button, index, 1)
            layout.addWidget(background_button, index, 2)
            layout.addWidget(bold, index, 3)
            layout.addWidget(italic, index, 4)
            layout.addWidget(underline, index, 5)
        layout.setSpacing(17)
        self.load_style(CustomStyle.styles.items())
        self.setLayout(layout)

    def load_style(self, source):
        """
        Runs when user selects 'load from ready style'
        Replaces current settings with that style
        """
        for token, value in source:
            button = self.styling[token]["foreground_button"]
            if value["color"]:
                color = "#" + value["color"]
                button.setText(color)
                button.setStyleSheet(f"background-color: {color}")
            else:
                button.setText("")
                button.setStyleSheet("background-color: light gray")

            button = self.styling[token]["background_button"]
            if value["bgcolor"]:
                color = "#" + value["bgcolor"]
                button.setText(color)
                button.setStyleSheet(f"background-color: {color}")
            else:
                button.setText("")
                button.setStyleSheet("background-color: light gray")

            self.styling[token]["bold"].setChecked(bool(value["bold"]))
            self.styling[token]["italic"].setChecked(bool(value["italic"]))
            self.styling[token]["underline"].setChecked(bool(value["underline"]))

    def ask_color(self):
        """
        Asking user to input a color when pressed the button
        """
        color = QColorDialog.getColor()
        if color.isValid():
            color = color.name().upper()
            self.sender().setText(color)
            self.sender().setStyleSheet(f"background-color: {color}")


class ColoringDialog(QDialog):
    """
    Color settings dialog (Code -> Colors)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coloring Settings")
        self.resize(750, 600)
        layout = QFormLayout()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.scroll_area_widget = ColorListWidget()
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.choose_style = QComboBox(self)
        self.choose_style.addItems(get_all_styles())
        self.choose_style.currentTextChanged.connect(self.changed)
        layout.addWidget(QLabel("Load from ready style", self))
        layout.addWidget(self.choose_style)
        layout.addWidget(QLabel("Custom", self))
        layout.addWidget(self.scroll_area)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def changed(self, value):
        """Calls style updating when user loads pre-built theme"""
        self.scroll_area_widget.load_style(get_style_by_name(value))


class CustomStyle:
    """
    This class stores user's current style.
    https://pygments.org/docs/tokens/
    """
    styles = dict(get_style_by_name("monokai"))

    @staticmethod
    def get_style_by_name(name):
        """
        Changes current style by loading pre-built theme
        """
        for key, value in get_style_by_name(name):
            CustomStyle.styles[key] = value

    @staticmethod
    def get_style_by_dict(styling_dict):
        """
        Changes current style by iterating over dictionary (coming from color dialog)
        """
        for token, styling in styling_dict.items():
            CustomStyle.styles[token] = {
                "color": styling["foreground_button"].text().strip("#").lower() or None,
                "bgcolor": styling["background_button"].text().strip("#").lower() or None,
                "bold": styling["bold"].isChecked(),
                "italic": styling["italic"].isChecked(),
                "underline": styling["underline"].isChecked()
            }
