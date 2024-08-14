# -*- coding: UTF8 -*-

from collections import defaultdict
import datetime
import logging
import re
from typing import (Optional, Tuple)

import log
from shogi.position import Position
from . import move
from . import piece

_KIFU_PIECES = '歩香桂銀金角飛玉と杏圭??馬龍'
_KIFU_COLS = '１２３４５６７８９'
_KIFU_ROWS = '一二三四五六七八九'
_HEADER_MOVES_SEPARATOR = '手数----指手---------消費時間--'
_RESULT_D = {
  '中断': ('Aborted', None, 'Game was aborted.'),
  '投了': ('Resignation', -1, 'The player whose turn it was, is the one who resigned. Time that it took the player to resign can also be noted.'),
  '千日手': ('Repetition', 0, 'Four-fold repetition.'),
  '詰み': ('Checkmate', -1, 'Checkmate or stalemate. The player whose turn it was, is the one who is checkmated.'),
  '切れ負け': ('Time', -1, 'Losing on time. The player whose turn it was, is the one who ran out of time. Some sites use "Time-up" instead.'),
  '反則勝ち': ('IllegalPrecedingMove', 1, 'Indicates that the immediately preceding move was illegal.'),
  '反則負け': ('IllegalMove', -1, 'Indicates that the player whose turn this was supposed to be somehow lost by illegality.'),
  '入玉勝ち': ('EnteringKing', 1, 'Indicates that the player whose it was, declared win by entering king.')
}

_REGEXP_MOVE_TIME = re.compile(r'(\d+):(\d+)')
_REGEXP_CUM_MOVE_TIME = re.compile(r'(\d+):(\d+):(\d+)')

class GameResult:
  def __init__(self, p):
    result, side_to_move_points, description = p
    logging.debug('GameResult.__init__(): result = %s, description = %s', result, description)
    self.result = result
    self.side_to_move_points = side_to_move_points
    self.description = description

def _create_kifu_dict(s, offset = 0):
  return dict(map(lambda t: (t[1], t[0] + offset), filter(lambda t: t[1] != '?', enumerate(s))))

_KIFU_COLS_D = _create_kifu_dict(_KIFU_COLS)
_KIFU_ROWS_D = _create_kifu_dict(_KIFU_ROWS)
_KIFU_PIECES_D = _create_kifu_dict(_KIFU_PIECES, 1)

def kifu_cell(cell: int) -> str:
  (row, col) = divmod(cell, 9)
  return _KIFU_COLS[col] + _KIFU_ROWS[row]

_KIFU_PROMOTED_SINGLE_CHAR_S = set([piece.TOKIN, piece.HORSE, piece.DRAGON])

def kifu_piece(p: int) -> str:
  p = abs(p)
  if piece.is_promoted(p) and not p in _KIFU_PROMOTED_SINGLE_CHAR_S:
    return '成' + _KIFU_PIECES[piece.unpromote(p) - 1]
  r = _KIFU_PIECES[p - 1]
  assert r != '?'
  return r

def kifu_move(m: move.Move, prev: Optional[move.Move]) -> str:
  ''' converts parsed move back to kifu '''
  prev_to_cell = prev and prev.to_cell
  if not m.from_cell is None:
    t = '(' + move.ascii_cell(m.from_cell) + ')'
  else:
    t = ''
  if prev_to_cell == m.to_cell:
    r = '同\u3000'
  else:
    r = kifu_cell(m.to_cell)
  if m.from_cell is None:
    return r + kifu_piece(m.to_piece) + '打' + t
  elif m.from_piece == m.to_piece:
    return r + kifu_piece(m.to_piece) + t
  else:
    return r + kifu_piece(m.from_piece) + '成' + t

def _iter_is_empty(it):
  for _c in it:
    return False
  return True

