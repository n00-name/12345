"""modules for work with os, PySide"""
from dataclasses import dataclass
import os
from os.path import abspath, basename
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QRadioButton, \
    QVBoxLayout, QWidget, QLabel, QTreeWidgetItem, QTreeWidget

from ide.expansion.file_types import GenericFolder
from ide.registry import Registry
from ide.ui.tabbing import CodeEditorTab


@dataclass
class FoundFragment:
    """
    A data class designed to store a string containing the fragment being searched for
    and a file in which the search is in progress
    """
    line_with_fragment: str
    line_file_path: str


class Search(QMainWindow):
    """Create search window and keep function for start search"""

    searching_files_formats = ("py", "cpp")  # in future: in PRO version/plugin add search in more formats

    def __init__(self, main_window=None):
        super().__init__()
        self.setWindowTitle("Search")
        self.resize(400, 400)
        self.main_window = main_window

        self.file_search = FileSearch(self)
        if self.main_window.project is not None:
            self.project_search = ProjectSearch(self.file_search)
        self.line_edit = LineEdit(self, 100, 12)

        self.warning_label = QLabel()
        self.warning_label.setVisible(False)

        self.file_radio_button = QRadioButton("Search in file")
        self.file_radio_button.setChecked(True)
        self.project_radio_button = QRadioButton("Search in project")
        print(self.main_window.project)
        if self.main_window.project is None:
            self.project_radio_button.setEnabled(False)
            self.project_radio_button.setVisible(False)
        self.horizontal_layout = HLayout()
        self.horizontal_layout.add_widgets([self.file_radio_button, self.project_radio_button])
        self.list_widget = ListWidget()

        self.tree_widget = TreeWidget(window=self)
        self.tree_widget.setEnabled(False)
        self.tree_widget.setVisible(False)

        self.widget = EmptyWidget(self.horizontal_layout)

        widgets = [self.line_edit, self.widget, self.warning_label, self.tree_widget, self.list_widget]
        self.layout = VLayout()
        self.layout.add_widgets(widgets)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.widget_signals_init()

    def widget_signals_init(self):
        """Initializes widget signal functions"""
        self.tree_widget.itemDoubleClicked.connect(self.open_file_from_tree)
        self.project_radio_button.toggled.connect(lambda: self.choose_search(self.line_edit.text()))
        self.tree_widget.itemCollapsed.connect(lambda: self.tree_widget.setFixedHeight(20))
        self.tree_widget.itemExpanded.connect(lambda: self.tree_widget.setFixedHeight(100))
        self.tree_widget.itemChanged.connect(self.tree_widget.item_change_event)

    def choose_search(self, text: str):
        """
        Check RadioButtons and start functions

        :param str text: the searched fragment
        """
        self.list_widget.clear()

        if self.file_radio_button.isChecked():
            self.file_search.scroll = self.file_search.scroll_to_element
            self.tree_widget.setVisible(False)
            self.tree_widget.setEnabled(False)
            self.file_search.search_in_file_manager(text)
        elif self.project_radio_button.isChecked():
            self.file_search.scroll = self.project_search.scroll_to_element
            self.tree_widget.setVisible(True)
            self.tree_widget.setEnabled(True)
            self.project_search.project_search_manager(text)

    def open_file_from_tree(self, item: QTreeWidgetItem, column: int):
        """
        Opens the file at the address corresponding to the element :param item that was clicked

        :param QTreeWidgetItem item: Tree element that stores the relative path to the file in which the search is
                    performed and the name of this file
        :param int column: top-level element index
        """
        if item is not self.tree_widget.topLevelItem(0):
            self.main_window.open_file(abspath(item.whatsThis(column)))

    def list_all_specified_files(self, path: str = None) -> list[str]:

        """
        Get all files, which match Search.searching_files_formats

        :param str path: path to the directory in which the search for the necessary files will be performed
        """

        if path is None:
            path = self.main_window.project.root

        directories = os.listdir(path)

        files = []
        for directory in directories:
            absolute_path = os.path.join(path, directory)
            for file_type in Registry.find_file_types(absolute_path):
                if (absolute_path.split(".")[-1] in Search.searching_files_formats) and (absolute_path not in files):
                    files.append(absolute_path)
                elif isinstance(file_type, GenericFolder) and "venv" not in absolute_path:
                    temp = self.list_all_specified_files(path=absolute_path)
                    for python_file in temp:
                        files.append(python_file)

        return files


