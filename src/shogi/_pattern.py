# -*- coding: UTF8 -*-

from enum import IntEnum
import logging
from typing import List, Optional, Union

from . import cell
from . import piece
from . import position
from .move import Move

_Operation = IntEnum('_Operation', ['IN', 'NOT_IN', 'PIECES_EQ', 'FROM_IN', 'TO_IN', 'MAX_MOVES'])
_GENERALS_S = set([piece.SILVER, piece.GOLD, piece.PROMOTED + piece.SILVER])

def adjacent_pawns(row: int, start_col: int, end_col: int, excl: List[int]):
  row = str(row)
  s = set(excl)
  return [('P', str(col) + row) for col in range(start_col, end_col) if not col in s]

def _swinging_rook_column(col: int) -> bool:
  return 1 <= col <= 5

class PositionForPatternRecognition(position.Position):
  def __init__(self, sfen: str = None):
    super().__init__(sfen)
    self._taken_general = False
    self.last_move = None
    self._count_moves_d = {}
    self._was_drops = False
  def do_move(self, m: Move):
    u = super().do_move(m)
    if (not u is None) and abs(u.taken_piece) in _GENERALS_S:
      self._taken_general = True
    self.last_move = m
    p = m.from_piece
    if not p is None:
      self._count_moves_d[p] = self._count_moves_d.get(p, 0) + 1
    if (not self._was_drops) and m.is_drop():
      self._was_drops = True
  def is_opening(self) -> bool:
    return not self._taken_general
  def count_piece_moves(self, p: int) -> int:
    return self._count_moves_d.get(p, 0)
  def first_rook_move_rank(self, m: Move) -> Optional[int]:
    if self._was_drops:
      return None
    side = self.side_to_move
    assert side * m.to_piece > 0
    rook = side * piece.ROOK
    if m.from_piece != rook or self._count_moves_d.get(rook, 0) > 0:
      return None
    col = (m.to_cell % 9) + 1
    if side > 0:
      col = 10 - col
    king = side * piece.KING
    if _swinging_rook_column(col) and self._count_moves_d.get(king, 0) > 0:
      return None
    return col

def _latin_to_piece(s: str) -> int:
  if s.islower():
    p = piece.from_upper(s.upper())
    assert p > 0
    return -p
  p = piece.from_upper(s)
  assert p > 0
  return p

class _PiecePattern:
  def __init__(self, piece_latin_letter: str, cell_pattern: Union[str,int]):
    self._repr = (piece_latin_letter, cell_pattern)
    if piece_latin_letter == 'max-gold-moves':
      self._op = _Operation.MAX_MOVES
      self._piece = piece.GOLD
      assert isinstance(cell_pattern, int)
      self._count = cell_pattern
      self._list = None
      return
    self._op = _Operation.IN
    if piece_latin_letter.startswith('!'):
      self._op = _Operation.NOT_IN
      self._piece = _latin_to_piece(piece_latin_letter[1:])
    elif piece_latin_letter == ' ':
      self._piece = piece.FREE
    elif piece_latin_letter == 'from':
      self._op = _Operation.FROM_IN
      self._piece = None
    elif piece_latin_letter == 'to':
      self._op = _Operation.TO_IN
      self._piece = None
    else:
      self._piece = _latin_to_piece(piece_latin_letter)
    if isinstance(cell_pattern, int):
      self._op = _Operation.PIECES_EQ
      self._count = cell_pattern
      self._list = None
    else:
      self._count = None
      self._list = list(map(cell.digital_parse, cell_pattern.split(',')))
  def __str__(self):
    return f'PiecePattern({self._repr})'
  def match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    if self._op == _Operation.IN:
      return any(pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece for c in self._list)
    if self._op == _Operation.NOT_IN:
      return all(pos.board[c if side > 0 else cell.swap_side(c)] != side * self._piece for c in self._list)
    if self._op == _Operation.PIECES_EQ:
      p = pos.sente_pieces if side * self._piece > 0 else pos.gote_pieces
      return p[abs(self._piece) - 1] == self._count
    if self._op == _Operation.MAX_MOVES:
      return pos.count_piece_moves(self._piece * side) <= self._count
    m = pos.last_move
    if m is None:
      return False
    c = m.from_cell if self._op == _Operation.FROM_IN else m.to_cell
    if c is None:
      return False
    if side < 0:
      c = cell.swap_side(c)
    return c in self._list
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    res = self.match(pos, side)
    if not res:
      logging.debug('%s not matched', self)
    return res

class _PositionPattern:
  def __init__(self, data: list):
    self._patterns = list(map(lambda t: _PiecePattern(t[0], t[1]), data))
  def match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.match(pos, side) for p in self._patterns)
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.debug_match(pos, side) for p in self._patterns)

class Recognizer:
  def __init__(self, p):
    self._position_patterns = [(_PositionPattern(data), value) for data, value in p]
  def find(self, pos: PositionForPatternRecognition):
    side = -pos.side_to_move
    for p, ct in self._position_patterns:
      if p.debug_match(pos, side):
        return ct
      logging.debug('Pattern %s not matched', ct.name)
    return None
  def update_set(self, pos: PositionForPatternRecognition, sente_set: set, gote_set: set):
    ct = self.find(pos)
    if not ct is None:
      st = sente_set if pos.side_to_move < 0 else gote_set
      if ct in st:
        return False
      st.add(ct)
      return True
    return False
