# -*- coding: UTF8 -*-

from typing import Optional
from . import kifu, move, position

class PositionWithHistory(position.Position):
  def __init__(self, sfen: Optional[str] = None):
    self.history = []
    super().__init__(sfen)
  def do_move(self, m: move.Move):
    u = super().do_move(m)
    self.history.append((m, u))
  def undo_last_move(self):
    if len(self.history) > 0:
      m, u = self.history.pop()
      self.undo_move(m, u)
  def kifu_line(self):
    a = []
    prev = None
    for m, _ in self.history:
      a.append(kifu.kifu_move(m, prev))
      prev = m
    return ' '.join(("☗'" if (i & 1) == 0 else "☖'") + t for i, t in enumerate(a))
