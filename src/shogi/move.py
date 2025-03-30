# -*- coding: UTF8 -*-

from datetime import timedelta
from typing import Optional

from . import cell
from . import piece

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
    self.time = None
    self.cum_time = None
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
      a.append(f'from_cell = {cell.digital_str(self.from_cell)}')
    a.append(f'to_piece = {self.to_piece}')
    a.append(f'to_cell = {cell.digital_str(self.to_cell)}')
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
  def usi_str(self) -> str:
    if self.is_drop():
      return piece.to_string(abs(self.to_piece)) + '*' + cell.usi_str(self.to_cell)
    s = cell.usi_str(self.from_cell) + cell.usi_str(self.to_cell)
    if self.from_piece != self.to_piece:
      assert piece.promote(self.from_piece) == self.to_piece
      s += '+'
    return s
  def kifu_str(self, prev) -> str:
    ''' converts parsed move back to kifu '''
    prev_to_cell = prev and prev.to_cell
    if not self.from_cell is None:
      t = '(' + cell.digital_str(self.from_cell) + ')'
    else:
      t = ''
    if prev_to_cell == self.to_cell:
      r = '同\u3000'
    else:
      r = cell.kifu_str(self.to_cell)
    if self.from_cell is None:
      return r + piece.kifu_str(self.to_piece) + '打' + t
    if self.from_piece == self.to_piece:
      return r + piece.kifu_str(self.to_piece) + t
    return r + piece.kifu_str(self.from_piece) + '成' + t
  def time_str(self) -> Optional[str]:
    if self.time is None:
      return None
    m, s = divmod(round(self.time.total_seconds()), 60)
    return str(m) + ':' + str(s)
  def cum_time_str(self) -> Optional[str]:
    if self.cum_time is None:
      return None
    t, s = divmod(round(self.cum_time.total_seconds()), 60)
    h, m = divmod(t, 60)
    return str(h) + ':' + str(m) + ':' + str(s)
  def zero_or_none_time(self) -> bool:
    return (self.time is None) or (self.time == timedelta.min)
  def drop_times(self):
    self.time = None
    self.cum_time = None

class UndoMove:
  def __init__(self, taken_piece: int):
    self.taken_piece = taken_piece
