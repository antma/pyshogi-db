# -*- coding: UTF8 -*-

import datetime
import itertools
import logging
import re
from typing import List, Optional, Tuple

import log
from . import cell
from . import move
from . import piece
from . import position
from . import result
from .game import Game

from ._misc import iter_is_empty

_HEADER_MOVES_SEPARATOR = '手数----指手---------消費時間--'

_REGEXP_MOVE_TIME = re.compile(r'(\d+):(\d+)')
_REGEXP_CUM_MOVE_TIME = re.compile(r'(\d+):(\d+):(\d+)')
_REGEXP_TIME_CONTROL = re.compile(r'(\d+)分?[+](\d+)秒?')
_REGEXP_WITHOUT_INCREMENT_TIME_CONTROL = re.compile(r'(\d+)分?')

def _create_kifu_dict(s, offset = 0):
  return dict(map(lambda t: (t[1], t[0] + offset), filter(lambda t: t[1] != '?', enumerate(s))))

_KIFU_COLS_D = _create_kifu_dict(cell.KIFU_COLS)
_KIFU_ROWS_D = _create_kifu_dict(cell.KIFU_ROWS)
_KIFU_PIECES_D = _create_kifu_dict(piece.KIFU_PIECES, 1)

def move_parse(s: str, side_to_move: int, last_move: Optional[move.Move]) -> Optional[move.Move]:
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
      logging.debug('unknown piece %s', t)
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

def _parse_datetime(s: str) -> Optional[datetime.datetime]:
  try:
    return datetime.datetime.strptime(s, '%Y/%m/%d %H:%M:%S')
  except ValueError:
    pass
  try:
    return datetime.datetime.strptime(s, '%Y/%m/%d')
  except ValueError:
    pass
  return None

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

def _parse_player_name(game: Game, s: str, key: str):
  game.parse_player_name(s, key)

class TimeControl:
  def __init__(self, initial: int, byoyomi: int):
    self.initial = initial
    self.byoyomi = byoyomi
  def __str__(self):
    return f"{self.initial}分+{self.byoyomi}秒"

def parse_time_control(s: str) -> Optional[TimeControl]:
  m = _REGEXP_WITHOUT_INCREMENT_TIME_CONTROL.fullmatch(s)
  if not m is None:
    return TimeControl(int(m.group(1)), 0)
  m = _REGEXP_TIME_CONTROL.fullmatch(s)
  if not m is None:
    return TimeControl(int(m.group(1)), int(m.group(2)))
  return None

def game_parse(s: str) -> Optional[Game]:
  try:
    return _game_parse(s)
  except ValueError as err:
    logging.debug(repr(err))
    return None

def _strip_comment(t):
  """Everything after '#' will be ignored by parsers."""
  logging.debug('%s', t)
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
  '終了日時': 'end_date',
  '場所': 'location',
  '棋戦': 'event',
  '持ち時間': 'time_control',
  '手合割': 'handicap',
  '先手': 'sente',
  '後手': 'gote'
}

_HEADER_WRITE_ORDER_L = ['start_sfen', 'start_date', 'end_date', 'location', 'event', 'time_control', 'handicap', 'sente', 'gote']
_HEADER_EN_D = dict((t[1], t[0]) for t in _HEADER_JP_D.items())
_SIDE_S = set(['sente', 'gote'])

def _pieces_parse(s: str) -> List[int]:
  p = [0] * piece.ROOK
  if s == 'なし':
    return p
  last_piece = None
  t = None
  for c in (s + ' '):
    if last_piece is None:
      last_piece = _KIFU_PIECES_D.get(c)
      t = 0
    else:
      if c.isspace():
        p[last_piece - 1] = max(1, t)
        last_piece = None
        t = None
      elif c == '十':
        t += 10
      else:
        t += _KIFU_ROWS_D[c] + 1
  return p

def _board_parse(s: List[str]) -> List[int]:
  if s[0] != '  ９ ８ ７ ６ ５ ４ ３ ２ １':
    log.raise_value_error('_board_parse: expected column numbers')
  sep = '+---------------------------+'
  if s[1] != sep:
    log.raise_value_error('_board_parse: expected board separator')
  b = [None] * 81
  for row in range(9):
    it = iter(s[row + 2])
    if next(it) != '|':
      log.raise_value_error(f'_board_parse: expected left board separator at row {row+1}')
    for col in reversed(range(9)):
      n = 9 * row + col
      t = next(it)
      if t == 'v':
        side = -1
      else:
        if t != ' ':
          if t == '・':
            b[n] = piece.FREE
            continue
          log.raise_value_error(f"_board_parse: expected space at row {row+1}, column {col+1}, but '{t}' found")
        side = 1
      t = next(it)
      p = _KIFU_PIECES_D.get(t)
      if p is None:
        if t != '・':
          log.raise_value_error(f"_board_parse: expected empty cell character at {row+1}, column {col+1}, but '{t}' found")
        b[n] = piece.FREE
      else:
        b[n] = p * side
    if next(it) != '|':
      log.raise_value_error(f'_board_parse: expected right board separator at row {row+1}')
    if _KIFU_ROWS_D.get(next(it)) != row:
      log.raise_value_error(f'_board_parse: expected row number at row {row+1}')
    if not iter_is_empty(it):
      log.raise_value_error(f'_board_parse: extra data at row {row+1}')
  if s[11] != sep:
    log.raise_value_error('_board_parse: expected board separator')
  return b

