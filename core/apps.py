from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        # Importing the game modules is what populates the registry. It has to
        # happen here rather than at module level: the app registry is not
        # ready while apps.py itself is being imported.
        from core.games import autodiscover  # pylint: disable=import-outside-toplevel

        autodiscover()
