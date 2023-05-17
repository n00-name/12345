# usage:
# python -m unittest tests     # from project root
import filecmp
import os
import unittest

from ide.configuration.config import Config


class ConfigTestCase(unittest.TestCase):
    '''
    Check Configuration.
    '''
    def test_simple(self):
        '''
        Checking for the presence of parameters in sections.
        '''
        sections = Config.get_sections()
        self.assertIn('last_state', sections)
        self.assertIn('misc', sections)
        self.assertIn('editor', sections)
        self.assertIn('appearance', sections)
        self.assertIn('run', sections)
        self.assertIn('plugins', sections)


class ConfigSaveTestCase(unittest.TestCase):
    '''
    Checking saving configs.
    '''
    def test_save(self):
        '''
        Checking the correct saving of the config file.
        '''
        Config.save('tests/1.yml')
        self.assertTrue(filecmp.cmp('tests/1.yml', 'tests/original_config.yml'))
        # todo: use difflib to compare files

    def tearDown(self) -> None:
        if os.path.exists("tests/1.yml"):
            os.remove("tests/1.yml")
