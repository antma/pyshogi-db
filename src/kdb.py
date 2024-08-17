# -*- coding: UTF8 -*-

import hashlib
import logging
import lzma
import sqlite3
from typing import (Optional, Tuple)

import shogi
from shogi.position import Position
from shogi.kifu import Game

def _insert(table, a):
  return 'INSERT INTO ' + table + '(' + ', '.join(a) + ') VALUES (' +  ', '.join('?' * len(a)) + ')'

def _md5_digest(data):
  m = hashlib.md5()
  m.update(data)
  return m.digest()

def _u64_to_i64(x):
  return x - 0x8000000000000000

def _side_to_str(side: int) -> str:
  return "sente" if side > 0 else "gote"

def sfen_hashes(sfen: str) -> Tuple[int, int]:
  m = hashlib.md5()
  m.update(bytes(sfen, 'ascii'))
  x = int(m.hexdigest(), 16)
  lo, hi = (x & 0xffff_ffff_ffff_ffff), x >> 64
  assert x == (lo + (hi << 64))
  return (_u64_to_i64(lo), _u64_to_i64(hi))

class MoveWithStat:
  def __init__(self, packed_move: int, games: int, score: float, sum_of_opponent_ratings: int):
    self.packed_move = packed_move
    self.games = games
    self.score = score
    self.sum_of_opponent_ratings = sum_of_opponent_ratings
  def __repr__(self):
    return f'MoveWithStat ( packed_move = {self.packed_move}, games = {self.games}, score = {self.score}, sum_of_opponent_ratings = {self.sum_of_opponent_ratings})'

class KifuDB:
  def __init__(self, database = ':memory:'):
    self._database = database
    self._connection = None
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
  pos_hash1 integer,
  pos_hash2 integer,
  move integer,
  game integer)''')
    c.execute('''CREATE TABLE IF NOT EXISTS time_controls (time_control text PRIMARY KEY)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pos ON moves(pos_hash1)')
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
  def find_data_by_game_id(self, game_id: int) -> Optional[str]:
    compressed_data = self._select_single_value('SELECT data FROM kifus WHERE rowid = ?', (game_id, ))
    if compressed_data is None:
      return None
    return lzma.decompress(compressed_data).decode('UTF8')
  def find_game_by_kifu_md5(self, kifu_md5):
    return self._get_rowid('kifus', 'md5', kifu_md5)
  def get_time_countrol_rowid(self, time_control: str, force = False) -> Optional[int]:
    return self._get_rowid('time_controls', 'time_control', time_control, force)
  def player_with_most_games(self, side: int) -> Optional[str]:
    side = _side_to_str(side)
    return self._select_single_value(f'select {side}, count(*) as c from kifus group by {side} order by c desc limit 1')
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
  def insert(self, data: str) -> bool:
    b = bytes(data, 'UTF8')
    kifu_md5 = _md5_digest(b)
    rowid = self.find_game_by_kifu_md5(kifu_md5)
    if not rowid is None:
      logging.debug('KIFU file has been already inserted in DB (rowid = %d).', rowid)
      return False
    g = shogi.kifu.Game.parse(data)
    if g is None:
      return False
    data = lzma.compress(b)
    fields = ['sente', 'gote', 'start_date', 'sente_rating', 'gote_rating', 'time_control']
    v = g.get_row_values_from_headers(fields)
    tc = v.pop()
    if tc is None:
      tc = ''
    tc = self.get_time_countrol_rowid(tc, force = True)
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
    for m in g.parsed_moves:
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
  def moves_with_stats(self, pos: Position, player: Tuple[str, int], time_control: Optional[str]) -> list[MoveWithStat]:
    name, side = player
    #side = _side_to_str(player[1])
    player_side = _side_to_str(side)
    oside = _side_to_str(-side)
    orating = f'kifus.{oside}_rating'
    hash1, hash2 = sfen_hashes(pos.sfen())
    values = [hash1, hash2, name]
    conds = ['moves.pos_hash1 == ?', 'moves.pos_hash2 == ?', f'kifus.{player_side} == ?']
    if not time_control is None:
      tc = self.get_time_countrol_rowid(time_control, force = False)
      if tc is None:
        return []
      values.append(tc)
      conds.append('kifus.time_control == ?')
    conds.extend([f'{orating} > 0', 'kifus.result >= -1', 'kifus.result <= 1'])
    cond = ' AND '.join('(' + s + ')' for s in conds)
    q = f'''SELECT moves.move, COUNT(*) as c, SUM(kifus.result), SUM({orating}) FROM moves
INNER JOIN kifus ON moves.game == kifus.rowid
WHERE {cond}
GROUP BY moves.move
ORDER BY c DESC
'''
    logging.debug(q)
    c = self._connection.cursor()
    res = c.execute(q, values)
    l = []
    for t in res:
      n = t[1]
      sente_score = 0.5 * (t[2] + n)
      score = sente_score if side > 0 else n - sente_score
      l.append(MoveWithStat(t[0], n, score, t[3]))
    c.close()
    logging.debug('%s', l)
    return l
  def load_game(self, game_id: int) -> Optional[Game]:
    kifu = self.find_data_by_game_id(game_id)
    if kifu is None:
      return None
    return Game.parse(kifu)
