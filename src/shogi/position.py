# -*- coding: UTF8 -*-

import itertools
from typing import Optional
import logging
import log

from .move import (Move, UndoMove, IllegalMove, Nifu, UnresolvedCheck)
from . import piece

SFEN_INITIAL = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"

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
  def _find_king(self, side: int) -> Optional[int]:
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
    (rk, ck) = divmod(self._find_king(s), 9)
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
  def __init__(self, sfen = SFEN_INITIAL):
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
      logging.debug("Illegal position (king under check) = %s", self.sfen())
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
