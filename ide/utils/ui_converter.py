"""
Utility script for converting .ui files into .py.
Run with command line arguments.
"""
import argparse

from ide.utils.ui_convert.convertations import ConvertationMonitoring, ConvertationOneFile,\
    ConvertationRecursive, ConvertationQrc
from ide.utils.ui_convert.ui_scriptoutput import ScriptOutput


def main():
    parser = argparse.ArgumentParser()
    runtype_group = parser.add_mutually_exclusive_group()
    runtype_group.add_argument("-q", "--qrc", dest="qrc",
                               help="qrc convertation: convert resources.qrc ",
                               action="store_true")
    runtype_group.add_argument("-r", "--recursive", dest="recursive",
                               help="recursive convertation: convert all .ui "
                                    "files found in parent folder and subfolders",
                               action="store_true")
    runtype_group.add_argument("-m", "--monitoring", dest="monitoring",
                               help="monitoring mode: scan OS events, convert .ui files "
                                    "in parent folder and subfolders if they were modified",
                               action="store_true")
    runtype_group.add_argument("-o", "--onefile", dest="onefile",
                               help="one file convertation: requires relative to parent "
                                    "folder file path in command line arguments",
                               action="store_true")
    parser.add_argument("path", help="path to file used in onefile mode", nargs="?")
    parser.add_argument("-s", "--silent", dest="silent",
                        help="hide additional convertation info such as "
                             "file names converted in recursive mode",
                        action="store_true")

    args = parser.parse_args()

    if True in vars(args).values():
        run_types = {
            "qrc": ConvertationQrc,
            "recursive": ConvertationRecursive,
            "monitoring": ConvertationMonitoring,
            "onefile": ConvertationOneFile,
        }
        run_type = list(vars(args).keys())[list(vars(args).values()).index(True)]
        ScriptOutput.print(f"Running in {run_type} mode\n")
        run_types[run_type](args).run()
    else:
        ScriptOutput.print("ui_converter.py: error: one of the arguments -r -m -o is required")


if __name__ == "__main__":
    main()
