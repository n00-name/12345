from enum import Enum

from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QWidget


class GutterAnnotation(Enum):
    """Represents annotation on line numbering gutter"""

    COLOR = 0
    TEXT = 1

    def __init__(self, type_: int, data: str | QColor | None = None):
        self.type = type_
        self.data = data


class NumberGutter(QWidget):
    """
    Line numbering left gutter
    Modification of: https://nachtimwald.com/2009/08/15/qtextedit-with-line-numbers/
    """

    def __init__(self, editor, edit=None):
        super().__init__()
        self.edit = edit
        self.app = editor.app
        self.highest_line = 0
        self.gutter_annotations: dict[int, list[GutterAnnotation]] = {}
        self.widest_annotation = ""

    def recalculate_annotations(self):
        """
        Recalculate self.widest_annotation
        """
        for _, annotations in self.gutter_annotations.items():
            for annotation in annotations:
                if annotation.type == GutterAnnotation.TEXT:
                    self.widest_annotation = annotation.data \
                        if len(self.widest_annotation) < len(annotation.data) \
                        else self.widest_annotation

    def add_annotation(self, line: int, annotation: GutterAnnotation) -> None:
        """
        Add annotation on line
        """
        if line in self.gutter_annotations:
            self.gutter_annotations[line].append(annotation)
        else:
            self.gutter_annotations[line] = [annotation]
        if annotation.type == GutterAnnotation.TEXT:
            self.widest_annotation = annotation.data \
                if len(self.widest_annotation) < len(annotation.data) \
                else self.widest_annotation

    def remove_annotation(self, line: int, annotation: GutterAnnotation) -> None:
        """
        Remove specific annotation on specific line
        """
        if line in self.gutter_annotations:
            if annotation in self.gutter_annotations[line]:
                self.gutter_annotations[line].remove(annotation)
        self.recalculate_annotations()

    def remove_annotations(self, line: int | None = None) -> None:
        """
        Remove annotations on line or all
        """
        if line is None:
            self.gutter_annotations = {}
            self.widest_annotation = 0
        else:
            self.gutter_annotations[line] = []
            self.recalculate_annotations()

    def update(self, *args):
        """
        Update width and display
        """
        width_self = self.fontMetrics().boundingRect(str(self.highest_line) + "xy").width()
        width_add = self.fontMetrics().boundingRect(self.widest_annotation).width()
        width = width_self + width_add + 8
        if self.width() != width:
            self.setFixedWidth(width)
        super().update(*args)

    def paintEvent(self, event):
        """
        Paint gutter
        """
        bottom_edit_y = self.edit.verticalScrollBar().value() - 4
        page_bottom = bottom_edit_y + self.edit.viewport().height()
        font_metrics = self.fontMetrics()
        current_block = self.edit.document().findBlock(self.edit.textCursor().position())
        painter = QPainter(self)
        if self.app.config.editor.use_default_font:
            font = self.app.default_font
        else:
            font = QFont(self.app.config.editor.font_name, self.app.config.editor.font_size)
        font.setPixelSize(self.app.config.editor.font_size)
        painter.setFont(font)

        line_count = 0
        block = self.edit.document().begin()
        while block.isValid():
            line_count += 1
            additional_text = ""

            block_top_left_pos = \
                self.edit.document().documentLayout().blockBoundingRect(block).topLeft()

            if block_top_left_pos.y() > page_bottom:
                break

            prev_painter_pen = None
            if block != current_block:
                prev_painter_pen = painter.pen()
                painter.setPen(prev_painter_pen.color().darker())

            if line_count in self.gutter_annotations:
                for annotation in self.gutter_annotations[line_count]:
                    if annotation.type == GutterAnnotation.COLOR:
                        if prev_painter_pen is None:
                            prev_painter_pen = painter.pen()
                        painter.setPen(annotation.data)
                    elif annotation.type == GutterAnnotation.TEXT:
                        additional_text += annotation.data

            painter.drawText(
                self.width() - font_metrics.boundingRect(str(line_count) +
                                                         additional_text).width() - 20,
                round(block_top_left_pos.y()) - bottom_edit_y + font_metrics.ascent(),
                str(line_count) + additional_text
            )

            if prev_painter_pen is not None:
                painter.setPen(prev_painter_pen)

            block = block.next()

        self.highest_line = line_count
        painter.end()

        super().paintEvent(event)
