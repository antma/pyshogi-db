# -*- coding: UTF8 -*-

from typing import Tuple, Set
from enum import IntEnum
from .game import Game
from .position import Position
from ._pattern import Recognizer

Castle = IntEnum('Castle',
  [ #static rook
   'BOAT_CASTLE', 'LEFT_HAND_MINO', 'STATIC_ROOK_ANAGUMA',
    #swinging rook
   'CASTLE_TOWER_MINO', 'TOPKNOT_MINO', 'HALF_MINO_CASTLE', 'HIGH_MINO_CASTLE', 'MINO_CASTLE', 'SILVER_CROWN', 'KIMURA_MINO',
   'PEERLESS_GOLDS', 'SWINGING_ROOK_ANAGUMA',
  ])

'''HALF_MINO_CASTLE should be after MINO_CASTLE since it's pattern is subset'''

_RECOGNIZER = Recognizer( [
  ([('K', '28'), ('S', '27'), ('G', '38'), ('N', '29'), ('L', '19'),
    ('P', '47'), ('P', '37'), ('P', '26'), ('P', '15,16,17')], Castle.SILVER_CROWN),
  ([('K', '28'), ('S', '38'), ('G', '47'), ('G', '49'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HIGH_MINO_CASTLE),
  ([('K', '28'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'),
    ('P', '47'), ('P', '37'), ('P', '26'), ('P', '15,16,17')], Castle.TOPKNOT_MINO),
  ([('K', '87'), ('S', '78'), ('G', '69'), ('N', '89'), ('L', '99'),
    ('P', '67'), ('P', '76'), ('P', '86'), ('P', '95,96,97')], Castle.CASTLE_TOWER_MINO),
  ([('K', '78'), ('S', '79'), ('G', '69'), ('G', '58'), ('B', '88'), ('N', '89'), ('L', '99'),
    ('P', '57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '95,96,97')], Castle.BOAT_CASTLE),
  ([('K', '28'), ('G', '38'), ('S', '47'), ('N', '29'), ('L', '19'),
    ('P', '46'), ('P', '37'), ('P', '27'), ('P', '16,17')], Castle.KIMURA_MINO),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('G', '58'),
    ('P', '46,47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.MINO_CASTLE),
  ([('K', '28,39'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'), ('!G', '58'), ('!S', '58'),
    ('P', '47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')], Castle.HALF_MINO_CASTLE),
  ([('K', '38'), ('S', '28'), ('G', '48'), ('G', '58'), ('L', '19'), ('N', '29'),
    ('P', '27'), ('P', '37'), ('P', '47'), ('P', '15,16,17')], Castle.PEERLESS_GOLDS),
  ([('K', '19'), ('S', '28'), ('G', '39,49'), ('L', '18'), ('N', '29'),
    ('P', '27'), ('P', '16,17')], Castle.SWINGING_ROOK_ANAGUMA),
  ([('K', '99'), ('S', '88'), ('G', '79,69'), ('L', '98'), ('N', '89'),
    ('P', '87'), ('P', '96,97')], Castle.STATIC_ROOK_ANAGUMA),
  ([('K', '88'), ('S', '78'), ('G', '69'), ('G', '58'), ('L', '99'), ('N', '89'),
    ('P', '87'), ('P', '76'), ('P', '67'), ('P', '95,96,97')], Castle.LEFT_HAND_MINO),
])

def position_update_set_of_castles(pos: Position, sente_set, gote_set):
  _RECOGNIZER.update_set(pos, sente_set, gote_set)

def game_find_castles(g: Game, max_hands: int = 50) -> Tuple[Set[Castle], Set[Castle]]:
  sente_castles = set()
  gote_castles = set()
  assert g.start_pos is None
  pos = Position()
  for m in g.moves[:max_hands]:
    pos.do_move(m)
    side = -pos.side_to_move
    if not pos.opponent_piece_in_the_camp(side):
      position_update_set_of_castles(pos, sente_castles, gote_castles)
  return (sente_castles, gote_castles)
