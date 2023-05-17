class RunProfile:
    """
    Represents an action and its parameters for running code
    """

    command: str
    """Command to run"""

    envs: str
    """Environment variables for that run profile"""

    name: str
    """Profile name"""

    open_in_separate_terminal: bool = False
    """Whether this run profile will be executed in native terminal or in IDE's embedded"""

    def __init__(self, name, command, envs, open_in_sep_term) -> None:
        self.name = name
        self.command = command
        self.envs = envs
        self.open_in_separate_terminal = open_in_sep_term
