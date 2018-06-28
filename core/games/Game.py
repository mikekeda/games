"""
Base Game Class
"""

from abc import ABC, abstractmethod

GAMES_INFO = (
    {
        'title': "Tic-tac-toe",
        'classname': "TicTacToe",
        'description': "Tic-tac-toe (also known as noughts and crosses or " +
                       "Xs and Os) is a paper-and-pencil game for two " +
                       "players, X and O, who take turns marking the " +
                       "spaces in a 3×3 grid. The player who succeeds in " +
                       "placing three of their marks in a horizontal, " +
                       "vertical, or diagonal row wins the game."
    },
    {
        'title': "Connect four",
        'classname': "ConnectFour",
        'description': "Connect Four (also known asCaptain's Mistress, " +
                       "Four Up, Plot Four, Find Four, Four in a Row, " +
                       "our in a Line is a two-player connection game " +
                       "in which the players first choose a color " +
                       "and then take turns dropping one colored disc " +
                       "from the top into a seven-column, six-row " +
                       "vertically suspended grid."
    },
)

GAMES = ((game['classname'], game['title']) for game in GAMES_INFO)


class Game(ABC):
    """ Game interface. """
    @classmethod
    @abstractmethod
    def is_board_valid(cls, board: list):
        """ Check if given board is valid. """
        pass

    @classmethod
    @abstractmethod
    def is_valid_move(cls, board: list, player: int, row: int, col: int):
        """ Check if given move is valid. """
        pass

    @classmethod
    @abstractmethod
    def who_is_winner(cls, board: list):
        """ Find out who is the winner. """
        pass

    @classmethod
    @abstractmethod
    def who_is_going_to_move(cls, board: list):
        """ Find out who is going to move. """
        pass

    @classmethod
    @abstractmethod
    def move(cls, board: list, player: int, row: int, col: int):
        """ Make a move. """
        pass

    @classmethod
    @abstractmethod
    def available_moves(cls, board: list):
        """ Return list of available moves for given border. """
        pass

    @classmethod
    @abstractmethod
    def render_board(cls, board: list):
        """ Render given board. """
        pass
