'''
Application launch.
'''

import sys

from ide.application import Application
from ide.logs import logger

if __name__ == "__main__":
    print(sys.argv)
    logger.info("Running application")
    app = Application(sys.argv)
    app.run()
