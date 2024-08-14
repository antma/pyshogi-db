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
ASCII_LONG_NAMES = [None, 'pawn', 'lance', 'knight', 'silver', 'gold', 'bishop', 'rook', 'king', 'token', \
 'promotedlance', 'promotedknight', 'promotedsilver', None, 'horse', 'dragon']

_UNPROMOTED_PIECES = set([FREE, GOLD, KING])

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
