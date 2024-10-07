# -*- coding: UTF8 -*-

from math import exp

def _sigmoid(x: float) -> float:
  return 1.0 / (1.0 + exp(-x))

def win_rate(value: float) -> float:
  return _sigmoid(value / 900)

def win_rate_to_centipawns(rate: float) -> int:
  N = 10000
  u, v = -N, N
  while v - u > 1:
    mid = (u + v) // 2
    if win_rate(float(mid)) <= rate:
      u = mid
    else:
      v = mid
  return u

def winning_percentage(value: float) -> int:
  return round(win_rate(value) * 100.0)
