import os
from abc import ABC, abstractmethod
from argparse import Namespace

from watchdog.observers import Observer

from ide.utils.ui_convert.convert_file import convert_file, convert_qrc
from ide.utils.ui_convert.ui_file_handler import UiFileUpdateHandler
from ide.utils.ui_convert.ui_scriptoutput import ScriptOutput


class ConvertationMode(ABC):
    def __init__(self, args=Namespace(path=None, silent=False)):
        self.args = args

    @abstractmethod
    def run(self):
        pass


class ConvertationRecursive(ConvertationMode):
    def run(self):
        files_converted = 0

        for root, _, files in os.walk(
            os.path.abspath(
                os.path.join(
                    *(
                        [os.path.dirname(__file__)]
                        + ['..'] * 3
                        + ['data_ui']
                    )
                )
            )
        ):
            for name in files:
                if name.endswith(".ui"):
                    convert_file(os.path.join(root, name))
                    if not self.args.silent:
                        ScriptOutput.print(os.path.relpath(os.path.join(root, name)))
                    files_converted += 1

        if files_converted > 0:
            ScriptOutput.print(f"\nSuccessfully converted {files_converted} files")
        else:
            ScriptOutput.print("Did not find any files to convert")


class ConvertationMonitoring(ConvertationMode):
    def run(self):
        ScriptOutput.print("Script will automatically convert .ui files when they are modified "
                           "and delete/create .py files if their sources were deleted/created.")

        event_handler = UiFileUpdateHandler()
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(
            os.path.abspath(os.path.join(*([os.path.dirname(__file__)] + ['..'] * 3 + ['data_ui'])))), recursive=True)
        observer.start()

        input("Press Enter to exit monitoring mode . . .\n\n")
        ScriptOutput.print(f"Files were converted {event_handler.count} time(s)")

        observer.stop()
        observer.join()


class ConvertationOneFile(ConvertationMode):
    def run(self):
        if self.args.path is not None:
            file_path = os.path.join(
                os.path.abspath(os.path.join(*([os.path.dirname(__file__)] + ['..'] * 3 + ['data_ui']))),
                self.args.path)

            ScriptOutput.print("Target path:", file_path, "\n")

            if os.path.isfile(file_path):
                if not file_path.endswith(".ui"):
                    ScriptOutput.print("File does not have .ui extension")
                else:
                    convert_file(file_path)
                    ScriptOutput.print("File successfully converted")
            else:
                ScriptOutput.print(f"File {self.args.path} not found")
        else:
            ScriptOutput.print("ui_convert.py: error: in onefile mode an argument required: path")


class ConvertationQrc(ConvertationMode):
    def run(self):
        path = os.path.abspath(os.path.join(*([os.path.dirname(__file__)] + ['..'] * 3)))
        file_path = os.path.join(path, 'resources.qrc')
        ScriptOutput.print("Target path:", file_path, "\n")

        if os.path.isfile(file_path):
            convert_qrc(file_path)
        else:
            ScriptOutput.print("File resources.qrc not found")
