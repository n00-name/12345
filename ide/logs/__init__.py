"""
This code creates the application logging settings. A logger object named "application" is created and the logging
level is set to DEBUG. Next, handlers are created for files and consoles, their logging level and formatting are
configured, and then they are added to the logger object. If the file "ide/logs/last_run.log" is not found, then
the logging level is set to 1000 (above all levels).
"""

from .logger import logger
