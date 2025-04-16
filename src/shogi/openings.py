# -*- coding: UTF8 -*-

from enum import IntEnum
from typing import Optional, Tuple, Set
from . import kifu
from .game import Game
from ._pattern import Recognizer, SFENMap, PositionForPatternRecognition, adjacent_pawns, last_row_pieces

Opening = IntEnum('Opening',
  ['OPPOSING_ROOK', 'THIRD_FILE_ROOK', 'FORTH_FILE_ROOK', 'GOKIGEN_CENTRAL_ROOK', 'DOUBLE_SWINGING_ROOK',
   'FORTH_THIRD_FILE_ROOK_STRATEGY',
   'QUICK_ISHIDA', 'ISHIDA_STYLE', 'MASUDAS_ISHIDA_STYLE',
   'SAKATA_OPPOSING_ROOK', 'AMAHIKO_OPPOSING_ROOK',
   'FUJII_SYSTEM',
   'LEGHORN_SPECIAL',
    #static
   'SLEEVE_ROOK', 'RIGHT_HAND_FORTH_FILE_ROOK',
   'RIGHT_HAND_KING',
   'DOUBLE_WING_ATTACK', 'DOUBLE_WING_ATTACK_CLIMBING_SILVER',
   'UFO_SILVER',
   'RECLINING_SILVER',
   'BISHOP_EXCHANGE', 'ONE_TURN_LOSS_BISHOP_EXCHANGE', 'BISHOP_EXCHANGE_RECLINING_SILVER', 'BISHOP_EXCHANGE_CLIMBING_SILVER',
   'SIDE_PAWN_PICKER', 'BISHOP33_STRATEGY', 'AONO_STYLE', 'YUUKI_STYLE', 'BISHOP45_STRATEGY',
   'MARUYAMA_VACCINE', 'SILVER_37_SUPER_RAPID', 'SUPER_RAPID_ATTACK',
   'URESINO_STYLE', 'PRIMITIVE_CLIMBING_SILVER', 'IJIMAS_BACK_BISHOP_STRATEGY',
   'SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE',
   'SPEARING_THE_BIRD',
   'SILVER_HORNED_SNOW_ROOF',
   'CLIMBING_GOLD',

   #internal usage
    'NONE', 'SWINGING_ROOK'
])

_OPENINGS_D = SFENMap({
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
  'lnsgkgsnl/1r5+B1/pppppp1pp/6p2/9/2P6/PP1PPPPPP/7R1/LNSGKGSNL w B 4': Opening.NONE, #[not BISHOP_EXCHANGE]
  # 'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
  # 'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
})

_OPENINGS_POS_AND_MOVE_D = SFENMap({
  'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12 8h7g' : Opening.BISHOP_EXCHANGE, #[wars/0004]
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/4P4/PPPP1PPPP/1B2R4/LNSGKGSNL w - 4 2h5h': Opening.GOKIGEN_CENTRAL_ROOK, #[wars/0064]
  'lnsgk1snl/6g2/p1pppp2p/6R2/5b3/1rP6/P2PPPP1P/1SG4S1/LN2KG1NL b B4Pp 21 B*4e' : Opening.BISHOP45_STRATEGY, #[wars/0066]
  'lnsgk1snl/6gb1/p1pppp2p/6pR1/9/P1r6/3PPPP1P/1BG6/LNS1KGSNL b 2P3p 17 8f7f': Opening.SIDE_PAWN_PICKER, #[wars/0084]
  'lnsgk1snl/6gb1/p1pppp2p/6pR1/9/P1r6/2BPPPP1P/2G6/LNS1KGSNL w 2P3p 18 8h7g': Opening.BISHOP33_STRATEGY, #[wars/0084]
  'lnsgk1snl/1r4gb1/p1ppppppp/7P1/1p7/9/PPPPPPP1P/1BG4R1/LNS1KGSNL w - 8 2e2d': Opening.DOUBLE_WING_ATTACK, #[wars/0088]
  'ln1gk1snl/1rs3gb1/p1pppppp1/8p/1p7/9/PPPPPPPSP/1BG4R1/LNS1KG1NL w P 16 3h2g': Opening.DOUBLE_WING_ATTACK_CLIMBING_SILVER, #[wars/0088]
  'lnsgkgsnl/4r4/pppp1pb1p/6pR1/9/2P1P4/PP1P1PP1P/1S2G4/LN1GK1SNL b B2Pp 17 B*3c': Opening.SUPER_RAPID_ATTACK,
  'lnsgkgs+Rl/4r4/pppp1pb1p/6p2/9/2P1P4/PP1P1PP1P/1S2G4/LN1GK1SNL w BN2Pp 18 2d2a+': Opening.SUPER_RAPID_ATTACK,
  #'lnsgk1snl/1r4g2/pppppp1pp/6p2/7P1/2P6/PP1PPPP1P/1+b5R1/LNSGKGSNL b b 7 2b8h+': Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE, #[wars/0074]
  #'ln1gk1snl/1r1s2g2/p1pppp1pp/1p4p2/9/2P4P1/PPSPPPP1P/2G4R1/LN2KGSNL w Bb 12 6h7g': Opening.BISHOP_EXCHANGE, #[wars/0030]
  #'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13 2b3c': Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
  #'ln1gk2nl/1r1s2g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/2G2S1R1/LN2KG1NL b Bb 17 2b3c': Opening.BISHOP_EXCHANGE, #[vE-7Y9XLfgs]
  #'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15 2b3c': Opening.BISHOP_EXCHANGE, #[SPSX76u6-vA]
})

