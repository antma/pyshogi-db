# -*- coding: UTF8 -*-
''' shogi rules (move generation, etc.) '''

def side_to_str(side: int) -> str:
  return "sente" if side > 0 else "gote"

from . import cell
from . import evaluation
from . import history
from . import kifu
from . import move
from . import openings
from . import piece
from . import position