def _move_parse(s: str, side_to_move: int, last_move: Optional[move.Move]) -> Optional[move.Move]:
  it = iter(s)
  try:
    t = next(it)
    if t == '同':
      t = next(it)
      if t != '\u3000':
        logging.debug('expected unicode wide space')
        return None
      to_cell = last_move and last_move.to_cell
      if to_cell is None:
        return None
    else:
      col = _KIFU_COLS_D.get(t)
      if col is None:
        logging.debug('expected to column, but %s found', t)
        return None
      row = _KIFU_ROWS_D.get(next(it))
      if row is None:
        logging.debug('expected to row, but %s found', t)
        return None
      to_cell = 9 * row + col
    has_been_promoted = False
    t = next(it)
    if t == '成':
      has_been_promoted = True
      t = next(it)
    p = _KIFU_PIECES_D.get(t)
    if p is None:
      return None
    if has_been_promoted:
      if piece.is_promoted(p):
        logging.debug('double promotion in %s', s)
        return None
      p = piece.promote(p)
    t = next(it)
    promoted = False
    if t == '成':
      promoted = True
      t = next(it)
    if t == '打':
      if promoted or (not _iter_is_empty(it)):
        return None
      return move.Move(None, None, side_to_move * p, to_cell)
    if t != '(':
      logging.debug("expected '(', but '%s' found", t)
      return None
    t = next(it)
    if not t.isdigit():
      logging.debug('expected from column, but %s found', t)
      return None
    col = int(t) - 1
    if not 0 <= col < 9:
      logging.debug('from column is not in [1..9]')
      return None
    row = next(it)
    if not row.isdigit():
      logging.debug('expected from row, but %s found', row)
      return None
    t = next(it)
    if t != ')':
      logging.debug("expected ')', but '%s' found", t)
      return None
    if not _iter_is_empty(it):
      logging.debug("extra data")
      return None
    row = int(row) - 1
    if not 0 <= row < 9:
      logging.debug('from row is not in [1..9]')
      return None
    to_piece = piece.promote(p) if promoted else p
    #logging.debug('row = %s, col = %s', row, col)
    return move.Move(side_to_move * p, 9 * row + col, side_to_move * to_piece, to_cell)
  except StopIteration:
    logging.debug("not enough data")
    return None

def _parse_key_value(s: str, sep: str) -> Optional[Tuple[str, str]]:
  i = s.find(sep)
  if i < 0:
    return None
  return (s[:i], s[i+1:])

def _parse_move_times(s: Optional[str]) -> Tuple[Optional[datetime.timedelta], Optional[datetime.timedelta]]:
  if not s or not s.startswith('(') or not s.endswith(')'):
    return (None, None)
  s = s[1:len(s)-1]
  a = list(s.split('/'))
  if not (1 <= len(a) <= 2):
    return (None, None)
  m = _REGEXP_MOVE_TIME.fullmatch(a[0])
  if m is None:
    return (None, None)
  u = datetime.timedelta(minutes = int(m.group(1)), seconds = int(m.group(2)))
  if len(a) == 1:
    return (u, None)
  m = _REGEXP_CUM_MOVE_TIME.fullmatch(a[1])
  if m is None:
    return (u, None)
  v = datetime.timedelta(hours = int(m.group(1)), minutes = int(m.group(2)), seconds = int(m.group(3)))
  return (u, v)

def _parse_player_name(d: dict, s: str, key: str):
  if s.endswith(')'):
    i = s.rfind('(')
    if i >= 0:
      t = s[i+1:len(s)-1]
      if (len(t) > 0) and t.isdigit():
        d[key] = s[:i]
        d[key + '_rating'] = int(t)
        return
  d[key] = s

class KifuMove:
  def __init__(self, a: list[str]):
    self.kifu = a[1]
    self.time = None
    self.cum_time = None
    if len(a) >= 3:
      self.time, self.cum_time = _parse_move_times(a[2])
  def parse(self, side_to_move: int, last_move: Optional[move.Move]) -> Optional[move.Move]:
    return _move_parse(self.kifu, side_to_move, last_move)

