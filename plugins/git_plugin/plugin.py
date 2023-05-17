'''
Plugin GIT
'''

from ide.expansion.plugins import EditorPlugin
from ide.frames.editor.window import EditorWindow

from plugins.git_plugin.ui import GitToolTab


class GitPlugin(EditorPlugin):
    def on_enable(self, editor: EditorWindow):
        if editor.project is not None:
            editor.ui.bottom_tabs.addTab(GitToolTab(editor), "")
            editor.ui.bottom_tabs.setTabText(editor.ui.bottom_tabs.count() - 1, "Git")
