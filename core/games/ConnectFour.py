from collections import Counter
from copy import deepcopy

from core.games.Game import Game, GAMES_INFO


class ConnectFour(Game):
    title = GAMES_INFO[1]["title"]
    rows = 6
    cols = 7
    need_players = 2
    current_turn = 0
    cell_empty_value = "*"
    cell_values = ("X", "O")
    render_values_map = {cell_empty_value: "", cell_values[0]: "🔵", cell_values[1]: "🔴"}
    board = [[cell_empty_value] * cols] * rows
    need_inline_to_win = 4

    @classmethod
    def is_board_valid(cls, board):
        linear_board = [cell for row in board for cell in row]
        board_counter = Counter(linear_board)

        allowed_values = {cls.cell_empty_value, *set(cls.cell_values)}
        if set(board_counter.keys()) - allowed_values:
            return False, "Only {} are allowed".format(", ".join(allowed_values))

        if not (
            board_counter[cls.cell_values[1]]
            <= board_counter[cls.cell_values[0]]
            <= board_counter[cls.cell_values[1]] + 1
        ):
            return False, "The balance of values isn't correct"

        for col in range(cls.cols):
            cursor = 0
            for row in range(cls.rows):
                if board[row][col] != cls.cell_empty_value:
                    if row != cursor:
                        return False, "Invalid move"

                    cursor += 1

        return True, None

    @classmethod
    def is_valid_move(cls, board, player, row, col):
        if any([row < 0, row >= cls.rows, col < 0, col >= cls.cols]):
            return False

        if (
            board[row][col] != cls.cell_empty_value
            or cls.who_is_winner(board) is not None
        ):
            return False

        board[row][col] = cls.cell_values[player]

        return cls.is_board_valid(board)[0]

    @classmethod
    def who_is_winner(cls, board):
        """ Figure out who is the winner. -1 - means it's a draw. """
        for player, cell in enumerate(cls.cell_values):
            for row in board:
                if cell * cls.need_inline_to_win in "".join(row):
                    return player

            for j in range(cls.cols):
                if cell * cls.need_inline_to_win in "".join([row[j] for row in board]):
                    return player

            for k in range(
                -(cls.rows - cls.need_inline_to_win),
                cls.cols - cls.need_inline_to_win + 1,
            ):
                i, j = 0, 0
                if k < 0:
                    j = -k
                else:
                    i = k

                row = []
                while i < cls.rows and j < cls.cols:
                    row.append(board[i][j])
                    i += 1
                    j += 1

                if cell * cls.need_inline_to_win in "".join(row):
                    return player

            for k in range(
                -(cls.rows - cls.need_inline_to_win),
                cls.cols - cls.need_inline_to_win + 1,
            ):
                i, j = cls.rows - 1, 0
                if k < 0:
                    j = -k
                else:
                    i = cls.rows - k - 1

                row = []
                while i >= 0 and j < cls.cols:
                    row.append(board[i][j])
                    i -= 1
                    j += 1

                if cell * cls.need_inline_to_win in "".join(row):
                    return player

        if all(
            board[i][j] != cls.cell_empty_value
            for i in range(cls.rows)
            for j in range(cls.cols)
        ):
            return -1  # draw

        return None

    @classmethod
    def who_is_going_to_move(cls, board):
        linear_board = [cell for row in board for cell in row]
        board_counter = Counter(linear_board)

        return board_counter[cls.cell_values[0]] - board_counter[cls.cell_values[1]]

    @classmethod
    def move(cls, board, player, row, col):
        if cls.is_valid_move(deepcopy(board), player, row, col):
            board[row][col] = cls.cell_values[player]

        return board

    @classmethod
    def bot_move(cls, board, player):
        """ Bot make a move. """

        return board

    @classmethod
    def available_moves(cls, board):
        for j in range(cls.cols):
            for i in range(cls.rows):
                if board[i][j] == cls.cell_empty_value:
                    yield i, j
                    break

    @classmethod
    def render_board(cls, board):
        for i, row in enumerate(board):
            board[i] = [cls.render_values_map.get(cell, cell) for cell in row]

        return board
