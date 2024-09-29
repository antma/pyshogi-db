# -*- coding: UTF8 -*-

from collections import defaultdict
from typing import List, MutableMapping, Optional

from .move import Move
from .position import Position
from .result import GameResult

class Game:
  moves: List[Move] = []
  start_pos: Optional[str]
  pos: Position
  c: MutableMapping[str, List[int]]
  checks: List[bool]
  game_result: Optional[GameResult] = None
  def has_result(self) -> bool:
    return not self.game_result is None
  def set_result(self, game_result: GameResult):
    if self.game_result is None:
      self.game_result = game_result
  def _insert_sfen(self):
    sfen = self.pos.sfen(move_no = False)
    l = self.c[sfen]
    l.append(len(self.checks))
    check = self.pos.is_check()
    self.checks.append(check)
    if len(l) >= 4:
      u, v = l[0], l[-1]
      if check and all(self.checks[u:v:2]):
        self.set_result(GameResult.ILLEGAL_PRECEDING_MOVE)
      else:
        self.set_result(GameResult.REPETITION)
    if (not check) and self.pos.fesa_impasse_points():
      #https://lishogi.org/explanation/impasse
      self.set_result(GameResult.ENTERING_KING)
  def __init__(self, start_pos = None):
    self.start_pos = start_pos
    self.pos = Position(start_pos)
    self.c = defaultdict(list)
    self.checks = []
    self._insert_sfen()
  def do_usi_move(self, usi_move: str):
    if usi_move == 'resign':
      self.set_result(GameResult.RESIGNATION)
      return
    m = self.pos.parse_usi_move(usi_move)
    try:
      self.pos.do_move(m)
    except IllegalMove:
      self.set_result(GameResult.ILLEGAL_MOVE)
      return
    self.moves.append(m)
    self._insert_sfen()
  def usi_position_command(self) -> str:
    s = 'position '
    if self.start_pos is None:
      s += 'startpos'
    else:
      s += 'sfen ' + self.start_pos
    if len(self.moves) > 0:
      s += ' moves ' + ' '.join(m.usi_str() for m in self.moves)
    return s
