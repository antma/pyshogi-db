# -*- coding: UTF8 -*-

import logging
from typing import Optional
from enum import IntEnum
from .game import Game
from ._pattern import Recognizer, RecognizerResult, PositionForPatternRecognition, adjacent_pawns, last_row_pieces

Castle = IntEnum('Castle',
  [ #static rook
   'BOAT_CASTLE',
   'STATIC_ROOK_ANAGUMA', 'MATSUO_STYLE_ANAGUMA', 'SILVER_CROWN_ANAGUMA', 'BIG_FOUR',
   'KUSHIKATSU_CASTLE',
   'LEFT_HAND_MINO', 'FOUR_PIECE_MINO',
   'MILLENIUM_CASTLE', 'GIRL_IN_THE_HOUSE',
   'YAGURA_CASTLE', 'SILVER_YAGURA', 'HALF_YAGURA', 'COMPLETE_YAGURA', 'YAGURA_ANAGUMA',
   'KIKUSUI_YAGURA', 'SILVER_STANDING_YAGURA', 'DIAMOND_YAGURA', 'RAPID_CASTLE', 'DOI_YAGURA',
   'CRAB_CASTLE',
   'ELMO_CASTLE', 'BONANZA_CASTLE',
   'EDGE_KING_SILVER_CROWN',
    #double static rook
   'SNOW_ROOF_CASTLE', 'STRAWBERRY_CASTLE', 'CENTRAL_HOUSE', 'NAKAHARAS_KING',
    #swinging rook
   'CASTLE_TOWER_MINO', 'TOPKNOT_MINO', 'HALF_MINO_CASTLE', 'HIGH_MINO_CASTLE', 'MINO_CASTLE', 'SILVER_CROWN', 'KIMURA_MINO',
   'DIAMOND_MINO', 'GOLD_MINO',
   'PEERLESS_GOLDS', 'SWINGING_ROOK_ANAGUMA', 'SILVER_MINO',
   'INVINCIBLE_CASTLE', 'DUCK_LEGS_CASTLE',
   'RIGHT_HAND_YAGURA',
  ])

def _mirror_columns(s):
  b = []
  for t in s.split(','):
    assert len(t)==2
    b.append(str(10 - int(t[0])) + t[1])
  return ','.join(b)

def _mirror_columns_in_pattern(pat):
  return [(piece, _mirror_columns(s)) for piece, s in pat]

_LEFT_HAND_SILVER_CROWN_PATTERN = [('K', '88'), ('S', '87'), ('G', '78'), ('P', '86'), ('P', '76'), ('P', '66,67'), ('L', '99'), ('N', '89'), ('P', '95,96,97'), ('to', '78')]
_YAGURA_PATTERN = [('G', '67'), ('G', '78'), ('S', '77'), ('K', '88'), ('N', '89'), ('L', '99'),
    ('P', '66'), ('P', '87'), ('P', '97')] #('P', '76'),
_HIGH_MINO_CASTLE_BASE = [('G', '47'), ('K', '28'), ('S', '38'), ('G', '49'),  ('L', '19'),
   ('P', '15,16,17')] #('P', '46'),
_CASTLE_TOWER_MINO_BASE = [('K', '87'), ('S', '78'), ('G', '69'), ('N', '89'), ('L', '99'), ('P', '76'), ('P', '86'), ('P', '95,96,97')]

'''HALF_MINO_CASTLE should be after MINO_CASTLE since it's pattern is subset'''

