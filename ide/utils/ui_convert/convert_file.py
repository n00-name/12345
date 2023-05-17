import os


def convert_file(path: str) -> None:
    os.system(f"pyside6-uic {path} > {path[:-2] + 'py'}")

def convert_qrc(path: str) -> None:
    os.system(f"pyside6-rcc {path} -o {path[:-4] + '_rc.py'}")
