import core.games


def games_list(request):
    """ List of available games. """
    return {'games': core.games.GAMES_INFO}
