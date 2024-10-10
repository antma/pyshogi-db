# -*- coding: UTF8 -*-

import hashlib
import functools
import logging
import lzma
import os
import shutil
import sqlite3
from typing import (Optional, Tuple)

from elo_rating import performance
import shogi
from shogi.game import Game
from shogi.history import PositionWithHistory
from shogi.move import Move
from shogi.position import Position
from shogi.kifu import TimeControl, game_parse
from shogi.piece import side_to_str
import usi

def _insert(table, a):
  return 'INSERT INTO ' + table + '(' + ', '.join(a) + ') VALUES (' +  ', '.join('?' * len(a)) + ')'

def _md5_digest(data):
  m = hashlib.md5()
  m.update(data)
  return m.digest()

def _u64_to_i64(x):
  return x - 0x8000000000000000

def _conditions_and_join(conds: list[str]) -> str:
  return ' AND '.join('(' + s + ')' for s in conds)

_POSITION_CONDITION = _conditions_and_join(['pos_hash1 == ?', 'pos_hash2 == ?'])
_GET_EVAL_FIELDS = ['nodes', 'time', 'depth', 'seldepth', 'pv']
_STORE_EVAL_FIELDS = ['pos_hash1', 'pos_hash2', 'nodes', 'time', 'score', 'engine_id', 'depth', 'seldepth', 'pv']

def sfen_hashes(sfen: str) -> Tuple[int, int]:
  m = hashlib.md5()
  m.update(bytes(sfen, 'ascii'))
  x = int(m.hexdigest(), 16)
  lo, hi = (x & 0xffff_ffff_ffff_ffff), x >> 64
  assert x == (lo + (hi << 64))
  return (_u64_to_i64(lo), _u64_to_i64(hi))

class GameStat:
  def __init__(self, games: int, score: float, sum_of_opponent_ratings: int):
    self.games = games
    self.score = score
    self.sum_of_opponent_ratings = sum_of_opponent_ratings
    self.percent = None
    if self.games > 0:
      self.percent = (100.0 * self.score) / self.games
  def __add__(self, other):
    if isinstance(other, GameStat):
      return GameStat(self.games + other.games, self.score + other.score, self.sum_of_opponent_ratings + other.sum_of_opponent_ratings)
    return NotImplemented
  def performance(self) -> Optional[float]:
    if self.percent is None:
      return None
    return performance(self.sum_of_opponent_ratings / self.games, self.percent)

class MoveGameStat(GameStat):
  def __init__(self, packed_move: int, games: int, score: float, sum_of_opponent_ratings: int):
    self.packed_move = packed_move
    super().__init__(games, score, sum_of_opponent_ratings)
  def __repr__(self):
    return f'MoveGameStat ( packed_move = {self.packed_move}, games = {self.games}, score = {self.score}, sum_of_opponent_ratings = {self.sum_of_opponent_ratings})'

class PlayerAndTimeControlFilter:
  '''class for filtering DB'''
  def __init__(self, player_name: str, player_side: int, time_control: Optional[int]):
    self.player = (player_name, player_side)
    self.time_control = time_control

