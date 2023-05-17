import os

import autopep8
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtGui import QTextCursor, QIcon
from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QWidgetAction
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QAbstractItemView

from ide.expansion.file_types import PythonFile, GenericFolder
from ide.expansion.plugins import EditorPlugin
from ide.frames.dialogs.plugins.dialog import PluginsDialog
from ide.logs import logger

try:
    from data_ui.editor import Ui_MainWindow
except ImportError:
    from ide.utils.ui_converter import ConvertationRecursive, ScriptOutput  # pylint: disable=ungrouped-imports

    ScriptOutput.logging_mode = True
    ScriptOutput.print("File \"editor.py\" not found in data_ui, starting .ui files conversion "
                       "(probably first application launch)")
    ConvertationRecursive().run()
    from data_ui.editor import Ui_MainWindow  # pylint: disable=ungrouped-imports

from ide.configuration.config import Config  # pylint: disable=ungrouped-imports
from ide.expansion.highlighting import ColoringDialog, CustomStyle, QFormatter
from ide.expansion.project import Project
from ide.expansion.search import Search
from ide.frames.dialogs.run_profiles.dialog import RunProfilesDialog
from ide.registry import Registry
from ide.ui.file_tree_items import FileTreeItem
from ide.ui.tabbing import AbstractWorkspaceTab
from ide.ui.tabbing import CodeEditorTab
from ide.ui.contextmenus.file_menus import DeleteFilesAction
from ide.utils.terminal import TerminalTextEdit
from ide.frames.dialogs.about.dialog import AboutDialog


