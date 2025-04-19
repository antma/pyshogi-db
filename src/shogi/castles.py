# -*- coding: UTF8 -*-

import logging
from typing import Optional, Tuple, Set
from enum import IntEnum
from .game import Game
from ._pattern import Recognizer, PositionForPatternRecognition, adjacent_pawns

Castle = IntEnum('Castle',
  [ #static rook
   'BOAT_CASTLE', 'LEFT_HAND_MINO', 'STATIC_ROOK_ANAGUMA', 'SILVER_CROWN_ANAGUMA',
   'MILLENIUM_CASTLE', 'GIRL_IN_THE_HOUSE',
   'YAGURA_CASTLE', 'SILVER_YAGURA', 'HALF_YAGURA', 'COMPLETE_YAGURA', 'YAGURA_ANAGUMA',
   'KIKUSUI_YAGURA', 'SILVER_STANDING_YAGURA', 'DIAMOND_YAGURA', 'RAPID_CASTLE', 'DOI_YAGURA',
   'CRAB_CASTLE',
   'ELMO_CASTLE', 'BONANZA_CASTLE',
   'EDGE_KING_SILVER_CROWN',
   'KUSHIKATSU_CASTLE',
    #double static rook
   'SNOW_ROOF_CASTLE', 'STRAWBERRY_CASTLE',
    #swinging rook
   'CASTLE_TOWER_MINO', 'TOPKNOT_MINO', 'HALF_MINO_CASTLE', 'HIGH_MINO_CASTLE', 'MINO_CASTLE', 'SILVER_CROWN', 'KIMURA_MINO',
   'DIAMOND_MINO', 'GOLD_MINO',
   'PEERLESS_GOLDS', 'SWINGING_ROOK_ANAGUMA', 'SILVER_MINO',
  ])

def _mirror_columns(s):
  b = []
  for t in s.split(','):
    assert len(t)==2
    b.append(str(10 - int(t[0])) + t[1])
  return ','.join(b)

def _mirror_columns_in_pattern(pat):
  return [(piece, _mirror_columns(s)) for piece, s in pat]

_LEFT_HAND_SILVER_CROWN_PATTERN = [('K', '88'), ('S', '87'), ('G', '78'), ('P', '86'), ('P', '76'), ('P', '66,67'), ('L', '99'), ('N', '89'), ('P', '95,96,97')]
_YAGURA_PATTERN = [('G', '67'), ('G', '78'), ('S', '77'), ('K', '88'), ('N', '89'), ('L', '99'),
    ('P', '66'), ('P', '76'), ('P', '87'), ('P', '97')]
_HIGH_MINO_CASTLE_BASE = [('G', '47'), ('to', '47'), ('K', '28'), ('S', '38'), ('G', '49'),  ('L', '19'),
    ('P', '46'),  ('P', '15,16,17')]
_CASTLE_TOWER_MINO_BASE = [('K', '87'), ('S', '78'), ('G', '69'), ('N', '89'), ('L', '99'), ('P', '76'), ('P', '86'), ('P', '95,96,97')]

'''HALF_MINO_CASTLE should be after MINO_CASTLE since it's pattern is subset'''

