from django.template.defaulttags import register


@register.filter
def board_rows(rows: list, flip: bool = False):
    """Pair every cell with its coordinates so templates can label squares.

    Yields ``(row_index, [(col_index, value), ...])``. With ``flip`` the rows
    come out in reverse, for games where row 0 is the bottom of the board.
    """
    indexed = [(index, list(enumerate(row))) for index, row in enumerate(rows)]

    return list(reversed(indexed)) if flip else indexed
