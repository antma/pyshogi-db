# -*- coding: UTF8 -*-

from enum import IntEnum
import logging
from typing import List, Optional, Tuple, Union
from functools import reduce

import log
from . import cell
from . import piece
from . import position
from .move import Move
from ._misc import sfen_moveno

_Operation = IntEnum('_Operation', ['EQ', 'IN', 'NOT_IN', 'PIECES_EQ', 'FROM_IN', 'TO_IN', 'MAX_MOVES', 'SIDE', 'BASE_PATTERN', 'LAST_ROW', 'PAWNS_IN', 'PAWNS_MASK', 'NO_MOVE'])
_END_OF_THE_ROOK_S = set([piece.PAWN, piece.BISHOP, piece.HORSE])
#_END_OF_THE_OPENING_S = set([piece.SILVER, piece.GOLD, piece.PROMOTED + piece.SILVER, piece.LANCE, piece.PROMOTED + piece.LANCE, piece.ROOK, piece.DRAGON])
_END_OF_THE_OPENING_S = set([piece.SILVER, piece.GOLD, piece.PROMOTED + piece.SILVER, piece.LANCE, piece.PROMOTED + piece.LANCE])
_GOTE_END_OF_THE_OPENING_S = set(-p for p in _END_OF_THE_OPENING_S)

def adjacent_pawns(row: int, start_col: int, end_col: int, excl: Optional[List[int]] = None):
  s = set() if excl is None else set(excl)
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

def _has_pieces_in_hand(p):
  #return any(i > 0 for i in p[1:])
  return p[piece.ROOK-1] > 0

