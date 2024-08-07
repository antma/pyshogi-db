# -*- coding: UTF8 -*-

_KIFU_PIECES = '歩香桂銀金角飛玉と杏圭全馬龍'
_KIFU_COLS = '１２３４５６７８９'
_KIFU_ROWS = '一二三四五六七八九'

def _create_kifu_dict(s):
  return dict(map(lambda t: (t[1], t[0]), enumerate(s)))

_KIFU_COLS_D = _create_kifu_dict(_KIFU_COLS)
_KIFU_ROWS_D = _create_kifu_dict(_KIFU_ROWS)
_KIFU_PIECES_D = _create_kifu_dict(_KIFU_PIECES)

def _iter_is_empty(it):
  for _ in it:
    return False
  return True

def kifu_move_parse(s: str, last_taken_piece_cell):
  it = iter(s)
  promoted = False
  try:
    t = next(it)
    if t == '同':
      t = next(it)
      if t != '\u3000':
        return None
      to_cell = last_taken_piece_cell
      if to_cell is None:
        return None
    else:
      col = _KIFU_COLS_D.get(t)
      if col is None:
        return None
      row = _KIFU_COLS_D.get(next(it))
      if row is None:
        return None
      to_cell = 9 * row + col
    piece = _KIFU_PIECES_D.get(next(it))
    if piece is None:
      return None
    t = next(it)
    if t == '成':
      promoted = True
      t = next(it)
    if t == '打':
      if promoted or (not _iter_is_empty(it)):
        return None
      return (piece, None, to_cell, None)
    if t != '(':
      return None
    t = next(it)
    if not t.isdigit():
      return None
    col = ord(t) - 49
    t = next(it)
    if not t.isdigit():
      return None
    t = next(it)
    if (t != ')') or (not _iter_is_empty(it)):
      return None
    row = ord(t) - 49
    return (piece, 9 * row + col, to_cell, promoted)
  except StopIteration:
    return None