class Game:
  def __init__(self, kifu_version, headers, moves, parsed_moves, result, comments, last_legal_sfen):
    logging.debug('KIFU headers = %s', headers)
    self.kifu_version = kifu_version
    self.headers = headers
    self.moves = moves
    self.parsed_moves = parsed_moves
    self.result = result
    self.comments = comments
    self.last_legal_sfen = last_legal_sfen
  @staticmethod
  def parse(s: str):
    try:
      return _game_parse(s)
    except ValueError as err:
      logging.debug(repr(err))
      return None
  def get_row_values_from_headers(self, keys):
    return [self.headers.get(key) for key in keys]
  def sente_points(self) -> Optional[int]:
    p = self.result.side_to_move_points
    if p is None:
      return None
    if (len(self.parsed_moves) % 2) != 0:
      p *= -1
    return p

def _strip_comment(t):
  """Everything after '#' will be ignored by parsers."""
  line, s = t
  s = s.rstrip()
  if line == 0:
    return s
  i = s.rfind('#')
  if i < 0:
    return s
  return s[:i]

def _game_parse(game: str) -> Optional[Game]:
  '''
  https://lishogi.org/explanation/kif
  '''
  it = filter(lambda t: t != '', map(_strip_comment, enumerate(game.split('\n'))))
  t = next(it)
  a = list(t.split())
  if len(a) != 3:
    log.raise_value_error('Illegal number of fields in KIFU header')
  if a[0] != '#KIF':
    log.raise_value_error(f'Expected "#KIFU", but "{a[0]}" found')
  p = _parse_key_value(a[1], '=')
  if (p is None) or (p[0] != 'version'):
    log.raise_value_error(f'Expected "version", but "{a[1]}" found')
  version = p[1]
  p = _parse_key_value(a[2], '=')
  if (p is None) or (p[0] != 'encoding'):
    log.raise_value_error(f'Expected "encoding", but "{a[2]}" found')
  _encoding = p[1]
  d = {}
  while True:
    t = next(it)
    if t == _HEADER_MOVES_SEPARATOR:
      break
    p = _parse_key_value(t, '：')
    if p is None:
      log.raise_value_error(f'Expected header section and moves section separator, but "{t}" found')
    key, value = p
    if key == '開始日時':
      year, month, day = value.split('/')
      if year.isdigit() and month.isdigit() and day.isdigit():
        d['start_date'] = datetime.date(int(year), int(month), int(day))
    elif key == '場所':
      d['location'] = value
    elif key == '持ち時間':
      d['time_control'] = value
    elif key == '手合割':
      if value == '平手':
        value = None
      d['handicap'] = value
    elif key == '先手':
      _parse_player_name(d, value, 'sente')
    elif key == '後手':
      _parse_player_name(d, value, 'gote')
  comments = defaultdict(list)
  moves = []
  parsed_moves = []
  prev_move = None
  side_to_move = 1
  game_result = None
  location_81dojo = d.get('location') == '81Dojo'
  pos = Position()
  illegal_move_idx = None
  ignored_moves = 0
  for s in it:
    i = len(moves)
    if s.startswith('*'):
      comments[i].append(s)
      if location_81dojo:
        if s == '*時間切れにて終局':
          #time over
          game_result = GameResult(_RESULT_D['切れ負け'])
          break
        elif s == '*反則手にて終局':
          if (not illegal_move_idx is None) and (ignored_moves == 0):
            #illegal previous move
            game_result = GameResult(_RESULT_D['反則勝ち'])
            break
      continue
    t = str(i+1)
    a = list(filter(lambda t: t != '', s.split(' ')))
    if (len(a) < 2) or (t != a[0]):
      break
    km = KifuMove(a)
    moves.append(km)
    logging.debug('Move %s', km.kifu)
    p = _RESULT_D.get(km.kifu)
    if not p is None:
      logging.debug('Result %s', p)
      game_result = GameResult(p)
      break
    mv = km.parse(side_to_move, prev_move)
    if mv is None:
      break
    if illegal_move_idx is None:
      parsed_moves.append(mv)
      try:
        pos.do_move(mv)
      except move.IllegalMove as err:
        logging.debug("Move #%s %s is illegal. %s", t, a[1], repr(err))
        illegal_move_idx = len(moves) - 1
    else:
      ignored_moves += 1
    prev_move = mv
    side_to_move *= -1
  return Game(version, d, moves, parsed_moves, game_result, comments, pos.sfen())
