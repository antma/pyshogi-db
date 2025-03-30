# -*- coding: UTF8 -*-

import logging
from typing import Optional

from . import piece

KIFU_COLS = '１２３４５６７８９'
KIFU_ROWS = '一二三四五六七八九'

def digital_str(cell: int) -> str:
  row, col = divmod(cell, 9)
  return f'{1+col}{1+row}'

def usi_str(cell: int) -> str:
  row, col = divmod(cell, 9)
  return chr(49 + col) + chr(97 + row)

def kifu_str(cell: int) -> str:
  (row, col) = divmod(cell, 9)
  return KIFU_COLS[col] + KIFU_ROWS[row]

def usi_parse(col: str, row: str) -> Optional[int]:
  x = int(col) - 1
  if not 0 <= x < 9:
    logging.warning('column %s is not in [1-9]', col)
    return None
  y = ord(row) - 97
  if not 0 <= y < 9:
    logging.warning('row %s is not in [1-9]', row)
    return None
  return 9 * y + x

def digital_parse(s: str) -> Optional[int]:
  if len(s) != 2:
    logging.warning('digital_parse(): cell.digital_parse illegal input string length')
    return None
  it = iter(s)
  x = int(next(it)) - 1
  if not 0 <= x < 9:
    logging.warning("digital_parse(): column %s is not in [1-9] for input '%s'", x, s)
    return None
  y = int(next(it)) - 1
  if not 0 <= y < 9:
    logging.warning("digital_parse(): row %s is not in [1-9] for input '%s'", y, s)
    return None
  return 9 * y + x

def can_drop(cell: int, p: int) -> bool:
  assert 0 < abs(p) < piece.KING
  if p == piece.LANCE or p == piece.PAWN:
    return cell >= 9
  if p == -piece.LANCE or p == -piece.PAWN:
    return cell < 72
  if p == piece.KNIGHT:
    return cell >= 18
  if p == -piece.KNIGHT:
    return cell < 63
  return True