class FileSearch:
    """Keep function for search in file"""

    def __init__(self, window: Search):
        self.window = window

    def search_in_file_manager(self, text: str):
        """
        Start search in project

        :param str text: searching fragment
        """

        if len(self.window.main_window.opened_workspace_tabs.keys()) != 0:
            self.window.warning_label.setVisible(False)
            self.window.list_widget.list_widget_form(self.search_in_file(text, True, None))
        else:
            self.window.warning_label.setVisible(True)
            self.window.warning_label.setText("Attention! No open file :(")

    def get_active_tab(self) -> CodeEditorTab:
        """Get open tab"""
        tab_index = self.window.main_window.ui.workspace_tabs.currentIndex()
        return list(self.window.main_window.opened_workspace_tabs.values())[tab_index]

    def get_active_tab_path(self) -> str:
        """Get open tab path"""
        tab_index = self.window.main_window.ui.workspace_tabs.currentIndex()
        return list(self.window.main_window.opened_workspace_tabs.keys())[tab_index]

    def search_in_file(self, text: str, search_flag: bool,
                       path: str = None) -> list[FoundFragment]:

        """
        Search for the received fragment in the received file

        :param str path: desired file path
        :param bool search_flag: Set search mode(True: search in file, False: search in project)
        :param str text: searching fragment

        """
        file = self.transform_text(self.get_text_object_on_path(search_flag, path))

        lines = []

        if not text.startswith(" ") and text:
            for line in file:
                if text in line:
                    lines.append(FoundFragment(line_with_fragment=line, line_file_path=path))

        return lines

    def transform_text(self, tab: CodeEditorTab | list) -> list[str]:
        """
        Converts the getting parameter tab to a list of strings

        :param CodeEditorTab | list tab: An object that stores the text of the searched file
        """
        if isinstance(tab, CodeEditorTab):
            return (tab.text_edit.toPlainText()).split("\n")
        return tab.split("\n")

    def get_text_object_on_path(self, search_flag: bool, path: str = None) -> CodeEditorTab | str:
        """
        Return TextIO or CodeEditorTab object

        :param bool search_flag: set search mode(True: search in file, False: search in project)
        :param str path: path to text file
        """
        if search_flag:
            return self.get_active_tab()

        if path in self.window.main_window.opened_workspace_tabs.keys():
            return self.window.main_window.opened_workspace_tabs[path]

        return open(abspath(path), encoding='utf-8').read()

    def scroll_choose(self, list_item: QListWidgetItem):
        """
        Start need scroll function depending on radio button

         :param QListWidgetItem list_item: an element that stores a string with the desired fragment and the path
         to the file of this string
         """
        if self.window.file_radio_button.isChecked():
            self.scroll_to_element(list_item)
        elif self.window.project_radio_button.isChecked():
            self.window.project_search.scroll_to_element(list_item)

    def scroll_to_element(self, list_item: QListWidgetItem):
        """
        Scrolls the viewport to the given line

        :param list_item: store the line containing the searched fragment
        """
        if list_item.whatsThis() == "":
            key = self.get_active_tab_path()
        else:
            key = list_item.whatsThis()

        if not (self.window.main_window.opened_workspace_tabs[key]).text_edit.find(list_item.text()):
            (self.window.main_window.opened_workspace_tabs[key]).text_edit.find(
                list_item.text(), QTextDocument.FindFlag.FindBackward)


class ProjectSearch:
    """Keep function for search in project"""

    def __init__(self, file_search_object: FileSearch):
        self.file_search_object = file_search_object

    def project_search_manager(self, text: str):
        """
        If there are open files start project search

        :param str text: the searched fragment
        """
        if len(self.file_search_object.window.main_window.list_all_python_files()) == 0:
            self.file_search_object.window.warning_label.setVisible(True)
            self.file_search_object.window.warning_label.setText("Attention! No python files in current project :|")
            self.file_search_object.window.tree_widget.setVisible(False)
            self.file_search_object.window.tree_widget.setEnabled(False)
        else:
            self.file_search_object.window.warning_label.setVisible(False)
            self.project_search(text)

    def project_search(self, text: str):
        """
        start search in project

        :param str text: searching fragment
        """
        project_file_path = self.path_list_form()
        for path in project_file_path:
            data = self.file_search_object.search_in_file(text, False, path)
            self.file_search_object.window.list_widget.list_widget_form(data)

    def scroll_to_element(self, List_item: QListWidgetItem):
        """
        Scroll to searching fragment

        :param str List_item: object that stores information about a fragment
        """
        self.file_search_object.window.main_window.open_file(List_item.whatsThis())
        self.file_search_object.scroll_to_element(List_item)

    def path_list_form(self) -> list[str]:
        """Generates a list of project files in which the fragment is searched"""

        paths = []

        for obj in self.file_search_object.window.tree_widget.get_all_children():
            if obj.checkState(0) == Qt.CheckState.Checked:
                paths.append(obj.whatsThis(0))

        return paths


