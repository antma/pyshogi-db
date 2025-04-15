# -*- coding: UTF8 -*-

from enum import IntEnum
import logging
from typing import List, Optional, Union

from . import cell
from . import piece
from . import position
from .move import Move

_Operation = IntEnum('_Operation', ['IN', 'NOT_IN', 'PIECES_EQ', 'FROM_IN', 'TO_IN', 'MAX_MOVES', 'SIDE'])
_GENERALS_S = set([piece.SILVER, piece.GOLD, piece.PROMOTED + piece.SILVER])
_BISHOP_S = set([piece.BISHOP, piece.HORSE])
_ROOK_S = set([piece.ROOK, piece.DRAGON])

def adjacent_pawns(row: int, start_col: int, end_col: int, excl: List[int]):
  row = str(row)
  s = set(excl)
  return [('P', str(col) + row) for col in range(start_col, end_col) if not col in s]

_FIRST_ROW = 'LNSGKGSNL'

def last_row_pieces(excl: str):
  a = []
  s = set(map(int, excl))
  for i, c in enumerate(_FIRST_ROW):
    col = i + 1
    if not col in s:
      a.append((c, str(col) + '9'))
  return a

def _swinging_rook_column(col: int) -> bool:
  return 1 <= col <= 5

class PositionForPatternRecognition(position.Position):
  def __init__(self, sfen: str = None):
    super().__init__(sfen)
    self._taken_general = False
    self._taken_bishop = False
    self._taken_rook = False
    self.last_move = None
    self._count_moves_d = {}
    self._was_drops = False
    self._cached_sfen = None
  def do_move(self, m: Move):
    self._cached_sfen = None
    u = super().do_move(m)
    if not u is None:
      tp = abs(u.taken_piece)
      if (not self._taken_general) and tp in _GENERALS_S:
        self._taken_general = True
      if (not self._taken_bishop) and tp in _BISHOP_S:
        self._taken_bishop = True
      if (not self._taken_rook) and tp in _ROOK_S:
        self._taken_rook = True
    self.last_move = m
    p = m.from_piece
    if not p is None:
      self._count_moves_d[p] = self._count_moves_d.get(p, 0) + 1
    if (not self._was_drops) and m.is_drop():
      self._was_drops = True
  def sfen(self, move_no = True) -> str:
    if not move_no:
      return super().sfen(move_no)
    if self._cached_sfen is None:
      self._cached_sfen = super().sfen()
    return self._cached_sfen
  def is_opening(self) -> bool:
    return not (self._taken_general or self._taken_rook)
  def count_piece_moves(self, p: int) -> int:
    return self._count_moves_d.get(p, 0)
  def first_rook_move_rank(self, m: Move) -> Optional[int]:
    if self._was_drops or self._taken_bishop:
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
  def _op_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return any(pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece for c in self._list)
  def _op_not_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(pos.board[c if side > 0 else cell.swap_side(c)] != side * self._piece for c in self._list)
  def _op_pieces_eq(self, pos: PositionForPatternRecognition, side: int) -> bool:
    p = pos.sente_pieces if side * self._piece > 0 else pos.gote_pieces
    return p[abs(self._piece) - 1] == self._count
  def _op_max_moves(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.count_piece_moves(self._piece * side) <= self._count
  def _op_side(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return side == self._count
  def _op_from_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    m = pos.last_move
    if m is None:
      return False
    c = m.from_cell
    if c is None:
      return False
    if side < 0:
      c = cell.swap_side(c)
    return c in self._list
  def _op_to_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    m = pos.last_move
    if m is None:
      return False
    c = m.to_cell
    assert not c is None
    if side < 0:
      c = cell.swap_side(c)
    return c in self._list
  def __init__(self, piece_latin_letter: str, cell_pattern: Union[str,int]):
    self._repr = (piece_latin_letter, cell_pattern)
    self._piece = None
    self._count = None
    self._list = None
    if piece_latin_letter == 'side':
      self._op = _Operation.SIDE
      self.match = _PiecePattern._op_side
      assert isinstance(cell_pattern, int)
      self._count = cell_pattern
      return
    if piece_latin_letter == 'max-gold-moves':
      self._op = _Operation.MAX_MOVES
      self.match = _PiecePattern._op_max_moves
      self._piece = piece.GOLD
      assert isinstance(cell_pattern, int)
      self._count = cell_pattern
      return
    self._op = _Operation.IN
    self.match = _PiecePattern._op_in
    if piece_latin_letter.startswith('!'):
      self._op = _Operation.NOT_IN
      self.match = _PiecePattern._op_not_in
      self._piece = _latin_to_piece(piece_latin_letter[1:])
    elif piece_latin_letter == ' ':
      self._piece = piece.FREE
    elif piece_latin_letter == 'from':
      self._op = _Operation.FROM_IN
      self.match = _PiecePattern._op_from_in
    elif piece_latin_letter == 'to':
      self._op = _Operation.TO_IN
      self.match = _PiecePattern._op_to_in
    else:
      self._piece = _latin_to_piece(piece_latin_letter)
    if isinstance(cell_pattern, int):
      self._op = _Operation.PIECES_EQ
      self.match = _PiecePattern._op_pieces_eq
      self._count = cell_pattern
    else:
      self._list = list(map(cell.digital_parse, cell_pattern.split(',')))
  def __str__(self):
    return f'PiecePattern({self._repr})'
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    res = self.match(self, pos, side)
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

def _sfen_moveno(s: str) -> int:
  a = s.split()
  return int(a[3])

class SFENMap:
  def __init__(self, d):
    a = []
    max_moves = 0
    for key, value in d.items():
      n = _sfen_moveno(key)
      a.append((key, n, value))
      if max_moves < n:
        max_moves = n
    f = [None] * (max_moves + 1)
    for key, n, value in a:
      if f[n] is None:
        f[n] = {}
      f[n][key] = value
    self._d = f
  def get(self, pos: PositionForPatternRecognition, m: Optional[Move] = None):
    if pos.move_no >= len(self._d):
      return None
    t = self._d[pos.move_no]
    if t is None:
      return None
    s = pos.sfen()
    if not m is None:
      s += ' ' + m.usi_str()
    return t.get(s)
