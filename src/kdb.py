# -*- coding: UTF8 -*-

import lzma
import sqlite3

import shogi

def _insert(table, a):
  return 'INSERT INTO ' + table + '(' + ', '.join(a) + ') VALUES (' +  ', '.join('?' * len(a)) + ')'

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
  data blob)''')
    c.close()
  def insert(self, data: str) -> bool:
    g = shogi.kifu.Game.parse(data)
    if g is None:
      return False
    b = bytes(data, 'UTF8')
    data = lzma.compress(b)
    fields = ['sente', 'gote', 'start_date', 'sente_rating', 'gote_rating', 'time_control', 'moves', 'result', 'data']
    q = _insert('kifus', fields)
    v = g.get_row_values(data, fields)
    c = self._connection.cursor()
    c.execute(q, v)
    self._connection.commit()
    c.close()
    return True
