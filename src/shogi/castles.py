# -*- coding: UTF8 -*-

from typing import Tuple, Set
from enum import IntEnum
from .game import Game
from .position import Position
from ._pattern import PositionPattern

Castles = IntEnum('Castles',
  ['CASTLE_TOWER_MINO', 'BOAT_CASTLE', 'TOPKNOT_MINO', 'HALF_MINO_CASTLE', 'SILVER_CROWN'])

_PATTERNS = [
  (PositionPattern([('K', '28'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'),
                    ('P', '47'), ('P', '37'), ('P', '26'), ('P', '15,16,17')]), Castles.TOPKNOT_MINO),
  (PositionPattern([('K', '87'), ('S', '78'), ('G', '69'), ('B', '88'), ('N', '89'), ('L', '99'),
                    ('P', '67'), ('P', '76'), ('P', '86'), ('P', '95,96,97')]), Castles.CASTLE_TOWER_MINO),
  (PositionPattern([('K', '78'), ('S', '79'), ('G', '69'), ('G', '58'), ('B', '88'), ('N', '89'), ('L', '99'),
                    ('P', '57'), ('P', '67'), ('P', '76'), ('P', '87'), ('P', '95,96,97')]), Castles.BOAT_CASTLE),
  (PositionPattern([('K', '28'), ('S', '38'), ('G', '49'), ('N', '29'), ('L', '19'),
                    ('P', '47'), ('P', '37'), ('P', '27'), ('P', '15,16,17')]), Castles.HALF_MINO_CASTLE)
]

def position_update_set_of_castles(pos: Position, side: int, st):
  for p, ct in _PATTERNS:
    if (not ct in st) and p.match(pos, side):
      st.add(ct)

def game_find_castles(g: Game, max_hands: int = 60) -> Tuple[Set[Castles], Set[Castles]]:
  sente_castles = set()
  gote_castles = set()
  assert g.start_pos is None
  pos = Position()
  for m in g.moves[:max_hands]:
    pos.do_move(m)
    side = -pos.side_to_move
    position_update_set_of_castles(pos, side, sente_castles if side > 0 else gote_castles)
  return (sente_castles, gote_castles)
