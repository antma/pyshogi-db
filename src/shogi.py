# -*- coding: UTF8 -*-
''' shogi rules (move generation, etc.) '''

import logging
import log

FREE = 0
PAWN = 1
LANCE = 2
KNIGHT = 3
SILVER = 4
GOLD = 5
BISHOP = 6
ROOK = 7
KING = 8

ASCII_PIECES = 'plnsgbrk'

class Position:
  def _set_cell(self, row, col, piece):
    if not -KING <= piece <= KING:
      log.raise_value_error(f'Position._set_cell(): illegal piece {piece}')
    if (0 <= row < 9) and (0 <= col < 9):
      self.board[9 * row + col] = piece
    else:
      log.raise_value_error(f'Position._set_cell(): illegal cell ({row+1}, {col+1})')
  def __init__(self, sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"):
    self.board = [FREE] * 81
    self.sente_pieces = [0] * 6
    self.gote_pieces = [0] * 6
    a = list(sfen.split(' '))
    self.moveno = int(a[3])
    d = dict(map(lambda t: (t[1], t[0] + 1), enumerate(ASCII_PIECES)))
    for row, t in enumerate(a[0].split('/')):
      col = 9
      for c in t:
        if c.isdigit():
          for _ in range(int(c)):
            col -= 1
            self._set_cell(row, col, FREE)
        elif c.islower():
          col -= 1
          piece = d.get(c)
          if piece is None:
            log.raise_value_error(f"Position.__init__(sfen: {sfen}) unknown piece '{c}'")
          self._set_cell(row, col, -piece)
        elif c.isupper():
          col -= 1
          piece = d.get(c.lower())
          if piece is None:
            log.raise_value_error(f'Position.__init__(sfen: {sfen}) unknown piece {c}')
          self._set_cell(row, col, piece)
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
