# -*- coding: UTF8 -*-

from typing import Optional
from . import position
from .move import Move, kifu_line

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
    return kifu_line([m for m, _ in self._history], self.start_side_to_move)
  def last_move(self) -> Optional[Move]:
    if self._history:
      return self._history[-1][0]
    return None
