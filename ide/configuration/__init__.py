"""
This code defines the Config class, which is a global configuration for the IDE. The class has several static variables
that store the values of the settings.

The configSection class is also defined, which is a subclass of the dictionary and is used to store configuration
section data.

The Config class has methods for loading the configuration from a file, saving changes back to the file, and for
regenerating the default configuration file if the file is missing.

The configuration is stored as a dictionary, which can be saved to a YAML file. Each dictionary key starts with
cfg__<section>__<name>, where <section> is the name of the section and <name> is the name of the setting.

For ease of access to the settings, the __getattr__ and __setattr__ methods are used, which allow you to get and set
the values of the settings via dot notation, for example: config.appearance.theme = "dark".

The Mode class is also defined, which is used to define the application mode. The constants LIGHT and PROJECT can be
used to set the value of cfg__last_state__last_mode.
"""
