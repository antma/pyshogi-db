# -*- coding: UTF8 -*-

import logging
from typing import Optional

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
  return 9 * y + x
