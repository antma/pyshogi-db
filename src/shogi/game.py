# -*- coding: UTF8 -*-

from collections import defaultdict
import logging
from typing import Mapping, Optional

import log
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
  def adjourn(self):
    if (self.game_result is None) and (not self.pos.has_legal_move()):
      self.set_result(GameResult.CHECKMATE)
  def _insert_sfen(self):
    self._positions = None
    if self._disable_game_result_auto_detection:
      return
    sfen = self.pos.sfen(move_no = False)
    l = self._repetitions_dict[sfen]
    l.append(len(self._checks))
    check = self.pos.is_check()
    self._checks.append(check)
    if len(l) >= 2:
      logging.debug("Position '%s' was repeated %d times on moves %s", sfen, len(l), l)
    if len(l) >= 4:
      u, v = l[0], l[-1]
      if check and all(self._checks[u:v:2]):
        self.set_result(GameResult.ILLEGAL_PRECEDING_MOVE)
      else:
        self.set_result(GameResult.REPETITION)
    if (not check) and self.pos.fesa_impasse_points():
      #https://lishogi.org/explanation/impasse
      self.set_result(GameResult.ENTERING_KING)
  def move_no_to_side_to_move(self, move_no: int) -> int:
    if move_no < self.start_move_no:
      log.raise_value_error('move number is too small')
    return self.start_side_to_move * pow(-1, (move_no - self.start_move_no) & 1)
  def __init__(self, start_pos = None, disable_game_result_auto_detection: bool = False):
    self._disable_game_result_auto_detection = disable_game_result_auto_detection
    self.tags = {}
    self.moves = []
    #comments: move_no -> List[str]
    #comments before move
    self.comments = defaultdict(list)
    self.start_pos = start_pos
    self.pos = Position(start_pos)
    self.start_move_no = self.pos.move_no
    self.start_side_to_move = self.pos.side_to_move
    self.game_result = None
    self._repetitions_dict = defaultdict(list)
    self._checks = []
    self._insert_sfen()
    self._positions = None
  def append_comment_before_move(self, move_no: int, s: str):
    self.comments[move_no].append(s)
  def do_move(self, m: Move):
    try:
      self.pos.do_move(m)
    except IllegalMove:
      self.set_result(GameResult.ILLEGAL_MOVE)
      return
    self.moves.append(m)
    self._insert_sfen()
  def do_usi_move(self, usi_move: str):
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
  def positions(self) -> Mapping[int, str]:
    if not self._positions is None:
      return self._positions
    pos = Position(self.start_pos)
    d = {pos.move_no: pos.sfen()}
    for m in self.moves:
      pos.do_move(m)
      d[pos.move_no] = pos.sfen()
    self._positions = d
    return d
  def parse_player_name(self, s: str, key: str):
    if s.endswith(')'):
      i = s.rfind('(')
      if i >= 0:
        t = s[i+1:len(s)-1]
        if (len(t) > 0) and t.isdigit():
          self.set_tag(key, s[:i])
          self.set_tag(key + '_rating', int(t))
          return
    self.set_tag(key, s)
  def set_ratings(self, d: Mapping[str, int]):
    for side in [1, -1]:
      name = side_to_str(side)
      player = self.get_tag(name)
      if not player is None:
        rating = d.get(player)
        if not rating is None:
          self.set_tag(name + '_rating', rating)
  def total_time(self) -> int:
    sente_time = None
    gote_time = None
    flags = 0
    for m in reversed(self.moves):
      if m.cum_time is None:
        continue
      if m.to_piece > 0:
        if sente_time is None:
          sente_time = m.cum_time
          flags |= 1
      else:
        if gote_time is None:
          gote_time = m.cum_time
          flags |= 2
      if flags == 3:
        return round((sente_time + gote_time).total_seconds())
    return None
  def player_stats(self, player_name: str):
    side = None
    points = self.sente_points()
    if points is None:
      logging.warning('Game without result')
      return None
    if self.get_tag('sente') == player_name:
      side = 'sente'
      oside = 'gote'
    elif self.get_tag('gote') == player_name:
      side = 'gote'
      oside = 'sente'
      points *= -1
    if side is None:
      return None
    opponent = self.get_tag(oside)
    if opponent is None:
      return None
    rating = self.get_tag(side + '_rating')
    if rating is None:
      logging.warning('Game without player rating')
      return None
    assert isinstance(rating, int)
    orating = self.get_tag(oside + '_rating')
    if orating is None:
      logging.warning('Game without opponent rating')
      return None
    assert isinstance(orating, int)
    return {
      'side': side,
      'opponent' : opponent,
      'points' : points,
      'rating' : int(rating),
      'orating': int(orating),
      'hands' : len(self.moves),
      'date': self.get_tag('start_date'),
      'time_control' : self.get_tag('time_control'),
      'duration': self.total_time(),
    }
  def drop_zero_times(self):
    if all(m.zero_or_none_time() for m in self.moves):
      for m in self.moves:
        m.drop_times()
