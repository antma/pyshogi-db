# -*- coding: UTF8 -*-
''' shogi rules (move generation, etc.) '''

import logging
import log

from . import piece

class Position:
  '''shogi position'''
  def _set_cell(self, row, col, p):
    if not piece.is_legal(p):
      log.raise_value_error(f'Position._set_cell(): illegal piece {p}')
    if (0 <= row < 9) and (0 <= col < 9):
      self.board[9 * row + col] = p
    else:
      log.raise_value_error(f'Position._set_cell(): illegal cell ({row+1}, {col+1})')
  def __init__(self, sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"):
    self.board = [piece.FREE] * 81
    self.sente_pieces = [0] * 6
    self.gote_pieces = [0] * 6
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
    for row in range(8):
      u = 8 * row
      t = 0
      if row > 0:
        s += '/'
      for i in range(u + 7, u - 1, -1):
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
    for c, t in zip(piece.ASCII_PIECES, self.sente_pieces):
      if t > 0:
        w += c.upper() * t
    for c, t in zip(piece.ASCII_PIECES, self.gote_pieces):
      if t > 0:
        w += c * t
    if w == '':
      s += '-'
    else:
      s += w
    if moveno:
      s += ' ' + str(self.moveno)
    return s
