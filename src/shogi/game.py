# -*- coding: UTF8 -*-

from collections import defaultdict
from typing import List, Optional

from .move import Move, IllegalMove
from .piece import side_to_str
from .position import Position
from .result import GameResult, side_to_move_points

def player_with_rating_from_dict(d: dict, side:int) -> Optional[str]:
  name = side_to_str(side)
  player = d.get(name)
  if player is None:
    return None
  rating = d.get(name + '_rating')
  if rating is None:
    return player
  return f'{player}({rating})'

class Game:
  def has_result(self) -> bool:
    return not self.game_result is None
  def last_move(self) -> Optional[Move]:
    if not self.moves:
      return None
    return self.moves[-1]
  def set_result(self, game_result: GameResult):
    if self.game_result is None:
      self.game_result = game_result
  def _insert_sfen(self):
    sfen = self.pos.sfen(move_no = False)
    l = self._repetitions_dict[sfen]
    l.append(len(self._checks))
    check = self.pos.is_check()
    self._checks.append(check)
    if len(l) >= 4:
      u, v = l[0], l[-1]
      if check and all(self._checks[u:v:2]):
        self.set_result(GameResult.ILLEGAL_PRECEDING_MOVE)
      else:
        self.set_result(GameResult.REPETITION)
    if (not check) and self.pos.fesa_impasse_points():
      #https://lishogi.org/explanation/impasse
      self.set_result(GameResult.ENTERING_KING)
  def __init__(self, start_pos = None):
    self.tags = {}
    self.moves = []
    self.comments = defaultdict(list)
    self.game_result = None
    self.start_pos = start_pos
    self.pos = Position(start_pos)
    self.first_move_no = self.pos.move_no
    self._repetitions_dict = defaultdict(list)
    self._checks = []
    self._insert_sfen()
  def append_comment_before_move(self, move_no: int, s: str):
    k = move_no - self.first_move_no - 1
    if k >= 0:
      self.comments[k].append(s)
  def set_move_comments(self, comment: Optional[List[str]]):
    if isinstance(comment, str):
      comment = [comment]
    if comment:
      self.comments[len(self.moves)] = comment
  def do_move(self, m: Move):
    try:
      self.pos.do_move(m)
    except IllegalMove:
      self.set_result(GameResult.ILLEGAL_MOVE)
      return
    self.moves.append(m)
    self._insert_sfen()
  def do_usi_move(self, usi_move: str, comment: Optional[List[str]] = None):
    self.set_move_comments(comment)
    if usi_move == 'resign':
      self.set_result(GameResult.RESIGNATION)
      return
    self.do_move(self.pos.parse_usi_move(usi_move))
  def usi_position_command(self) -> str:
    s = 'position '
    if self.start_pos is None:
      s += 'startpos'
    else:
      s += 'sfen ' + self.start_pos
    if len(self.moves) > 0:
      s += ' moves ' + ' '.join(m.usi_str() for m in self.moves)
    return s
  def get_tag(self, key: str):
    return self.tags.get(key)
  def set_tag(self, key: str, value):
    self.tags[key] = value
  def get_row_values_from_tags(self, keys):
    return [self.get_tag(key) for key in keys]
  def player_with_rating(self, side: int) -> Optional[str]:
    return player_with_rating_from_dict(self.tags, side)
  def sente_points(self) -> Optional[int]:
    p = side_to_move_points(self.game_result)
    if p is None:
      return None
    if self.pos.side_to_move < 0:
      p *= -1
    return p
  def text_result(self) -> Optional[int]:
    p = self.sente_points()
    if p is None:
      return None
    if p > 0:
      return "1-0"
    if p < 0:
      return "0-1"
    return "1/2"