#'ln1gkgsnl/1r1s3b1/p1pppp1pp/6p2/1p2P4/2P6/PPBP1PPPP/4R4/LNSGKGSNL w - 10': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/6p2/4p4/2P4P1/PP1PPPP1P/1B2GS1R1/LNSGK2NL b - 9': Opening.GOKIGEN_CENTRAL_ROOK,
#'ln1gkgsnl/1r1s3b1/p1pppp1pp/1p4p2/4P4/2P6/PP1P1PPPP/1B2R4/LNSGKGSNL w - 8': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/4p1p2/7P1/2P6/PP1PPPP1P/1B5R1/LNSGKGSNL b - 7': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15': Opening.BISHOP_EXCHANGE, #[wars/0017]

_RECOGNIZER = Recognizer([
  ([('K', '48'), ('G', '58'), ('S', '47'), ('N', '37'), ('L', '19'), ('R', '29') ,
    ('P', '46'), ('P', '36'), ('P', '56,57'), ('P', '25,26'), ('P', '16,17')], Opening.RIGHT_HAND_KING),
  ([('S', '27'), ('to', '27'), ('P', '25,26'), ('B', '88'), ('R', '28'), ('P', '76,77')] +
    last_row_pieces('3') + adjacent_pawns(7, 1, 10, [2, 7]), Opening.PRIMITIVE_CLIMBING_SILVER),
  ([('S', '37'), ('to', '37'), ('P', '25,26'), ('B', '88'), ('R', '28'), ('P', '36'), ('P', '76,77'), ('G', '78')] +
    last_row_pieces('36') + adjacent_pawns(7, 1, 10, [2, 3, 7]), Opening.PRIMITIVE_CLIMBING_SILVER),
  ([('R', '58'), ('to', '58'), ('P', '55,56'), ('P', '76'), ('B', '77,88')] +
    last_row_pieces('') + adjacent_pawns(7, 2, 9, [5, 7]), Opening.GOKIGEN_CENTRAL_ROOK),
  #([('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85')], Opening.RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85'),
    ('B', 1), ('b', 1), ('P', '36'), ('N', '29,37'), ('G', '48,58'),
     ], Opening.BISHOP_EXCHANGE_RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '26,28'),
    ('B', 0), ('b', 0), ('P', '36'), ('N', '37'), ('P', '76'), ('G', '78'),
     ], Opening.RECLINING_SILVER),
  ([('B', '79'), ('K', '59'), ('S', '78'), ('P', '56'), ('R', '28'), ('!r', '82'),
    ('P', '25,26'), ('P', '96,97'), ('P', '16,17'),
    ('L', '19'), ('L', '99'), ('N', '29'), ('N', '89'), ('S', '39,48'), ('G', '69'), ('G', '58,69')] +
   adjacent_pawns(7, 3, 9, [5]), Opening.IJIMAS_BACK_BISHOP_STRATEGY),
  ([('G', '77'), ('R', '88'), ('P', '76'), ('P', '26,27'), ('to', '88'),
    ('B', 1), ('b', 1), #bishops exchanged
    ('P', '96,97'), ('P', '16,17')] +
    last_row_pieces('6') + adjacent_pawns(7, 3, 9, [7]), Opening.SAKATA_OPPOSING_ROOK),
  ([('S', '77'), ('R', '28'), ('B', 1), ('b', 1), ('P', '76'), ('P', '67'), #('r', '82'),
   ('K', '59'), ('L', '99'), ('L', '19'), ('N', '29'), ('N', '89'), ('from', '68,88'), ('to', '77'), ('G', '78'),
   ('max-gold-moves', 2),
   ], Opening.BISHOP_EXCHANGE),
  ([('S', '26'), ('from', '27'), ('to', '26'), ('P', '25'), ('R', '28'), ('P', '37'),
    ('B', 1), ('b', 1)], Opening.BISHOP_EXCHANGE_CLIMBING_SILVER),
  ([('B', '77'), ('from', '88'), ('to', '77'), ('K', '78'), ('G', '58,67'),
   ('P', '87'), ('P', '76'), ('P', '66,67'), ('P', '56'), ('S', '48,57'), ('R', '28'), ('!p', '43')] +
   last_row_pieces('2345'), Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE),
  ([('B', '66'), ('R', '88'), ('to', '88'), ('S', '77'), ('P', '76')] +
    last_row_pieces('7') + adjacent_pawns(7, 2, 9, [7]), Opening.AMAHIKO_OPPOSING_ROOK),
  ([('B', '79'), ('K', '78'), ('S', '57'), ('R', '28'), ('P', '56'), ('P', '67'), ('P', '47'), ('P', '25')] +
    last_row_pieces('357') + adjacent_pawns(7, 3, 9, [5]), Opening.SPEARING_THE_BIRD),
  ([('P', '36'), ('to', '36'), ('R', '68'), ('S', '38'), ('S', '67,78'), ('G', '58,69'), ('B', '77'),
    ('P', '76'), ('P', '66,67'), ('P', '57'), ('P', '87'), ('P', '27'), ('P', '15,16')] +
    last_row_pieces('367'), Opening.FUJII_SYSTEM),
  ([('P', '46'), ('to', '46'), ('R', '68'), ('S', '38'), ('S', '67,78'), ('G', '58,69'), ('B', '77'),
    ('P', '76'), ('P', '66,67'), ('P', '57'), ('P', '87'), ('P', '27'), ('P', '15,16')] +
    last_row_pieces('367'), Opening.FUJII_SYSTEM),
  ([('K', '69'), ('G', '78'), ('G', '58'), ('S', '67'), ('S', '47'), ('to', '47'),
    ('P', '76'), ('P', '66'), ('P', '56,57'), ('P', '46'), ('N', '89'), ('L', '99'), ('N', '29,37'), ('L', '19'), ('B', '77,88')], Opening.SILVER_HORNED_SNOW_ROOF),
  ([('P', '75'), ('R', '78'), ('to', '78'), ('from', '28'), ('B', '88'), ('p', '34')] +
   last_row_pieces('') + adjacent_pawns(7, 1, 10, [7]), Opening.QUICK_ISHIDA),
  ([('K', '48'), ('to', '48'), ('R', '78'), ('P', '75'), ('B', '88'), ('r', '82'), ('p', '34')] +
   last_row_pieces('5') + adjacent_pawns(7, 1, 10, [7]), Opening.MASUDAS_ISHIDA_STYLE),
  ([('R', '76'), ('N', '77'), ('to', '77'), ('P', '66'), ('P', '75'), ('P', '87'), ('B', '88,97'), ('P', '96,97'), ('L', '99')], Opening.ISHIDA_STYLE),
  ([('G', '27'), ('to', '27'), ('from', '38'), ('P', '25,26'), ('R', '28'),
    ('P', '37'), ('p', '35'), ('N', '29'), ('L', '19')], Opening.CLIMBING_GOLD),
  ([('HORSE', '22'), ('to', '22'), ('from', '88'), ('side', -1), ('R', '28'), ('G', '69,78'), ('P', '76')] +
   adjacent_pawns(7, 3, 7, []) + last_row_pieces('6'), Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE),
  ([('R', '68'), ('to', '68'), ('from', '28'), ('B', 1), ('b', 1), ('S', '77')] +
   last_row_pieces('7') + adjacent_pawns(7, 2, 9, [7]), Opening.LEGHORN_SPECIAL),
  ([('S', '36'), ('to', '36'), ('from', '27'), ('R', '28'), ('G', '78'), (' ', '25'), (' ', '24')] +
   last_row_pieces('36') + adjacent_pawns(7, 3, 7, []), Opening.UFO_SILVER),
  ([ ('R', '78'), ('from', '68'), ('to', '78'), ('P', '75'), ('K', '38'), ('B', '88')] +
  last_row_pieces('5') + adjacent_pawns(7, 2, 9, [7]), Opening.FORTH_THIRD_FILE_ROOK_STRATEGY),
], 'openings')

