# -*- coding: UTF8 -*-

from typing import Optional

from . import piece

def ascii_cell(cell: int) -> str:
  row, col = divmod(cell, 9)
  return f'{1+col}{1+row}'

class IllegalMove(Exception):
  pass
class Nifu(IllegalMove):
  pass
class UnresolvedCheck(IllegalMove):
  pass

class Move:
  def __init__(self, from_piece: Optional[int], from_cell: Optional[int], to_piece: int, to_cell: int):
    assert((from_cell is None) or (0 <= from_cell < 81))
    assert 0 <= to_cell < 81
    self.from_piece = from_piece
    self.from_cell = from_cell
    self.to_piece = to_piece
    self.to_cell = to_cell
    #-1: illegal
    #0: wasn't validated
    #1: legal
    self.legal = 0
  def __eq__(self, other):
    if not isinstance(other, Move):
      return False
    return (self.from_piece == other.from_piece) and (self.from_cell == other.from_cell) and \
           (self.to_piece == other.to_piece) and (self.to_cell == other.to_cell)
  def is_drop(self):
    return self.from_cell is None
  def __repr__(self):
    a = []
    if not self.from_piece is None:
      a.append(f'from_piece = {self.from_piece}')
      a.append(f'from_cell = {ascii_cell(self.from_cell)}')
    a.append(f'to_piece = {self.to_piece}')
    a.append(f'to_cell = {ascii_cell(self.to_cell)}')
    return 'Move {' + ', '.join(a) + '}'
  def pack_to_int(self):
    '''
    Order such drops fits into 16bits int
    0: is_drop
    [1, 8): to_cell
    [8, 12): abs(to_piece)
    [12, 19): from_cell
    19: promoted
    '''
    if self.is_drop():
      return (abs(self.to_piece) << 8) + (self.to_cell << 1) + 1
    r = 0 if self.from_piece == self.to_piece else 1
    r <<= 7
    r += self.from_cell
    r <<= 4
    r += abs(self.to_piece)
    return ((r << 7) + self.to_cell) << 1
  @staticmethod
  def unpack_from_int(x: int, side: int):
    drop = x & 1
    x >>= 1
    to_cell = x & 0x7f
    x >>= 7
    to_piece = x & 15
    if drop != 0:
      return Move(None, None, to_piece * side, to_cell)
    x >>= 4
    from_cell = x & 0x7f
    x >>= 7
    from_piece = to_piece if x == 0 else to_piece - piece.PROMOTED
    return Move(from_piece * side, from_cell, to_piece * side, to_cell)

class UndoMove:
  def __init__(self, taken_piece: int):
    self.taken_piece = taken_piece