_RECOGNIZER = Recognizer( [
  ( [('K', '28'), ('S', '27'), ('G', '38'), ('L', '19'), ('P', '26'), ('P', '16,17')], 'SILVER_CROWN'),
  ( [('base-pattern', 'SILVER_CROWN'), ('N', '29'), ('P', '46,47'), ('P', '37')], Castle.SILVER_CROWN),
  ( [('base-pattern', 'SILVER_CROWN'), ('N', '37'), ('P', '46'), ('P', '36')], Castle.SILVER_CROWN),
  (_LEFT_HAND_SILVER_CROWN_PATTERN, Castle.SILVER_CROWN),
  ([('K', '98'), ('S', '87'), ('G', '78'), ('to', '78'), ('N', '89'), ('L', '99'),
  ('P', '96,97'), ('P', '86'), ('P', '76'), ('G', '49,58,67,68')], Castle.EDGE_KING_SILVER_CROWN),
  ([('K', '99'), ('S', '87'), ('G', '78'), ('L', '98'), ('N', '89'), ('P', '96,97')] +
   adjacent_pawns(6, 6, 9, []), Castle.SILVER_CROWN_ANAGUMA),
  ([('S', '47'), ('G', '58'), ('G', '49'), ('S', '38'), ('K', '28'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '36'), ('P', '27'), ('P', '16,17')], Castle.DIAMOND_MINO),
  (_HIGH_MINO_CASTLE_BASE, 'HIGH_MINO'),
  ([('base-pattern', 'HIGH_MINO'), ('P', '37'), ('P', '27'), ('N', '29')], Castle.HIGH_MINO_CASTLE),
  ([('base-pattern', 'HIGH_MINO'), ('P', '36'), ('P', '27'), ('N', '37')], Castle.HIGH_MINO_CASTLE),
  ([('base-pattern', 'HIGH_MINO'), ('P', '36'), ('P', '26'), ('N', '29')], Castle.HIGH_MINO_CASTLE),
  ([('K', '28'), ('S', '38'), ('S', '47'), ('G', '49'), (' ', '48'), ('!G', '58'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.SILVER_MINO),
  ([('K', '28'), ('S', '38'), ('G', '49'), ('L', '19'),
    ('P', '37'), ('P', '26'), ('P', '15,16,17')], Castle.TOPKNOT_MINO), #('N', '29')
  (_CASTLE_TOWER_MINO_BASE, 'TOWER_MINO'),
  ([('base-pattern', 'TOWER_MINO'), ('P', '67')], Castle.CASTLE_TOWER_MINO),
  ([('base-pattern', 'TOWER_MINO'), ('G', '67'), ('P', '66')], Castle.CASTLE_TOWER_MINO),
  ([('K', '78'), ('S', '79'), ('G', '69'), ('G', '58'), ('S', '48'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '56,57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '95,96,97')], Castle.BOAT_CASTLE),
  ([('K', '28'), ('G', '38'), ('S', '47'), ('L', '19'), ('P', '27'), ('P', '16,17'), ('!S', '46')], 'KIMURA_MINO'),
  ([('base-pattern', 'KIMURA_MINO'), ('N', '29'), ('P', '37')], Castle.KIMURA_MINO),
  ([('base-pattern', 'KIMURA_MINO'), ('N', '37'), ('P', '36')], Castle.KIMURA_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('G', '58'),
    ('P', '46,47'), ('P', '36,37'), ('P', '27'), ('P', '15,16,17')], Castle.MINO_CASTLE),
  ([('K', '28'), ('G', '38'), ('S', '48'), ('N', '29'), ('L', '19'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.GOLD_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('!G', '58'), ('!S', '58'),
    ('P', '47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HALF_MINO_CASTLE),
  ([('K', '38'), ('G', '48'), ('G', '58'), ('S', '28,39'), ('N', '29'), ('L', '19'),
    ('P', '27'), ('P', '37'), ('P', '47'), ('P', '15,16,17')], Castle.PEERLESS_GOLDS),
  ([('K', '19'), ('S', '28'), ('G', '39,49'), ('L', '18'), ('N', '29'),
    ('P', '27'), ('P', '16,17')], Castle.SWINGING_ROOK_ANAGUMA),
  ([('K', '99'), ('S', '88'), ('L', '98'), ('N', '89'), ('P', '86,87'), ('P', '96,97')], 'STATIC_ROOK_ANAGUMA'),
  ([('base-pattern', 'STATIC_ROOK_ANAGUMA'), ('G', '69,78,87'), ('to', '88')], Castle.STATIC_ROOK_ANAGUMA),
  ([('base-pattern', 'STATIC_ROOK_ANAGUMA'), ('G', '79'), ('G', '78')], Castle.STATIC_ROOK_ANAGUMA),
  ([('K', '88'), ('S', '78'), ('G', '69'), ('G', '58,67'), ('L', '99'), ('N', '89'),
    ('P', '87'), ('P', '76,77'), ('P', '66,67'), ('P', '95,96,97')], Castle.LEFT_HAND_MINO),
  ([('K', '68'), ('G', '58'), ('G', '78'), ('B', '88'), ('S', '79'), ('N', '89'), ('L', '99'),
    ('P', '96,97'), ('P', '87'), ('P', '76'), ('P', '67'), ('P', '57')], Castle.STRAWBERRY_CASTLE),
  ([('K', '89'), ('G', '79'), ('S', '88'), ('N', '77'), ('P', '87'), ('P', '76'), ('P', '67'), ('P','96,97'), ('L', '99')], Castle.MILLENIUM_CASTLE),
  ([('K', '69'), ('G', '78'), ('G', '58'), ('S', '67'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('N', '89'), ('L', '99')], Castle.SNOW_ROOF_CASTLE),
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
    ('P', '56'), ('P', '66'), ('P', '76'), ('P', '87'), ('P', '95,96,97')], Castle.HALF_YAGURA),
  ([('G', '67'), ('G', '78'), ('S', '77'), ('K', '99'), ('N', '89'), ('L', '98'),
    ('P', '66'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.YAGURA_ANAGUMA),
  ([('G', '67'), ('G', '78'), ('S', '88'), ('K', '89'), ('N', '77'), ('L', '99'),
    ('P', '66'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.KIKUSUI_YAGURA),
  ([('G', '67'), ('G', '78'), ('S', '76'), ('K', '88'), ('N', '89'), ('L', '99'),
    ('P', '66'), ('P', '75'), ('P', '86'), ('P', '96,97')], Castle.SILVER_STANDING_YAGURA),
  ([('G', '67'), ('G', '78'), ('S', '77'), ('K', '88'), ('N', '89'), ('L', '99'), ('S', '66'),
    ('P', '65'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.DIAMOND_YAGURA),
  ([('G', '58'), ('G', '78'), ('S', '68'), ('K', '69'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '56,57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '97')], Castle.CRAB_CASTLE),
  ([('G', '58'), ('G', '68'), ('K', '78'), ('S', '77'), ('N', '89'), ('L', '99'),
    ('P', '67'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.BONANZA_CASTLE),
  ([('G', '67'), ('K', '78'), ('S', '77'), ('G', '69'), ('N', '89'), ('L', '99'),
    ('P', '87'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('P', '95,96,97')], Castle.RAPID_CASTLE),
  ([('G', '58'), ('G', '67'), ('S', '77'), ('K', '78'), ('N', '89'), ('L', '99'),
    ('P', '87'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('P', '96,97')], Castle.DOI_YAGURA),
  ([('K', '98'), ('S', '88'), ('to', '88'), ('N', '89'), ('L', '99'), ('P', '87'), ('P', '97')], Castle.KUSHIKATSU_CASTLE),
], 'castles')

del _LEFT_HAND_SILVER_CROWN_PATTERN
del _HIGH_MINO_CASTLE_BASE
del _YAGURA_PATTERN
del _CASTLE_TOWER_MINO_BASE

def position_update_set_of_castles(pos: PositionForPatternRecognition, sente_set, gote_set):
  _RECOGNIZER.update_set(pos, sente_set, gote_set)

def position_find_castle(pos: PositionForPatternRecognition) -> Optional[Castle]:
  return _RECOGNIZER.find(pos)

def sfen_find_castle(sfen: str) -> Optional[Castle]:
  pos = PositionForPatternRecognition(sfen)
  return position_find_castle(pos)

def game_find_castles(g: Game, max_hands: int = 50) -> Tuple[Set[Castle], Set[Castle]]:
  _RECOGNIZER.reoder()
  sente_castles = set()
  gote_castles = set()
  assert g.start_pos is None
  pos = PositionForPatternRecognition()
  #sente_drops, gote_drops = False, False
  for m in g.moves[:max_hands]:
    pos.do_move(m)
    '''
    side = -pos.side_to_move
    if m.is_drop():
      if side > 0:
        sente_drops = True
      else:
        gote_drops = True
    drops = sente_drops if side > 0 else gote_drops
    '''
    if not pos.is_opening():
      logging.debug('Out of opening: %s', pos.sfen())
      break
    position_update_set_of_castles(pos, sente_castles, gote_castles)
  return (sente_castles, gote_castles)
