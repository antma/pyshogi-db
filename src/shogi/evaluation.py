# -*- coding: UTF8 -*-

from math import exp

def _sigmoid(x: float) -> float:
  return 1.0 / (1.0 + exp(-x))

def win_rate(value: float) -> float:
  return _sigmoid(value / 900)

def winning_percentage(value: float) -> int:
  return round(win_rate(value) * 100.0)