def _game_parse(game_kif: str) -> Optional[Game]:
  '''
  https://lishogi.org/explanation/kif
  '''
  it = filter(lambda t: t != '', map(_strip_comment, enumerate(game_kif.split('\n'))))
  game = Game()
  t = next(it)
  _version, _encoding = None, None
  try:
    a = list(t.split())
    if len(a) != 3:
      log.raise_value_error('Illegal number of fields in KIFU header', logging.INFO)
    if a[0] != '#KIF':
      log.raise_value_error(f'Expected "#KIFU", but "{a[0]}" found', logging.INFO)
    p = _parse_key_value(a[1], '=')
    if (p is None) or (p[0] != 'version'):
      log.raise_value_error(f'Expected "version", but "{a[1]}" found', logging.INFO)
    _version = p[1]
    p = _parse_key_value(a[2], '=')
    if (p is None) or (p[0] != 'encoding'):
      log.raise_value_error(f'Expected "encoding", but "{a[2]}" found', logging.INFO)
    _encoding = p[1]
  except ValueError:
    it = itertools.chain([t], it)
  while True:
    t = next(it)
    if t == _HEADER_MOVES_SEPARATOR:
      break
    p = _parse_key_value(t, '：')
    if p is None:
      log.raise_value_error(f'Expected header section and moves section separator, but "{t}" found')
    key, value = p
    key = _HEADER_JP_D.get(key)
    if key is None:
      if p[0] == '後手の持駒':
        gote_pieces = _pieces_parse(value)
        board = []
        for _ in range(12):
          board.append(next(it))
        board = _board_parse(board)
        t = next(it)
        p = _parse_key_value(t, '：')
        if p is None:
          log.raise_value_error("Can't parse sente pieces")
        key, value = p
        if key != '先手の持駒':
          log.raise_value_error("Can't parse sente pieces")
        sente_pieces = _pieces_parse(value)
        t = next(it)
        if t == '後手番':
          side_to_move = -1
        else:
          side_to_move = 1
          it = itertools.chain([t], it)
        game2 = Game(position.Position.build_sfen(board, side_to_move, 1, sente_pieces, gote_pieces))
        game2.tags = game.tags
        game = game2
    else:
      if key in _SIDE_S:
        _parse_player_name(game, value, key)
      elif key.endswith('_date'):
        date = _parse_datetime(value)
        if not date is None:
          game.set_tag(key, date)
      elif key == 'time_control':
        tc = parse_time_control(value)
        if tc is None:
          log.raise_value_error(f"Can not parse time control '{value}'")
        game.set_tag(key, tc)
      else:
        game.set_tag(key, value)
  prev_move = None
  location_81dojo = game.get_tag('location') == '81Dojo'
  for s in it:
    if s.startswith('*'):
      game.append_comment_before_move(game.pos.move_no, s[1:])
      if location_81dojo:
        if s == '*時間切れにて終局':
          #time over
          game.set_result(result.GameResult.TIME)
          break
        if s == '*反則手にて終局':
          assert not game.has_result()
          game.set_result(result.GameResult.ILLEGAL_PRECEDING_MOVE)
          break
        if s == '*接続切れにて終局':
          assert not game.has_result()
          game.set_result(result.GameResult.BAD_CONNECTION)
          break
      continue
    a = list(filter(lambda t: t != '', s.split(' ')))
    t = str(game.pos.move_no)
    if (len(a) < 2) or (t != a[0]):
      break
    km = a[1]
    game_result = result.game_result_by_jp(km)
    if not game_result is None:
      game.set_result(game_result)
      break
    logging.debug("%s", km)
    mv = move_parse(km, game.pos.side_to_move, prev_move)
    if mv is None:
      return None
    if len(a) > 2:
      mv.time, mv.cum_time = _parse_move_times(a[2])
    game.do_move(mv)
    if game.has_result():
      break
    prev_move = mv
  if (game.game_result == result.GameResult.CHECKMATE) and game.pos.has_legal_move():
    logging.error("Illegal checkmate move record in KIFU, 'checkmated' side has legal moves")
    return None
  game.adjourn()
  game.drop_zero_times()
  return game

def _game_write_tags(g: Game, f):
  if not g.start_pos is None:
    g.set_tag('start_sfen', g.start_pos)
  for key in _HEADER_WRITE_ORDER_L:
    p = g.get_tag(key)
    if not p is None:
      if key == 'start_sfen':
        f.write(position.Position(p).kifu_str())
      else:
        if isinstance(p, datetime.date):
          p = p.isoformat().replace('-', '/').replace('T', ' ')
        if not isinstance(p, str):
          p = str(p)
        if key == 'sente':
          p = g.player_with_rating(1)
        if key == 'gote':
          p = g.player_with_rating(-1)
        f.write(_HEADER_EN_D[key] + '：' + str(p) + '\n')
  f.write(_HEADER_MOVES_SEPARATOR + '\n')

def _game_write_moves(g: Game, f):
  prev = None
  move_no = g.start_move_no
  for m in g.moves:
    t = str(move_no) + ' ' + m.kifu_str(prev)
    t1 = m.time_str()
    if not t1 is None:
      t2 = m.cum_time_str()
      if not t2 is None:
        t1 += '/' + t2
      t += ' (' + t1 + ')'
    f.write(t + '\n')
    move_no += 1
    p = g.comments.get(move_no)
    if p:
      for s in p:
        f.write('*' + s + '\n')
    prev = m
  #game result
  if not g.game_result is None:
    if g.game_result == result.GameResult.BAD_CONNECTION:
      p = '*'
    else:
      p = str(move_no) + ' '
    f.write(p + result.japan_str(g.game_result) + '\n')

def game_write_to_file(g: Game, f):
  f.write('#KIF version=2.0 encoding=UTF-8\n')
  _game_write_tags(g, f)
  _game_write_moves(g, f)
