# -*- coding: UTF8 -*-

import itertools
import logging
from typing import Optional, Tuple
import log
from ._misc import iter_is_empty
from .game import Game
from .move import Move
from .result import GameResult
from . import cell, piece, position

_MOVE_TAKE_S = set(['-', 'x'])

def _parse_psn_move(s: str, side: int) -> Optional[Move]:
  it = iter(s)
  t = next(it)
  promoted = False
  if t == '+':
    promoted = True
    t = next(it)
  p = piece.from_upper(t)
  if promoted:
    p = piece.promote(p)
  p *= side
  t = next(it)
  if t == '*':
    col = next(it)
    row = next(it)
    to_cell = cell.usi_parse(col, row)
    if (to_cell is None) or (not iter_is_empty(it)):
      return None
    return Move(None, None, p, to_cell)
  col = t
  row = next(it)
  from_cell = cell.usi_parse(col, row)
  if from_cell is None:
    return None
  if next(it) not in _MOVE_TAKE_S:
    return None
  col = next(it)
  row = next(it)
  to_cell = cell.usi_parse(col, row)
  t = next(it, None)
  to_piece = p
  if not t is None:
    if t == '+':
      to_piece = piece.promote(p)
    elif t != '=':
      return None
    if not iter_is_empty(it):
      return None
  return Move(p, from_cell, to_piece, to_cell)

def _parse_psn_header(line: str) -> Optional[Tuple[str, str]]:
  if not line.startswith('['):
    return None
  i = line.find(' "', 1)
  if i < 0:
    return None
  j = i + 2
  k = line.find('"]', j)
  if k < 0:
    return None
  key = line[1:i].lower()
  value = line[j:k]
  return (key, value)

def game_parse(game_psn: str) -> Game:
  it = iter(game_psn.split('\n'))
  g = Game()
  while True:
    s = next(it, None)
    if s is None:
      log.raise_value_error('no moves')
    p = _parse_psn_header(s)
    if p is None:
      it = itertools.chain([s], it)
      break
    if p[0] == 'sfen':
      if p[1] != position.SFEN_STARTPOS:
        g.set_tag('sfen_startpos', p[1])
    else:
      logging.debug("set_tag: %s %s", p[0], p[1])
      g.set_tag(p[0], p[1])
  for i, s in enumerate(it):
    mn = str(i+1) + '.'
    logging.debug('%s %s', mn, s)
    if not s.startswith(mn):
      break
    jt = iter(s[len(mn):].split())
    t = next(jt, None)
    if t is None:
      break
    if t == 'Mate':
      g.set_result(GameResult.CHECKMATE)
      break
    if t == 'Resigns':
      g.set_result(GameResult.RESIGNATION)
      break
    m = _parse_psn_move(t, g.pos.side_to_move)
    if m is None:
      log.raise_value_error(f'can not parse move {mn}{t}')
    g.do_move(m)
  return g
