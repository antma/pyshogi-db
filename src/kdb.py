# -*- coding: UTF8 -*-

import hashlib
import logging
import lzma
import sqlite3
from typing import Tuple

import shogi

def _insert(table, a):
  return 'INSERT INTO ' + table + '(' + ', '.join(a) + ') VALUES (' +  ', '.join('?' * len(a)) + ')'

def _md5_digest(data):
  m = hashlib.md5()
  m.update(data)
  return m.digest()

def _u64_to_i64(x):
  return x - 0x8000000000000000

def sfen_hashes(sfen: str) -> Tuple[int, int]:
  m = hashlib.md5()
  m.update(bytes(sfen, 'ascii'))
  x = int(m.hexdigest(), 16)
  lo, hi = (x & 0xffff_ffff_ffff_ffff), x >> 64
  assert x == (lo + (hi << 64))
  return (_u64_to_i64(lo), _u64_to_i64(hi))

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
  time_control text,
  moves integer,
  result integer,
  md5 blob,
  data blob)''')
    c.execute('''CREATE TABLE IF NOT EXISTS moves (
  pos_hash1 integer,
  pos_hash2 integer,
  move integer,
  game integer)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pos ON moves(pos_hash1)')
    c.close()
  def find_game_by_kifu_md5(self, kifu_md5):
    c = self._connection.cursor()
    res = c.execute('SELECT rowid FROM kifus WHERE md5 == ?', (kifu_md5, ))
    r = res.fetchone()
    c.close()
    if r is None:
      return r
    return r[0]
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
