# -*- coding: UTF8 -*-

import logging

from . import cell
from . import piece
from .position import Position

class _PiecePattern:
  def __init__(self, piece_latin_letter: str, cell_pattern: str):
    self.op_eq = True
    if piece_latin_letter.startswith('!'):
      self.op_eq = False
      self._piece = piece.from_upper(piece_latin_letter[1:])
      assert self._piece > 0
    elif piece_latin_letter == ' ':
      self._piece = piece.FREE
    else:
      self._piece = piece.from_upper(piece_latin_letter)
      assert self._piece > 0
    self._list = list(map(cell.digital_parse, cell_pattern.split(',')))
  def match(self, pos: Position, side: int) -> bool:
    if self.op_eq:
      return any(pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece for c in self._list)
    return all(pos.board[c if side > 0 else cell.swap_side(c)] != side * self._piece for c in self._list)

class PositionPattern:
  def __init__(self, data: list):
    self._patterns = list(map(lambda t: _PiecePattern(t[0], t[1]), data))
  def match(self, pos: Position, side: int) -> bool:
    return all(p.match(pos, side) for p in self._patterns)
