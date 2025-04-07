# -*- coding: UTF8 -*-

from enum import IntEnum
from math import exp
from typing import Optional

def _sigmoid(x: float) -> float:
  return 1.0 / (1.0 + exp(-x))

def win_rate(value: float) -> float:
  return _sigmoid(value / 900)

def win_rate_to_centipawns(rate: float) -> int:
  n = 10000
  u, v = -n, n
  while v - u > 1:
    mid = (u + v) // 2
    if win_rate(float(mid)) <= rate:
      u = mid
    else:
      v = mid
  return u

class MistakeType(IntEnum):
  NORMAL = 1
  INACCURACY = 2
  MISTAKE = 3
  SERIOUS_MISTAKE = 4
  BLUNDER = 5
  def __str__(self) -> str:
    match self.value:
      case MistakeType.NORMAL: return 'Normal'
      case MistakeType.INACCURACY: return 'Inaccuracy'
      case MistakeType.MISTAKE: return 'Mistake'
      case MistakeType.SERIOUS_MISTAKE: return 'Serious mistake'
      case MistakeType.BLUNDER: return 'Blunder'

def win_rate_delta_to_mistake_type(delta: float) -> Optional[MistakeType]:
  if delta > 0.5:
    return MistakeType.BLUNDER
  if delta > 0.25:
    return MistakeType.SERIOUS_MISTAKE
  if delta > 0.1:
    return MistakeType.MISTAKE
  if delta > 0.05:
    return MistakeType.INACCURACY
  if delta > 0.02:
    return MistakeType.NORMAL
  return None

def mistake_str(side: int, old_win_rate: float, new_win_rate: float, pv: str, brief: bool = True) -> Optional[str]:
  delta = (old_win_rate - new_win_rate) * side
  mt = win_rate_delta_to_mistake_type(delta)
  if (mt is None) or (brief and mt == MistakeType.NORMAL):
    return None
  spv = 'PV'
  return f'{mt} ({old_win_rate * 100.0:.0f}% → {new_win_rate * 100.0:.0f}%). {spv}: {pv}'

def winning_percentage(value: float) -> int:
  return round(win_rate(value) * 100.0)
