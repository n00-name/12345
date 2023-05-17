import json
import os
import time
from shutil import rmtree

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QListWidget, \
    QVBoxLayout, QSpacerItem, QSizePolicy, QInputDialog, QPlainTextEdit, QTreeWidget, QDialog, QTreeWidgetItem, \
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox, QTextEdit, QSplitter
from git import Repo

from ide.ui.file_tree_items import FileTreeItem


class GitBranchList(QListWidget):
    def __init__(self, tool_tab):
        super().__init__()
        self.tool_tab = tool_tab
        self.repo: Repo = tool_tab.repo
        self.refresh()

    def refresh(self) -> None:
        if self.repo is not None:
            self.clear()
            for branch in [head.name for head in self.repo.heads]:
                if self.repo.active_branch.name == branch:
                    self.addItem(f"> {branch}")
                else:
                    self.addItem(branch)


class GitCommitTable(QTableWidget):
    def __init__(self, tool_tab):
        super().__init__()
        self.tool_tab = tool_tab
        self.repo: Repo = tool_tab.repo
        self.setColumnCount(3)
        self.setHorizontalHeaderItem(0, QTableWidgetItem("Commit"))
        self.setHorizontalHeaderItem(1, QTableWidgetItem("Author"))
        self.setHorizontalHeaderItem(2, QTableWidgetItem("Date"))
        self.setVerticalHeaderLabels(["Commit", "Author", "Date"])
        self.refresh()

    def refresh(self) -> None:
        if self.repo is not None:
            self.clear()
            commits = list(self.repo.iter_commits(self.repo.active_branch.name))
            self.setRowCount(len(commits))
            for row, commit in enumerate(commits):
                self.setItem(row, 0, QTableWidgetItem(commit.message))
                self.setItem(row, 1, QTableWidgetItem(commit.author.name))
                commit_time = time.strftime("%a, %d %b %Y %H:%M", time.gmtime(commit.committed_date))
                self.setItem(row, 2, QTableWidgetItem(commit_time))


class CommitWindow(QDialog):
    def __init__(self, tab: "GitToolTab", is_initial=False):
        super().__init__()
        self.tab = tab
        self.repo: Repo = tab.repo
        self.committed = False

        self.setWindowTitle("Commit")
        central = QWidget()
        central_hbox = QHBoxLayout(central)
        central.setLayout(central_hbox)
        self.setLayout(central_hbox)

        self.changes_tree_item = QTreeWidgetItem()
        self.changes_tree_item.setText(0, "Changes")
        self.changes_tree_item.setFlags(self.changes_tree_item.flags() |
                                        Qt.ItemFlag.ItemIsUserCheckable |
                                        Qt.ItemFlag.ItemIsAutoTristate)
        self.changes_tree_item.setCheckState(0, Qt.CheckState.Unchecked)
        self.untracked_tree_item = QTreeWidgetItem()
        self.untracked_tree_item.setText(0, "Untracked")
        self.untracked_tree_item.setFlags(self.untracked_tree_item.flags() |
                                          Qt.ItemFlag.ItemIsUserCheckable |
                                          Qt.ItemFlag.ItemIsAutoTristate)
        self.untracked_tree_item.setCheckState(0, Qt.CheckState.Unchecked)
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel(
            "Commit to " + self.tab.repo.active_branch.name if not is_initial else "Initial commit"
        )
        self.file_tree.addTopLevelItem(self.changes_tree_item)
        self.file_tree.addTopLevelItem(self.untracked_tree_item)
        for item in self.repo.index.diff(None):
            self.changes_tree_item.addChild(FileTreeItem(
                os.path.abspath(os.path.join(self.repo.working_dir, item.a_path)), True, True))
        for item in self.repo.untracked_files:
            self.untracked_tree_item.addChild(FileTreeItem(
                os.path.abspath(os.path.join(self.repo.working_dir, item)), True, True))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.file_tree)

        self.commit_message_edit = QPlainTextEdit()
        self.commit_message_edit.setPlaceholderText("Commit message")
        splitter.addWidget(self.commit_message_edit)
        if is_initial:
            # TODO: make .gitignore selected by default in initial commits
            self.commit_message_edit.setPlainText("Initial commit")

        button_panel = QWidget()
        panel_vbox = QVBoxLayout(button_panel)
        button_panel.setLayout(panel_vbox)
        splitter.addWidget(button_panel)

        central_hbox.addWidget(splitter)

        self.commit_button = QPushButton()
        self.commit_button.setText("Commit")
        panel_vbox.addWidget(self.commit_button)
        self.commit_button.clicked.connect(self.trigger_commit)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        panel_vbox.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.trigger_cancel)

        panel_vbox.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def trigger_cancel(self) -> None:
        self.close()

    def trigger_commit(self) -> None:
        for i in range(self.changes_tree_item.childCount()):
            if isinstance(self.changes_tree_item.child(i), FileTreeItem) and \
                self.changes_tree_item.child(i).checkState(0).Checked:
                self.tab.repo.git.add(self.changes_tree_item.child(i).path)
        for i in range(self.untracked_tree_item.childCount()):
            if isinstance(self.untracked_tree_item.child(i), FileTreeItem) and \
                self.untracked_tree_item.child(i).checkState(0).value == 1:
                self.tab.repo.git.add(self.untracked_tree_item.child(i).path)
        self.tab.repo.index.commit(self.commit_message_edit.toPlainText())
        self.committed = True
        self.tab.branch_list.refresh()
        self.tab.commit_table.refresh()
        self.close()

    @staticmethod
    def initial_commit_dialog(tab):
        window = CommitWindow(tab, is_initial=True)
        window.exec()
        return window.committed