_RECOGNIZER = Recognizer( [
  ( [('K', '99'), ('G', '88'), ('G', '78'), ('S', '87'), ('S', '77'),
     ('P', '76'), ('P', '96,97'), ('L', '98'), ('N', '89')], Castle.BIG_FOUR), #('P', '86'), ('P', '67'),
  ( [('K', '19'), ('G', '28'), ('G', '38'), ('S', '27'), ('S', '37'),
     ('P', '36'), ('P', '16,17'), ('L', '18'), ('N', '29')], Castle.BIG_FOUR), #('P', '26'),
  ( [('K', '99'), ('G', '67'), ('G', '78'), ('S', '88'), ('S', '79'), ('P', '66'),
     ('P', '76'), ('P', '87'), ('P', '96,97'), ('L', '98'), ('N', '89')], Castle.MATSUO_STYLE_ANAGUMA),
  ( [('K', '28'), ('S', '27'), ('G', '38'), ('L', '19'), ('P', '26')], 'SILVER_CROWN'), #('P', '16,17')
  ( [('base-pattern', 'SILVER_CROWN'), ('N', '29'), ('P', '46,47'), ('P', '37')], Castle.SILVER_CROWN),
  ( [('base-pattern', 'SILVER_CROWN'), ('N', '37'), ('P', '36'), ('P', '16,17')], Castle.SILVER_CROWN), #('P', '46'),
  (_LEFT_HAND_SILVER_CROWN_PATTERN, Castle.SILVER_CROWN),
  ([('K', '98'), ('S', '87'), ('G', '78'), ('to', '78'), ('N', '89'), ('L', '99'),
  ('P', '96,97'), ('P', '86'), ('P', '76'), ('G', '49,58,67,68')], Castle.EDGE_KING_SILVER_CROWN),
  ([('K', '99'), ('S', '87'), ('G', '78'), ('L', '98'), ('N', '89'), ('P', '96,97')] +
   adjacent_pawns(6, 7, 9), Castle.SILVER_CROWN_ANAGUMA), #('P', '66,67'),
  ([('S', '47'), ('G', '58'), ('G', '49'), ('S', '38'), ('K', '28'), ('N', '29,37'), ('L', '19'),
    ('P', '36,37'), ('P', '26,27')], Castle.DIAMOND_MINO), #('P', '16,17'), ('P', '46'),
  (_HIGH_MINO_CASTLE_BASE, 'HIGH_MINO'),
  ([('base-pattern', 'HIGH_MINO'), ('P', '37'), ('P', '27'), ('N', '29')], Castle.HIGH_MINO_CASTLE),  #high mino
  ([('base-pattern', 'HIGH_MINO'), ('P', '36'), ('P', '56'), ('N', '29')], Castle.HIGH_MINO_CASTLE),  #advanced pawns
  ([('base-pattern', 'HIGH_MINO'), ('P', '36'), ('N', '37'), ('P', '56,57')], Castle.HIGH_MINO_CASTLE), #advanced knight
  ([('K', '28'), ('S', '38'), ('S', '47'), ('G', '49'), (' ', '48'), ('!G', '58'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.SILVER_MINO),
  ([('K', '28'), ('S', '38'), ('G', '49'), ('L', '19'),
    ('P', '37'), ('P', '26'), ('P', '15,16,17')], Castle.TOPKNOT_MINO), #('N', '29')
  ([('K', '87'), ('G', '58,67'), ('S', '77'), ('S', '78'), ('P', '66,67'), ('P', '95,96,97')] +
   last_row_pieces('123457') + adjacent_pawns(6, 7, 9), Castle.FOUR_PIECE_MINO),
  (_CASTLE_TOWER_MINO_BASE, 'TOWER_MINO'),
  ([('base-pattern', 'TOWER_MINO'), ('P', '67')], Castle.CASTLE_TOWER_MINO),
  ([('base-pattern', 'TOWER_MINO'), ('G', '67'), ('P', '66')], Castle.CASTLE_TOWER_MINO),
  ([('K', '78'), ('S', '79'), ('G', '69'), ('G', '58'), ('S', '48'), ('B', '77,88'), ('N', '89'), ('L', '99'),
    ('P', '56,57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '95,96,97')], Castle.BOAT_CASTLE),
  ([('K', '28'), ('G', '38'), ('S', '47'), ('L', '19'), ('P', '26,27'), ('!S', '27')], 'KIMURA_MINO'), #('P', '16,17'),
  ([('base-pattern', 'KIMURA_MINO'), ('N', '29'), ('P', '36,37'), ('P', '46')], Castle.KIMURA_MINO),
  ([('base-pattern', 'KIMURA_MINO'), ('N', '37'), ('P', '36'), ('!S', '46')], Castle.KIMURA_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29,37'), ('L', '19'), ('G', '58'),
    ('P', '27'), (' ', '59')], Castle.MINO_CASTLE), #('P', '46,47'), ('P', '15,16,17'), ('P', '36,37'),
  ([('K', '28'), ('G', '38'), ('S', '48'), ('N', '29'), ('L', '19'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.GOLD_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('!P', '58'), ('!G', '58'), ('!S', '58'), ('!G', '47'), ('!S', '47'),
    ('P', '46,47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HALF_MINO_CASTLE),
  ([('K', '38'), ('G', '48'), ('G', '58'), ('S', '28,39'), ('N', '29,37'), ('L', '19'),
    ('P', '26,27'), ('P', '36,37'), ('P', '47'), ('P', '15,16,17')], Castle.PEERLESS_GOLDS),
  ([('K', '19'), ('S', '28'), ('G', '39,49'), ('L', '18'), ('N', '29'),
    ('P', '27'), ], Castle.SWINGING_ROOK_ANAGUMA), #('P', '16,17')
  ([('K', '99'), ('S', '88'), ('L', '98'), ('N', '89'), ('P', '86,87'), ('P', '96,97')], 'STATIC_ROOK_ANAGUMA'),
  ([('base-pattern', 'STATIC_ROOK_ANAGUMA'), ('G', '69,78,87'), ('to', '88')], Castle.STATIC_ROOK_ANAGUMA),
  ([('base-pattern', 'STATIC_ROOK_ANAGUMA'), ('G', '79'), ('G', '78')], Castle.STATIC_ROOK_ANAGUMA),
  ([('K', '88'), ('S', '78'), ('G', '69'), ('G', '58,67'), ('L', '99'), ('N', '89'),
    ('P', '87'), ('P', '66,67'), ('P', '95,96,97')], Castle.LEFT_HAND_MINO), #('P', '76,77'),
  ([('K', '68'), ('G', '58'), ('G', '78'), ('B', '88'), ('S', '79'), ('N', '89'), ('L', '99'),
    ('P', '96,97'), ('P', '87'), ('P', '76'), ('P', '67'), ('P', '57')], Castle.STRAWBERRY_CASTLE),
  ([('K', '89'), ('G', '79'), ('S', '88'), ('N', '77'), ('P', '87'), ('P', '76'), ('P', '67'), ('P','96,97'), ('L', '99')], Castle.MILLENIUM_CASTLE),
  ([('K', '69'), ('G', '78'), ('G', '58'), ('S', '67'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('N', '89'), ('L', '99'), ('P', 0) ], Castle.SNOW_ROOF_CASTLE), #('P', '97')
  ([('G', '79'), ('S', '68'), ('K', '78'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.ELMO_CASTLE), #('P', '67')
  ([('G', '68'), ('K', '78'), ('G', '69'), ('S', '79'), ('N', '89'), ('L', '99'),
    ('P', '67'), ('P', '87'), ('P', '76,77'), ('P', '96,97')], Castle.GIRL_IN_THE_HOUSE),
  (_YAGURA_PATTERN, 'YAGURA'),
  ([('base-pattern', 'YAGURA'), ('P', '56'), ('S', '57')], Castle.COMPLETE_YAGURA),
  ([('base-pattern', 'YAGURA')], Castle.YAGURA_CASTLE),
  ([('S', '67'), ('G', '78'), ('S', '77'), ('K', '88'), ('N', '89'), ('L', '99'),
    ('P', '66'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.SILVER_YAGURA),
  ([('G', '67'), ('G', '68'), ('S', '77'), ('K', '78'), ('N', '89'), ('L', '99'),
    ('P', '76'), ('P', '87')], Castle.HALF_YAGURA), #('P', '95,96,97'), ('P', '56,57'),('P', '66')
  ([('G', '67'), ('G', '78'), ('S', '77'), ('K', '99'), ('N', '89'), ('L', '98'),
    ('P', '87'), (' ', '88')], Castle.YAGURA_ANAGUMA), #('P', '76'), ('P', '96,97'), ('P', '66'),
  ([('G', '67'), ('G', '78'), ('S', '88'), ('K', '89'), ('N', '77'), ('L', '99'),
    ('P', '66'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.KIKUSUI_YAGURA),
  ([('G', '67'), ('G', '78'), ('S', '76'), ('K', '88'), ('N', '89'), ('L', '99'),
    ('P', '75'), ('P', '86,87')], Castle.SILVER_STANDING_YAGURA), #('P', '66'), ('P', '96,97')
  ([('G', '67'), ('G', '78'), ('S', '77'), ('K', '88'), ('N', '89'), ('L', '99'), ('S', '66'),
    ('P', '65'), ('P', '87'), ('P', '96,97')], Castle.DIAMOND_YAGURA), #('P', '76'),
  ([('G', '58'), ('G', '78'), ('S', '68'), ('K', '69'),('N', '89'), ('L', '99'),
    ('P', '56,57'), ('P', '67'), ('P', '76,77'), ('P', '87')], Castle.CRAB_CASTLE), #('P', '96,97'), ('B', '88'), 
  ([('G', '58'), ('G', '68'), ('K', '78'), ('S', '77'),
    ('P', '87')] + last_row_pieces('1234567'), 'BONANZA'),
  ([('base-pattern', 'BONANZA'), ('to', '58,68,78')], Castle.BONANZA_CASTLE),
  ([('base-pattern', 'BONANZA'), ('to', '77'), ('from', '88')], Castle.BONANZA_CASTLE),
  ([('G', '67'), ('K', '78'), ('S', '77'), ('G', '69'), ('N', '89'), ('L', '99'),
    ('P', '87'), ('P', '66'), ('P', '56,57'), ('P', '95,96,97')], Castle.RAPID_CASTLE), #('P', '76'),
  ([('G', '58'), ('G', '67'), ('S', '77'), ('K', '78'), ('N', '89'), ('L', '99'),
    ('P', '87'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('P', '96,97')], Castle.DOI_YAGURA),
  ([('K', '98'), ('S', '88'), ('to', '88'), ('N', '89'), ('L', '99'), ('P', '87'), ('P', '97')], Castle.KUSHIKATSU_CASTLE),
  ([('R', '58'), ('S', '48'), ('S', '68'), ('P', '67'), ('P', '47'), ('P', '56,57')] +
    last_row_pieces('123789'), Castle.INVINCIBLE_CASTLE),
  ([('K', '58'), ('S', '48'), ('G', '38'), ('G', '78')]
   + last_row_pieces('1234567') + adjacent_pawns(7, 4, 7), Castle.CENTRAL_HOUSE),
  ([('K', '28'), ('S', '37'), ('G', '38'), ('P', '27'), ('P', '36'), ('P', '15,16,17'), ('L', '19'), ('N', '29')], 'RIGHT_HAND_YAGURA'),
  ([('base-pattern', 'RIGHT_HAND_YAGURA'), ('P', '47')], Castle.RIGHT_HAND_YAGURA),
  ([('base-pattern', 'RIGHT_HAND_YAGURA'), ('to', '28')], Castle.RIGHT_HAND_YAGURA),
  ([('K', '69'), ('G', '59'), ('S', '88'), ('G', '78'), ('S', '48'), ('P', '67'), ('P', '47'), ('N', '77,89')], Castle.NAKAHARAS_KING),
  ([('K', '58'), ('G', '79'), ('G', '39'), ('S', '68'), ('S', '48')] + adjacent_pawns(7, 4, 7), Castle.DUCK_LEGS_CASTLE),
])

del _LEFT_HAND_SILVER_CROWN_PATTERN
del _HIGH_MINO_CASTLE_BASE
del _YAGURA_PATTERN
del _CASTLE_TOWER_MINO_BASE

def _position_update_set_of_castles(rr: RecognizerResult, pos: PositionForPatternRecognition):
  _RECOGNIZER.update_set(rr, pos)

def position_find_castle(pos: PositionForPatternRecognition) -> Optional[Castle]:
  return _RECOGNIZER.find(pos)

def sfen_find_castle(sfen: str) -> Optional[Castle]:
  pos = PositionForPatternRecognition(sfen)
  return position_find_castle(pos)

def game_find_castles(g: Game, max_hands: int = 62) -> RecognizerResult:
  assert g.start_pos is None
  _RECOGNIZER.reorder()
  rr = RecognizerResult()
  pos = PositionForPatternRecognition(True)
  for m in g.moves[:max_hands]:
    pos.do_move(m)
    if not pos.is_opening(0):
      logging.debug('Out of opening: %s', pos.sfen())
      break
    if pos.is_opening(m.to_piece):
      _position_update_set_of_castles(rr, pos)
  return rr

def stats():
  return _RECOGNIZER.stats()

def log_stats(old_stats, func_name):
  _RECOGNIZER.log_stats(old_stats, func_name)
