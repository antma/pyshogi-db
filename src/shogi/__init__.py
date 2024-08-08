# -*- coding: UTF8 -*-
''' shogi rules (move generation, etc.) '''

from typing import Optional
import logging
import log

from . import kifu
from . import piece
from . import move

SFEN_INITIAL = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"

class Position:
  '''shogi position'''
  def _set_cell(self, row, col, p):
    if not piece.is_legal(p):
      log.raise_value_error(f'Position._set_cell(): illegal piece {p}')
    if (0 <= row < 9) and (0 <= col < 9):
      self.board[9 * row + col] = p
    else:
      log.raise_value_error(f'Position._set_cell(): illegal cell ({row+1}, {col+1})')
  def __init__(self, sfen = SFEN_INITIAL):
    self.board = [piece.FREE] * 81
    self.sente_pieces = [0] * piece.ROOK
    self.gote_pieces = [0] * piece.ROOK
    a = list(sfen.split(' '))
    self.moveno = int(a[3])
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
      for c in a[2]:
        if c.islower():
          self.gote_pieces[d.get(c) - 1] += 1
        elif c.isupper():
          self.sente_pieces[d.get(c.lower()) - 1] += 1
        else:
          log.raise_value_error(f'Position.__init__(sfen: {sfen}) piece in hand should be alphabetic')
  def sfen(self, moveno = True) -> str:
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
    if moveno:
      s += ' ' + str(self.moveno)
    return s
  def _validate_move(self, m: move.Move):
    if self.side_to_move * m.to_piece <= 0:
      raise ValueError("position side_to_move field isn't matched to move to_piece field'")
    if m.is_drop():
      if self.board[m.to_cell] != piece.FREE:
        raise ValueError('drop piece on occupied cell')
      c = self.sente_pieces if m.to_piece > 0 else self.gote_pieces
      if c[abs(m.to_piece) - 1] <= 0:
        raise ValueError('dropping piece which not in the player hand')
    else:
      if self.side_to_move * m.from_piece <= 0:
        raise ValueError("position side_to_move field isn't matched to move from_piece field'")
      taken_piece = self.board[m.to_cell]
      if taken_piece * self.side_to_move > 0:
        raise ValueError("player takes his piece'")

  def do_move(self, m: move.Move) -> Optional[move.UndoMove]:
    try:
      self._validate_move(m)
    except ValueError as err:
      log.raise_value_error(f'Position.do_move(m = {m}): {err}. SFEN = "{self.sfen()}"')
    #if self.side_to_move * m.to_piece <= 0:
    #  log.raise_value_error("Position.do_move(): position side_to_move field isn't matched to move to_piece field'")
    if m.is_drop():
      #if self.board[m.to_cell] != piece.FREE:
      #  log.raise_value_error('Position.do_move(): drop piece on occupied cell')
      self.board[m.to_cell] = m.to_piece
      c = self.sente_pieces if m.to_piece > 0 else self.gote_pieces
      #if c[m.to_piece - 1] <= 0:
      #  log.raise_value_error('Position.do_move(): dropping piece which not in the player hand')
      c[abs(m.to_piece) - 1] -= 1
      u = None
    else:
      taken_piece = self.board[m.to_cell]
      if taken_piece == piece.FREE:
        u = None
      else:
        logging.debug('taken_piece = %s', piece.to_string(taken_piece))
        u = move.UndoMove(taken_piece)
        c = self.sente_pieces if taken_piece < 0 else self.gote_pieces
        a = abs(taken_piece)
        if a != piece.KING:
          c[piece.unpromote(a) - 1] += 1
      self.board[m.from_cell] = piece.FREE
      self.board[m.to_cell] = m.to_piece
    self.side_to_move *= -1
    self.moveno += 1
    return u
