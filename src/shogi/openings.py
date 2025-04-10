# -*- coding: UTF8 -*-

from enum import IntEnum
from typing import Optional, Tuple, Set
from . import kifu
from .game import Game
from ._pattern import Recognizer, PositionForPatternRecognition, adjacent_pawns, last_row_pieces

Opening = IntEnum('Opening',
  ['OPPOSING_ROOK', 'THIRD_FILE_ROOK', 'FORTH_FILE_ROOK', 'GOKIGEN_CENTRAL_ROOK', 'RIGHT_HAND_FORTH_FILE_ROOK', 'DOUBLE_SWINGING_ROOK',
   'QUICK_ISHIDA', 'SAKATA_OPPOSING_ROOK',
   'AMAHIKO_OPPOSING_ROOK',
    #static
   'BISHOP_EXCHANGE', 'RIGHT_HAND_KING', 'DOUBLE_WING_ATTACK',
   'BISHOP_EXCHANGE_RECLINING_SILVER', 'RECLINING_SILVER',
   'SIDE_PAWN_PICKER', 'BISHOP33_STRATEGY', 'AONO_STYLE', 'YUUKI_STYLE',
   'MARUYAMA_VACCINE', 'SILVER_37_SUPER_RAPID',
   'URESINO_STYLE', 'PRIMITIVE_CLIMBING_SILVER', 'IJIMAS_BACK_BISHOP_STRATEGY',
   'BISHOP_EXCHANGE_CLIMBING_SILVER',
   'SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE',
   'SPEARING_THE_BIRD',

   #internal usage
   'SWINGING_ROOK',
  ])

_OPENINGS_D = {
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/2P6/9/PP1PPPPPP/1B5R1/LNSGKGSNL w - 4' : Opening.QUICK_ISHIDA,
  'ln1g1gsnl/1r3k1b1/p1sppp1pp/2p3p2/1p2P4/2P6/PPBP1PPPP/3SRK3/LN1G1GSNL b - 15': Opening.SILVER_37_SUPER_RAPID,
  'lnsgkgsnl/4r2+B1/pppp1p1pp/4p1p2/7P1/2P6/PP1PPPP1P/7R1/LNSGKGSNL w B 8': Opening.MARUYAMA_VACCINE,
  'lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B1S3R1/LN1GKGSNL w - 2': Opening.URESINO_STYLE,
  'lnsgk1snl/1r4gb1/p1ppppppp/9/1p5P1/9/PPPPPPP1P/1BG3SR1/LNS1KG1NL w - 8': Opening.DOUBLE_WING_ATTACK,
  'ln1gk1snl/1rs3gb1/p1ppppppp/9/1p5P1/9/PPPPPPP1P/1BG3SR1/LNS1KG1NL b - 9': Opening.DOUBLE_WING_ATTACK,
  'lnsgk1snl/1r4gb1/p1ppppppp/9/7P1/1p7/PPPPPPP1P/1BG3SR1/LNS1KG1NL b - 9': Opening.DOUBLE_WING_ATTACK,
  'lnsgk1snl/6gb1/p1pppp2p/6R2/9/1rP6/P2PPPP1P/1BG6/LNS1KGSNL w 3P2p 16': Opening.SIDE_PAWN_PICKER,
  'lnsgk1snl/6g2/p1ppppb1p/6R2/9/1rP6/P2PPPP1P/1BG6/LNS1KGSNL b 3P2p 17': Opening.BISHOP33_STRATEGY,
  'ln1gk1snl/3s2g2/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsgk2nl/6gs1/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsg2snl/4k1g2/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsgk1snl/6g2/p1ppppb1p/6R2/9/1rP6/P2PPPP1P/1BGK5/LNS2GSNL w 3P2p 18': Opening.YUUKI_STYLE,
  # 'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
  # 'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
}

_OPENINGS_POS_AND_MOVE_D = {
  'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12 8h7g' : Opening.BISHOP_EXCHANGE, #[wars/0004]
  #'ln1gk1snl/1r1s2g2/p1pppp1pp/1p4p2/9/2P4P1/PPSPPPP1P/2G4R1/LN2KGSNL w Bb 12 6h7g': Opening.BISHOP_EXCHANGE, #[wars/0030]
  #'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13 2b3c': Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
  #'ln1gk2nl/1r1s2g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/2G2S1R1/LN2KG1NL b Bb 17 2b3c': Opening.BISHOP_EXCHANGE, #[vE-7Y9XLfgs]
  #'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15 2b3c': Opening.BISHOP_EXCHANGE, #[SPSX76u6-vA]
}

