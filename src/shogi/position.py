# -*- coding: UTF8 -*-

import itertools
from typing import (Iterator, Optional, Tuple)
import logging
import log

from .move import (Move, UndoMove, IllegalMove, Nifu, UnresolvedCheck)
from . import cell
from . import piece

SFEN_STARTPOS = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"

_GOLD_L = [piece.GOLD, piece.promote(piece.PAWN), piece.promote(piece.LANCE), piece.promote(piece.KNIGHT), piece.promote(piece.SILVER)]
_BISHOP_L = [piece.BISHOP, piece.HORSE]
_ROOK_L = [piece.ROOK, piece.DRAGON]
_GENERAL_L = _GOLD_L + [piece.SILVER]

_BISHOP_S = set(_BISHOP_L)
_ROOK_S = set(_ROOK_L)
_NEAR_S = set([piece.KING, piece.HORSE, piece.DRAGON])
_ATTACK_UP_FAR_S = set([piece.LANCE] + _ROOK_L)
_ATTACK_UP_NEAR_S = set(itertools.chain(_ATTACK_UP_FAR_S, _GENERAL_L, [piece.PAWN]))
_ATTACK_DIAG_UP_NEAR_S = set(itertools.chain(_BISHOP_L, _GENERAL_L))
_ATTACK_ROOK_NEAR_S = set(itertools.chain(_ROOK_L, _GOLD_L))
_ATTACK_BISHOP_NEAR_S = set(itertools.chain(_BISHOP_L, [piece.SILVER]))
_FIVE_POINTS_S = set(itertools.chain(_BISHOP_L, _ROOK_L))
_GOLD_S = set(_GOLD_L)
_COULD_BE_PROMOTED_S = set([piece.PAWN, piece.LANCE, piece.KNIGHT, piece.SILVER, piece.BISHOP, piece.ROOK])
_UNIQUE_S = set([piece.PAWN, piece.LANCE, piece.KING])

del _GOLD_L
del _ROOK_L
del _BISHOP_L
del _GENERAL_L

