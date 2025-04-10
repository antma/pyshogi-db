# -*- coding: UTF8 -*-

import logging
from typing import Optional, Tuple, Set
from enum import IntEnum
from .game import Game
from ._pattern import Recognizer, PositionForPatternRecognition

Castle = IntEnum('Castle',
  [ #static rook
   'BOAT_CASTLE', 'LEFT_HAND_MINO', 'STATIC_ROOK_ANAGUMA',
   'MILLENIUM_CASTLE', 'ELMO_CASTLE',
    #double static rook
   'SNOW_ROOF_CASTLE', 'STRAWBERRY_CASTLE',
    #swinging rook
   'CASTLE_TOWER_MINO', 'TOPKNOT_MINO', 'HALF_MINO_CASTLE', 'HIGH_MINO_CASTLE', 'MINO_CASTLE', 'SILVER_CROWN', 'KIMURA_MINO',
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

_SILVER_CROWN_BASE = [('K', '28'), ('S', '27'), ('G', '38'), ('L', '19'), ('P', '26'), ('P', '15,16,17')]
_SILVER_CROWN_PATTERN1 = _SILVER_CROWN_BASE + [('N', '29'), ('P', '46,47'), ('P', '37')]
_SILVER_CROWN_PATTERN2 = _SILVER_CROWN_BASE + [('N', '37'), ('G', '47'), ('P', '46'), ('P', '36')]
_LEFT_HAND_SILVER_CROWN_PATTERN = [('K', '88'), ('S', '87'), ('G', '78'), ('P', '86'), ('P', '76'), ('P', '67'), ('L', '99'), ('N', '89'), ('P', '95,96,97')]

_STATIC_ROOK_ANAGUMA_BASE = [('K', '99'), ('S', '88'), ('L', '98'), ('N', '89'), ('P', '86,87'), ('P', '96,97')]
_STATIC_ROOK_ANAGUMA_PATTERN1 = _STATIC_ROOK_ANAGUMA_BASE + [('G', '69,78,87'), ('to', '88')]
_STATIC_ROOK_ANAGUMA_PATTERN2 = _STATIC_ROOK_ANAGUMA_BASE + [('G', '79'), ('G', '78')]

_KIMURA_MINO_BASE = [('K', '28'), ('G', '38'), ('S', '47'), ('L', '19'), ('P', '27'), ('P', '16,17')] #('P', '46'),
_KIMURA_MINO_PATTERN1 = _KIMURA_MINO_BASE + [('N', '29'), ('P', '37')]
_KIMURA_MINO_PATTERN2 = _KIMURA_MINO_BASE + [('N', '37'), ('P', '36')]

'''HALF_MINO_CASTLE should be after MINO_CASTLE since it's pattern is subset'''

_RECOGNIZER = Recognizer( [
  (_SILVER_CROWN_PATTERN1, Castle.SILVER_CROWN),
  (_SILVER_CROWN_PATTERN2, Castle.SILVER_CROWN),
  (_LEFT_HAND_SILVER_CROWN_PATTERN, Castle.SILVER_CROWN),
  ([('K', '28'), ('S', '38'), ('G', '47'), ('G', '49'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HIGH_MINO_CASTLE),
  ([('K', '28'), ('S', '38'), ('S', '47'), ('G', '49'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.SILVER_MINO),
  ([('K', '28'), ('S', '38'), ('G', '49'), ('L', '19'),
    ('P', '37'), ('P', '26'), ('P', '15,16,17')], Castle.TOPKNOT_MINO), #('N', '29')
  ([('K', '87'), ('S', '78'), ('G', '69'), ('N', '89'), ('L', '99'),
    ('P', '67'), ('P', '76'), ('P', '86'), ('P', '95,96,97')], Castle.CASTLE_TOWER_MINO),
  ([('K', '78'), ('S', '79'), ('G', '69'), ('G', '58'), ('S', '48'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '56,57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '95,96,97')], Castle.BOAT_CASTLE),
  (_KIMURA_MINO_PATTERN1, Castle.KIMURA_MINO),
  (_KIMURA_MINO_PATTERN2, Castle.KIMURA_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('G', '58'),
    ('P', '46,47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.MINO_CASTLE),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('!G', '58'), ('!S', '58'),
    ('P', '47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HALF_MINO_CASTLE),
  ([('K', '38'), ('S', '28'), ('G', '48'), ('G', '58'), ('L', '19'), ('N', '29'),
    ('P', '27'), ('P', '37'), ('P', '47'), ('P', '15,16,17')], Castle.PEERLESS_GOLDS),
  ([('K', '19'), ('S', '28'), ('G', '39,49'), ('L', '18'), ('N', '29'),
    ('P', '27'), ('P', '16,17')], Castle.SWINGING_ROOK_ANAGUMA),
  (_STATIC_ROOK_ANAGUMA_PATTERN1, Castle.STATIC_ROOK_ANAGUMA),
  (_STATIC_ROOK_ANAGUMA_PATTERN2, Castle.STATIC_ROOK_ANAGUMA),
  ([('K', '88'), ('S', '78'), ('G', '69'), ('G', '58'), ('L', '99'), ('N', '89'),
    ('P', '87'), ('P', '76,77'), ('P', '67'), ('P', '95,96,97')], Castle.LEFT_HAND_MINO),
  ([('K', '68'), ('G', '58'), ('G', '78'), ('B', '88'), ('S', '79'), ('N', '89'), ('L', '99'),
    ('P', '96,97'), ('P', '87'), ('P', '76'), ('P', '67'), ('P', '57')], Castle.STRAWBERRY_CASTLE),
  ([('K', '89'), ('G', '79'), ('S', '88'), ('N', '77'), ('P', '87'), ('P', '76'), ('P', '67'), ('P','96,97'), ('L', '99')], Castle.MILLENIUM_CASTLE),
  ([('K', '69'), ('G', '78'), ('G', '58'), ('S', '67'), ('P', '76'), ('P', '66'), ('P', '56,57'), ('N', '89'), ('L', '99')], Castle.SNOW_ROOF_CASTLE),
  ([('G', '79'), ('S', '68'), ('K', '78'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '67'), ('P', '76'), ('P', '87'), ('P', '96,97')], Castle.ELMO_CASTLE),
])

def position_update_set_of_castles(pos: PositionForPatternRecognition, sente_set, gote_set):
  _RECOGNIZER.update_set(pos, sente_set, gote_set)

def position_find_castle(pos: PositionForPatternRecognition) -> Optional[Castle]:
  return _RECOGNIZER.find(pos)

def sfen_find_castle(sfen: str) -> Optional[Castle]:
  pos = PositionForPatternRecognition(sfen)
  return position_find_castle(pos)

def game_find_castles(g: Game, max_hands: int = 50) -> Tuple[Set[Castle], Set[Castle]]:
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
