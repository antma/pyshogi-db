# -*- coding: UTF8 -*-

import log

FREE = 0
PAWN = 1
LANCE = 2
KNIGHT = 3
SILVER = 4
GOLD = 5
BISHOP = 6
ROOK = 7
KING = 8
PROMOTED = 8
TOKIN = PAWN + PROMOTED
HORSE = BISHOP + PROMOTED
DRAGON = ROOK + PROMOTED

ASCII_PIECES = 'plnsgbrk'
ASCII_LONG_NAMES = [None, 'pawn', 'lance', 'knight', 'silver', 'gold', 'bishop', 'rook', 'king', 'tokin', \
 'promotedlance', 'promotedknight', 'promotedsilver', None, 'horse', 'dragon']

KIFU_PIECES = '歩香桂銀金角飛玉と杏圭??馬龍'
CSA_PIECES = ['FU', 'KY', 'KE', 'GI', 'KI', 'KA', 'HI', 'OU', 'TO', 'NY', 'NK', 'NG',  None, 'UM', 'RY']

_UNPROMOTED_PIECES = set([FREE, GOLD, KING])

_GENERAL_MOVES = [(-1, -1), (-1, 0), (-1, 1)]
GOLD_MOVES = _GENERAL_MOVES + [(0, -1), (0, 1), (1, 0)]
SILVER_MOVES = _GENERAL_MOVES + [(1, -1), (1, 1)]
KNIGHT_MOVES = [(-2, -1), (-2, 1)]
del _GENERAL_MOVES

def is_legal(piece: int) -> bool:
  return abs(piece) <= DRAGON

def to_string(piece: int) -> str:
  p = abs(piece)
  b = True
  if p > PROMOTED:
    p -= PROMOTED
    b = False
  s = ASCII_PIECES[p - 1]
  if piece > 0:
    s = s.upper()
  return s if b else '+' + s

def is_promoted(piece: int) -> bool:
  return abs(piece) > KING

def promote(piece: int) -> int:
  a = abs(piece)
  if a in _UNPROMOTED_PIECES:
    log.raise_value_error("promotion of gold or king is illegal")
  if a > KING:
    log.raise_value_error("piece is already promoted")
  return (piece + PROMOTED) if piece > 0 else (piece - PROMOTED)

def unpromote(piece: int) -> int:
  if piece > KING:
    return piece - PROMOTED
  if piece < -KING:
    return piece + PROMOTED
  return piece

_KIFU_PROMOTED_SINGLE_CHAR_S = set([TOKIN, HORSE, DRAGON])
def kifu_str(p: int) -> str:
  p = abs(p)
  if is_promoted(p) and not p in _KIFU_PROMOTED_SINGLE_CHAR_S:
    return '成' + KIFU_PIECES[unpromote(p) - 1]
  r = KIFU_PIECES[p - 1]
  assert r != '?'
  return r

def side_to_str(side: int) -> str:
  return "sente" if side > 0 else "gote"

class PromotionZone:
  def __init__(self, side: int):
    if side > 0:
      self._f = lambda k: k < 27
    else:
      self._f = lambda k: k >= 54
  def __contains__(self, k: int) -> bool:
    return self._f(k)

def from_upper(c: str) -> int:
  if len(c) != 1:
    return -1
  if not c.isupper():
    return -2
  i = ASCII_PIECES.find(c.lower())
  if i < 0:
    return i
  return i + 1