def position_find_opening(pos: PositionForPatternRecognition) -> Optional[Opening]:
  assert isinstance(pos, PositionForPatternRecognition)
  ot = _OPENINGS_D.get(pos)
  if not ot is None:
    if ot == Opening.NONE:
      ot = None
    return ot
  m = pos.last_move
  if not m is None:
    ot = _OPENINGS_POS_AND_MOVE_D.get(pos, m)
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

def _update_set_of_oppenings_by_rooks(pos: PositionForPatternRecognition, col: int, my_set: Set[Opening], opponent_set: Set[Opening]):
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
  elif col == 7:
    if _almost_empty(my_set) and pos.move_no <= 5:
      my_set.add(Opening.SLEEVE_ROOK)

def _remove_redundant(s):
  s.discard(Opening.SWINGING_ROOK)
  if Opening.SAKATA_OPPOSING_ROOK in s:
    s.discard(Opening.BISHOP_EXCHANGE)
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.AMAHIKO_OPPOSING_ROOK in s:
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.PRIMITIVE_CLIMBING_SILVER in s:
    s.discard(Opening.RIGHT_HAND_FORTH_FILE_ROOK)
  if Opening.LEGHORN_SPECIAL in s:
    s.discard(Opening.FORTH_FILE_ROOK)
  if Opening.QUICK_ISHIDA in s:
    s.discard(Opening.THIRD_FILE_ROOK)

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
      _update_set_of_oppenings_by_rooks(pos, col, my_set, opponent_set)
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
