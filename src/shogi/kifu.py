# -*- coding: UTF8 -*-

import logging

from typing import Optional
from . import move
from . import piece

_KIFU_PIECES = '歩香桂銀金角飛玉と杏圭全?馬龍'
_KIFU_COLS = '１２３４５６７８９'
_KIFU_ROWS = '一二三四五六七八九'

def _create_kifu_dict(s, offset = 0):
  return dict(map(lambda t: (t[1], t[0] + offset), filter(lambda t: t[1] != '?', enumerate(s))))

_KIFU_COLS_D = _create_kifu_dict(_KIFU_COLS)
_KIFU_ROWS_D = _create_kifu_dict(_KIFU_ROWS)
_KIFU_PIECES_D = _create_kifu_dict(_KIFU_PIECES, 1)

def _iter_is_empty(it):
  for _c in it:
    return False
  return True

def move_parse(s: str, side_to_move: int, last_move: Optional[move.Move]) -> Optional[move.Move]:
  it = iter(s)
  promoted = False
  try:
    t = next(it)
    if t == '同':
      t = next(it)
      if t != '\u3000':
        logging.debug('expected unicode wide space')
        return None
      to_cell = last_move and last_move.to_cell
      if to_cell is None:
        return None
    else:
      col = _KIFU_COLS_D.get(t)
      if col is None:
        logging.debug('expected to column, but %s found', t)
        return None
      row = _KIFU_ROWS_D.get(next(it))
      if row is None:
        logging.debug('expected to row, but %s found', t)
        return None
      to_cell = 9 * row + col
    p = _KIFU_PIECES_D.get(next(it))
    if p is None:
      return None
    t = next(it)
    if t == '成':
      promoted = True
      t = next(it)
    if t == '打':
      if promoted or (not _iter_is_empty(it)):
        return None
      return move.Move(None, None, side_to_move * p, to_cell)
    if t != '(':
      logging.debug("expected '(', but '%s' found", t)
      return None
    t = next(it)
    if not t.isdigit():
      logging.debug('expected from column, but %s found', t)
      return None
    col = int(t) - 1
    if not (0 <= col < 9):
      logging.debug('from column is not in [1..9]')
      return None
    row = next(it)
    if not row.isdigit():
      logging.debug('expected from row, but %s found', row)
      return None
    t = next(it)
    if t != ')':
      logging.debug("expected ')', but '%s' found", t)
      return None
    if not _iter_is_empty(it):
      logging.debug("extra data")
      return None
    row = int(row) - 1
    if not (0 <= row < 9):
      logging.debug('from row is not in [1..9]')
      return None
    to_piece = piece.promote(p) if promoted else p
    logging.debug('row = %s, col = %s', row, col)
    return move.Move(side_to_move * p, 9 * row + col, side_to_move * to_piece, to_cell)
  except StopIteration:
    logging.debug("not enough data")
    return None
