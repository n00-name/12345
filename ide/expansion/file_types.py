import os

from ide.ui.tabbing import ImageEditorTab


class FileType:
    """
    Represents a file type
    """

    id: str
    """Provides a text identifier of that file type"""

    # TODO: define what image class will be used and correct annotation below
    icon: ... = None
    """Returns icon for that file type"""

    do_custom_open: bool = False
    """States whether or not the file should be opened by IDE or in somewhat other way."""

    def applies(self, file_path: str) -> bool:
        """
        Checks whether the file belongs to given type
        :param str file_path: path to file that will be checked
        """

    # TODO: define editor window class
    def custom_open(self, editor, file_path: str) -> None:
        """
        Opens given file in given editor. Called when file of
        that type is opened, but do_custom_open is set to True
        :param editor: editor window
        :param str file_path: path to target file
        """

    # TODO: define editor window and context menu classes
    def setup_context_menu(self, editor, menu, context_file: str, context_project) -> None:
        """
        Creates context menu items based on available actions for that file type
        :param editor: editor window
        :param menu: context menu
        :param str context_file: file, for which the menu should be generated
        :param Project context_project: current project
        """


class GenericFile(FileType):
    id = "generic_file"

    def applies(self, file_path: str) -> bool:
        return os.path.isfile(file_path)

    def setup_context_menu(self, editor, menu, context_file: str, context_project) -> None:
        from ide.ui.contextmenus.file_menus import DeleteFileAction
        menu.addAction(DeleteFileAction(context_file, editor))


class GenericFolder(FileType):
    id = "generic_folder"
    icon = "images/icons/folder.png"

    def applies(self, file_path: str) -> bool:
        return os.path.isdir(file_path)

    def setup_context_menu(self, editor, menu, context_file: str, context_project) -> None:
        from ide.ui.contextmenus.file_menus import DeleteFileAction, NewFileAction, NewFolderAction
        from PySide6.QtWidgets import QMenu
        new_menu = QMenu()
        new_menu.setTitle("New...")
        new_menu.addAction(NewFileAction(context_file, editor))
        new_menu.addAction(NewFolderAction(context_file, editor))
        menu.addMenu(new_menu)
        menu.addAction(DeleteFileAction(context_file, editor))


class GenericLink(FileType):
    id = "generic_link"

    def applies(self, file_path: str) -> bool:
        return os.path.islink(file_path)


class PythonFile(GenericFile):
    id = "python_file"
    icon = "images/icons/module.png"

    def applies(self, file_path: str) -> bool:
        return super().applies(file_path) and file_path.endswith(".py")


class CppFile(GenericFile):
    id = "cpp_file"
    icon = "images/icons/cpp.png"

    def applies(self, file_path: str) -> bool:
        return super().applies(file_path) and file_path.endswith(".cpp")


class TxtFile(GenericFile):
    id = "txt_file"
    icon = "images/icons/txt.png"

    def applies(self, file_path: str) -> bool:
        return super().applies(file_path) and file_path.endswith(".txt")


class ImageFile(GenericFile):
    id = "image_file"
    do_custom_open = True
    icon = "images/icons/image.png"

    def applies(self, file_path: str) -> bool:
        return super().applies(file_path) and file_path.endswith((".png", ".jpg", ".jpeg"))

    def custom_open(self, editor, file_path: str) -> None:
        heading = file_path.split("/")[-1]
        tab = ImageEditorTab(file_path)
        editor.open_tab_raw(file_path, heading, tab)
        if file_path in editor.app.config.misc.recent_files:
            editor.app.config.misc.recent_files.remove(file_path)
        editor.app.config.misc.recent_files.insert(0, file_path)


class VideoFile(GenericFile):
    id = "video_file"
    icon = "images/icons/video.png"

    def applies(self, file_path: str) -> bool:
        return super().applies(file_path) and file_path.endswith((".mp4", "avi", ".mkv"))
