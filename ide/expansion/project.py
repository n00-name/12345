import os
import venv

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from ide.ui.forms import *
from ide.expansion.run_profiles import RunProfile


class Project:
    """
    Represents an existing project
    """

    root: str
    """File path to project root"""

    config: dict
    """Local project configuration"""

    run_profiles: list[RunProfile]
    """Project run profiles"""

    def __init__(self, root: str, default_config_preset: dict = None, default_run_profiles_preset: list = None):
        """
        Creates a project representation from project folder
        :param str root: project root file path
        :param dict default_config_preset: default config preset
        """
        if default_config_preset is None:
            default_config_preset = {
                "last_opened": {
                    "files": [],
                    "index": -1
                }
            }
        if default_run_profiles_preset is None:
            default_run_profiles_preset = []

        if not os.path.exists(root):
            os.mkdir(root)
        if not os.path.exists(os.path.join(root, ".ide")):
            os.mkdir(os.path.join(root, ".ide"))
        if not os.path.exists(os.path.join(root, ".ide", "project.yml")):
            with open(os.path.join(root, ".ide", "project.yml"), "w", encoding='utf-8') as project_conf:
                project_conf.write(yaml.dump(default_config_preset, Dumper=Dumper, default_flow_style=False))
        if not os.path.exists(os.path.join(root, ".ide", "run_profiles.yml")):
            with open(os.path.join(root, ".ide", "run_profiles.yml"), "w", encoding='utf-8') as profiles:
                profiles.write(yaml.dump(default_run_profiles_preset, Dumper=Dumper, default_flow_style=False))

        self.root = root

        with open(os.path.join(root, ".ide", "project.yml"), "r", encoding='utf-8') as project_conf:
            self.config = yaml.load(project_conf.read(), Loader=Loader)
        with open(os.path.join(root, ".ide", "run_profiles.yml"), "r", encoding='utf-8') as project_conf:
            self.run_profiles = []
            config = yaml.load(project_conf.read(), Loader=Loader)
            for profile in config:
                self.run_profiles.append(RunProfile(
                    profile["name"],
                    profile["command"],
                    profile["envs"],
                    profile["separate_term"]
                ))

    def save_config(self) -> None:
        """
        Saves project config
        """
        with open(os.path.join(self.root, ".ide", "project.yml"), "w", encoding='utf-8') as project_conf:
            project_conf.write(yaml.dump(self.config, Dumper=Dumper, default_flow_style=False))
        with open(os.path.join(self.root, ".ide", "run_profiles.yml"), "w", encoding='utf-8') as project_conf:
            config = []
            for profile in self.run_profiles:
                config.append({
                    "name": profile.name,
                    "command": profile.command,
                    "envs": profile.envs,
                    "separate_term": profile.open_in_separate_terminal
                })
            project_conf.write(yaml.dump(config, Dumper=Dumper, default_flow_style=False))


class ProjectGenerator:
    """Represents abstract project generator"""

    id: str
    name: str
    icon: ... = None

    def __init__(self):
        self.id = self.__class__.id
        self.name = self.__class__.name
        self.icon = self.__class__.icon

    def prepare_forms(self) -> list[Form]:
        """Construct all forms for this generator"""

    def validate(self, values: dict[str, dict[str, object]]) -> str | bool:
        """
        Validates the form
        :param values: form{fields{}}
        :return: str with error if not valid or True
        """

    def accept(self, values: dict[str, dict[str, object]], project_path: str) -> None:
        """
        Creates project with defined parameters
        :param values: form{fields{}}
        :param project_path: Selected project path
        """


class EmptyProjectGenerator(ProjectGenerator):
    id = "empty_project_generator"
    name = "Empty Project"
    icon = None

    def prepare_forms(self) -> list[Form]:
        return []

    def validate(self, values: dict[str, dict[str, object]]) -> str | bool:
        return True

    def accept(self, values: dict[str, dict[str, object]], project_path: str) -> None:
        if not os.path.exists(project_path):
            os.mkdir(project_path)
        with open(os.path.join(project_path, "welcome.txt"), "w", encoding='utf-8') as file:
            file.write("Welcome to your brand new project!\n")


class PythonProjectGenerator(ProjectGenerator):
    id = "python_project_generator"
    name = "Python Project"
    icon = None

    class InterpreterForm(Form):
        name = "Python Interpreter Settings"
        id = "interpreter_form"
        fields = {"interpreter_path": FilePathField()}

    def prepare_forms(self) -> list[Form]:
        return [self.InterpreterForm()]

    def validate(self, values: dict[str, dict[str, object]]) -> str | bool:
        return True

    def accept(self, values: dict[str, dict[str, object]], project_path: str) -> None:
        if not os.path.exists(project_path):
            os.mkdir(project_path)

        venv.create(project_path + "/venv", with_pip=True)

        with open(os.path.join(project_path, "main.py"), "w") as file:
            file.write("def main():\n"
                       "    print(\"Hello, World!\")\n"
                       "\n"
                       "\n"
                       "if __name__ == \"__main__\":\n"
                       "    main()\n")
        project = Project(project_path)
        project.run_profiles.append(RunProfile("main.py", values["interpreter_form"]["interpreter_path"]
                                               + " main.py", "", False))
        project.save_config()
