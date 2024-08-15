# -*- coding: UTF8 -*-

from datetime import timedelta
import tkinter as tk
from  tkinter import ttk
from typing import Optional

from shogi.kifu import Game
from shogi.position import Position
from . import tks_pos
from . import pieces

def _timedelta_to_str(t: Optional[timedelta]) -> str:
  if t is None:
    return ''
  return str(t)

class MovesTreeView:
  def __init__(self, parent, game: Game):
    self._tree = ttk.Treeview(parent, columns = ('move_no', 'kifu', 'time', 'cum_time'))
    self._tree.column('#0', width = 0, stretch = tk.NO)
    #self._tree.column('move_no', anchor = tk.CENTER
    for i, m in enumerate(game.moves):
      t = (str(i + 1), m.kifu, _timedelta_to_str(m.time), _timedelta_to_str(m.cum_time))
      self._tree.insert(parent = '', index = tk.END, iid = i, text = '', values = t)
    self._tree.pack(side = tk.LEFT, expand = True, fill = tk.Y)

class GameWindow:
  def __init__(self, parent, images: pieces.ShogiPiecesImages, game: Game):
    self._frame = tk.Frame(parent)
    self._board = tks_pos.TksPosition(self._frame, images)
    pos = Position()
    self._board.draw_position(pos)
    self._moves_view = MovesTreeView(self._frame, game)
    self._frame.pack()