class PositionForPatternRecognition(position.Position):
  def __init__(self, castle_detection_mode: bool, sfen: str = None):
    super().__init__(sfen)
    self._castles_detection_mode = castle_detection_mode
    self._taken = set()
    self._sente_opening = True
    self._gote_opening = True
    self._rooks_exchange = False
    self._sente_captures_mask = 0
    self._gote_rev_captures_mask = 0
    self._moves_destination_s = set()
    self._promotions = 0
    self.last_move = None
    self._count_moves_d = {}
    self._was_drops = False
    self._cached_sfen = None
    self._patterns_d = {}
    self._sente_unmovable_pieces = 511
    self._gote_unmovable_pieces = 511
    if sfen is None:
      self._sente_pawns = 511 << 54
      self._gote_rev_pawns = self._sente_pawns
      self._sente_king = 76
      self._gote_rev_king = 76
    else:
      self._sente_pawns = 0
      self._gote_rev_pawns = 0
      self._sente_king = None
      self._gote_rev_king = None
      for i, p in enumerate(self.board):
        if p == piece.PAWN:
          self._sente_pawns |= 1 << i
        elif p == -piece.PAWN:
          self._gote_rev_pawns |= 1 << cell.swap_side(i)
        elif p == piece.KING:
          assert self._sente_king is None
          self._sente_king = i
        elif p == -piece.KING:
          assert self._gote_rev_king is None
          self._gote_rev_king = cell.swap_side(i)
      assert not self._sente_king is None
      assert not self._gote_rev_king is None
  def was_destination_move(self, to_piece: int, to_cell: int) -> bool:
    return (to_piece, to_cell) in self._moves_destination_s
  def get_king_normalized_pos(self, side: int) -> int:
    return self._sente_king if side > 0 else self._gote_rev_king
  def pawns(self, side: int) -> int:
    p = self._sente_pawns if side > 0 else self._gote_rev_pawns
    #counter example wars/0111.kif
    #if self._castles_detection_mode:
    #  q = self._sente_captures_mask if side > 0 else self._gote_rev_captures_mask
    #  p ^= p & q
    return p
  def pawns_in(self, side: int, mask: int) -> bool:
    return (self.pawns(side) & mask) != 0
  def pawns_mask(self, side: int, mask: int) -> bool:
    return (self.pawns(side) & mask) == mask
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
    return self._patterns_d[key]
  def do_move(self, m: Move):
    self._cached_sfen = None
    self._moves_destination_s.add((m.to_piece, m.to_cell))
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
      elif m.to_piece == piece.KING:
        self._sente_king = m.to_cell
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
      elif m.to_piece == -piece.KING:
        self._gote_rev_king = cell.swap_side(m.to_cell)
    if piece.is_promoted(m.to_piece):
      self._promotions += 1
    u = super().do_move(m)
    if not u is None:
      if m.to_piece > 0:
        self._sente_captures_mask |= 1 << m.to_cell
        #counter example HIGH_MINO_CASTLE-H94.kif
        #_SENTE_CAMP = ((1 << (9*4)) - 1) << (5 * 9)
        #if (_SENTE_CAMP & self._sente_captures_mask) != 0:
        #  self._sente_opening = False
      else:
        self._gote_rev_captures_mask |= 1 << cell.swap_side(m.to_cell)
        #_SENTE_CAMP = ((1 << (9*4)) - 1) << (5 * 9)
        #if (_SENTE_CAMP & self._gote_rev_captures_mask) != 0:
        #  self._gote_opening = False
      tp = abs(u.taken_piece)
      if tp == piece.PAWN:
        if u.taken_piece > 0:
          self._sente_pawns -= 1 << m.to_cell
        else:
          self._gote_rev_pawns -= 1 << cell.swap_side(m.to_cell)
      else:
        self._taken.add(tp)
        if m.to_piece > 0:
          assert u.taken_piece < 0
          if u.taken_piece in _GOTE_END_OF_THE_OPENING_S:
            self._sente_opening = False
        else:
          assert u.taken_piece > 0
          if u.taken_piece in _END_OF_THE_OPENING_S:
            self._gote_opening = False
        if (not self._rooks_exchange) and (self.sente_pieces[piece.ROOK-1] > 0) and (self.gote_pieces[piece.ROOK-1] > 0):
          self._rooks_exchange = True
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
  def _is_opening_rook_exchanged(self, side: int) -> bool:
    if self._rooks_exchange:
      return False
    if side == 0:
      return self._sente_opening or self._gote_opening
    if side > 0:
      return self._sente_opening and (not _has_pieces_in_hand(self.sente_pieces))
    return self._gote_opening and (not _has_pieces_in_hand(self.gote_pieces))
  def is_opening(self, side: int) -> bool:
    if side == 0:
      return self._sente_opening or self._gote_opening
    return self._sente_opening if side > 0 else self._gote_opening
    #return self._taken.isdisjoint(_END_OF_THE_OPENING_S)
  def count_piece_moves(self, p: int) -> int:
    return self._count_moves_d.get(p, 0)
  def first_rook_move_rank(self, m: Move) -> Optional[int]:
    if self._was_drops or (not self._taken.isdisjoint(_END_OF_THE_ROOK_S)):
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
  def _op_no_move(self, pos: PositionForPatternRecognition, side: int) -> bool:
    c = self._arg
    if side < 0:
      c = cell.swap_side(c)
    return not pos.was_destination_move(side * self._piece, c)
  def _op_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return any(pos.board[c if side > 0 else cell.swap_side(c)] == side * self._piece for c in self._arg)
  def _op_not_in(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(pos.board[c if side > 0 else cell.swap_side(c)] != side * self._piece for c in self._arg)
  def _op_pieces_eq(self, pos: PositionForPatternRecognition, side: int) -> bool:
    p = pos.sente_pieces if side * self._piece > 0 else pos.gote_pieces
    return p[abs(self._piece) - 1] == self._arg
  '''
  def _op_max_moves(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return pos.count_piece_moves(self._piece * side) <= self._arg
  '''
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
    self.repr = (piece_latin_letter, cell_pattern)
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
    if piece_latin_letter == 'no-move':
      self._match = _PiecePattern._op_no_move
      self._op = _Operation.NO_MOVE
      assert isinstance(cell_pattern, str)
      p, c = cell_pattern.split('-')
      self._piece = _latin_to_piece(p)
      self._arg = cell.digital_parse(c)
      assert not self._arg is None
      return
    '''
    if piece_latin_letter == 'max-gold-moves':
      self._op = _Operation.MAX_MOVES
      self._match = _PiecePattern._op_max_moves
      self._piece = piece.GOLD
      assert isinstance(cell_pattern, int)
      self._arg = cell_pattern
      return
    '''
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
      logging.debug('%s: %s, l = %d', self.repr, self._arg, l)
      if (l == 1) and (self._op == _Operation.IN):
        self._arg = self._arg[0]
        self._op = _Operation.EQ
        self._match = _PiecePattern._op_eq
      if l > 1:
        t = list(map(int, cell_pattern.split(',')))
        assert all(u < v for u, v in zip(t, t[1:])), cell_pattern
    logging.debug('op = %s, arg = %s', self._op.name, self._arg)
    if (self._op == _Operation.IN) and (self._piece == piece.PAWN):
      assert isinstance(self._arg, list), self.repr
      self._arg = sum(1 << i for i in self._arg)
      self._op = _Operation.PAWNS_IN
      self._match = _PiecePattern._op_pawns_in
    if self._op in (_Operation.TO_IN, _Operation.FROM_IN):
      assert isinstance(self._arg, list)
      self._arg = set(self._arg)
  def __str__(self):
    return f'PiecePattern({self.repr})'
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
  def king_possible_cells(self, d):
    if self._op == _Operation.BASE_PATTERN:
      return d[self._arg]
    if (self._op == _Operation.LAST_ROW) and (self._arg & (1 << 4) != 0):
      return set([76])
    if self._piece == piece.KING:
      if self._op == _Operation.EQ:
        return set([self._arg])
      if self._op == _Operation.IN:
        return self._arg
    return None
  def is_king_pattern(self) -> bool:
    return (self._piece == piece.KING) and (self._op in (_Operation.EQ, _Operation.IN))


def _unique_data(data, value):
  s = set()
  for t in data:
    if t in s:
      logging.error('%s is not unique in %s. data = %s', t, value.name, data)
      return False
    s.add(t)
  return True

class _PPAllocator:
  def __init__(self):
    self._pp_d = {}
  def find(self, p):
    assert isinstance(p, _PiecePattern)
    q = self._pp_d.get(p.repr)
    if not q is None:
      return q
    self._pp_d[p.repr] = p
    return p
  def piece_pattern(self, t):
    return self.find(_PiecePattern(t[0], t[1]))
  def stats(self):
    calls, hits = 0, 0
    for p in self._pp_d.values():
      c = p.calls - 1
      calls += c
      hits += p.hits
    return (calls, hits)

class _PositionPattern:
  def __init__(self, data: list, value, allocator: _PPAllocator):
    assert isinstance(allocator, _PPAllocator)
    assert _unique_data(data, value), data
    t = []
    pm = 0
    for p in map(lambda t: _PiecePattern(t[0], t[1]), data):
      x = p.get_pawn_mask()
      if x is None:
        t.append(allocator.find(p))
      else:
        assert (pm & x) == 0
        pm |= x
    if pm > 0:
      t.append(allocator.piece_pattern(('adj-pawns', pm)))
    self._patterns = t
  def king_possible_cells(self, d):
    r = None
    for p in self._patterns:
      q = p.king_possible_cells(d)
      if not q is None:
        if r is None:
          r = q.copy()
        else:
          r = r.intersection(q)
    if r is None:
      r = set(range(81))
    assert len(r) > 0
    return r
  def match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.match(pos, side) for p in self._patterns)
  def debug_match(self, pos: PositionForPatternRecognition, side: int) -> bool:
    return all(p.debug_match(pos, side) for p in self._patterns)
  def reorder(self):
    self._patterns.sort()
  def _find_king_pattern_index(self) -> Optional[int]:
    for i, p in enumerate(self._patterns):
      if p.is_king_pattern():
        return i
    return None
  def remove_king_pattern(self):
    i = self._find_king_pattern_index()
    if not i is None:
      self._patterns.pop(i)

