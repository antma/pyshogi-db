# -*- coding: UTF8 -*-

from enum import IntEnum
from typing import List, Tuple, Set
from .game import Game
from .position import Position

Opening = IntEnum('Opening',
  ['OPPOSING_ROOK', 'RIGHT_HAND_FORTH_FILE_ROOK', 'DOUBLE_SWINGING_ROOK',
   'QUICK_ISHIDA',
  ])

_OPENINGS_D = {
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/2P6/9/PP1PPPPPP/1B5R1/LNSGKGSNL w - 4' : Opening.QUICK_ISHIDA,
}

def swinging_rook(rooks: Tuple[int, int]) -> bool:
  return 1 <= rooks[0] <= 5

def update_set_of_oppenings_by_rooks(rooks: Tuple[int, int], s: Set[Opening], rook_limit: int):
  if rooks[1] >= rook_limit:
    'quick ishida != third file rook'
    return
  r = rooks[0]
  if r == 2:
    s.add(Opening.OPPOSING_ROOK)
  if r == 6:
    s.add(Opening.RIGHT_HAND_FORTH_FILE_ROOK)

def _rooks_limit(moves_numbers: List[int], max_hands: int) -> int:
  return max_hands if not moves_numbers else moves_numbers[0]

def game_find_openings(g: Game, max_hands: int = 60) -> Tuple[Set[Opening], Set[Opening]]:
  sente_openings = set()
  gote_openings = set()
  assert g.start_pos is None
  pos = Position()
  sente_moves_numbers = []
  gote_moves_numbers = []
  for m in g.moves[:max_hands]:
    pos.do_move(m)
    ot = _OPENINGS_D.get(pos.sfen())
    if not ot is None:
      s, m = (sente_openings, sente_moves_numbers) if pos.side_to_move < 0 else (gote_openings, gote_moves_numbers)
      s.add(ot)
      m.append(pos.move_no - 1)
  sente_rook_limit = _rooks_limit(sente_moves_numbers, max_hands)
  gote_rook_limit = _rooks_limit(gote_moves_numbers, max_hands)
  sente_rooks, gote_rooks = g.rooks(max(sente_rook_limit, gote_rook_limit))
  sente_double_swinging_rook = False
  gote_double_swinging_rook = False
  if swinging_rook(sente_rooks) and swinging_rook(gote_rooks):
    if sente_rooks[1] > gote_rooks[1]:
      sente_double_swinging_rook = True
      sente_openings.add(Opening.DOUBLE_SWINGING_ROOK)
    else:
      gote_double_swinging_rook = True
      gote_openings.add(Opening.DOUBLE_SWINGING_ROOK)
  if not sente_double_swinging_rook:
    update_set_of_oppenings_by_rooks(sente_rooks, sente_openings, sente_rook_limit)
  if not gote_double_swinging_rook:
    update_set_of_oppenings_by_rooks(gote_rooks, gote_openings, gote_rook_limit)
  return (sente_openings, gote_openings)

"""
class Opening:
  def __init__(self, usi_moves: str, jp_name: str, en_name: str, url: str):
    self.usi_moves = usi_moves
    self.jp_name = jp_name
    self.en_name = en_name
    self.url = url

OPENINGS = [
  Opening('7g7f 3c3d 8h2b+ 3a2b B*4e',
    '筋違角', 'Wrong Diagonal Bishop', 'https://en.wikipedia.org/wiki/Wrong_Diagonal_Bishop'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h 8f7f',
   '相横歩取り','Double Side Pawn Capture', 'https://en.wikipedia.org/wiki/Double_Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*2h 3i2h B*4e',
   '横歩取り☖４五角', 'Side Pawn Capture, Bishop*45', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop*45'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*3h',
    '', '3rd File Pawn Drop Option', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d',
    '横歩取り', 'Side Pawn Picker', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2a3c',
    '横歩取り3三桂', 'Side Pawn Capture Knight-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c',
    '横歩取り3三角', 'Side Pawn Capture Bishop-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3f 8f8e',
    '', "Chūza's Rook", 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i5h',
    '青野流', 'Aono Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i6h',
    '勇気流', 'Yūki Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3c+',
    '', 'Takebe Rx33+ variation', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 4c4d 2f2e 2b3c 3i4h 8b4b 5g5f 9c9d 9g9f 7a7b 5i6h 3a3b 6h7h 5a6b 4i5h 6b7a 3g3f 7a8b 7i6h 4a5b 6h5g',
    '5七銀左急戦', 'Left Silver-57 Rapid Attack', 'https://en.wikipedia.org/wiki/Left_Silver-57_Rapid_Attack'),
  Opening('7g7f 8c8d 5g5f 3c3d 5f5e 5a4b 2h5h 7a6b 5i4h 8d8e 8h7g 7c7d 7i6h 6b7c',
    '超速3七銀', 'Super High Speed Silver-37', 'https://en.wikipedia.org/wiki/Super_High_Speed_Silver-37'),
]
"""
