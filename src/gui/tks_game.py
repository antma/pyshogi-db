# -*- coding: UTF8 -*-

from datetime import timedelta
import logging
import tkinter as tk
from  tkinter import ttk, font
from typing import Optional

import kdb
from shogi.kifu import Game
from shogi.position import Position
from . import pieces
from . import tks_pos
from . import tks_tree
from . import table

def _timedelta_to_str(t: Optional[timedelta]) -> str:
  if t is None:
    return ''
  return str(t)

class _Positions:
  def __init__(self, game: Game):
    self._game = game
    self._sfens = []
  def goto_move(self, move_no: int) -> Position:
    if move_no == 0:
      return Position()
    while move_no >= len(self._sfens):
      self._sfens.append(None)
    sfen = self._sfens[move_no]
    if not sfen is None:
      return Position(sfen)
    i = move_no
    while (i >= 0) and (self._sfens[i] is None):
      i -= 1
    if i < 0:
      pos = Position()
      i = 0
    else:
      pos = Position(self._sfens[i])
    cur_move = i
    for j in range(i, move_no):
      if j >= len(self._game.parsed_moves):
        break
      m = self._game.parsed_moves[j]
      pos.do_move(m)
      cur_move = j + 1
    self._sfens[cur_move] = pos.sfen()
    return pos

class TableMoves:
  def __init__(self, game_window):
    view_font = game_window.table_font
    parent = game_window.frame2
    game = game_window.game
    self._positions = _Positions(game)
    self._game_window = game_window
    columns = ('move_no', 'kifu', 'time', 'cum_time')
    self.table = table.Table(parent, 'TableMoves', columns, view_font, tk.BROWSE)
    cw = self.table.make_columns_width()
    for i, m in enumerate(game.moves):
      t = (str(i + 1), m.kifu, _timedelta_to_str(m.time), _timedelta_to_str(m.cum_time))
      self.table.insert_row(t, cw)
    self.table.adjust_columns_width(cw)
    self.table.tree.pack(side = tk.LEFT, anchor = tk.N + tk.E, expand = tk.YES, fill = tk.BOTH)
    self.table.tree.bind('<<TreeviewSelect>>', self._select_event)
  def widget(self):
    return self.table.tree
  def _select_event(self, event):
    item = self.table.tree.selection()
    logging.debug(f'Select item {item}, event {event}')
    self.goto_move(int(item[0]))
  def goto_move(self, move_no: int):
    pos = self._positions.goto_move(move_no)
    self._game_window.draw_position(pos)

class TableHeaders:
  def __init__(self, game_window):
    game = game_window.game
    parent = game_window.frame2
    columns = ('key', 'value')
    self.table = table.Table(parent, 'TableHeaders', columns, game_window.table_font, tk.NONE)
    cw = self.table.make_columns_width()
    a = []
    sente = game.player_with_rating(1)
    if sente is None:
      sente = '-'
    a.append(('Sente', sente))
    gote = game.player_with_rating(-1)
    if gote is None:
      gote = '-'
    a.append(('Gote', gote))
    for title, key in [ ('Date', 'start_date'), ('Time control', 'time_control')]:
      p = game.get_header_value(key)
      if p is None:
        continue
      if not isinstance(p, str):
        p = str(p)
      a.append((title, p))
    tr = game.text_result()
    if not tr is None:
      a.append(('Result', tr))
    cw = self.table.make_columns_width()
    for t in a:
      self.table.insert_row(t, cw)
    #self.table.tree.column('key', anchor = tk.W)
    self.table.adjust_columns_width(cw)
    self.table.tree['height'] = len(a)
    self.table.tree.pack(side = tk.TOP, anchor = tk.N, expand = tk.YES, fill = tk.X)

class GameWindow:
  def __init__(self, parent, images: pieces.ShogiPiecesImages, db: kdb.KifuDB, game_id: int):
    self.db = db
    self.table_font = font.Font(family = 'Times', size = 12, slant = font.ROMAN)
    self.game = db.load_game(game_id)
    self.frame = tk.Frame(parent)
    self._board = tks_pos.TksPosition(self.frame, images)
    pos = Position()
    self._board.draw_position(pos)
    self.frame2 = tk.Frame(parent)
    #self.frame2.grid_columnconfigure(0, weight=1)
    #self.frame2.grid_rowconfigure(0, weight=1)
    #self._table_moves.widget().grid(row = 0, column = 0, sticky = tk.N + tk.E + tk.S + tk.W)
    #self._moves_with_stat = tks_tree.MovesWithStatTreeView(self)
    self._table_moves = TableMoves(self)
    self._table_headers = TableHeaders(self)
    self._moves_with_stat = tks_tree.TableMovesWithStat(self)
    #self._table_moves.widget().pack(side = tk.LEFT, expand = tk.YES, fill = tk.Y)
    self.frame.pack(side = tk.LEFT)
    self.frame2.pack(side = tk.LEFT, expand = tk.YES, fill = tk.BOTH)
  def draw_position(self, pos: Position):
    self._board.draw_position(pos)
    self._moves_with_stat.draw_position(pos)