#'ln1gkgsnl/1r1s3b1/p1pppp1pp/6p2/1p2P4/2P6/PPBP1PPPP/4R4/LNSGKGSNL w - 10': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/6p2/4p4/2P4P1/PP1PPPP1P/1B2GS1R1/LNSGK2NL b - 9': Opening.GOKIGEN_CENTRAL_ROOK,
#'ln1gkgsnl/1r1s3b1/p1pppp1pp/1p4p2/4P4/2P6/PP1P1PPPP/1B2R4/LNSGKGSNL w - 8': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/4p1p2/7P1/2P6/PP1PPPP1P/1B5R1/LNSGKGSNL b - 7': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15': Opening.BISHOP_EXCHANGE, #[wars/0017]

_RECOGNIZER = Recognizer([
  ([('K', '48'), ('G', '58'), ('S', '47'), ('N', '37'), ('L', '19'), ('R', '29') ,
    ('P', '46'), ('P', '36'), ('P', '57,56'), ('P', '25,26'), ('P', '16,17')], Opening.RIGHT_HAND_KING),
  ([('S', '27'), ('to', '27'), ('P', '25,26'), ('B', '88'), ('R', '28'), ('P', '76,77')] +
    last_row_pieces('3') + adjacent_pawns(7, 1, 10, [2, 7]), Opening.PRIMITIVE_CLIMBING_SILVER),
  ([('P', '55,56'), ('P', '76'), ('B', '88,77'), ('R', '58')] +
    last_row_pieces('') + adjacent_pawns(7, 2, 9, [5, 7]), Opening.GOKIGEN_CENTRAL_ROOK),
  #([('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85')], Opening.RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85'),
    ('B', 1), ('b', 1), ('P', '36'), ('N', '29,37'), ('G', '48,58'),
     ], Opening.BISHOP_EXCHANGE_RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '26,28'),
    ('B', 0), ('b', 0), ('P', '36'), ('N', '37'), ('P', '76'),
     ], Opening.RECLINING_SILVER),
  ([('B', '79'), ('K', '59'), ('S', '78'), ('P', '56'), ('R', '28'), ('!r', '82'),
    ('P', '25,26'), ('P', '96,97'), ('P', '16,17'),
    ('L', '19'), ('L', '99'), ('N', '29'), ('N', '89'), ('S', '39,48'), ('G', '69'), ('G', '58,69')] +
   adjacent_pawns(7, 3, 9, [5]), Opening.IJIMAS_BACK_BISHOP_STRATEGY),
  ([('G', '77'), ('R', '88'), ('P', '76'), ('P', '26,27'), ('to', '88'),
    ('B', 1), ('b', 1), #bishops exchanged
    ('P', '96,97'), ('P', '16,17')] +
    last_row_pieces('6') + adjacent_pawns(7, 3, 9, [7]), Opening.SAKATA_OPPOSING_ROOK),
  ([('S', '77'), ('R', '28'), ('r', '82'), ('B', 1), ('b', 1), ('P', '76'), ('P', '67'),
   ('K', '59'), ('L', '99'), ('L', '19'), ('N', '29'), ('N', '89'), ('from', '88,68'), ('to', '77'), ('G', '78'),
   ('max-gold-moves', 2),
   ], Opening.BISHOP_EXCHANGE),
  ([('S', '26'), ('from', '27'), ('to', '26'), ('P', '25'), ('R', '28'), ('P', '37'),
    ('B', 1), ('b', 1)], Opening.BISHOP_EXCHANGE_CLIMBING_SILVER),
  ([('B', '77'), ('from', '88'), ('to', '77'), ('K', '78'), ('G', '58'), ('G', '69'), ('S', '79'), ('N', '89'), ('L', '99'),
   ('P', '87'), ('P', '76'), ('P', '67'), ('P', '56'), ('S', '57,48'), ('R', '28')], Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE),
  ([('B', '66'), ('R', '88'), ('to', '88'), ('S', '77'), ('P', '76')] +
    last_row_pieces('7') + adjacent_pawns(7, 2, 9, [7]), Opening.AMAHIKO_OPPOSING_ROOK),
  ([('B', '79'), ('K', '78'), ('S', '57'), ('R', '28'), ('P', '56'), ('P', '67'), ('P', '47'), ('P', '25')] +
    last_row_pieces('357') + adjacent_pawns(7, 3, 9, [5]), Opening.SPEARING_THE_BIRD),
])