class KifuDB:
  def __init__(self, database_name: str, database_dir: str, backup_dir: Optional[str] = None):
    filename = database_name + '.db'
    self._database = os.path.join(database_dir, filename)
    if not os.path.lexists(self._database):
      if not backup_dir is None:
        backup_file = os.path.join(backup_dir, filename)
        if os.path.lexists(backup_file):
          logging.info("Copying database '%s' from backup directory '%s'", filename, backup_dir)
          shutil.copyfile(os.path.join(backup_dir, filename), self._database)
    self._connection = None
    self._cached_player_with_most_games = None
  def __enter__(self):
    self._connection = sqlite3.connect(self._database)
    self.create_tables()
    return self
  def __exit__(self, exl_type, exc_value, traceback):
    self._connection.close()
  def create_tables(self):
    c = self._connection.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kifus (
  sente text,
  gote text,
  start_date real,
  sente_rating integer,
  gote_rating integer,
  time_control integer,
  moves integer,
  result integer,
  md5 blob,
  data blob)''')
    c.execute('''CREATE TABLE IF NOT EXISTS moves (
  pos_hash1 integer NOT NULL,
  pos_hash2 integer NOT NULL,
  move integer NOT NULL,
  game integer NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS time_controls (time_control text PRIMARY KEY)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pos ON moves(pos_hash1)')
    c.execute('''CREATE TABLE IF NOT EXISTS engines (
  name text NOT NULL,
  time integer NOT NULL,
  hash integer NOT NULL,
  threads integer NOT NULL,
  PRIMARY KEY (name, time, hash, threads)
)''')
    c.execute('''CREATE TABLE IF NOT EXISTS analysis (
  pos_hash1 integer NOT NULL,
  pos_hash2 integer NOT NULL,
  nodes integer NOT NULL,
  time integer NOT NULL,
  score integer NOT NULL,
  engine_id integer NOT NULL,
  depth integer NOT NULL,
  seldepth integer,
  pv TEXT NOT NULL
)''')
    c.execute('CREATE INDEX IF NOT EXISTS analysis_idx ON analysis(pos_hash1)')
    c.close()
  def _select_single_value(self, q, parameters = ()):
    c = self._connection.cursor()
    res = c.execute(q, parameters)
    r = res.fetchone()
    c.close()
    if r is None:
      return r
    return r[0]
  def _get_rowid(self, table_name: str, field_name: str, value, force = False) -> Optional[int]:
    r = self._select_single_value(f'SELECT rowid FROM {table_name} WHERE {field_name} == ?', (value, ))
    if not r is None:
      return r
    if not force:
      return None
    self.insert_values(table_name, [field_name], [value])
    return self._get_rowid(table_name, field_name, value, False)
  def _get_engine_id(self, params: usi.USIEngineSearchParameters, force: bool = False) -> Optional[int]:
    fields = ['name', 'time', 'hash', 'threads']
    conds = [ f'{s} == ?' for s in fields]
    values = (params.engine_name, params.time_ms, params.hash_size, params.threads)
    cond = _conditions_and_join(conds)
    r = self._select_single_value(f'SELECT rowid FROM engines WHERE {cond}', values)
    if not r is None:
      return r
    if not force:
      return None
    self.insert_values('engines', fields, values)
    return self._get_engine_id(params, False)
  def find_data_by_game_id(self, game_id: int) -> Optional[str]:
    compressed_data = self._select_single_value('SELECT data FROM kifus WHERE rowid = ?', (game_id, ))
    if compressed_data is None:
      return None
    return lzma.decompress(compressed_data).decode('UTF8')
  def find_game_by_kifu_md5(self, kifu_md5):
    return self._get_rowid('kifus', 'md5', kifu_md5)
  def get_time_control_rowid(self, time_control: TimeControl, force = False) -> Optional[int]:
    return self._get_rowid('time_controls', 'time_control', str(time_control), force)
  def _player_with_most_games(self, side: int) -> Optional[str]:
    side = side_to_str(side)
    return self._select_single_value(f'select {side}, count(*) as c from kifus group by {side} order by c desc limit 1')
  def player_with_most_games(self) -> Optional[str]:
    if not self._cached_player_with_most_games is None:
      if self._cached_player_with_most_games == '':
        return None
      return self._cached_player_with_most_games
    self._cached_player_with_most_games = ''
    p1 = self._player_with_most_games(1)
    if p1 is None:
      return None
    p2 = self._player_with_most_games(-1)
    if (p2 is None) or (p1 != p2):
      return None
    self._cached_player_with_most_games = p1
    logging.debug('Player with most games is %s', p1)
    return p1
  def insert_values(self, table_name, fields, values):
    assert len(fields) == len(values)
    q = _insert(table_name, fields)
    c = self._connection.cursor()
    c.execute(q, values)
    c.close()
    self._connection.commit()
  def insert_many_values(self, table_name, fields, values):
    q = _insert(table_name, fields)
    c = self._connection.cursor()
    for v in values:
      assert len(fields) == len(v)
      c.execute(q, v)
    c.close()
    self._connection.commit()
  def insert_kifu_file(self, filename: str) -> bool:
    with open(filename, 'r', encoding = 'UTF8') as f:
      kifu = f.read()
      return self._insert_kifu_data(filename, kifu)
  def _insert_kifu_data(self, filename: str, data: str) -> bool:
    b = bytes(data, 'UTF8')
    kifu_md5 = _md5_digest(b)
    rowid = self.find_game_by_kifu_md5(kifu_md5)
    if not rowid is None:
      logging.info('KIFU file has been already inserted in DB (rowid = %d).', rowid)
      return False
    g = game_parse(data)
    if g is None:
      logging.warning("Can not parse KIFU file '%s'", os.path.basename(filename))
      return False
    data = lzma.compress(b)
    fields = ['sente', 'gote', 'start_date', 'sente_rating', 'gote_rating', 'time_control']
    v = g.get_row_values_from_tags(fields)
    tc = v.pop()
    if tc is None:
      tc = ''
    tc = self.get_time_control_rowid(tc, force = True)
    v.append(tc)
    fields.append('moves')
    v.append(len(g.moves))
    fields.append('result')
    v.append(g.sente_points())
    fields.append('md5')
    v.append(kifu_md5)
    fields.append('data')
    v.append(data)
    self.insert_values('kifus', fields, v)
    rowid = self.find_game_by_kifu_md5(kifu_md5)
    assert not rowid is None
    pos = shogi.position.Position()
    vals = []
    for m in g.moves:
      sfen = pos.sfen()
      try:
        pos.do_move(m)
      except shogi.move.IllegalMove:
        break
      h1, h2 = sfen_hashes(sfen)
      vals.append([h1, h2, m.pack_to_int(), rowid])
    fields = ['pos_hash1', 'pos_hash2', 'move', 'game']
    self.insert_many_values('moves',  fields, vals)
    return True
  def time_control_stats(self):
    q = '''SELECT time_controls.time_control, COUNT(*) as c FROM kifus
INNER JOIN time_controls ON time_controls.rowid == kifus.time_control
GROUP BY time_controls.rowid
ORDER BY c DESC'''
    c = self._connection.cursor()
    res = list(c.execute(q))
    c.close()
    return res
  def moves_with_stats(self, pos: Position, player_and_tc: PlayerAndTimeControlFilter) -> list[MoveGameStat]:
    l = []
    if player_and_tc is None:
      logging.debug('moves_with_stats(): player_and_tc is None')
      return l
    name, side = player_and_tc.player
    time_control = player_and_tc.time_control
    player_side = side_to_str(side)
    oside = side_to_str(-side)
    orating = f'kifus.{oside}_rating'
    hash1, hash2 = sfen_hashes(pos.sfen())
    values = [hash1, hash2, name]
    conds = ['moves.pos_hash1 == ?', 'moves.pos_hash2 == ?', f'kifus.{player_side} == ?']
    if not time_control is None:
      values.append(time_control)
      conds.append('kifus.time_control == ?')
    conds.extend([f'{orating} > 0', 'kifus.result >= -1', 'kifus.result <= 1'])
    cond = _conditions_and_join(conds)
    q = f'''SELECT moves.move, COUNT(*) as c, SUM(kifus.result), SUM({orating}) FROM moves
INNER JOIN kifus ON moves.game == kifus.rowid
WHERE {cond}
GROUP BY moves.move
ORDER BY c DESC
'''
    c = self._connection.cursor()
    for t in c.execute(q, values):
      n = t[1]
      sente_score = 0.5 * (t[2] + n)
      score = sente_score if side > 0 else n - sente_score
      l.append(MoveGameStat(t[0], n, score, t[3]))
    c.close()
    logging.debug('%s', l)
    return l
  def build_tree(self, player_and_tc: PlayerAndTimeControlFilter, max_games: int):
    pos = PositionWithHistory()
    moves = self.moves_with_stats(pos, player_and_tc)
    #stack: (moves, (move, undo move))
    stack = [moves]
    r = []
    while len(stack) > 0:
      moves = stack.pop()
      if len(moves) == 0:
        pos.undo_last_move()
      else:
        ms = moves.pop()
        if ms.games >= max_games:
          m = Move.unpack_from_int(ms.packed_move, pos.side_to_move)
          pos.do_move(m)
          r.append((ms.performance(), ms.games, ms.percent, pos.kifu_line(), pos.sfen()))
          stack.append(moves)
          moves = self.moves_with_stats(pos, player_and_tc)
          stack.append(moves)
        else:
          stack.append(moves)
    r.sort(reverse = True)
    return r
  def _build_histogram_data_for_player_filter(self, player_and_tc: PlayerAndTimeControlFilter, step: int):
    d = {}
    if player_and_tc is None:
      logging.debug('moves_with_stats(): player_and_tc is None')
      return d
    name, side = player_and_tc.player
    time_control = player_and_tc.time_control
    player_side = side_to_str(side)
    oside = side_to_str(-side)
    orating = f'{oside}_rating'
    conds = [f'{player_side} == ?']
    values = [name]
    if not time_control is None:
      values.append(time_control)
      conds.append('time_control == ?')
    conds.extend([f'{orating} > 0', 'result >= -1', 'result <= 1'])
    cond = _conditions_and_join(conds)
    q = f'''SELECT ({orating} / {step}) * {step} as b, COUNT(*), SUM(result), SUM({orating})
FROM kifus
WHERE {cond}
GROUP BY b
ORDER BY b
'''
    c = self._connection.cursor()
    for t in c.execute(q, values):
      n = t[1]
      sente_score = 0.5 * (t[2] + n)
      score = sente_score if side > 0 else n - sente_score
      #percent = 100.0 * score / n
      d[t[0]] = GameStat(n, score, t[3])
      #l.append((t[0], n, percent, t[3] / n))
    c.close()
    return d
  def build_histogram_data(self, player: str, time_control: TimeControl, step: int) -> dict[int, GameStat]:
    tc = self.get_time_control_rowid(time_control, force = False)
    if tc is None:
      return {}
    sd = self._build_histogram_data_for_player_filter(PlayerAndTimeControlFilter(player, 1, tc), step)
    gd = self._build_histogram_data_for_player_filter(PlayerAndTimeControlFilter(player, -1, tc), step)
    for key, value in gd.items():
      p = sd.get(key)
      if p is None:
        sd[key] = value
      else:
        #https://stackoverflow.com/questions/1047021/overriding-in-python-iadd-method
        sd[key] += value
    return sd
  def player_time_control_stats(self, player: str, time_control: TimeControl) -> Optional[GameStat]:
    tc = self.get_time_control_rowid(time_control, force = False)
    if tc is None:
      logging.warning('Time control %s is absent in database', time_control)
      return None
    gs = []
    for side in (-1, 1):
      player_side = side_to_str(side)
      opponent_side = side_to_str(-side)
      opponent_rating = opponent_side + '_rating'
      cond = _conditions_and_join(['time_control == ?', f'{player_side} == ?', f'{opponent_rating} > 0'])
      values = (tc, player)
      q = f'SELECT COUNT(*) as c, SUM(result), SUM({opponent_rating}) FROM kifus WHERE {cond}'
      logging.debug(q)
      c = self._connection.cursor()
      res = c.execute(q, values)
      r = res.fetchone()
      c.close()
      if r is None:
        continue
      n = r[0]
      sente_score = 0.5 * (r[1] + n)
      score = sente_score if side > 0 else n - sente_score
      gs.append(GameStat(n, score, r[2]))
    if len(gs) == 0:
      return None
    return functools.reduce(lambda x, y: x + y, gs)
  def load_game(self, game_id: int) -> Optional[Game]:
    kifu = self.find_data_by_game_id(game_id)
    if kifu is None:
      return None
    return game_parse(kifu)
  def make_player_and_tc_filter(self, game: Game) -> Optional[PlayerAndTimeControlFilter]:
    player = self.player_with_most_games()
    if player is None:
      return None
    time_control = game.get_tag('time_control')
    if not time_control is None:
      time_control = self.get_time_control_rowid(time_control, force = False)
      if time_control is None:
        return None
    if player == game.get_tag('sente'):
      return PlayerAndTimeControlFilter(player, 1, time_control)
    if player == game.get_tag('gote'):
      return PlayerAndTimeControlFilter(player, -1, time_control)
    return None
  def _position_already_analysed_by_engine_id(self, engine_id, hashes):
    conds = ['pos_hash1 == ?', 'pos_hash2 == ?', 'engine_id == ?']
    values = (hashes[0], hashes[1], engine_id)
    cond = _conditions_and_join(conds)
    query = f'SELECT 1 FROM analysis WHERE {cond} LIMIT 1'
    return not self._select_single_value(query, values) is None
  def _position_already_analysed_by_better_engine(self, params: usi.USIEngineSearchParameters, hashes):
    conds = ['analysis.pos_hash1 == ?', 'analysis.pos_hash2 == ?', '(engines.time > ?) OR (engines.hash > ?) OR (engines.threads > ?)']
    values = (hashes[0], hashes[1], params.time_ms, params.hash_size, params.threads)
    cond = _conditions_and_join(conds)
    query = f'''SELECT 1 FROM engines
INNER JOIN analysis ON engines.rowid == analysis.engine_id
WHERE {cond}
LIMIT 1'''
    return not self._select_single_value(query, values) is None
  def _store_position_analyse(self, engine_id: int, info: usi.InfoMessage, hashes):
    fields = _STORE_EVAL_FIELDS
    values = [hashes[0], hashes[1], info.get('nodes'), info.get('time'), info.score_i16(), engine_id, info.get('depth'), info.get('seldepth')]
    values.append(' '.join(info.get('pv')))
    self.insert_values('analysis', fields, values)
  def analyse_game(self, engine: usi.USIEngine, game_id: int):
    engine_id = self._get_engine_id(engine.params, force = True)
    logging.debug("Analyse game #%d: engine_id = %d", game_id, engine_id)
    game = self.load_game(game_id)
    if game is None:
      logging.error("Can not load game #%d{game_id} from db '%s'", game_id, self._database)
      return
    engine.new_game()
    pos = PositionWithHistory()
    usi_moves = []
    for m in game.moves:
      usi_moves.append(m.usi_str())
      pos.do_move(m)
    while len(usi_moves) > 0:
      sfen = pos.sfen()
      pos_hashes = sfen_hashes(sfen)
      ok = True
      if self._position_already_analysed_by_engine_id(engine_id, pos_hashes):
        logging.debug("Position '%s' has already been analysed by engine_id '%d'", sfen, engine_id)
        ok = False
      elif self._position_already_analysed_by_better_engine(engine.params, pos_hashes):
        logging.debug("Position '%s' has analysed by better engine", sfen)
        ok = False
      if ok:
        info, _ = engine.analyse_position(None, usi_moves)
        #engine.new_game()
        #info, _ = engine.analyse_position(sfen, [])
        self._store_position_analyse(engine_id, info, pos_hashes)
      usi_moves.pop()
      pos.undo_last_move()
  def _get_position_analysis(self, pos: Position) -> Optional[usi.InfoMessage]:
    values = sfen_hashes(pos.sfen())
    fields = _GET_EVAL_FIELDS
    sf = ','.join(fields)
    query = f'SELECT score,{sf} FROM analysis WHERE {_POSITION_CONDITION} ORDER BY nodes LIMIT 1'
    c = self._connection.cursor()
    logging.debug(query)
    res = c.execute(query, values)
    r = res.fetchone()
    c.close()
    if r is None:
      return r
    logging.debug("%s", r)
    d = {}
    for i, key in enumerate(fields):
      d[key] = r[i+1]
    info = usi.InfoMessage(d)
    info.set_score(r[0])
    return info
  def load_game_analysis(self, game: Game):
    a = []
    pos = Position()
    for m in game.moves:
      pos.do_move(m)
      r = self._get_position_analysis(pos)
      if r is None:
        break
      a.append(r)
    logging.debug('Found analysis for %d moves', len(a))
    return a
