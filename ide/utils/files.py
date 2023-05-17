import os
import shutil


def remove(path: str):
    """
    Fully remove directory
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def mkfile(path: str):
    """
    Create file
    """
    if not os.path.exists(os.path.split(path)[0]):
        os.makedirs(os.path.split(path)[0])
    with open(path, "w", encoding="utf-8") as file:
        file.write("")


def mkdir(path: str):
    """
    Create directory
    """
    if not os.path.exists(path):
        os.makedirs(path)