class GitignoreWindow(QDialog):
    def __init__(self, tab: "GitToolTab"):
        super().__init__()
        self.tab = tab
        self.repo: Repo = tab.repo
        self.selected_template = None

        # Use gitignore.io repo to search for templates
        try:
            response = requests.get("https://api.github.com/repos/toptal/gitignore/contents/templates", timeout=100)
            if response.status_code == 200:
                self.templates = json.loads(response.content.decode())
            else:
                self.templates = None
        except requests.exceptions.ConnectionError:
            self.templates = None

        self.setWindowTitle("Add gitignore")

        main_widget = QWidget()
        panel_vbox = QVBoxLayout(main_widget)
        self.setLayout(panel_vbox)

        custom_button = QPushButton("Create custom gitignore")
        self.search_line = QLineEdit()
        self.error_label = QLabel("Couldn't connect to gitignore.io GitHub\ntemplates repository, try again")
        self.refresh_button = QPushButton("Refresh")
        self.templates_list = QListWidget()
        self.preview_button = QPushButton("Preview template")
        self.add_button = QPushButton("Add gitignore")
        self.continue_button = QPushButton("Continue without gitignore")

        panel_vbox.addWidget(custom_button)
        custom_button.clicked.connect(lambda: GitignorePreviewDialog(self, ""))

        panel_vbox.addWidget(QLabel("Find in gitignore.io"))

        self.search_line.textEdited.connect(self.refresh_templates_list)
        panel_vbox.addWidget(self.search_line)

        self.refresh_button.clicked.connect(self.refresh_repo)
        panel_vbox.addWidget(self.error_label)
        panel_vbox.addWidget(self.refresh_button)
        self.templates_list.itemClicked.connect(self.select_template)
        self.templates_list.itemClicked.connect(self.refresh_templates_list)

        if self.templates is not None:
            self.refresh_templates_list()
            self.enable_templates_list()
        else:
            self.templates_list.clear()
            self.enable_refresh_button()

        panel_vbox.addWidget(self.templates_list)

        self.preview_button.setEnabled(False)
        panel_vbox.addWidget(self.preview_button)
        self.preview_button.clicked.connect(self.preview_template)

        self.add_button.setEnabled(False)
        panel_vbox.addWidget(self.add_button)
        self.add_button.clicked.connect(self.trigger_add)

        panel_vbox.addWidget(self.continue_button)
        panel_vbox.setAlignment(Qt.AlignVCenter)
        self.continue_button.clicked.connect(self.trigger_continue)

        panel_vbox.addWidget(QLabel("Powered by gitignore.io API"))

    def trigger_continue(self) -> None:
        """Window closing method. Bound to signal (button)."""
        self.close()

    def trigger_add(self) -> None:
        """Gitignore apply method. Bound to signal (button)."""
        try:
            response = requests.get(self.selected_template["download_url"], timeout=100)

            if response.status_code == 200:
                with open(os.path.join(self.tab.git_path, ".gitignore"), "w", encoding='utf-8') as file:
                    file.write(response.content.decode())
                self.close()
            else:
                self.show_connection_error()
        except requests.exceptions.ConnectionError:
            self.show_connection_error()

    def refresh_templates_list(self) -> None:
        """Templates list refresh method. Bound to signal."""
        self.templates_list.clear()

        selected_template_in_list = False
        for template in self.templates:
            if template["name"].lower().find(self.search_line.text().lower()) != -1 \
                and template["name"].endswith(".gitignore"):

                self.templates_list.addItem(template["name"])

                if self.selected_template is not None:
                    if template["name"] == self.selected_template["name"]:
                        selected_template_in_list = True

        # Add selected template to list even if it doesn't match search string
        if not selected_template_in_list and self.selected_template is not None:
            self.templates_list.addItem(self.selected_template["name"])

        if self.selected_template is not None:
            for i in range(self.templates_list.count()):
                item = self.templates_list.item(i)
                if item.text() == self.selected_template["name"]:
                    item.setSelected(True)

    def refresh_repo(self) -> None:
        """Gitignore.io templates refresh method. Bound to signal (button)."""

        try:
            response = requests.get("https://api.github.com/repos/toptal/gitignore/contents/templates", timeout=100)
            if response.status_code == 200:
                self.templates = json.loads(response.content.decode())
                self.templates_list.clear()
                for template in self.templates:
                    if template["name"].endswith(".gitignore"):
                        self.templates_list.addItem(template["name"])
                self.enable_templates_list()
            else:
                self.templates = None
                self.enable_refresh_button()
        except requests.exceptions.ConnectionError:
            self.templates = None
            self.enable_refresh_button()

    def enable_templates_list(self) -> None:
        """
        Hides refresh button and shows templates list.
        Called when gitignore.io templates found successfully.
        """
        self.templates_list.setVisible(True)
        self.error_label.setVisible(False)
        self.refresh_button.setVisible(False)

    def enable_refresh_button(self) -> None:
        """
        Hides templates list button, shows refresh button and disables confirm button.
        Called when gitignore.io templates not found.
        """
        self.templates_list.setVisible(False)
        self.error_label.setVisible(True)
        self.refresh_button.setVisible(True)
        self.add_button.setEnabled(False)
        self.preview_button.setEnabled(False)

    def select_template(self) -> None:
        """Gitignore template selection method. Bound to signal (templates list)."""
        for template in self.templates:
            if template["name"] == self.templates_list.selectedItems()[0].text():
                self.selected_template = template

        if self.selected_template is not None:
            self.add_button.setEnabled(True)
            self.preview_button.setEnabled(True)

    def preview_template(self) -> None:
        """Shows template preview and editing dialog. Bound to signal (button)."""
        try:
            response = requests.get(self.selected_template["download_url"], timeout=100)

            if response.status_code == 200:
                GitignorePreviewDialog(self, response.content.decode())
            else:
                self.show_connection_error()
        except requests.exceptions.ConnectionError:
            self.show_connection_error()

    @staticmethod
    def show_connection_error() -> None:
        """Shows connection error message"""
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setText("\n".join([
            "Couldn't connect to gitignore.io GitHub",
            "templates repository, please try again",
        ]))
        dialog.exec_()


