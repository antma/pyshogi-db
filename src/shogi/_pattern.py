# -*- coding: UTF8 -*-

from enum import IntEnum
import logging
from typing import List, Optional, Union
from functools import reduce

import log
from . import cell
from . import piece
from . import position
from .move import Move

_Operation = IntEnum('_Operation', ['EQ', 'IN', 'NOT_IN', 'PIECES_EQ', 'FROM_IN', 'TO_IN', 'MAX_MOVES', 'SIDE', 'BASE_PATTERN', 'LAST_ROW', 'PAWNS_IN', 'PAWNS_MASK'])
_GENERALS_S = set([piece.SILVER, piece.GOLD, piece.PROMOTED + piece.SILVER])
_BISHOP_S = set([piece.BISHOP, piece.HORSE])
_ROOK_S = set([piece.ROOK, piece.DRAGON])

def adjacent_pawns(row: int, start_col: int, end_col: int, excl: List[int]):
  s = set(excl)
  return [('adj-pawns', sum(1 << (col - 1) for col in range(start_col, end_col) if not col in s) << (9 * (row - 1)))]

_FIRST_ROW = 'LNSGKGSNL'

def last_row_pieces(excl: str):
  s = excl
  for u, v in zip(s, s[1:]):
    assert u < v, excl
  m = 511 - reduce(lambda x, y: x | y, ((1 << (int(c) - 1)) for c in s), 0)
  return [('last-row', m)]

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
    self._patterns_d = {}
    self._sente_unmovable_pieces = 511
    self._gote_unmovable_pieces = 511
    self._sente_pawns = 511 << 54
    self._gote_rev_pawns = self._sente_pawns
  def pawns_in(self, side: int, mask: int) -> bool:
    return ((self._sente_pawns if side > 0 else self._gote_rev_pawns) & mask) != 0
  def pawns_mask(self, side: int, mask: int) -> bool:
    return ((self._sente_pawns if side > 0 else self._gote_rev_pawns) & mask) == mask
  def _check_pawns(self):
    s = 0
    g = 0
    for i, c in enumerate(self.board):
      if c == piece.PAWN:
        s += 1 << i
      elif c == -piece.PAWN:
        g += 1 << cell.swap_side(i)
    assert self._sente_pawns == s
    assert self._gote_rev_pawns == g
  def check_last_row(self, mask: int, side: int) -> bool:
    m = self._sente_unmovable_pieces if side > 0 else self._gote_unmovable_pieces
    return (m & mask) == mask
  def clear_patterns_matches(self):
    self._patterns_d = {}
  def set_pattern_match(self, key: str, value: bool):
    self._patterns_d[key] = value
  def get_pattern_match(self, key: str):
    p = self._patterns_d.get(key)
    assert not p is None
    return p
  def do_move(self, m: Move):
    self._cached_sfen = None
    if self.side_to_move > 0:
      if not m.from_cell is None:
        if m.from_cell >= 72:
          self._sente_unmovable_pieces &= 511 ^ (1 << (m.from_cell % 9))
        if m.from_piece == piece.PAWN:
          self._sente_pawns -= 1 << m.from_cell
      if m.to_cell < 9:
        self._gote_unmovable_pieces &= 511 ^ (1 << (8 - (m.to_cell % 9)))
      if m.to_piece == piece.PAWN:
        self._sente_pawns += 1 << m.to_cell
    else:
      if not m.from_cell is None:
        if m.from_cell < 9:
          self._gote_unmovable_pieces &= 511 ^ (1 << (8 - (m.from_cell % 9)))
        if m.from_piece == -piece.PAWN:
          self._gote_rev_pawns -= 1 << cell.swap_side(m.from_cell)
      if m.to_cell >= 72:
        self._sente_unmovable_pieces &= 511 ^ (1 << (m.to_cell % 9))
      if m.to_piece == -piece.PAWN:
        self._gote_rev_pawns += 1 << cell.swap_side(m.to_cell)
    u = super().do_move(m)
    if not u is None:
      tp = abs(u.taken_piece)
      if (not self._taken_general) and tp in _GENERALS_S:
        self._taken_general = True
      if (not self._taken_bishop) and tp in _BISHOP_S:
        self._taken_bishop = True
      if (not self._taken_rook) and tp in _ROOK_S:
        self._taken_rook = True
      if tp == piece.PAWN:
        if u.taken_piece > 0:
          self._sente_pawns -= 1 << m.to_cell
        else:
          self._gote_rev_pawns -= 1 << cell.swap_side(m.to_cell)
    self.last_move = m
    p = m.from_piece
    if not p is None:
      self._count_moves_d[p] = self._count_moves_d.get(p, 0) + 1
    if (not self._was_drops) and m.is_drop():
      self._was_drops = True
    #self._check_pawns()
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
  def _op_pawns_mask(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.pawns_mask(side, self._arg)
  def _op_pawns_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.pawns_in(side, self._arg)
  def _op_last_row(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.check_last_row(self._arg, side)
  def _op_base_pattern(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.get_pattern_match(self._arg)
  def _op_eq(self, pos: PositionForPatternRecognition, side: int) -> bool:
    c = self._arg
    return pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece
  def _op_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return any(pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece for c in self._arg)
  def _op_not_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(pos.board[c if side > 0 else cell.swap_side(c)] != side * self._piece for c in self._arg)
  def _op_pieces_eq(self, pos: PositionForPatternRecognition, side: int) -> bool:
    p = pos.sente_pieces if side * self._piece > 0 else pos.gote_pieces
    return p[abs(self._piece) - 1] == self._arg
  def _op_max_moves(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.count_piece_moves(self._piece * side) <= self._arg
  def _op_side(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return side == self._arg
  def _op_from_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    m = pos.last_move
    if m is None:
      return False
    c = m.from_cell
    if c is None:
      return False
    if side < 0:
      c = cell.swap_side(c)
    return c in self._arg
  def _op_to_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    m = pos.last_move
    if m is None:
      return False
    c = m.to_cell
    assert not c is None
    if side < 0:
      c = cell.swap_side(c)
    return c in self._arg
  def __init__(self, piece_latin_letter: str, cell_pattern: Union[str,int]):
    self._repr = (piece_latin_letter, cell_pattern)
    self._piece = None
    self._arg = None
    self.hits = 0
    self.calls = 1
    if piece_latin_letter == 'adj-pawns':
      self._op = _Operation.PAWNS_MASK
      assert isinstance(cell_pattern, int)
      self._arg = cell_pattern
      self._match = _PiecePattern._op_pawns_mask
      return
    if piece_latin_letter == 'last-row':
      self._op = _Operation.LAST_ROW
      assert isinstance(cell_pattern, int)
      self._arg = cell_pattern
      self._match = _PiecePattern._op_last_row
      return
    if piece_latin_letter == 'base-pattern':
      self._op = _Operation.BASE_PATTERN
      assert isinstance(cell_pattern, str)
      self._arg = cell_pattern
      self._match = _PiecePattern._op_base_pattern
      return
    if piece_latin_letter == 'side':
      self._op = _Operation.SIDE
      self._match = _PiecePattern._op_side
      assert isinstance(cell_pattern, int)
      self._arg = cell_pattern
      return
    if piece_latin_letter == 'max-gold-moves':
      self._op = _Operation.MAX_MOVES
      self._match = _PiecePattern._op_max_moves
      self._piece = piece.GOLD
      assert isinstance(cell_pattern, int)
      self._arg = cell_pattern
      return
    self._op = _Operation.IN
    self._match = _PiecePattern._op_in
    if piece_latin_letter.startswith('!'):
      self._op = _Operation.NOT_IN
      self._match = _PiecePattern._op_not_in
      self._piece = _latin_to_piece(piece_latin_letter[1:])
    elif piece_latin_letter == ' ':
      self._piece = piece.FREE
    elif piece_latin_letter == 'from':
      self._op = _Operation.FROM_IN
      self._match = _PiecePattern._op_from_in
    elif piece_latin_letter == 'to':
      self._op = _Operation.TO_IN
      self._match = _PiecePattern._op_to_in
    else:
      self._piece = _latin_to_piece(piece_latin_letter)
    if isinstance(cell_pattern, int):
      self._op = _Operation.PIECES_EQ
      self._match = _PiecePattern._op_pieces_eq
      self._arg = cell_pattern
    else:
      self._arg = list(map(cell.digital_parse, cell_pattern.split(',')))
      l = len(self._arg)
      logging.debug('%s: %s, l = %d', self._repr, self._arg, l)
      if (l == 1) and (self._op == _Operation.IN):
        self._arg = self._arg[0]
        self._op = _Operation.EQ
        self._match = _PiecePattern._op_eq
      if l > 1:
        t = list(map(int, cell_pattern.split(',')))
        assert all(u < v for u, v in zip(t, t[1:])), cell_pattern
    logging.debug('op = %s, arg = %s', self._op.name, self._arg)
    if (self._op == _Operation.IN) and (self._piece == piece.PAWN):
      assert isinstance(self._arg, list), self._repr
      self._arg = sum(1 << i for i in self._arg)
      self._op = _Operation.PAWNS_IN
      self._match = _PiecePattern._op_pawns_in
    if self._op in (_Operation.TO_IN, _Operation.FROM_IN):
      assert isinstance(self._arg, list)
      self._arg = set(self._arg)
  def __str__(self):
    return f'PiecePattern({self._repr})'
  def __lt__(self, other):
    return self.hits * other.calls < other.hits * self.calls
  def match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    r = self._match(self, pos, side)
    self.calls += 1
    if r:
      self.hits += 1
    return r
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    res = self.match(pos, side)
    if not res:
      logging.debug('%s not matched', self)
    return res
  def get_pawn_mask(self) -> Optional[int]:
    if (self._piece == piece.PAWN) and (self._op == _Operation.EQ):
      assert isinstance(self._arg, int)
      return 1 << self._arg
    if self._op == _Operation.PAWNS_MASK:
      assert isinstance(self._arg, int)
      return self._arg
    return None
  def find_global(self):
    global _PIECE_PATTERNS_CALLS
    _PIECE_PATTERNS_CALLS += 1
    p = _PIECE_PATTERNS_D.get(self._repr)
    if not p is None:
      return p
    _PIECE_PATTERNS_D[self._repr] = self
    return self

_PIECE_PATTERNS_D = {}
_PIECE_PATTERNS_CALLS = 0

def piece_patterns_stats():
  calls, hits = 0, 0
  for p in _PIECE_PATTERNS_D.values():
    c = p.calls - 1
    calls += c
    hits += c - p.hits
  logging.info('%d hits, %d calls (%.2f%%)', hits, calls, (hits * 100.0) / calls)

def _piece_pattern(t):
  global _PIECE_PATTERNS_CALLS
  _PIECE_PATTERNS_CALLS += 1
  p = _PIECE_PATTERNS_D.get(t)
  if not p is None:
    return p
  p = _PiecePattern(t[0], t[1])
  _PIECE_PATTERNS_D[t] = p
  return p

def _unique_data(data, value):
  s = set()
  for t in data:
    if t in s:
      logging.error('%s is not unique in %s. data = %s', t, value.name, data)
      return False
    s.add(t)
  return True

class _PositionPattern:
  def __init__(self, data: list, value):
    assert _unique_data(data, value), data
    t = []
    pm = 0
    for p in map(lambda t: _PiecePattern(t[0], t[1]), data):
      x = p.get_pawn_mask()
      if x is None:
        t.append(p.find_global())
      else:
        assert (pm & x) == 0
        pm |= x
    if pm > 0:
      t.append(_piece_pattern(('adj-pawns', pm)))
    self._patterns = t
  def match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.match(pos, side) for p in self._patterns)
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.debug_match(pos, side) for p in self._patterns)
  def reorder(self):
    self._patterns.sort()

class Recognizer:
  def __init__(self, p, tp = None):
    self._position_patterns = [(_PositionPattern(data, value), value) for data, value in p]
    self._u = 1
    self._v = 2
    self._n = 0
    logging.info('%s: %d unique piece patterns, %d total piece patterns', tp, len(_PIECE_PATTERNS_D), _PIECE_PATTERNS_CALLS)
  def reorder(self):
    self._n += 1
    if self._n >= self._v:
      self._u, self._v = self._v, self._u + self._v
      for p, _ in self._position_patterns:
        p.reorder()
  def find(self, pos: PositionForPatternRecognition):
    pos.clear_patterns_matches()
    side = -pos.side_to_move
    f = _PositionPattern.debug_match if log.is_debug() else _PositionPattern.match
    for p, ct in self._position_patterns:
      r = f(p, pos, side)
      if isinstance(ct, str):
        pos.set_pattern_match(ct, r)
        if not r:
          logging.debug('Pattern %s not matched', ct)
      else:
        if r:
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
