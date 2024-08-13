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

class CanvasBoard:
  def _cell_coords(self, i):
    row, col = divmod(i, 9)
    col = 8 - col
    return (col * (self._cell_width + 1), row * (self._cell_width + 1))
  def __init__(self, parent_window, images: ShogiPiecesImages, cell_width: int):
    self._parent = parent_window
    self._images = images
    self._cell_width = cell_width
    self._board = [piece.FREE] * 81
    s = (cell_width + 1) * 9
    self._canvas = tk.Canvas(parent_window, height = s, width = s, bg = '#fff')
    for i in range(81):
      x1, y1 = self._cell_coords(i)
      self._canvas.create_rectangle(x1, y1, x1 + (cell_width + 1), y1 + (cell_width + 1))
    self.draw_position(Position())
    self._canvas.pack()
  def draw_position(self, pos: Position):
    for i, (old, new) in enumerate(zip(self._board, pos.board)):
      if old == new:
        continue
      if old != piece.FREE:
        self._canvas.delete(f'cell{i}')
      if new != piece.FREE:
        p = self._images.get(new)
        x1, y1 = self._cell_coords(i)
        self._canvas.create_image(x1 + 1, y1 + 1, anchor = tk.N + tk.W, image = p, tag = f'cell{i}')
      self._board[i] = new