class GitignorePreviewDialog(QDialog):
    def __init__(self, parent_window: "GitignoreWindow", template: str):
        super().__init__()
        self.parent_window = parent_window
        main_widget = QWidget()
        panel_vbox = QVBoxLayout(main_widget)
        self.setLayout(panel_vbox)

        if parent_window.selected_template is None or template == "":
            panel_vbox.addWidget(QLabel("Create new .gitignore"))
        else:
            panel_vbox.addWidget(QLabel("Preview of " + parent_window.selected_template["name"]))

        self.text_edit = QTextEdit()
        self.text_edit.setText(template)
        panel_vbox.addWidget(self.text_edit)

        button_panel = QWidget()
        buttons_hbox = QHBoxLayout(button_panel)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_gitignore_file)
        buttons_hbox.addWidget(save_button)
        close_button = QPushButton("Close")
        close_button.clicked.connect(lambda: self.close())
        buttons_hbox.addWidget(close_button)

        button_panel.setLayout(buttons_hbox)
        panel_vbox.addWidget(button_panel)
        self.exec_()

    def save_gitignore_file(self) -> None:
        """Saves the gitignore file"""
        with open(os.path.join(self.parent_window.tab.git_path, ".gitignore"), "w", encoding='utf-8') as file:
            file.write(self.text_edit.toPlainText())

        self.close()
        self.parent_window.close()