class Position:
  '''shogi position'''
  def _set_cell(self, row, col, p):
    if not piece.is_legal(p):
      log.raise_value_error(f'Position._set_cell(): illegal piece {p}')
    if (0 <= row < 9) and (0 <= col < 9):
      self.board[9 * row + col] = p
    else:
      log.raise_value_error(f'Position._set_cell(): illegal cell ({row+1}, {col+1})')
  def find_king(self, side: int) -> Optional[int]:
    if side > 0:
      for i in range(80, -1, -1):
        if self.board[i] == piece.KING:
          return i
    else:
      p = -piece.KING
      for i in range(81):
        if self.board[i] == p:
          return i
    return None
  def _scan_board(self, side, r, c, dr, dc, far, near) -> bool:
    #logging.debug('dr = %s, dc = %s', dr, dc)
    k = 0
    while True:
      k += 1
      r += dr
      if (r < 0) or (r > 8):
        return False
      c += dc
      if (c < 0) or (c > 8):
        return False
      p = self.board[9 * r + c]
      t = p * side
      if t > 0:
        p = abs(p)
        #logging.debug('piece = %s, k = %d, (r = %d, c = %d)', p, k, r, c)
        if k > 1:
          return p in far
        return (p in _NEAR_S) or (p in near)
      if t < 0:
        return False
  def _king_under_check(self, side: int) -> bool:
    s = side
    (rk, ck) = divmod(self.find_king(s), 9)
    if self._scan_board(-s, rk, ck, -s, 0, _ATTACK_UP_FAR_S, _ATTACK_UP_NEAR_S) or \
       self._scan_board(-s, rk, ck, -s, -1, _BISHOP_S, _ATTACK_DIAG_UP_NEAR_S) or \
       self._scan_board(-s, rk, ck, -s, 1, _BISHOP_S, _ATTACK_DIAG_UP_NEAR_S) or \
       self._scan_board(-s, rk, ck, 0, -1, _ROOK_S, _ATTACK_ROOK_NEAR_S) or \
       self._scan_board(-s, rk, ck, 0, 1, _ROOK_S, _ATTACK_ROOK_NEAR_S) or \
       self._scan_board(-s, rk, ck, s, 0, _ROOK_S, _ATTACK_ROOK_NEAR_S) or \
       self._scan_board(-s, rk, ck, s, -1, _BISHOP_S, _ATTACK_BISHOP_NEAR_S) or \
       self._scan_board(-s, rk, ck, s, 1, _BISHOP_S, _ATTACK_BISHOP_NEAR_S):
      return True
    #knight check
    row = rk - 2 * s
    if 0 <= row < 9:
      u = 9 * row + ck
      knight = -piece.KNIGHT * s
      if (ck > 0) and (self.board[u - 1] == knight):
        return True
      if (ck < 8) and (self.board[u + 1] == knight):
        return True
    return False
  def __init__(self, sfen: Optional[str] = None):
    if sfen is None:
      sfen = SFEN_STARTPOS
    self.board = [piece.FREE] * 81
    self.sente_pieces = [0] * piece.ROOK
    self.gote_pieces = [0] * piece.ROOK
    a = list(sfen.split(' '))
    self.move_no = int(a[3])
    if a[1] == 'b':
      self.side_to_move = 1
    elif a[1] == 'w':
      self.side_to_move = -1
    else:
      log.raise_value_error(f"Position.__init__(sfen: {sfen}) unknown side to move")
    d = dict(map(lambda t: (t[1], t[0] + 1), enumerate(piece.ASCII_PIECES)))
    for row, t in enumerate(a[0].split('/')):
      col = 9
      promoted = False
      for c in t:
        if c.isdigit():
          if promoted:
            log.raise_value_error(f"Position.__init__(sfen: {sfen}) free cell can't be promoted")
          for _ in range(int(c)):
            col -= 1
            self._set_cell(row, col, piece.FREE)
        elif c.islower():
          col -= 1
          p = d.get(c)
          if p is None:
            log.raise_value_error(f"Position.__init__(sfen: {sfen}) unknown piece '{c}'")
          if promoted:
            p = piece.promote(p)
            promoted = False
          self._set_cell(row, col, -p)
        elif c.isupper():
          col -= 1
          p = d.get(c.lower())
          if p is None:
            log.raise_value_error(f'Position.__init__(sfen: {sfen}) unknown piece {c}')
          if promoted:
            p = piece.promote(p)
            promoted = False
          self._set_cell(row, col, p)
        elif c == '+':
          if promoted:
            log.raise_value_error(f"Position.__init__(sfen: {sfen}) double plus")
          promoted = True
        else:
          log.raise_value_error(f"Position.__init__(sfen: {sfen}) illegal character '{c}' in the board representation part")
      if col != 0:
        log.raise_value_error(f'Position.__init__(sfen: {sfen}) not enough data in row #{row+1}')
    if a[2] != '-':
      t = 0
      for c in a[2]:
        if c.islower():
          self.gote_pieces[d.get(c) - 1] += max(t, 1)
          t = 0
        elif c.isupper():
          self.sente_pieces[d.get(c.lower()) - 1] += max(t, 1)
          t = 0
        elif c.isdigit():
          t = 10 * t + int(c)
        else:
          log.raise_value_error(f'Position.__init__(sfen: {sfen}) piece in hand should be alphabetic')
      if t != 0:
        log.raise_value_error(f'Position.__init__(sfen: {sfen}) after number in hand should be alphabetic character')
    sente_c = self.sente_pieces[:]
    sente_c.append(0)
    gote_c = self.gote_pieces[:]
    gote_c.append(0)
    for p in self.board:
      if p > 0:
        sente_c[piece.unpromote(p) - 1] += 1
      elif p < 0:
        gote_c[piece.unpromote(-p) - 1] += 1
    if sente_c[piece.KING-1] != 1:
      log.raise_value_error(f'Position.__init__(sfen: {sfen}) illegal number of sente king')
    if gote_c[piece.KING-1] != 1:
      log.raise_value_error(f'Position.__init__(sfen: {sfen}) illegal number of gote king')
    if sente_c[piece.PAWN-1] + gote_c[piece.PAWN-1] != 18:
      log.raise_value_error(f'Position.__init__(sfen: {sfen}) illegal number of pawns')
    for p in [piece.LANCE, piece.KNIGHT, piece.SILVER, piece.GOLD]:
      if sente_c[p-1] + gote_c[p-1] != 4:
        name = piece.ASCII_LONG_NAMES[p]
        log.raise_value_error(f'Position.__init__(sfen: {sfen}) illegal number of {name}s')
    for p in [piece.BISHOP, piece.ROOK]:
      if sente_c[p-1] + gote_c[p-1] != 2:
        name = piece.ASCII_LONG_NAMES[p]
        log.raise_value_error(f'Position.__init__(sfen: {sfen}) illegal number of {name}s')
    if not self.is_legal():
      log.raise_value_error(f'Position.__init__(sfen: {sfen}) king under check')
  def sfen(self, move_no = True) -> str:
    s = ''
    for row in range(9):
      u = 9 * row
      t = 0
      if row > 0:
        s += '/'
      for i in range(u + 8, u - 1, -1):
        c = self.board[i]
        if c == 0:
          t += 1
        else:
          if t > 0:
            s += chr(48 + t)
            t = 0
          s += piece.to_string(c)
      if t > 0:
        s += chr(48 + t)
    s += ' '
    s += 'b' if self.side_to_move > 0 else 'w'
    s += ' '
    w = ''
    for p in range(piece.ROOK, piece.FREE, -1):
      t = self.sente_pieces[p-1]
      if t > 0:
        if t > 1:
          w += str(t)
        w += piece.ASCII_PIECES[p-1].upper()
    for p in range(piece.ROOK, piece.FREE, -1):
      t = self.gote_pieces[p-1]
      if t > 0:
        if t > 1:
          w += str(t)
        w += piece.ASCII_PIECES[p-1]
    if w == '':
      s += '-'
    else:
      s += w
    if move_no:
      s += ' ' + str(self.move_no)
    return s
  def _validate_move(self, m: Move):
    if self.side_to_move * m.to_piece <= 0:
      raise ValueError("position side_to_move field isn't matched to move to_piece field'")
    if m.is_drop():
      if self.board[m.to_cell] != piece.FREE:
        raise ValueError('drop piece on occupied cell')
      c = self.sente_pieces if m.to_piece > 0 else self.gote_pieces
      if c[abs(m.to_piece) - 1] <= 0:
        raise ValueError('dropping piece which not in the player hand')
      if not cell.can_drop(m.to_cell, m.to_piece):
        raise ValueError('dropping piece which can not move')
      if abs(m.to_piece) == piece.PAWN:
        col = m.to_cell % 9
        if any(map(lambda row: self.board[9 * row + col] == m.to_piece, range(9))):
          raise Nifu
    else:
      if self.side_to_move * m.from_piece <= 0:
        raise ValueError("position side_to_move field isn't matched to move from_piece field'")
      taken_piece = self.board[m.to_cell]
      if taken_piece * self.side_to_move > 0:
        raise ValueError("player takes his piece'")
  def is_legal(self) -> bool:
    return not self._king_under_check(-self.side_to_move)
  def is_check(self) -> bool:
    return self._king_under_check(self.side_to_move)
  def do_move(self, m: Move) -> Optional[UndoMove]:
    if m.legal < 0:
      raise IllegalMove()
    try:
      self._validate_move(m)
    except ValueError as err:
      m.legal = -1
      log.raise_value_error(f'Position.do_move(m = {m}): {err}. SFEN = "{self.sfen()}"')
    if m.is_drop():
      self.board[m.to_cell] = m.to_piece
      c = self.sente_pieces if m.to_piece > 0 else self.gote_pieces
      c[abs(m.to_piece) - 1] -= 1
      u = None
    else:
      taken_piece = self.board[m.to_cell]
      if taken_piece == piece.FREE:
        u = None
      else:
        u = UndoMove(taken_piece)
        a = abs(taken_piece)
        if a != piece.KING:
          c = self.sente_pieces if taken_piece < 0 else self.gote_pieces
          c[piece.unpromote(a) - 1] += 1
      self.board[m.from_cell] = piece.FREE
      self.board[m.to_cell] = m.to_piece
    self.side_to_move *= -1
    self.move_no += 1
    if (m.legal == 0) and not self.is_legal():
      m.legal = -1
      #logging.debug("Illegal position (king under check) = %s", self.sfen())
      self.undo_move(m, u)
      raise UnresolvedCheck
    m.legal = 1
    return u
  def undo_move(self, m: Move, u: Optional[UndoMove]):
    self.side_to_move *= -1
    self.move_no -= 1
    if m.is_drop():
      c = self.sente_pieces if m.to_piece > 0 else self.gote_pieces
      c[abs(m.to_piece) - 1] += 1
      self.board[m.to_cell] = piece.FREE
    else:
      taken_piece = u and u.taken_piece
      if taken_piece is None:
        taken_piece = piece.FREE
      if taken_piece != piece.FREE:
        a = abs(taken_piece)
        if a != piece.KING:
          c = self.sente_pieces if taken_piece < 0 else self.gote_pieces
          c[piece.unpromote(a) - 1] -= 1
      self.board[m.to_cell] = taken_piece
      self.board[m.from_cell] = m.from_piece
  def parse_usi_move(self, s: str) -> Move:
    it = iter(s)
    from_cell, from_piece = None, None
    to_cell, to_piece = None, None
    try:
      c = next(it)
      if c.isupper():
        to_piece = (piece.ASCII_PIECES.index(c.lower()) + 1) * self.side_to_move
        if next(it) != '*':
          log.raise_value_error(f"parse_usi_move('{s}'): expected '*'")
      elif c.isdigit():
        from_cell = cell.usi_parse(c, next(it))
        if from_cell is None:
          log.raise_value_error(f"parse_usi_move('{s}'): illegal from cell")
        from_piece = self.board[from_cell]
        if from_piece * self.side_to_move <= 0:
          log.raise_value_error(f"parse_usi_move('{s}'): illegal from piece")
      else:
        log.raise_value_error(f"parse_usi_move('{s}'): illegal first character '{c}'")
      to_cell = cell.usi_parse(next(it), next(it))
    except StopIteration:
      log.raise_value_error(f"parse_usi_move('{s}'): not enough data")
    if to_cell is None:
      log.raise_value_error(f"parse_usi_move('{s}'): illegal to cell")
    drop = from_cell is None
    taken_piece = self.board[to_cell]
    if drop:
      if taken_piece != piece.FREE:
        log.raise_value_error(f"parse_usi_move('{s}'): drop piece on occupied cell")
    else:
      if taken_piece * self.side_to_move > 0:
        log.raise_value_error(f"parse_usi_move('{s}'): eating own piece")
    promotion = False
    for c in it:
      if drop:
        log.raise_value_error(f"parse_usi_move('{s}'): drop promoted piece is impossible")
      if c == '+':
        if promotion:
          log.raise_value_error(f"parse_usi_move('{s}'): too many '+'")
        promotion = True
      else:
        log.raise_value_error(f"parse_usi_move('{s}'): expected '+'")
    if not drop:
      to_piece = piece.promote(from_piece) if promotion else from_piece
    return Move(from_piece, from_cell, to_piece, to_cell)
  def _kifu_pockets(self, side: int) -> str:
    r, c = ('先', self.sente_pieces) if side > 0 else ('後', self.gote_pieces)
    r += '手の持駒：'
    s = ''
    for i in reversed(range(piece.ROOK)):
      k = c[i]
      if k > 0:
        if s != '':
          s += ' '
        s += piece.KIFU_PIECES[i]
        u, v = divmod(k, 10)
        if u > 0:
          s += '十'
        if v > 1:
          s += cell.KIFU_ROWS[v-1]
    if s == '':
      s = 'なし'
    return r + s + '\n'
  def kifu_str(self):
    r = self._kifu_pockets(-1)
    hline = '+---------------------------+\n'
    r += "  ９ ８ ７ ６ ５ ４ ３ ２ １\n"
    r += hline
    for i, n in enumerate(cell.KIFU_ROWS):
      o = 9 * i
      t = '|'
      for j in reversed(range(9)):
        v = self.board[o + j]
        if v < 0:
          v = -v
          t += 'v'
        else:
          t += ' '
        t += '・' if v == 0 else piece.KIFU_PIECES[v-1]
      t += '|' + n + '\n'
      r += t
    r += hline
    r += self._kifu_pockets(1)
    if self.side_to_move < 0:
      r += '後手番\n'
    return r
  def fesa_impasse_points(self) -> bool:
    s = self.side_to_move
    king_in_zone, pieces_in_zone, points = False, 0, 0
    for p in self.board[0:27] if s > 0 else self.board[54:]:
      if p * s <= 0:
        continue
      p = abs(p)
      if p == piece.KING:
        king_in_zone = True
      else:
        pieces_in_zone += 1
        points += 5 if p in _FIVE_POINTS_S else 1
    if (not king_in_zone) or (pieces_in_zone < 10):
      return False
    for i, v in enumerate(self.sente_pieces if s > 0 else self.gote_pieces):
      if v == 0:
        continue
      p = i + 1
      points += (5 if p in _FIVE_POINTS_S else 1) * v
    threshold = 28 if s > 0 else 27
    return points >= threshold
  def _not_unique_piece(self, p: int, to_cell: int, moves) -> bool:
    s = 1 if p < 0 else -1
    r, c = divmod(to_cell, 9)
    t = 0
    for dr, dc in moves:
      y, x = r + s * dr, c + s * dc
      if (0 <= y < 9) and (0 <= x < 9):
        if self.board[9 * y + x] == p:
          t += 1
          if t >= 2:
            return True
    assert t == 1
    return False
  def _not_unique_scan(self, from_piece, r, c, dr, dc, k) -> bool:
    for _ in range(k):
      r += dr
      if (r < 0) or (r > 8):
        return 0
      c += dc
      if (c < 0) or (c > 8):
        return 0
      p = self.board[9 * r + c]
      if p != piece.FREE:
        return p == from_piece
    return False
  def not_unique_move(self, m: Move) -> bool:
    p = m.from_piece
    ap = abs(p)
    assert p
    if ap in _GOLD_S:
      return self._not_unique_piece(p, m.to_cell, piece.GOLD_MOVES)
    if ap in _UNIQUE_S:
      return False
    if ap == piece.SILVER:
      return self._not_unique_piece(p, m.to_cell, piece.SILVER_MOVES)
    if ap == piece.KNIGHT:
      return self._not_unique_piece(p, m.to_cell, piece.KNIGHT_MOVES)
    r, c = divmod(m.to_cell, 9)
    t = 0
    for dr in range(-1, 2):
      for dc in range(-1, 2):
        if (dr == 0) and (dc == 0):
          continue
        if abs(dr) == abs(dc):
          if ap in _BISHOP_S:
            k = 10
          elif ap == piece.DRAGON:
            k = 1
          else:
            k = 0
        else:
          if ap in _ROOK_S:
            k = 10
          elif ap == piece.HORSE:
            k = 1
          else:
            k = 0
        if (k > 0) and (self._not_unique_scan(m.from_piece, r, c, dr, dc, k)):
          t += 1
          if t >= 2:
            return True
    assert t == 1
    return False
  def western_move_str(self, m: Move, digital: bool = False) -> str:
    if m.is_drop():
      return piece.to_string(abs(m.to_piece)) + '*' + cell.western_str(m.to_cell, digital)
    s = piece.to_string(abs(m.from_piece))
    if self.not_unique_move(m):
      s += cell.western_str(m.from_cell, digital)
    s += '-' if self.board[m.to_cell] == piece.FREE else 'x'
    s += cell.western_str(m.to_cell, digital)
    p = m.from_piece
    if abs(p) in _COULD_BE_PROMOTED_S:
      pz = piece.PromotionZone(p)
      if (m.from_cell in pz) or (m.to_cell in pz):
        s += '=' if m.from_piece == m.to_piece else '+'
    return s
  @classmethod
  def clone(cls, pos):
    self = cls.__new__(cls)
    self.board = pos.board[:]
    self.side_to_move = pos.side_to_move
    self.move_no = pos.move_no
    self.sente_pieces = pos.sente_pieces[:]
    self.gote_pieces = pos.gote_pieces[:]
    return self
  @classmethod
  def build_sfen(cls, board, side_to_move, move_no, sente_pieces, gote_pieces):
    self = cls.__new__(cls)
    self.board = board
    self.side_to_move = side_to_move
    self.move_no = move_no
    self.sente_pieces = sente_pieces
    self.gote_pieces = gote_pieces
    return self.sfen()
  @classmethod
  def packed_to_sfen(cls, s: str):
    '''convert formate used in tsumeshogi DB to sfen'''
    board = [piece.FREE] * 81
    sente_pieces = [0] * piece.ROOK
    gote_pieces = [0] * piece.ROOK
    a = s.split('_')
    assert len(a) in range(39, 41)
    it = iter(a)
    for i, c in enumerate([18, 4, 4, 4, 4, 2, 2, 2]):
      for j in range(c):
        t = next(it, None)
        if t is None:
          break
        assert t[2] in ['0', '1']
        assert t[3] in ['1', '2']
        gote = t[2] == '1'
        promoted = t[3] == '2'
        if t.startswith('00'):
          assert not promoted
          if gote:
            gote_pieces[i] += 1
          else:
            sente_pieces[i] += 1
        else:
          col, row = int(t[0]), int(t[1])
          assert col in range(1, 10)
          assert row in range(1, 10)
          p = i + 1
          if p == piece.BISHOP:
            p = piece.ROOK
          elif p == piece.ROOK:
            p = piece.BISHOP
          if promoted:
            p = piece.promote(p)
          if gote:
            p *= -1
          k = 9 * (row - 1) + col - 1
          assert board[k] == piece.FREE
          board[k] = p
    self = cls.__new__(cls)
    self.board = board
    self.side_to_move = 1
    self.move_no = 1
    self.sente_pieces = sente_pieces
    self.gote_pieces = gote_pieces
    return self.sfen()
  def _generate_piece_moves(self, p: int, r: int, c: int, direction: Tuple[int, int, bool]) -> Iterator[int]:
    dr, dc, sliding = direction
    if p < 0:
      dr *= -1
    while True:
      r += dr
      if (r < 0) or (r > 8):
        break
      c += dc
      if (c < 0) or (c > 8):
        break
      q = self.board[9 * r + c]
      if q * p > 0:
        break
      yield 9 * r + c
      if not sliding or q != piece.FREE:
        break
  def _generate_some_moves(self):
    s = self.side_to_move
    c = self.sente_pieces if s > 0 else self.gote_pieces
    for i, p in enumerate(self.board):
      if p * s < 0:
        continue
      if p == piece.FREE:
        for j, _ in filter(lambda t: t[1] > 0, enumerate(c)):
          q = s * (j + 1)
          if cell.can_drop(i, q):
            yield Move(None, None, q, i)
      else:
        row, col = divmod(i, 9)
        for d in piece.MOVE_TABLE[abs(p)]:
          for to_cell in self._generate_piece_moves(p, row, col, d):
            yield Move(p, i, p, to_cell)
  def has_legal_move(self):
    pos = Position.clone(self)
    for m in self._generate_some_moves():
      try:
        pos.do_move(m)
        logging.debug('Found move %s in position %s', m.kifu_str(None), self.sfen())
        return True
      except IllegalMove:
        pass
    return False
  def opponent_piece_in_the_camp(self, side: int) -> bool:
    if side > 0:
      return any(p < 0 for p in self.board[63:])
    return any(p > 0 for p in self.board[:18])
