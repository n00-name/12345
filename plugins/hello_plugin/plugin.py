'''
Plugin Hello.
'''

from ide.expansion.plugins import GlobalPlugin


class HelloPlugin(GlobalPlugin):
    def on_enable(self):
        print("Hello from my plugin!")
