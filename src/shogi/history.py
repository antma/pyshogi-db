# -*- coding: UTF8 -*-

from typing import Optional
from . import position
from .move import Move

class PositionWithHistory(position.Position):
  def __init__(self, sfen: Optional[str] = None):
    self._history = []
    super().__init__(sfen)
    self.start_side_to_move = self.side_to_move
  def do_move(self, m: Move):
    u = super().do_move(m)
    self._history.append((m, u))
  def undo_last_move(self):
    if len(self._history) > 0:
      m, u = self._history.pop()
      self.undo_move(m, u)
  def kifu_line(self):
    a = []
    prev = None
    for m, _ in self._history:
      a.append(m.kifu_str(prev))
      prev = m
    return ' '.join(("☗'" if self.start_side_to_move * pow(-1, i & 1) > 0 else "☖'") + t for i, t in enumerate(a))
  def last_move(self) -> Optional[Move]:
    if self._history:
      return self._history[-1][0]
    return None
  def count_piece_moves(self, piece):
    return sum(1 for m in self._history if m[0].from_piece == piece)
