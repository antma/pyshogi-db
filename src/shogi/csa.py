# -*- coding: UTF8 -*-
''' parsing CSA format files downloaded from Shogi Quest application
    https://gist.github.com/Marken-Foo/b1047990ee0c65537582ebe591e2b6d7
'''
from typing import Optional

import log
from . import piece
from .game import Game
from .move import Move
from .position import Position
from .result import GameResult

def _create_csa_dict(s, offset = 0):
  return dict(map(lambda t: (t[1], t[0] + offset), enumerate(s)))

_PIECES_D = _create_csa_dict(piece.CSA_PIECES, 1)

def _parse_cell(it) -> Optional[int]:
  col = int(next(it))
  row = int(next(it))
  if (col == 0) and (row == 0):
    return None
  r = range(1, 10)
  if col not in r:
    log.raise_value_error('illegal column (column = %d)', col)
  if row not in r:
    log.raise_value_error('illegal row (row = %d)', row)
  return 9 * (row - 1) + (col - 1)

def _parse_move(pos: Position, s: str) -> Optional[Move]:
  it = iter(s)
  t = next(it, None)
  side = None
  if t == '+':
    side = 1
  elif t == '-':
    side = -1
  if side is None:
    return None
  from_cell = _parse_cell(it)
  to_cell = _parse_cell(it)
  if to_cell is None:
    log.raise_value_error(f'_parse_move(): illegal to_cell (move = {s})')
  p = ''.join(it)
  to_piece = _PIECES_D.get(p)
  if to_piece is None:
    log.raise_value_error(f'_parse_move(): illegal piece (piece = {p}, move = {s})')
  to_piece *= side
  if from_cell is None:
    return Move(None, None, to_piece, to_cell)
  from_piece = pos.board[from_cell]
  if piece.unpromote(from_piece) != piece.unpromote(to_piece):
    log.raise_value_error(f'_parse_move(): from_piece and to_piece contradict each other (move = {s}, from_piece = {from_piece}, to_piece = {to_piece})')
  if piece.is_promoted(from_piece) and (not piece.is_promoted(to_piece)):
    log.raise_value_error(f'_parse_move(): from_piece is promoted, but to_piece is not(move = {s}, from_piece = {from_piece}, to_piece = {to_piece})')
  return Move(from_piece, from_cell, to_piece, to_cell)

def game_parse(game_kif: str) -> Game:
  g = Game()
  it = iter(game_kif.split('\n'))
  t = next(it)
  if t != "'Shogi Quest":
    log.raise_value_error('Expected shogi quest')
  g.set_tag('location', 'Shogi Quest')
  t = next(it)
  if not t.startswith('N+'):
    log.raise_value_error('Expected sente')
  g.parse_player_name(t[2:], 'sente')
  t = next(it)
  if not t.startswith('N-'):
    log.raise_value_error('Expected gote')
  g.parse_player_name(t[2:], 'gote')
  for i in range(1, 10):
    t = next(it)
    if not t.startswith('P' + str(i)):
      log.raise_value_error('Expected starting position')
  if next(it) != '+':
    log.raise_value_error('Expected sente is side of first move')
  while True:
    t = next(it)
    if t.startswith('%'):
      if t == '%TORYO':
        g.set_result(GameResult.RESIGNATION)
      else:
        log.raise_value_error(f'unknown result (result={t}')
      break
    m = _parse_move(g.pos, t)
    if m is None:
      log.raise_value_error(f'can not parse move (move = {t})')
    g.do_move(m)
    t = next(it)
  return g