class LineEdit(QLineEdit):
    """Line edit class"""

    def __init__(self, parent: Search, x_cord: int, y_cord: int):
        super().__init__(parent=parent)
        self.setPlaceholderText("Enter something")
        self.move(x_cord, y_cord)


class ListWidget(QListWidget):
    """List widget class"""

    def __init__(self):
        super().__init__()
        self.set_stylesheet()

    def list_widget_form(self, lines: list[FoundFragment]):
        """
        Form list of lines containing searching fragment

        :param list[FoundFragment] lines: list of lines containing searching fragment
        """

        for line in lines:
            item = QListWidgetItem(line.line_with_fragment, self)
            item.setWhatsThis(line.line_file_path)
            item.setToolTip(line.line_file_path)

    def set_stylesheet(self):
        """Set style sheet for List Widget"""
        self.setStyleSheet("QListWidget"
                           "{"
                           "border : 1px solid black;"
                           "font-size: 15px;"
                           "}"
                           "QListView::item"
                           "{"
                           "border-bottom: 1px solid gray;"
                           "padding: 1px 0px;"
                           "}"
                           )


class TreeWidgetItem(QTreeWidgetItem):
    def __init__(self, parent):
        super().__init__(parent)
        self.is_called_in_parent: bool = False


class TreeWidget(QTreeWidget):
    """Tree widget class"""

    def __init__(self, window: Search):
        super().__init__()
        if window.main_window.project is None:
            return
        self.search_window = window
        self.setup_widget()
        self.add_items()

    def setup_widget(self):
        """Setup tree widget"""
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setFixedHeight(20)
        self.setStyleSheet("QTreeWidget { border : 0 px }")

    def add_items(self):
        """Setup child elements"""
        top_level_item = TreeWidgetItem(self)
        top_level_item.setText(0, "Files")
        top_level_item.setCheckState(0, Qt.CheckState.Checked)
        for path in self.search_window.list_all_specified_files():
            item = TreeWidgetItem(top_level_item)
            item.setText(0, self.path_parsing(path))
            item.setWhatsThis(0, path)
            item.setCheckState(0, Qt.CheckState.Checked)

    def path_parsing(self, path: str) -> str:
        """
        create name for child element

        :param str path: file path
        """
        root_path = self.search_window.main_window.project.root
        root_name = basename(root_path)
        path = path[(len(self.search_window.main_window.project.root) - len(root_name)):]
        return path

    def get_all_children(self) -> list[TreeWidgetItem]:
        """get tree widget child element"""

        children = []

        item = self.search_window.tree_widget.topLevelItem(0)

        for i in range(item.childCount()):
            children.append(item.child(i))

        return children

    def item_change_event(self, change_element: TreeWidgetItem):
        """
        Checks the state of elements

        :param TreeWidgetItem change_element: element which was changed
        """
        if change_element.is_called_in_parent:
            change_element.is_called_in_parent = False
            return

        if change_element.text(0) == "Files":
            for child in self.get_all_children():
                child.is_called_in_parent = True
                child.setCheckState(0, change_element.checkState(0))

        self.search_window.choose_search(self.search_window.line_edit.text())


class HLayout(QHBoxLayout):
    """Horizontal Layout widget"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_widgets(self, widgets: list[QWidget]):
        """
        Set widget for horizontal layout

        :param list[QWidget] widgets: list with widgets, which need to add on horizontal layout
        """
        for widget in widgets:
            self.addWidget(widget)


class VLayout(QVBoxLayout):
    """Vertical Layout widget"""

    def __init__(self):
        super().__init__()

    def add_widgets(self, widgets):
        """
        Set widget for vertical layout

        :param list[QWidget] widgets: list with widgets, which need to add on vertical layout
        """
        for widget in widgets:
            self.addWidget(widget)


class EmptyWidget(QWidget):
    """Empty widget for set central widget"""

    def __init__(self, layout):
        super().__init__()
        self.setLayout(layout)
