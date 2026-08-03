"""
Game registry.

Games register themselves with the :func:`register` decorator and are
discovered by importing every module in this package, so adding a game means
dropping one file into ``core/games/`` -- there is no list to keep in sync.
"""

from __future__ import annotations

import importlib
import pkgutil

from core.games.base import Game

_REGISTRY: dict[str, type[Game]] = {}


def register(game: type[Game]) -> type[Game]:
    """Class decorator adding a game to the registry."""
    if not game.slug:
        raise ValueError(f"{game.__name__} must define a slug")

    existing = _REGISTRY.get(game.slug)
    if existing is not None and existing is not game:
        raise ValueError(f"Slug {game.slug!r} is already used by {existing.__name__}")

    _REGISTRY[game.slug] = game
    return game


def autodiscover() -> None:
    """Import every sibling module so decorators run.

    Called from ``CoreConfig.ready()``. Importing twice is harmless because
    :func:`register` tolerates re-registering the same class.
    """
    package = importlib.import_module(__package__)
    for module in pkgutil.iter_modules(package.__path__):
        if module.name in {"base", "registry", "bots"}:
            continue
        importlib.import_module(f"{__package__}.{module.name}")


def get_game(slug: str) -> type[Game] | None:
    """Look up a game by slug, or ``None`` if there is no such game."""
    if not _REGISTRY:
        autodiscover()
    return _REGISTRY.get(slug)


def all_games() -> list[type[Game]]:
    """Every registered game, ordered by title."""
    if not _REGISTRY:
        autodiscover()
    return sorted(_REGISTRY.values(), key=lambda game: game.title)


def games_info() -> list[dict]:
    """Metadata for every game, for listing pages."""
    return [game.info() for game in all_games()]


def game_choices() -> list[tuple[str, str]]:
    """Choices for the ``Game.game`` model field.

    Passed to Django as a callable so it is evaluated lazily -- the registry is
    not yet populated when models are imported, and using a callable also means
    adding a game does not generate a migration.
    """
    return [(game.slug, game.title) for game in all_games()]
