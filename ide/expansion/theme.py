import darkdetect
import qdarktheme


class Theme:
    """
    Represents a theme
    """

    id: str
    """Id of that theme"""

    is_dark: bool = False
    """Is this theme dark"""

    def __init__(self):
        self.id = self.__class__.id
        self.is_dark = self.__class__.is_dark

    def on_apply(self) -> None:
        """
        Applies theme
        """


class QTAutoTheme(Theme):
    id = "qt-auto"

    def __init__(self):
        super().__init__()
        self.is_dark = darkdetect.isDark()

    def on_apply(self) -> None:
        qdarktheme.setup_theme("auto")


class LightTheme(Theme):
    id = "light"
    is_dark = False

    def on_apply(self) -> None:
        qdarktheme.setup_theme("light")


class DarkTheme(Theme):
    id = "dark"
    is_dark = True

    def on_apply(self) -> None:
        qdarktheme.setup_theme("dark")
