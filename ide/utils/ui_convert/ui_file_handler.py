import datetime
import os

from watchdog.events import FileSystemEventHandler

from ide.utils.ui_convert.convert_file import convert_file
from ide.utils.ui_convert.ui_scriptoutput import ScriptOutput


class UiFileUpdateHandler(FileSystemEventHandler):
    def __init__(self):
        self.mute_time = datetime.datetime.now()  # Won't convert files until this time
        self.count = 0

    def on_created(self, event):
        if event.src_path.endswith(".ui"):
            ScriptOutput.print(f"CREATED: File {os.path.relpath(event.src_path)} was created")
            with open(event.src_path[:-2] + "py", "a", encoding='utf-8') as file:
                file.close()

    def on_opened(self, event):
        if event.src_path.endswith(".ui") and datetime.datetime.now() >= self.mute_time:
            ScriptOutput.print(f"MODIFIED: File {os.path.relpath(event.src_path)} was modified")
            convert_file(event.src_path)
            self.mute_time = datetime.datetime.now() + datetime.timedelta(0, 1)
            self.count += 1

    def on_deleted(self, event):
        if event.src_path.endswith(".ui"):
            ScriptOutput.print(f"DELETED: File {os.path.relpath(event.src_path)} was deleted")
            os.remove(event.src_path[:-2] + "py")
