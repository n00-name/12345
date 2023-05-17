class ScriptOutput:
    pass


try:
    from ide.logs import logger
except ImportError:
    ScriptOutput.can_log = False


class ScriptOutput:
    """Utility class for redirecting script output to logs if needed"""
    can_log: bool = True
    logging_mode: bool = False

    @staticmethod
    def set_logging_mode(is_enabled: bool = True):
        if ScriptOutput.can_log:
            ScriptOutput.logging_mode = is_enabled

    @staticmethod
    def print(*text: list[str]):
        if ScriptOutput.logging_mode:
            logger.info('converter: ' + ''.join(text).replace("\n", ""))
        else:
            print(text)
