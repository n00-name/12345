# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import shutil
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SHP.IDE'
copyright = '2023, 2023, MSHP_os101'
author = '2023, MSHP_os101'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
]

autosummary_generate = True
templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autodoc_member_order = 'bysource'
html_theme = 'furo'
html_static_path = ['_static']


# Generating docs
def make_rst(path):
    path_list = path.replace("\\", "/").split("/")[2:]
    with open(f"build/{'_'.join(path_list)}.rst", "w") as file:
        file.writelines([
            path_list[-1].capitalize(), "\n",
            "=" * len(path_list[-1]), "\n\n",
        ])
        for filename in sorted(os.listdir(path)):
            if filename.endswith(".py"):
                file.write(
                    '\n'.join(
                        [
                            ".. code-block:: bash",
                            "",
                            "    # Path to file:",
                            f"   /{'/'.join(path_list)}/{filename}",
                            "",
                            f".. automodule:: {'.'.join(path_list + [filename[:-3]])}",
                            "    :members:",
                            "    :undoc-members:",
                            "    :show-inheritance:",
                            ""
                        ]
                    )
                )


if os.path.exists("build"):
    shutil.rmtree("build")
os.mkdir("build")

for root, dirs, files in os.walk("../../ide"):
    if any(file.endswith(".py") and file != "__init__.py" for file in files):
        make_rst(root)

with open("index.rst", "w") as file:
    file.writelines([
        ".. Simple.IDE documentation master file, created by\n",
        "   sphinx-quickstart on Mon Mar  6 15:24:26 2023.\n",
        "   You can adapt this file completely to your liking, but it should at least\n",
        "   contain the root `toctree` directive.\n\n",
        "Welcome to Simple.IDE's documentation!\n",
        "======================================\n\n",
        ".. toctree::\n",
        "  :maxdepth: 2\n",
        "  :caption: Contents:\n\n",
        *[f"  build/{filename}\n" for filename in os.listdir("build")],
    ])
