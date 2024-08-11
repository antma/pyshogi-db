# -*- coding: UTF8 -*-

import hashlib
import logging
import lzma
import sqlite3

import shogi

def _insert(table, a):
  return 'INSERT INTO ' + table + '(' + ', '.join(a) + ') VALUES (' +  ', '.join('?' * len(a)) + ')'

def _md5(data):
  m = hashlib.md5()
  m.update(data)
  return m.digest()

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
    c.close()
  def find_game_by_kifu_md5(self, kifu_md5):
    c = self._connection.cursor()
    res = c.execute('SELECT rowid FROM kifus WHERE md5 == ?', (kifu_md5, ))
    r = res.fetchone()
    c.close()
    if r is None:
      return r
    return r[0]
  def insert(self, data: str) -> bool:
    b = bytes(data, 'UTF8')
    kifu_md5 = _md5(b)
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
    c = self._connection.cursor()
    q = _insert('kifus', fields)
    c.execute(q, v)
    self._connection.commit()
    c.close()
    return True