class GitToolTab(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.commit_table = None
        self.delete_branch_button = None
        self.commit_window = None
        self.ignore_button = None
        self.add_button = None
        self.branch_list: GitBranchList | None = None
        self.checkout_button = None
        self.new_branch_button = None
        self.commit_button = None
        self.editor = editor
        self.git_path = self.editor.project.root
        self.repo = None
        if os.path.exists(os.path.join(self.git_path, ".git")):
            self.repo = Repo(self.git_path)

        self.hbox = QHBoxLayout(self)
        self.setLayout(self.hbox)

        self.git_panels = {
            'empty': self.create_empty_git_panel_widgets(),
            'non_empty': self.create_git_panel_widgets(),
        }
        self.replace_content()

    def replace_content(self) -> None:
        """
        Places content based on whether
        the repo is present or not
        """
        for item in self.git_panels['non_empty' if self.repo is None else 'empty']:
            item.hide()
        for item in self.git_panels['empty' if self.repo is None else 'non_empty']:
            item.show()
        self.update()

    def create_git_panel_widgets(self):
        button_panel = QWidget()
        panel_vbox = QVBoxLayout(button_panel)
        self.commit_button = QPushButton()
        self.commit_button.setText("Commit")
        self.commit_button.clicked.connect(self.trigger_commit)
        panel_vbox.addWidget(self.commit_button)
        self.new_branch_button = QPushButton()
        self.new_branch_button.setText("New branch")
        self.new_branch_button.clicked.connect(self.trigger_create_branch)
        panel_vbox.addWidget(self.new_branch_button)
        self.checkout_button = QPushButton()
        self.checkout_button.setText("Checkout")
        self.checkout_button.clicked.connect(self.trigger_checkout)
        panel_vbox.addWidget(self.checkout_button)
        self.delete_branch_button = QPushButton()
        self.delete_branch_button.setText("Delete branch")
        self.delete_branch_button.clicked.connect(self.trigger_checkout)
        panel_vbox.addWidget(self.delete_branch_button)
        panel_vbox.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        button_panel.setLayout(panel_vbox)
        self.hbox.addWidget(button_panel)
        self.branch_list = GitBranchList(self)
        self.hbox.addWidget(self.branch_list)
        self.commit_table = GitCommitTable(self)
        self.hbox.addWidget(self.commit_table)
        return button_panel, self.branch_list, self.commit_table

    def create_empty_git_panel_widgets(self):
        widget1 = QWidget()
        vbox = QVBoxLayout(widget1)
        label = QLabel()
        label.setText("No Git repo is currently present at project root")
        button = QPushButton()
        button.setText("Create")
        button.clicked.connect(self.init_git_repo)
        vbox.addWidget(label)
        vbox.addWidget(button)
        widget1.setLayout(vbox)
        self.hbox.addWidget(widget1)
        return [widget1]

    def init_git_repo(self) -> None:
        """
        Initializes empty Git repo in project root
        """
        if not os.path.exists(os.path.join(self.git_path, ".gitignore")):
            window = GitignoreWindow(self)
            window.exec()
        else:
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Question)
            dialog.setText("\n".join([
                "Found an existing .gitignore file inside the folder.",
                "Do you want to use it?",
                "Cancel to create new .gitignore file.",
            ]))
            dialog.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            selected_option = dialog.exec_()

            if selected_option == QMessageBox.Cancel:
                os.remove(os.path.join(self.git_path, ".gitignore"))
                window = GitignoreWindow(self)
                window.exec()

        self.repo = Repo.init(self.git_path)
        check = CommitWindow.initial_commit_dialog(self)
        if check:
            self.replace_content()
            self.branch_list.refresh()
        # TODO: this is temporarily, because the app isn't able to open empty git repos now
        else:  # Do not let user to create empty repo
            if os.path.exists(os.path.join(self.git_path, ".git")):
                rmtree(os.path.join(self.git_path, ".git"))

            if os.path.exists(os.path.join(self.git_path, ".gitignore")):
                dialog = QMessageBox()
                dialog.setIcon(QMessageBox.Question)
                dialog.setText("\n".join([
                    "Git repository won't be initialized after",
                    "cancelling initial commit, but there is",
                    "a .gitignore file left in project folder.",
                    "Do you want to delete it?",
                ]))
                dialog.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
                selected_option = dialog.exec_()

                if selected_option == QMessageBox.Ok:
                    os.remove(os.path.join(self.git_path, ".gitignore"))
                    # TODO: refresh project files tree in editor window

    def get_branches(self) -> list[str]:
        return [head.name for head in self.repo.heads]

    def trigger_create_branch(self) -> None:
        branch_name, check = QInputDialog.getText(self, "Create branch", "New branch name")
        if check:
            self.repo.create_head(branch_name)
            self.branch_list.refresh()

    def trigger_checkout(self) -> None:
        branch_name, check = QInputDialog.getItem(
            self,
            "Checkout branch",
            "Select branch",
            self.get_branches(),
            0,
            False
        )
        if check:
            self.repo.git.checkout(branch_name)
            self.branch_list.refresh()
            self.commit_table.refresh()

    def trigger_delete(self) -> None:
        branch_name, check = QInputDialog.getItem(
            self,
            "Delete branch",
            "Select branch",
            self.get_branches(),
            0,
            False
        )
        if check:
            self.repo.delete_head(branch_name)
            self.branch_list.refresh()
            self.commit_table.refresh()

    def trigger_commit(self) -> None:
        self.commit_window = CommitWindow(self)
        self.commit_window.show()
