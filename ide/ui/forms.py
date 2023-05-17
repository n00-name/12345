from PySide6.QtWidgets import QWidget, QLineEdit, QPlainTextEdit, QSpinBox, \
    QDoubleSpinBox, QHBoxLayout, QFileDialog, QGridLayout, \
    QLabel, QSizePolicy, QPushButton

from ide.utils.naming import id_to_name


class Form:
    id: str
    name: str
    fields: dict[str, "FormField"] = {}

    def __init__(self, initial_data: dict | None = None):
        self.fields = self.__class__.fields
        self.id = self.__class__.id
        self.name = self.__class__.name
        if initial_data is not None:
            for key, value in initial_data:
                self.fields[key].set_value(value)

    def setup(self) -> None:
        for _, field in self.fields.items():
            field.construct_widgets()

    def to_dict(self) -> dict[str, object]:
        result = {}
        for name, field in self.fields.items():
            result[name] = field.get_value()
        return result


class FormField:
    def __init__(self, initial=None, **kwargs):
        """
        Initializes the form field with some parameters and initial value
        """

    def set_value(self, value) -> None:
        """
        Set field value
        """

    def get_value(self) -> object:
        """
        Get field value
        """

    def get_widget(self) -> QWidget:
        """
        Get field widget
        """

    def construct_widgets(self) -> None:
        raise NotImplementedError()


class LineField(FormField):
    """Represents QLineEdit as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.widget = None
        self.initial = initial

    def set_value(self, value) -> None:
        self.widget.setText(value)

    def get_value(self) -> object:
        return self.widget.text()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QLineEdit()
        if self.initial is not None:
            self.widget.setText(self.initial)


class TextField(FormField):
    """Represents QPlainTextEdit as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.widget = None
        self.initial = initial

    def set_value(self, value) -> None:
        self.widget.setPlainText(value)

    def get_value(self) -> object:
        return self.widget.toPlainText()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QPlainTextEdit()
        if self.initial is not None:
            self.widget.setPlainText(self.initial)


class IntField(FormField):
    """Represents QSpinBox as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.widget = None
        self.initial = initial

    def set_value(self, value) -> None:
        self.widget.setValue(value)

    def get_value(self) -> object:
        return self.widget.value()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QSpinBox()
        if self.initial is not None:
            self.widget.setValue(self.initial)


class RealField(FormField):
    """Represents QDoubleSpinBox as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.initial = initial
        self.widget = None

    def set_value(self, value) -> None:
        self.widget.setValue(value)

    def get_value(self) -> object:
        return self.widget.value()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QDoubleSpinBox()
        if self.initial is not None:
            self.widget.setValue(self.initial)


class FilePathField(FormField):
    """Represents file path as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.button = None
        self.input = None
        self.layout = None
        self.widget = None
        self.initial = initial

    def trigger_path_choose(self):
        file_path, _ = QFileDialog.getOpenFileName(self.widget, "Select file")
        if file_path is not None and file_path != "":
            self.input.setText(file_path)

    def set_value(self, value) -> None:
        self.input.setText(value)

    def get_value(self) -> object:
        return self.input.text()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QWidget()
        self.layout = QHBoxLayout(self.widget)
        self.input = QLineEdit(self.widget)
        self.button = QPushButton(self.widget)
        self.button.setFixedWidth(self.button.height())
        self.button.setMaximumWidth(self.button.height())
        self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.setText("/")
        self.button.clicked.connect(self.trigger_path_choose)
        self.layout.addWidget(self.input)
        self.layout.addWidget(self.button)
        if self.initial is not None:
            self.input.setText(self.initial)


class FolderPathField(FormField):
    """Represents dir path as FormField"""

    def __init__(self, initial=None, **kwargs):
        super().__init__(initial, **kwargs)
        self.button = None
        self.input = None
        self.layout = None
        self.widget = None
        self.initial = initial

    def trigger_path_choose(self):
        file_path = QFileDialog.getExistingDirectory(self.widget, "Select directory")
        if file_path is not None and file_path != "":
            self.input.setText(file_path)

    def set_value(self, value) -> None:
        self.input.setText(value)

    def get_value(self) -> object:
        return self.input.text()

    def get_widget(self) -> QWidget:
        return self.widget

    def construct_widgets(self) -> None:
        self.widget = QWidget()
        self.layout = QHBoxLayout(self.widget)
        self.layout = QHBoxLayout(self.widget)
        self.input = QLineEdit(self.widget)
        self.button = QPushButton(self.widget)
        self.button.setFixedWidth(self.button.height())
        self.button.setMaximumWidth(self.button.height())
        self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.setText("/")
        self.button.clicked.connect(self.trigger_path_choose)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.input)
        if self.initial is not None:
            self.input.setText(self.initial)


class FormTab(QWidget):
    def __init__(self, form: Form):
        super().__init__()
        self.grid = QGridLayout(self)
        self.form = form
        form.setup()
        row = 0
        for field_id, field in form.fields.items():
            print(field_id)
            lbl = QLabel(self)
            lbl.setText(id_to_name(field_id))
            self.grid.addWidget(lbl, row, 0)
            self.grid.addWidget(field.get_widget(), row, 1)
            row += 1
