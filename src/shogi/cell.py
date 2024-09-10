# -*- coding: UTF8 -*-

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
