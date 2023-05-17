"""Logging instance for SHP.IDE"""

import logging
import sys


class ConsoleFormatter(logging.Formatter):
    """Formatter for logging instance"""
    reset = "\u001b[0m"
    gray = "\u001b[30m"
    bold_red = "\u001b[1;31m"
    red = "\u001b[31m"
    yellow = "\u001b[33m"
    cyan = "\u001b[36m"

    clear_format = "[%(levelname)s] %(message)s   ---> %(pathname)s:%(lineno)d"
    colored_formatters = {
        logging.DEBUG: gray + clear_format + reset,
        logging.INFO: cyan + clear_format + reset,
        logging.WARNING: yellow + clear_format + reset,
        logging.ERROR: red + clear_format + reset,
        logging.CRITICAL: bold_red + clear_format + reset
    }

    def format(self, record):
        log_fmt = self.colored_formatters.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("application")
logger.setLevel(logging.DEBUG)

try:
    file_handler = logging.FileHandler("ide/logs/last_run.log", "w")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("[%(asctime)s] %(name)s: '%(message)s' (%(levelname)s)",
                                       "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    if "--info" in sys.argv:
        console_handler.setLevel(logging.INFO)
    if "--debug" in sys.argv:
        console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ConsoleFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

except FileNotFoundError:  # Occurs when it's docs generation -> just skip it
    logger.setLevel(1000)  # Above all levels
