# -*- coding: UTF8 -*-

from datetime import timedelta
import logging
import tkinter as tk
from  tkinter import ttk, font
from typing import Optional

import kdb
from shogi.kifu import Game
from shogi.position import Position
from . import tks_pos
from . import pieces

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

class MovesTreeView:
  def __init__(self, game_window, game: Game):
    parent = game_window.frame
    self._positions = _Positions(game)
    self._game_window = game_window
    columns = ('move_no', 'kifu', 'time', 'cum_time')
    font_size = 12
    view_font = font.Font(family = 'Times', size = font_size, slant = font.ROMAN)
    style = ttk.Style()
    style.configure('Moves.Treeview', font = view_font, rowheight = round(font_size * 1.5))
    self._tree = ttk.Treeview(parent, style = 'Moves.Treeview', columns = columns, selectmode = tk.BROWSE, show = '')
    self._tree.column('#0', width = 0, stretch = tk.NO)
    col_widths = [0] * 4
    for i, m in enumerate(game.moves):
      t = (str(i + 1), m.kifu, _timedelta_to_str(m.time), _timedelta_to_str(m.cum_time))
      for j in range(4):
        col_widths[j] = max(col_widths[j], view_font.measure(t[j]))
      self._tree.insert(parent = '', index = tk.END, iid = i, text = '', values = t)
    for j in range(4):
      w = round(col_widths[j] * 1.5)
      self._tree.column(columns[j], anchor = tk.CENTER, minwidth = w, width = w, stretch = tk.NO)
    self._tree.pack(side = tk.LEFT, expand = True, fill = tk.Y)
    self._tree.bind('<<TreeviewSelect>>', self._select_event)
  def _select_event(self, event):
    item = self._tree.selection()
    logging.debug(f'Select item {item}, event {event}')
    self.goto_move(int(item[0]))
  def goto_move(self, move_no: int):
    pos = self._positions.goto_move(move_no)
    self._game_window.draw_position(pos)

class GameWindow:
  def __init__(self, parent, images: pieces.ShogiPiecesImages, db: kdb.KifuDB, game_id: int):
    game = db.load_game(game_id)
    self._db = db
    self.frame = tk.Frame(parent)
    self._board = tks_pos.TksPosition(self.frame, images)
    pos = Position()
    self._board.draw_position(pos)
    self._moves_view = MovesTreeView(self, game)
    self.frame.pack()
  def draw_position(self, pos: Position):
    self._board.draw_position(pos)