def position_find_opening(pos: PositionForPatternRecognition) -> Optional[Opening]:
  assert isinstance(pos, PositionForPatternRecognition)
  sfen = pos.sfen()
  ot = _OPENINGS_D.get(sfen)
  if not ot is None:
    return ot
  m = pos.last_move
  if not m is None:
    last_usi_move = m.usi_str()
    ot = _OPENINGS_POS_AND_MOVE_D.get(sfen + ' ' + last_usi_move)
    if not ot is None:
      return ot
  return _RECOGNIZER.find(pos)

def _position_update_set_of_openings(pos: PositionForPatternRecognition, sente_set, gote_set) -> Opening:
  ot = position_find_opening(pos)
  if ot is None:
    return None
  s = sente_set if pos.side_to_move < 0 else gote_set
  if ot in s:
    return None
  s.add(ot)
  return ot

_BEFORE_ROOK_OPENING_S = set([Opening.URESINO_STYLE, Opening.PRIMITIVE_CLIMBING_SILVER])

def _almost_empty(s: Set[Opening]) -> bool:
  return s.issubset(_BEFORE_ROOK_OPENING_S)

def _update_set_of_oppenings_by_rooks(col: int, my_set: Set[Opening], opponent_set: Set[Opening]):
  if col < 5:
    if Opening.SWINGING_ROOK in opponent_set:
      my_set.add(Opening.DOUBLE_SWINGING_ROOK)
      return
  if col == 2:
    if _almost_empty(my_set):
      my_set.add(Opening.OPPOSING_ROOK)
    my_set.add(Opening.SWINGING_ROOK)
  elif col == 3:
    'quick ishida != third file rook'
    if _almost_empty(my_set):
      my_set.add(Opening.THIRD_FILE_ROOK)
    my_set.add(Opening.SWINGING_ROOK)
  elif col == 4:
    if _almost_empty(my_set):
      my_set.add(Opening.FORTH_FILE_ROOK)
    my_set.add(Opening.SWINGING_ROOK)
  elif col == 5:
    my_set.add(Opening.SWINGING_ROOK)
  elif col == 6:
    if _almost_empty(my_set):
      my_set.add(Opening.RIGHT_HAND_FORTH_FILE_ROOK)

def _remove_redundant(s):
  s.discard(Opening.SWINGING_ROOK)
  if Opening.SAKATA_OPPOSING_ROOK in s:
    s.discard(Opening.BISHOP_EXCHANGE)
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.AMAHIKO_OPPOSING_ROOK in s:
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.PRIMITIVE_CLIMBING_SILVER in s:
    s.discard(Opening.RIGHT_HAND_FORTH_FILE_ROOK)

_GOTE_URESINO_FIRST_MOVE = kifu.move_parse('４二銀(31)', -1, None)

def game_find_openings(g: Game, max_hands: int = 60) -> Tuple[Set[Opening], Set[Opening]]:
  sente_openings = set()
  gote_openings = set()
  try:
    if g.moves[1] == _GOTE_URESINO_FIRST_MOVE:
      gote_openings.add(Opening.URESINO_STYLE)
  except IndexError:
    pass
  assert g.start_pos is None
  pos = PositionForPatternRecognition()
  for m in g.moves[:max_hands]:
    col = pos.first_rook_move_rank(m)
    if not col is None:
      side = pos.side_to_move
      my_set, opponent_set = (sente_openings, gote_openings) if side > 0 else (gote_openings, sente_openings)
      _update_set_of_oppenings_by_rooks(col, my_set, opponent_set)
    pos.do_move(m)
    _position_update_set_of_openings(pos, sente_openings, gote_openings)

  _remove_redundant(sente_openings)
  _remove_redundant(gote_openings)
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
