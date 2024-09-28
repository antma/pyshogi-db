# -*- coding: UTF8 -*-

from collections import defaultdict
import datetime
import logging
import re
from typing import (Optional, Tuple)

import log
from . import cell
from . import move
from . import piece
from . import position
from . import result

from ._misc import iter_is_empty

_HEADER_MOVES_SEPARATOR = '手数----指手---------消費時間--'

_REGEXP_MOVE_TIME = re.compile(r'(\d+):(\d+)')
_REGEXP_CUM_MOVE_TIME = re.compile(r'(\d+):(\d+):(\d+)')
_REGEXP_TIME_CONTROL = re.compile(r'(\d+)分?[+](\d+)秒?')

def _create_kifu_dict(s, offset = 0):
  return dict(map(lambda t: (t[1], t[0] + offset), filter(lambda t: t[1] != '?', enumerate(s))))

_KIFU_COLS_D = _create_kifu_dict(cell.KIFU_COLS)
_KIFU_ROWS_D = _create_kifu_dict(cell.KIFU_ROWS)
_KIFU_PIECES_D = _create_kifu_dict(piece.KIFU_PIECES, 1)

def side_to_str(side: int) -> str:
  return "sente" if side > 0 else "gote"

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
      if promoted or (not iter_is_empty(it)):
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
    if not iter_is_empty(it):
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
  if not 1 <= len(a) <= 2:
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

class TimeControl:
  def __init__(self, initial: int, byoyomi: int):
    self.initial = initial
    self.byoyomi = byoyomi
  def __str__(self):
    return f"{self.initial}分+{self.byoyomi}秒"

def parse_time_control(s: str) -> Optional[TimeControl]:
  m = _REGEXP_TIME_CONTROL.fullmatch(s)
  if m is None:
    return None
  return TimeControl(int(m.group(1)), int(m.group(2)))

class KifuMove:
  def __init__(self, a: list[str]):
    self.kifu = a[1]
    self.time = None
    self.cum_time = None
    if len(a) >= 3:
      self.time, self.cum_time = _parse_move_times(a[2])
  def parse(self, side_to_move: int, last_move: Optional[move.Move]) -> Optional[move.Move]:
    return _move_parse(self.kifu, side_to_move, last_move)

def player_with_rating_from_dict(d: dict, side:int) -> Optional[str]:
  name = side_to_str(side)
  player = d.get(name)
  if player is None:
    return None
  rating = d.get(name + '_rating')
  if rating is None:
    return player
  return f'{player}({rating})'

class Game:
  def __init__(self, kifu_version, headers, moves, parsed_moves, game_result, comments, last_legal_sfen):
    logging.debug('KIFU headers = %s', headers)
    self.kifu_version = kifu_version
    self.headers = headers
    self.moves = moves
    self.parsed_moves = parsed_moves
    self.result = game_result
    self.comments = comments
    self.last_legal_sfen = last_legal_sfen
  @staticmethod
  def parse(s: str):
    try:
      return _game_parse(s)
    except ValueError as err:
      logging.debug(repr(err))
      return None
  def get_header_value(self, key: str):
    return self.headers.get(key)
  def player_with_rating(self, side: int) -> Optional[str]:
    return player_with_rating_from_dict(self.headers, side)
  def get_row_values_from_headers(self, keys):
    return [self.headers.get(key) for key in keys]
  def sente_points(self) -> Optional[int]:
    p = result.side_to_move_points(self.result)
    if p is None:
      return None
    if (len(self.parsed_moves) % 2) != 0:
      p *= -1
    return p
  def text_result(self) -> Optional[int]:
    p = self.sente_points()
    if p is None:
      return None
    if p > 0:
      return "1-0"
    if p < 0:
      return "0-1"
    return "1/2"

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

_HEADER_JP_D = {
  '開始日時': 'start_date',
  '場所': 'location',
  '持ち時間': 'time_control',
  '手合割': 'handicap',
  '先手': 'sente',
  '後手': 'gote'
}

_HEADER_WRITE_ORDER_L = ['start_sfen', 'start_date', 'location', 'time_control', 'handicap', 'sente', 'gote']
_HEADER_EN_D = dict((t[1], t[0]) for t in _HEADER_JP_D.items())
_SIDE_S = set(['sente', 'gote'])

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
    key = _HEADER_JP_D.get(key)
    if not key is None:
      if key in _SIDE_S:
        _parse_player_name(d, value, key)
      elif key == 'start_date':
        year, month, day = value.split('/')
        if year.isdigit() and month.isdigit() and day.isdigit():
          d[key] = datetime.date(int(year), int(month), int(day))
      elif key == 'time_control':
        tc = parse_time_control(value)
        if tc is None:
          log.raise_value_error(f"Can not parse time control '{value}'")
        d[key] = tc
      elif key == 'handicap':
        if value == '平手':
          value = None
        d[key] = value
      else:
        d[key] = value
  comments = defaultdict(list)
  moves = []
  parsed_moves = []
  prev_move = None
  side_to_move = 1
  game_result = None
  location_81dojo = d.get('location') == '81Dojo'
  pos = position.Position()
  illegal_move_idx = None
  ignored_moves = 0
  for s in it:
    i = len(moves)
    if s.startswith('*'):
      comments[i].append(s)
      if location_81dojo:
        if s == '*時間切れにて終局':
          #time over
          game_result = result.GameResult.TIME
          break
        if s == '*反則手にて終局':
          if (not illegal_move_idx is None) and (ignored_moves == 0):
            #illegal previous move
            game_result = result.GameResult.ILLEGAL_PRECEDING_MOVE
            break
      continue
    t = str(i+1)
    a = list(filter(lambda t: t != '', s.split(' ')))
    if (len(a) < 2) or (t != a[0]):
      break
    km = KifuMove(a)
    moves.append(km)
    logging.debug('Move %s', km.kifu)
    game_result = result.game_result_by_jp(km.kifu)
    if not game_result is None:
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

class KifuOutputFile:
  def __init__(self, filename):
    self._filename = filename
    self._f = None
    self.move_no = None
  def __enter__(self):
    self._f = open(self._filename, 'w', encoding = 'UTF8', buffering = 16384)
    return self
  def __exit__(self, exl_type, exc_value, traceback):
    self._f.close()
    self._f = None
  def write(self, s: str):
    if self._f is None:
      logging.error("KifuMove.write method should be used inside with statement")
    else:
      self._f.write(s)
  def write_headers(self, h):
    for key in _HEADER_WRITE_ORDER_L:
      p = h.get(key)
      if not p is None:
        if key == 'start_sfen':
          self.write(position.Position(p).kifu_str())
        else:
          if not isinstance(p, str):
            p = str(p)
          self.write(_HEADER_EN_D[key] + '：' + str(p) + '\n')
    self.write(_HEADER_MOVES_SEPARATOR + '\n')
  def write_moves(self, moves: list[move.Move]):
    prev = None
    self.move_no = 0
    for m in moves:
      self.move_no += 1
      self.write(str(self.move_no) + ' ' + m.kifu_str(prev) + '\n')
      prev = m
  def write_result(self, r: Optional[result.GameResult]):
    if r is None:
      return
    self.move_no += 1
    self.write(str(self.move_no) + ' ' + result.japan_str(r) + '\n')