class EditorWindow(QMainWindow):
    """Editor window"""

    def __init__(self, app: "Application", project, do_restore_last=True):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.opened_workspace_tabs: dict[str, CodeEditorTab] = {}
        self.app = app
        self.dialog = None
        self.syntax_formatter = QFormatter(self.app)
        if project is not None:
            self.project = Project(project)
        else:
            self.project = None
        self.project_tree_item: FileTreeItem = None
        self.previous_expanded = None
        self.ui.project_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.ui.toolbar_about_btn.clicked.connect(self.trigger_open_about_dialog)
        # self.ui.toolbar_about_btn.setIcon(QIcon("images/logo/icon_negative.png"))
        self.code_run_task: None = None  # Used to avoid ShellRunTask cleaning

        self.ui.terminal_edit = TerminalTextEdit(self.ui.bottom_terminal_tab, cwd=self.project and self.project.root)
        self.ui.gridLayout_2.addWidget(self.ui.terminal_edit, 0, 0, 1, 1)

        self.ui.workspace_tabs.tabCloseRequested.connect(self.trigger_close_tab)
        self.ui.workspace_tabs.currentChanged.connect(self.trigger_changing_tabs)
        self.ui.toolbar_run_btn.clicked.connect(self.trigger_file_running)
        self.ui.toolbar_run_btn.setIcon(QIcon("images/icons/play_icon.png"))
        self.ui.project_tree.itemDoubleClicked.connect(self.trigger_file_opening_from_tree)
        self.ui.toolbar_edit_btn.clicked.connect(self.trigger_profile_edit)
        self.ui.toolbar_stop_btn.clicked.connect(self.trigger_process_stop)
        self.ui.toolbar_stop_btn.setIcon(QIcon("images/icons/stop_icon.png"))
        self.ui.toolbar_stop_btn.setEnabled(False)

        if self.project is not None:
            self.restore_last_opened_in_project()
            self.setWindowTitle("Simple.IDE - " + os.path.split(self.project.root)[-1])
            self.load_file_tree()
            self.refresh_run_profiles()
            self.app.config.last_state.last_mode = Config.Mode.PROJECT
            self.app.config.last_state.last_project = project
            self.ui.project_tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.project_tree.customContextMenuRequested.connect(self.trigger_tree_context_menu)
            logger.info("Opened project at %s", self.project.root)
        if self.project is None:
            if do_restore_last:
                self.restore_last_opened()
            self.setWindowTitle("Simple.IDE - Light Edit")
            self.app.config.last_state.last_mode = Config.Mode.LIGHT
            self.app.config.last_state.last_project = project
            self.ui.verticalLayout_2.removeWidget(self.ui.project_tree)
            light_edit_warning = QLabel()
            light_edit_warning.setText("Project tree is unavailable in light mode")
            self.ui.verticalLayout_2.addWidget(light_edit_warning)
            self.ui.h_splitter.moveSplitter(0, 2)
            self.ui.run_profile_box.setDisabled(True)
            self.ui.toolbar_run_btn.setDisabled(True)
            self.ui.toolbar_edit_btn.setDisabled(True)
            logger.warning("You're softlocked in this project... Sorry about that.")

        self.setup_top_menu()

        self.ui.terminal_edit.installEventFilter(self)
        self.ui.run_edit.installEventFilter(self)

        if self.app.config.editor.use_default_font:
            self.ui.run_edit.setStyleSheet(f"font-family: \"{self.app.default_font_family}\"")
        else:
            self.ui.run_edit.setStyleSheet(f"font-family: \"{self.app.config.editor.font_name}\"")

        for plugin in self.app.plugins:
            if isinstance(plugin.plugin, EditorPlugin):
                plugin.plugin.on_enable(self)

        # открытие файла
        shortcut = QShortcut(QKeySequence("Ctrl+o"), self)
        shortcut.activated.connect(self.trigger_file_opening)

        # сохранение файла
        shortcut_save = QShortcut(QKeySequence("Ctrl+s"), self)
        shortcut_save.activated.connect(self.trigger_file_saving)

        # запуск файла
        shortcut_run = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_run.activated.connect(self.trigger_file_running)

        # cоздание нового файла
        shortcut_new_file = QShortcut(QKeySequence("Ctrl+n"), self)
        shortcut_new_file.activated.connect(self.trigger_new_project_creation)

    def color_menu(self):
        dialog = ColoringDialog()
        logger.info("Opened color menu")
        if dialog.exec():
            CustomStyle.get_style_by_dict(dialog.scroll_area_widget.styling)
            self.syntax_formatter.get_style()
            for tab in self.opened_workspace_tabs.values():
                if isinstance(tab, CodeEditorTab):
                    tab.highlighter.rehighlight()

    def reformat_all_files(self) -> None:
        logger.info("Reformatting all files:")
        for file in self.list_all_python_files():
            self.reformat_single_file(path=file)

    def reformat_single_file(self, path) -> None:
        logger.info("Reformatting file %s...", path)
        autopep8.fix_file(
            path,
            options=autopep8.parse_args(['--in-place', '--aggressive', '--aggressive', '--list-fixes']),
        )
        for tab in self.opened_workspace_tabs.values():
            if tab.identifier == path:
                with open(path, "r", encoding='utf-8') as file:
                    new_code = file.read()
                    tab.text_edit.setPlainText(new_code)
                    tab.last_saved_text = new_code
                    if self.app.config.editor.use_default_font:
                        self.ui.run_edit.setStyleSheet(f"font-family: \"{self.app.default_font_family}\";"
                                                       f"font-size {tab.editor.app.config.editor.font_size}px;")
                    else:
                        tab.text_edit.setStyleSheet(f"font-family: \"{tab.editor.app.config.editor.font_name}\"; "
                                                    f"font-size: {tab.editor.app.config.editor.font_size}px;")

    def list_all_python_files(self, path=None) -> list[str]:
        if path is None:
            path = self.project.root

        directories = os.listdir(path)

        python_files = []
        for directory in directories:
            absolute_path = os.path.join(path, directory)
            for file_type in Registry.find_file_types(absolute_path):
                if isinstance(file_type, PythonFile):
                    python_files.append(absolute_path)
                elif isinstance(file_type, GenericFolder) and "venv" not in absolute_path:
                    temp = self.list_all_python_files(path=absolute_path)
                    for python_file in temp:
                        python_files.append(python_file)

        return python_files

    def reformat_current_file(self) -> None:
        for tab in self.opened_workspace_tabs.values():
            if tab.isVisible():
                for file_type in Registry.find_file_types(tab.identifier):
                    if isinstance(file_type, PythonFile):
                        self.reformat_single_file(tab.identifier)

    def refresh_run_profiles(self) -> None:
        """Refreshes run profile combobox"""
        self.ui.run_profile_box.clear()
        for profile in self.project.run_profiles:
            self.ui.run_profile_box.addItem(profile.name, profile)

    def close_editor(self) -> None:
        """
        Safely close the editor. `close` method should be called after it
        """
        logger.info("Closing editor")
        self.trigger_file_saving()

        for plugin in self.app.plugins:
            if isinstance(plugin, EditorPlugin):
                plugin.on_disable(self)

        opened_paths = []
        for tab in self.opened_workspace_tabs.values():
            if isinstance(tab, CodeEditorTab):
                opened_paths.append(tab.identifier)

        if self.project is None:
            self.app.config.last_state.last_opened = opened_paths
            self.app.config.last_state.opened_index = self.ui.workspace_tabs.currentIndex()
        else:
            self.project.config["last_opened"]["files"] = opened_paths
            self.project.config["last_opened"]["index"] = self.ui.workspace_tabs.currentIndex()
            self.project.save_config()
        if self in self.app.editors:
            self.app.editors.remove(self)

        self.ui.terminal_edit.process.kill()
        if isinstance(self.ui.run_edit, TerminalTextEdit):
            self.ui.run_edit.process.kill()

    def search_event(self):
        self.dialog = Search(main_window=self)
        self.dialog.line_edit.textEdited.connect(self.dialog.choose_search)
        self.dialog.list_widget.itemDoubleClicked.connect(self.dialog.file_search.scroll_choose)
        self.dialog.show()

    def closeEvent(
        self,
        event  # pylint: disable=unused-argument
    ) -> None:
        """Listener. Saves everything before closing"""
        logger.info("Saving...")
        self.close_editor()
        if self.dialog is not None:
            if self.dialog.isEnabled():
                self.dialog.close()

    def trigger_tree_context_menu(self, pos) -> None:
        """Utility method. Bound to signal"""
        item: FileTreeItem = self.ui.project_tree.itemAt(pos)
        if item is not None:
            menu = QMenu()

            if len(self.ui.project_tree.selectedItems()) > 1:
                paths = []
                for item in self.ui.project_tree.selectedItems():
                    paths.append(item.path)

                menu.addAction(DeleteFilesAction(paths, self))
            else:
                item.file_type.setup_context_menu(self, menu, item.path, self.project)
            menu.exec_(self.ui.project_tree.viewport().mapToGlobal(pos))

    def trigger_editor_closing(self) -> None:
        """Utility method. Bound to signal"""
        from ide.frames.welcome.window import WelcomeWindow

        self.app.config.last_state.last_mode = Config.Mode.UNKNOWN
        self.close_editor()
        self.app.welcome = WelcomeWindow(self.app)
        self.app.welcome.show()
        self.close()

    def trigger_file_opening(self) -> None:
        print("File opening triggered by Ctrl+O")  # отладочное сообщение
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd())
        logger.info("Trying to open file %s...", file_path)
        if file_path is not None and file_path != "":
            self.open_file(file_path)
            logger.info("File %s was successfully opened", file_path)
        else:
            logger.error("File path is None or Nothing!")

    def trigger_close_tab(self, tab_index) -> None:
        """Utility method. Bound to signal"""
        tab = self.ui.workspace_tabs.widget(tab_index)
        if isinstance(tab, AbstractWorkspaceTab):
            del self.opened_workspace_tabs[tab.identifier]
        if isinstance(tab, CodeEditorTab):
            tab.save()
        self.ui.workspace_tabs.removeTab(tab_index)
        if self.ui.workspace_tabs.count() == 0:
            self.ui.path_label.setText("Nothing has been opened yet")

    def trigger_changing_tabs(self, tab_index) -> None:
        """Utility method. Bound to signal"""
        tab = self.ui.workspace_tabs.widget(tab_index)
        if isinstance(tab, AbstractWorkspaceTab):
            self.ui.path_label.setText(tab.identifier)
        self.expand_current_tab_tree(tab, True)

    def trigger_file_saving(self) -> None:
        """Utility method. Bound to signal"""
        for tab in self.opened_workspace_tabs.values():
            if isinstance(tab, CodeEditorTab):
                tab.save()

    def trigger_file_running(self) -> None:
        """Utility method. Bound to signal"""
        for tab in self.opened_workspace_tabs.values():
            logger.info("Running file %s...", tab.identifier)
            if isinstance(tab, CodeEditorTab):
                tab.save()

        if self.ui.run_profile_box.currentData() is not None:
            cmd = self.ui.run_profile_box.currentData().command
        else:
            if isinstance(self.ui.workspace_tabs.currentWidget(), CodeEditorTab):
                cmd = f"python3 {self.ui.workspace_tabs.currentWidget().identifier}"
            else:
                cmd = ""

        if self.app.config.run.in_ide:
            self.ui.bottom_tabs.setCurrentWidget(self.ui.bottom_run_tab)
            self.ui.toolbar_stop_btn.setEnabled(True)
            self.ui.toolbar_run_btn.setEnabled(False)
            self.ui.run_edit = TerminalTextEdit(
                self.ui.bottom_terminal_tab,
                cwd=self.project and self.project.root,
                python_run_command='python main.py',
                run_button=self.ui.toolbar_run_btn
            )
            self.ui.gridLayout.addWidget(self.ui.run_edit, 0, 0, 1, 1)
            self.ui.run_edit.setFocus()
        else:
            bash_exec_cmd = f"echo {os.getcwd()} {tab.identifier}; {cmd}; echo; bash"
            terminal_exec_cmd = f"bash -c \"{bash_exec_cmd}\""
            terminal = self.app.config.run.terminal_choice
            exec_cmd = f"{terminal} -e '{terminal_exec_cmd}'"
            os.system(exec_cmd)

    def trigger_file_opening_from_tree(
        self,
        item: FileTreeItem,
        *args  # pylint: disable=unused-argument
    ) -> None:
        """Utility method. Bound to signal"""
        if os.path.isfile(item.path):
            self.open_file(item.path)

    def setup_top_menu(self) -> None:
        """
        Setup all actions for top menu
        """

        file_new_project = QWidgetAction(self)
        file_new_project.setText("New Project")
        file_new_project.triggered.connect(self.trigger_new_project_creation)
        self.ui.menuFile.addAction(file_new_project)

        self.ui.menuFile.addSeparator()

        file_open_file_here = QWidgetAction(self)
        file_open_file_here.setText("Open File Here")
        file_open_file_here.triggered.connect(self.trigger_file_opening)
        self.ui.menuFile.addAction(file_open_file_here)

        file_open_file = QWidgetAction(self)
        file_open_file.setText("Open File")
        file_open_file.triggered.connect(self.trigger_file_in_separate_editor_opening)
        self.ui.menuFile.addAction(file_open_file)

        file_open_project = QWidgetAction(self)
        file_open_project.setText("Open Project")
        file_open_project.triggered.connect(self.trigger_project_opening)
        self.ui.menuFile.addAction(file_open_project)

        self.ui.menuFile.addSeparator()

        file_save_project = QWidgetAction(self)
        file_save_project.setText("Save Project")
        file_save_project.triggered.connect(self.trigger_file_saving)
        self.ui.menuFile.addAction(file_save_project)

        self.ui.menuFile.addSeparator()

        file_close = QWidgetAction(self)
        file_close.setText("Close")
        file_close.triggered.connect(self.trigger_editor_closing)
        self.ui.menuFile.addAction(file_close)

        action = QWidgetAction(self)
        action.setText("Colors")
        action.triggered.connect(self.color_menu)
        self.ui.menuCode.addAction(action)

        action_2 = QWidgetAction(self)
        action_2.setText("All Files")
        action_2.triggered.connect(self.reformat_all_files)
        self.ui.menuRefactor.addAction(action_2)

        action_3 = QWidgetAction(self)
        action_3.setText("Current File")
        action_3.triggered.connect(self.reformat_current_file)
        self.ui.menuRefactor.addAction(action_3)

        action = QWidgetAction(self)
        action.setText("Run Profiles")
        action.triggered.connect(self.trigger_profile_edit)
        self.ui.menuRun.addAction(action)

        search_action = QWidgetAction(self)
        search_action.setText("Search")
        search_action.triggered.connect(self.search_event)
        self.ui.menuCode.addAction(search_action)

        plugin_action = QWidgetAction(self)
        plugin_action.setText("Plugins")
        plugin_action.triggered.connect(self.trigger_plugin_dialog)
        self.ui.menuTools.addAction(plugin_action)

    def trigger_plugin_dialog(self) -> None:
        """Utility method. Bound to signal"""
        dialog = PluginsDialog(self)
        dialog.exec()

    def trigger_profile_edit(self) -> None:
        """Utility method. Bound to signal"""
        dialog = RunProfilesDialog(self, self.project)
        dialog.exec()

    def trigger_open_about_dialog(self) -> None:
        dialog = AboutDialog(self.app.version)
        dialog.exec()

    def restore_last_opened(self) -> None:
        """
        Restores all files that were opened before IDE closed
        """
        for file_path in self.app.config.last_state.last_opened:
            if not os.path.exists(file_path):
                self.app.config.last_state.last_opened.remove(file_path)
            else:
                self.open_file(file_path)
        self.ui.workspace_tabs.setCurrentIndex(self.app.config.last_state.opened_index)

    def restore_last_opened_in_project(self) -> None:
        """
        Restores all files that were opened in this project before IDE closed
        """
        for file_path in self.project.config["last_opened"]["files"]:
            if not os.path.exists(file_path):
                self.project.config["last_opened"]["files"].remove(file_path)
            else:
                self.open_file(file_path)
        self.ui.workspace_tabs.setCurrentIndex(self.project.config["last_opened"]["index"])

    def load_file_tree(self) -> None:
        """
        Loads project file tree
        """
        self.project_tree_item = FileTreeItem(self.project.root, show_full_path=True)
        for i in range(self.ui.project_tree.topLevelItemCount()):
            self.ui.project_tree.takeTopLevelItem(i)
        self.ui.project_tree.addTopLevelItem(self.project_tree_item)
        FileTreeItem.hook_into_tree(self.ui.project_tree)

    def open_file(self, file_path: str) -> None:
        """
        Opens a file by given path. If file is already opened,
        switches to its tab
        :param str file_path: path to target file
        """
        logger.info("Opening file %s...", file_path)
        if not os.path.exists(file_path):
            logger.error("File %s doesn't exist!", file_path)
            return

        if file_path in self.opened_workspace_tabs:
            self.open_tab_raw(file_path, None, None)
            logger.info(
                "File %s already opened! Switching to tab %s",
                file_path,
                self.opened_workspace_tabs[file_path]
            )
        else:
            heading = file_path.split("/")[-1]
            file_types = Registry.find_file_types(file_path)
            if len(file_types) > 0:
                if file_types[0].do_custom_open:
                    file_types[0].custom_open(self, file_path)
                    return
            with open(file_path, "r", encoding='utf-8') as file:
                text = file.read()
            tab = CodeEditorTab(file_path, self)
            tab.set_area_text(text)
            self.open_tab_raw(file_path, heading, tab)
            if file_path in self.app.config.misc.recent_files:
                self.app.config.misc.recent_files.remove(file_path)
            self.app.config.misc.recent_files.insert(0, file_path)
            logger.info("Succesfully opened file %s at new tab", file_path)

    def open_tab_raw(self, identifier: str, heading: str, contents: CodeEditorTab) -> None:
        """
        Opens a new tab. If tab with such identifier is already opened,
        switches to it.
        :param str identifier: tab text id. E.g. full file path
        :param str heading: tab name
        :param QWidget contents: tab contents
        """
        if identifier in self.opened_workspace_tabs:
            for i in range(self.ui.workspace_tabs.count()):
                tab = self.ui.workspace_tabs.widget(i)
                if isinstance(tab, AbstractWorkspaceTab):
                    if identifier == tab.identifier:
                        self.ui.workspace_tabs.setCurrentIndex(i)
                        return
        else:
            self.opened_workspace_tabs[identifier] = contents
            self.ui.workspace_tabs.addTab(contents, "")
            self.ui.workspace_tabs.setTabText(self.ui.workspace_tabs.count() - 1, heading)
            self.ui.workspace_tabs.setCurrentIndex(self.ui.workspace_tabs.count() - 1)

    def refresh_file_tree(self) -> None:
        """
        Refreshes the file tree
        """
        if self.ui.project_tree is not None and self.project is not None:
            if self.project_tree_item is None:
                self.load_file_tree()
            else:
                self.project_tree_item.refresh()
                logger.debug("Refreshing file tree")

    def trigger_textedit_text_setting(self, text: str, widget: "QTextEdit") -> None:
        """Utility method. Bound to signal"""
        widget.setText(text)
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        widget.setTextCursor(cursor)

    def trigger_process_stop(self) -> None:
        """Utility method. Bound to signal"""
        if hasattr(self.ui.run_edit, "process") and not self.ui.run_edit.is_finished:
            self.ui.run_edit.process.kill()

    def trigger_new_project_creation(self) -> None:
        """Utility method. Bound to signal"""
        logger.info("Creating new project")
        from ide.frames.dialogs.new_project import new_project_setup_sequence
        new_project_setup_sequence.create_new_project()

    def trigger_project_opening(self) -> None:
        """Utility method. Bound to signal"""
        logger.info("Opening existing project")
        file_path = QFileDialog.getExistingDirectory(self, 'Open project', os.getcwd())
        if file_path is not None and file_path != "":
            editor = EditorWindow(self.app, project=file_path)
            editor.show()
            self.app.editors.append(editor)

    def trigger_file_in_separate_editor_opening(self) -> None:
        """Utility method. Bound to signal"""
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd())
        if file_path is not None and file_path != "":
            editor = EditorWindow(self.app, project=None, do_restore_last=False)
            editor.show()
            editor.open_file(file_path)
            self.app.editors.append(editor)
            self.close()

    def eventFilter(self, obj, event):
        """
        Installed eventFilter on bottom bar text edits
        """
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and obj.hasFocus():
                if obj is self.ui.run_edit and self.code_run_task is not None:
                    self.code_run_task.trigger_input()

        return super().eventFilter(obj, event)

    def expand_current_tab_tree(self, tab, mode):
        tabs = self.opened_workspace_tabs

        if self.previous_expanded:
            if self.previous_expanded in tabs.values():
                previous_tab_path = list(tabs.keys())[list(tabs.values()).index(self.previous_expanded)]
                if self.project_tree_item:
                    if self.project_tree_item.path in previous_tab_path:
                        self.project_tree_item.expand_to_file(previous_tab_path, False)

        if tab in tabs.values():
            current_tab_path = list(tabs.keys())[list(tabs.values()).index(tab)]
            if self.project_tree_item:
                if self.project_tree_item.path in current_tab_path:
                    self.project_tree_item.expand_to_file(current_tab_path, mode)

        self.previous_expanded = tab




