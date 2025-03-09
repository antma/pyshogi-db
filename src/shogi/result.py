# -*- coding: UTF8 -*-

from enum import IntEnum
from typing import Optional

GameResult = IntEnum('GameResult',
  ['ABORTED', 'RESIGNATION', 'REPETITION', 'CHECKMATE', 'TIME', 'ILLEGAL_PRECEDING_MOVE',
   'ILLEGAL_MOVE', 'ENTERING_KING', 'BAD_CONNECTION'])

_RESULT_D = {
  GameResult.ABORTED: ('中断', None, 'Game was aborted.'),
  GameResult.RESIGNATION: ('投了', -1, 'The player whose turn it was, is the one who resigned. Time that it took the player to resign can also be noted.'),
  GameResult.REPETITION: ('千日手', 0, 'Four-fold repetition.'),
  GameResult.CHECKMATE: ('詰み',  -1, 'Checkmate or stalemate. The player whose turn it was, is the one who is checkmated.'),
  GameResult.TIME: ('切れ負け', -1, 'Losing on time. The player whose turn it was, is the one who ran out of time. Some sites use "Time-up" instead.'),
  GameResult.ILLEGAL_PRECEDING_MOVE: ('反則勝ち', 1, 'Indicates that the immediately preceding move was illegal.'),
  GameResult.ILLEGAL_MOVE: ('反則負け', -1, 'Indicates that the player whose turn this was supposed to be somehow lost by illegality.'),
  GameResult.ENTERING_KING: ('入玉勝ち', 1, 'Indicates that the player whose it was, declared win by entering king.'),
  GameResult.BAD_CONNECTION: ('接続切れにて終局', -1, 'The player whose turn it was, lost by disconnection.')
}

_JP_D = dict((value[0], key) for key, value in _RESULT_D.items())

def japan_str(result: GameResult) -> str:
  return _RESULT_D[result][0]

def side_to_move_points(result: GameResult) -> Optional[int]:
  return _RESULT_D[result][1]

def description(result: GameResult) -> str:
  return _RESULT_D[result][2]

def game_result_by_jp(jp: str) -> Optional[GameResult]:
  return _JP_D.get(jp)
