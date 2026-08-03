/*
 * Client for a single game.
 *
 * Two ways of entering a move are supported, chosen by the board's
 * data-move-style attribute:
 *
 *   place  - click a square to drop a token there (tic-tac-toe, connect four)
 *   select - click one of your pieces, then click where it should go (chess)
 *
 * The server is authoritative: every click is sent as-is and the board is
 * redrawn from whatever comes back.
 */
(function () {
  'use strict';

  var board = document.querySelector('table.board');
  if (!board) {
    return;
  }

  function config(id, fallback) {
    var node = document.getElementById(id);
    return node ? JSON.parse(node.textContent) : fallback;
  }

  var players = config('game-players', []);
  var seat = config('game-seat', null);
  var gameId = config('game-id', null);
  var moveStyle = board.dataset.moveStyle || 'place';

  var info = document.getElementById('info');
  var selected = null;
  var legalMoves = [];

  var protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  var socket = new WebSocket(protocol + '://' + window.location.host + '/ws/game/' + gameId);

  function cell(row, col) {
    return board.querySelector('td[data-row="' + row + '"][data-col="' + col + '"]');
  }

  function coords(td) {
    return [parseInt(td.dataset.row, 10), parseInt(td.dataset.col, 10)];
  }

  function send(move) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ move: move }));
    }
  }

  function clearSelection() {
    if (selected) {
      selected.classList.remove('selected');
      selected = null;
    }
    board.querySelectorAll('td.target').forEach(function (td) {
      td.classList.remove('target');
    });
  }

  function movesFrom(row, col) {
    return legalMoves.filter(function (move) {
      return move.from && move.from[0] === row && move.from[1] === col;
    });
  }

  function showError(message) {
    var node = info && info.querySelector('p.error');
    if (!node) {
      return;
    }
    node.textContent = message;
    node.style.display = message ? '' : 'none';
  }

  board.addEventListener('click', function (event) {
    var td = event.target.closest('td');
    if (!td || !board.contains(td)) {
      return;
    }

    showError('');
    var position = coords(td);

    if (moveStyle !== 'select') {
      send({ to: position });
      return;
    }

    if (selected) {
      var origin = coords(selected);
      clearSelection();
      send({ from: origin, to: position });
      return;
    }

    var options = movesFrom(position[0], position[1]);
    if (!options.length) {
      return;
    }

    selected = td;
    td.classList.add('selected');
    options.forEach(function (move) {
      var target = cell(move.to[0], move.to[1]);
      if (target) {
        target.classList.add('target');
      }
    });
  });

  function render(data) {
    for (var row = 0; row < data.board.length; row += 1) {
      for (var col = 0; col < data.board[row].length; col += 1) {
        var td = cell(row, col);
        if (td) {
          td.textContent = data.board[row][col];
          td.classList.remove('win');
        }
      }
    }

    (data.highlight || []).forEach(function (square) {
      var td = cell(square[0], square[1]);
      if (td) {
        td.classList.add('win');
      }
    });
  }

  function updateStatus(data) {
    if (!info) {
      return;
    }

    info.querySelectorAll('p').forEach(function (node) {
      node.style.display = 'none';
    });

    if (data.winner === null || data.winner === undefined) {
      var turn = info.querySelector('#who_is_going_to_move');
      if (turn) {
        turn.textContent = players[data.turn];
      }
      info.querySelector('p.waiting').style.display = '';
    } else if (data.winner === -1) {
      info.querySelector('p.draw').style.display = '';
    } else {
      var winner = info.querySelector('#winner');
      if (winner) {
        winner.textContent = players[data.winner];
      }
      info.querySelector('p.winner').style.display = '';
    }
  }

  function setTurnState(data) {
    var yourTurn = seat !== null && data.turn === seat && data.winner === null;
    board.classList.toggle('your-turn', yourTurn);
    board.classList.toggle('waiting', !yourTurn);
  }

  socket.onmessage = function (event) {
    var data = JSON.parse(event.data);

    if (data.error) {
      showError(data.error);
      return;
    }

    legalMoves = data.moves || [];
    clearSelection();
    render(data);
    updateStatus(data);
    setTurnState(data);
  };

  socket.onclose = function () {
    board.classList.add('disconnected');
  };
})();