class RecognizerSet:
  def __init__(self):
    self._s = set()
    self._d = {}
  def __contains__(self, key):
    return key in self._s
  def add(self, value, move_no: int):
    if value not in self._s:
      self._s.add(value)
      self._d[value] = move_no
      return True
    return False
  def get_move_no(self, value):
    return self._d.get(value)
  def issubset(self, other_set) -> bool:
    return self._s.issubset(other_set)
  def discard(self, value):
    if value in self._s:
      self._s.remove(value)
      del self._d[value]
  def as_set(self):
    return self._s
  def len(self):
    return len(self._s)

class RecognizerResult:
  def __init__(self):
    self._sente = RecognizerSet()
    self._gote = RecognizerSet()
  def get_set(self, side: int) -> RecognizerSet:
    return self._sente if side > 0 else self._gote
  def get_sets(self, side: int) -> Tuple[RecognizerSet, RecognizerSet]:
    return (self._sente, self._gote) if side > 0 else (self._gote, self._sente)

class Recognizer:
  def __init__(self, p):
    self._allocator = _PPAllocator()
    self._position_patterns = [(_PositionPattern(data, value, self._allocator), value) for data, value in p]
    self._by_king = [ [] for _ in range(81)]
    d = {}
    for i, t in enumerate(self._position_patterns):
      p, value = t
      s = p.king_possible_cells(d)
      if isinstance(value, str):
        d[value] = s
      else:
        if len(s) == 81:
          logging.warning('Pattern %s: king position is not defined', value.name)
      for j in s:
        self._by_king[j].append(i)
      p.remove_king_pattern()
    self._u = 1
    self._v = 2
    self._n = 0
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
    for i in self._by_king[pos.get_king_normalized_pos(side)]:
      p, ct = self._position_patterns[i]
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
  def update_set(self, rr: RecognizerResult, pos: PositionForPatternRecognition) -> bool:
    ct = self.find(pos)
    if not ct is None:
      st = rr.get_set(-pos.side_to_move)
      return st.add(ct, pos.move_no - 1)
    return False
  def stats(self):
    return self._allocator.stats()
  def log_stats(self, old_stats, func_name):
    calls, hits = self._allocator.stats()
    calls -= old_stats[0]
    hits -= old_stats[1]
    hits = calls - hits
    logging.info('%s: %d hits, %d calls (%.2f%%)', func_name, hits, calls, (hits * 100.0) / calls)

class SFENMap:
  def __init__(self, d):
    a = []
    max_moves = 0
    for key, value in d.items():
      n = sfen_moveno(key)
      a.append((key, n, value))
      max_moves = max(max_moves, n)
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
