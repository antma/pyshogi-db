# -*- coding: UTF8 -*-

from typing import (Optional, Tuple)

_TBL = [-800, -677, -589, -538, -501, -470, -444, -422, -401, -383, -366, -351, -336, -322, -309, -296, -284, -273, -262, -251, -240, -230, -220, -211, -202, -193, -184, -175, -166, -158, -149, -141, -133, -125, -117, -110, -102, -95, -87, -80, -72, -65, -57, -50, -43, -36, -29, -21, -14, -7, 0, 7, 14, 21, 29, 36, 43, 50, 57, 65, 72, 80, 87, 95, 102, 110, 117, 125, 133, 141, 149, 158, 166, 175, 184, 193, 202, 211, 220, 230, 240, 251, 262, 273, 284, 296, 309, 322, 336, 351, 366, 383, 401, 422, 444, 470, 501, 538, 589, 677, 800]

def performance(opponentAverageRating: float, percent: float) -> float:
  if percent < 1.0:
    x1 = 1
  elif percent > 99.0:
    x1 = 99
  else:
    x1 = round(percent)
  y1 = _TBL[x1]
  x0 = x1 - 1
  y0 = _TBL[x0]
  x2 = x1 + 1
  y2 = _TBL[x2]
  #https://en.wikipedia.org/wiki/Lagrange_polynomial
  return opponentAverageRating + 0.5 * (y0 * (percent - x1) * (percent - x2) + y2 * (percent - x0) * (percent - x1)) - y1 * (percent - x0) * (percent - x2)

class Performance:
  def __init__(self):
    self.games = 0
    self.score = 0.0
    self.opponents_rating_sum = 0.0
  def add(self, opponent_rating: float, game_score: float):
    self.games += 1
    self.score += game_score
    self.opponents_rating_sum += opponent_rating
  def __repr__(self):
    return 'Performance(games: {}, score: {}, average_rating: {})'.format(self.games, self.score, self.opponents_rating_sum / self.games)
  def compute(self, min_games: int) -> Optional[float]:
    if self.games < min_games:
      return None
    return performance(self.opponents_rating_sum / self.games, 100.0 * (self.score / self.games))
