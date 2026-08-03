Games
======================

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/705d72004f7f46daa23202e59cc4718a)](https://app.codacy.com/manual/mikekeda/games?utm_source=github.com&utm_medium=referral&utm_content=mikekeda/games&utm_campaign=Badge_Grade_Dashboard)
[![Requirements Status](https://requires.io/github/mikekeda/games/requirements.svg?branch=master)](https://requires.io/github/mikekeda/games/requirements/?branch=master)

This is site where you can play board games.
Link to the site - [https://games.mkeda.me](https://games.mkeda.me)

Available Games
------------
-   **Tic-tac-toe** - Game for two players, X and O, who take turns marking the spaces in a 3×3 grid.
-   **Connect four** - Two players drop discs into a seven-column, six-row grid and try to line up four.
-   **Reversi** - Trap lines of your opponent's discs on an 8x8 board to flip them, and hold the most discs at the end.

Adding a game
------------
Games live in `core/games/`. Dropping a module in that directory is all it
takes: the registry imports everything in the package at startup, so there is
no list to update, no template to write and no migration to generate.

A game that is won by lining up tokens on a grid only needs its metadata:

```python
# core/games/gomoku.py
from core.games.base import LineUpGame
from core.games.bots import NegamaxBot
from core.games.registry import register


@register
class Gomoku(LineUpGame):
    slug = "Gomoku"            # stable id, used in URLs and stored in the db
    title = "Gomoku"
    description = "Line up five stones on a 15x15 board."

    rows = 15
    cols = 15
    need_in_line = 5
    tokens = ("B", "W")
    render_map = {"*": "", "B": "⚫", "W": "⚪"}
    cell_size = 32
    bot = NegamaxBot
```

Add `static/img/Gomoku.svg` for the card on the home page and it is playable.

The pieces you can override:

| Hook | Purpose |
| --- | --- |
| `initial_state()` | Opening position, including any `extra` state |
| `legal_moves(state)` | Which moves are available (ConnectFour uses this for gravity) |
| `apply(state, player, move)` | Produce the next state; must not mutate its input |
| `outcome(state)` | `Outcome(winner=...)`, or `None` while the game runs |
| `validate(state)` | Reject unreachable positions |
| `allowed_values()` | Cell values `validate` accepts; defaults to one token per player |
| `heuristic(state, player)` | Score a position so search bots can cut off |
| `move_style` | `place` (click a square) or `select` (click a piece, then its target) |
| `flip_board` | Draw row 0 at the bottom |

Games with travelling pieces subclass `GridGame` rather than `LineUpGame`, set
`move_style = MoveStyle.SELECT`, and use the `from_row`/`from_col` fields on
`Move`. They also need to override `allowed_values()`, because the default only
allows one token per player and a board of chess pieces has many. Anything that
does not fit on the grid (castling rights, en passant, a draw counter) goes in
`GameState.extra`, which is persisted as JSON. Every move is written to
`GameMove`, so rules that depend on history have a record to work from.

`core/tests/tests_engine.py` carries a deliberately tiny travelling-piece game
called `Hunt`, which is the worked example for all of the above.

Boards are drawn by `templates/games/board.html` and sized from the game's
`cell_size`; a game only needs `templates/games/<slug>.html` if the generic
grid cannot draw it.

Installation
------------
    # Install Redis
    sudo apt install redis-server
    # Install postgresql
    sudo add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install postgresql-10
    # Configure database
    sudo su - postgres
    psql
    CREATE USER games_admin WITH PASSWORD 'home_pass';
    CREATE DATABASE games;
    GRANT ALL PRIVILEGES ON DATABASE games to games_admin;
    # Install packages
    pip install -r requirements.txt
    # Apply migrations
    python manage.py migrate
    # Create an admin user
    python manage.py createsuperuser

Running
-------
    # Locally (runserver speaks ASGI because daphne is installed, so
    # websockets work in development too)
    python manage.py runserver

    # DEBUG defaults to on locally. Set it explicitly to turn it off:
    GAMES_DEBUG=0 python manage.py runserver

Rebuilding the stylesheet
-------
    cd static && npm install   # bootstrap and jquery
    npm install                # dart-sass, postcss
    npm start

**The sass build is currently broken, and `npm start` overwrites
`static/css/style.css` with an error stylesheet.** The vendored
`static/node_modules/bootstrap` is 5.3.3, while `sass/_bootstrap.scss` imports
partials that Bootstrap 5 removed (`jumbotron`, `media`, `custom-forms`,
`print`) and the templates still use Bootstrap 4 markup. The committed
`static/css/style.css` is Bootstrap 4.0.0 output and is what the site serves,
so keep a copy before running the build.

Two ways out, both a deliberate change rather than a rebuild:

* Build against Bootstrap 4 (`npm install --no-save bootstrap@4.6.2` and point
  `--load-path` at `node_modules`). This works, but 4.0 to 4.6 rewrites roughly
  60% of the rules, so it needs a visual pass over every page.
* Migrate `sass/_bootstrap.scss` and the templates to Bootstrap 5.

Board and card-artwork styling deliberately lives in `static/css/games.css`,
outside the sass build, so adding a game never depends on any of this.

Upgrade python packages
-------
    # Remove versions from requirements.txt
    # Upgrade python packages
    pip install --upgrade --force-reinstall -r requirements.txt
    # Update requirements.txt
    pip freeze > requirements.txt

Useful manage.py commands
-------
    # Run tests
    python manage.py test
    # Run tests and check code style and coverage
    python manage.py jenkins --enable-coverage --pep8-exclude migrations --pylint-rcfile .pylintrc
