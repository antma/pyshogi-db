# -*- coding: UTF8 -*-

import tkinter as tk
from gui.pieces import ShogiPiecesImages
import shogi
from shogi.position import Position
import shogi.piece as piece

class ShogiBoard:
  def __init__(self, parent_window, images: ShogiPiecesImages, cell_width: int):
    self._parent = parent_window
    self._images = images
    self._cell_width = cell_width
    self._board = [piece.FREE] * 81
    self._labels = [None] * 81
    self._frame = tk.Frame(parent_window)
    for i in range(9):
      self._frame.grid_rowconfigure(i, minsize=self._cell_width)
      self._frame.grid_columnconfigure(i, minsize=self._cell_width)
    for i in range(81):
      row, col = divmod(i, 9)
      label = tk.Label(self._frame)
      label.grid(row = row, column = 8 - col)
      self._labels[i] = label
    self.draw_position(Position())
    self._frame.pack()
  def draw_position(self, pos: Position):
    for i, (old, new) in enumerate(zip(self._board, pos.board)):
      if old == new:
        continue
      p = self._images.get(new)
      self._labels[i]['image'] = p
      self._board[i] = new

