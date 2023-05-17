from PySide6.QtWidgets import QApplication

from ide.frames.dialogs.new_project.dialog_select import NewProjectSelectDialog
from ide.frames.dialogs.new_project.dialog_locate import NewProjectLocateDialog
from ide.frames.dialogs.new_project.dialog_setup import NewProjectSetupDialog
from ide.frames.editor.window import EditorWindow


def create_new_project() -> tuple[None | bool, str]:
    dialog1 = NewProjectSelectDialog()
    dialog1.exec()
    if dialog1.return_code == NewProjectSelectDialog.RESULT_LEAVE:
        return None, "Aborted"
    project_gen = dialog1.return_gen

    forms = project_gen.prepare_forms()
    if len(forms) > 0:
        dialog2 = NewProjectSetupDialog(forms)
        dialog2.exec()
        if dialog2.return_code == NewProjectSetupDialog.RESULT_LEAVE:
            return None, "Aborted"
        values = dialog2.return_data
    else:
        values = {}

    dialog3 = NewProjectLocateDialog()
    dialog3.exec()
    if dialog3.return_code == NewProjectLocateDialog.RESULT_LEAVE:
        return None, "Aborted"
    project_gen.accept(values, dialog3.return_path)
    editor = EditorWindow(QApplication.instance(), project=dialog3.return_path, do_restore_last=False)
    editor.show()
    QApplication.instance().editors.append(editor)
    return True, "Success"
