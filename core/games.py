from collections import Counter
from copy import deepcopy

GAMES = (
    ('TicTacToe', 'Tic-tac-toe'),
)


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
)


class TicTacToe:
    title = GAMES_INFO[0]['title']
    rows = 3
    cols = 3
    need_players = 2
    current_turn = 0
    cell_empty_value = '*'
    render_empty_value = ''
    cell_values = ('X', 'O')
    render_values_map = {
        cell_empty_value: '',
        cell_values[0]: '✕',
        cell_values[1]: '◯'
    }
    board = [[cell_empty_value] * cols] * rows

    @classmethod
    def is_board_valid(cls, board):
        linear_board = [cell for row in board for cell in row]
        board_counter = Counter(linear_board)

        allowed_values = {cls.cell_empty_value, *set(cls.cell_values)}
        if set(board_counter.keys()) - allowed_values:
            return False, 'Only {} are allowed'.format(
                ', '.join(allowed_values))

        if not (board_counter[cls.cell_values[1]] <=
                board_counter[cls.cell_values[0]] <=
                board_counter[cls.cell_values[1]] + 1):
            return False, "The balance of values isn't correct"

        return True, None

    @classmethod
    def is_valid_move(cls, board, player, row, col):
        if board[row][col] != cls.cell_empty_value or \
                cls.who_is_winner(board) is not None:
            return False

        board[row][col] = cls.cell_values[player]

        if not cls.is_board_valid(board)[0]:
            return False

        return True

    @classmethod
    def who_is_winner(cls, board):
        """ Figure out who is the winner. -1 - means it's a draw. """
        for row in board:
            if row[0] != cls.cell_empty_value and \
                    all(cell == row[0] for cell in row[1:]):
                return cls.cell_values.index(row[0])

        for j in range(cls.cols):
            if board[0][j] != cls.cell_empty_value and all(
                    board[i][j] == board[0][j] for i in range(1, cls.rows)):
                return cls.cell_values.index(board[0][j])

        if board[0][0] != cls.cell_empty_value and all(
                board[i][i] == board[0][0] for i in range(1, cls.rows)):
            return cls.cell_values.index(board[0][0])

        if board[cls.rows - 1][0] != cls.cell_empty_value and all(
                board[cls.rows - 1 - i][i] == board[cls.rows - 1][0]
                for i in range(1, cls.rows)
        ):
            return cls.cell_values.index(board[cls.rows - 1][0])

        if all(
                board[i][j] != cls.cell_empty_value
                for i in range(cls.rows)
                for j in range(cls.cols)
        ):
            # Check a draw.
            return -1

        return None

    @classmethod
    def who_is_going_to_move(cls, board):
        linear_board = [cell for row in board for cell in row]
        board_counter = Counter(linear_board)

        return board_counter[cls.cell_values[0]] - \
            board_counter[cls.cell_values[1]]

    @classmethod
    def move(cls, board, player, row, col):
        if cls.is_valid_move(deepcopy(board), player, row, col):
            board[row][col] = cls.cell_values[player]

        return board

    @classmethod
    def available_moves(cls, board):
        for i in range(cls.rows):
            for j in range(cls.cols):
                if board[i][j] == cls.cell_empty_value:
                    yield i, j

    @classmethod
    def render_board(cls, board):
        for i, row in enumerate(board):
            board[i] = [
                cls.render_values_map.get(cell, cell)
                for cell in row
            ]

        return board
