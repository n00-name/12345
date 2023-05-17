import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget

from ide.registry import Registry


class FileTreeItem(QTreeWidgetItem):
    @staticmethod
    def hook_into_tree(tree: QTreeWidget):
        tree.itemExpanded.connect(FileTreeItem._on_item_expanded)

    @staticmethod
    def _on_item_expanded(item: QTreeWidgetItem):
        if isinstance(item, FileTreeItem):
            item.refresh_self()

    def __init__(self, path: str, show_full_path=False, checkable=False):
        super().__init__()
        self.path = path
        self.show_full_path = show_full_path
        self.checkable = checkable
        if show_full_path:
            self.setText(0, f"{os.path.split(path)[-1]} ({path})")
        else:
            self.setText(0, os.path.split(path)[-1])

        file_types = Registry.find_file_types(path)
        if len(file_types) < 1:
            raise ValueError(f"File {path} was not recognized")
        self.file_type = file_types[0]
        if self.file_type.icon:
            self.setIcon(0, QIcon(self.file_type.icon))

        self.child_files_added: list[FileTreeItem] = []
        self.child_file_paths_added: list[str] = []

        if os.path.isdir(self.path):
            self.temp_item = QTreeWidgetItem()
            self.addChild(self.temp_item)
            if self.checkable:
                self.temp_item.setFlags(self.temp_item.flags() | Qt.ItemFlag.ItemIsUserCheckable |
                                        Qt.ItemFlag.ItemIsAutoTristate)
                self.temp_item.setCheckState(0, Qt.CheckState.Unchecked)
        elif self.checkable:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            self.setCheckState(0, Qt.CheckState.Unchecked)

        self.is_populated = False

    def refresh_self(self) -> None:
        if not self.is_populated:
            self.removeChild(self.temp_item)

        if not os.path.exists(self.path):
            if self.parent() is not None:
                if self.path in self.parent().child_file_paths_added:
                    self.parent().child_file_paths_added.remove(self.path)
                if self in self.parent().child_files_added:
                    self.parent().child_files_added.remove(self)
                self.parent().removeChild(self)
            return

        if os.path.isdir(self.path):
            if self.checkable:
                self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable |
                              Qt.ItemFlag.ItemIsAutoTristate)
                self.setCheckState(0, Qt.CheckState.Unchecked)
            for child_file_path in os.listdir(self.path):
                if child_file_path not in self.child_file_paths_added:
                    child_tree_item = FileTreeItem(os.path.join(self.path, child_file_path),
                                                   checkable=self.checkable)
                    self.addChild(child_tree_item)
                    self.child_files_added.append(child_tree_item)
                    self.child_file_paths_added.append(child_file_path)
        elif self.checkable:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            self.setCheckState(0, Qt.CheckState.Unchecked)
        self.is_populated = True

    def refresh(self) -> None:
        """
        Recursively refreshes the tree.
        Deletes deleted files, adds new files.
        """
        if not self.is_populated:
            self.takeChildren()

        if not os.path.exists(self.path):
            if self.parent() is not None:
                if self.path in self.parent().child_file_paths_added:
                    self.parent().child_file_paths_added.remove(self.path)
                if self in self.parent().child_files_added:
                    self.parent().child_files_added.remove(self)
                self.parent().removeChild(self)
            return

        if os.path.isdir(self.path):
            if self.checkable:
                self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable |
                              Qt.ItemFlag.ItemIsAutoTristate)
                self.setCheckState(0, Qt.CheckState.Unchecked)
            for child_file_path in os.listdir(self.path):
                if child_file_path not in self.child_file_paths_added:
                    child_tree_item = FileTreeItem(os.path.join(self.path, child_file_path),
                                                   checkable=self.checkable)
                    self.addChild(child_tree_item)
                    self.child_files_added.append(child_tree_item)
                    self.child_file_paths_added.append(child_file_path)
                    child_tree_item.refresh()

            for child_tree_item in self.child_files_added:
                child_tree_item.refresh()
        elif self.checkable:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            self.setCheckState(0, Qt.CheckState.Unchecked)
        self.is_populated = True

    def get_checked(self) -> list[str]:
        checked = []
        if self.checkState(0).Checked or self.checkState(0).PartiallyChecked:
            checked.append(self.path)
            if os.path.isdir(self.path) and not self.is_populated and self.checkState(0).Checked:
                for root, _, files in os.walk(self.path):
                    for file in files:
                        checked.append(os.path.join(root, file))
            else:
                for child in self.child_files_added:
                    checked.extend(child.get_checked())
        print(checked)
        return checked

    def check(self, path: str | None = None) -> None:
        path_components = os.path.normpath(path).split(os.sep)
        for child_file in self.child_files_added:
            if os.path.abspath(child_file.path) == os.path.abspath(path_components[0]):
                if len(path_components) == 1:
                    child_file.check()
                else:
                    child_file.check(os.path.join(*(path_components[1:])))
                return

    def expand_to_file(self, path: str | None = None, mode: bool = True) -> None:
        self.setExpanded(mode)
        for item in self.child_files_added:
            if item.path == path:
                return
            if path.startswith(item.path):
                item.expand_to_file(path, mode)
                return
