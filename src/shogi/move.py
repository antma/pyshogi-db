# -*- coding: UTF8 -*-

from typing import Optional

def _cell(cell: int) -> str:
  row, col = divmod(cell, 9)
  return f'{1 + col}{1 + row}'

class IllegalMove(Exception):
  pass
class Nifu(IllegalMove):
  pass
class UnresolvedCheck(IllegalMove):
  pass

class Move:
  def __init__(self, from_piece: Optional[int], from_cell: Optional[int], to_piece: int, to_cell: int):
    assert((from_cell is None) or (0 <= from_cell < 81))
    assert(0 <= to_cell < 81)
    self.from_piece = from_piece
    self.from_cell = from_cell
    self.to_piece = to_piece
    self.to_cell = to_cell
  def is_drop(self):
    return self.from_cell is None
  def __str__(self):
    a = []
    if not self.from_piece is None:
      a.append(f'from_piece = {self.from_piece}')
      a.append(f'from_cell = {_cell(self.from_cell)}')
    a.append(f'to_piece = {self.to_piece}')
    a.append(f'to_cell = {_cell(self.to_cell)}')
    return 'Move {' + ', '.join(a) + '}'

class UndoMove:
  def __init__(self, taken_piece: int):
    self.taken_piece = taken_piece
