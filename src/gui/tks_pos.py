# -*- coding: UTF8 -*-
'''tks means tk(shogi). TK frame for display shogi position'''

import tkinter as tk
from typing import Optional

import shogi
from shogi.position import Position
from . import pieces

class TksPosition:
  def __init__(self, parent_window, images: pieces.ShogiPiecesImages):
    self.parent_window = parent_window
    self.images = images
    self.cell_width = self.images.cell_width
    self.height = 9 * (self.cell_width + 1)
    self._gote_hand = _Hand(self, -1)
    self._board = _Board(self)
    self._sente_hand = _Hand(self, 1)
    fs = self.cell_width // 5
    self.font = f'Arial {fs} bold'
  def draw_position(self, pos: Position):
    self._gote_hand.draw_position(pos)
    self._board.draw_position(pos)
    self._sente_hand.draw_position(pos)
  def select_cell(self, i: int):
    self._board.select_cell(i)

class _Board:
  def _cell_coords(self, i):
    row, col = divmod(i, 9)
    col = 8 - col
    return (col * (self._p.cell_width + 1), row * (self._p.cell_width + 1))
  def __init__(self, tk_position: TksPosition):
    self._p = tk_position
    cell_width = tk_position.cell_width
    self._board = [shogi.piece.FREE] * 81
    self._canvas = tk.Canvas(tk_position.parent_window, height = tk_position.height, width = tk_position.height, bg = '#FFCC99')
    self._rects = []
    self._selected_cell = None
    for i in range(81):
      x1, y1 = self._cell_coords(i)
      self._rects.append(self._canvas.create_rectangle(x1, y1, x1 + (cell_width + 1), y1 + (cell_width + 1), outline = '#000'))
    self._default_fill = self._canvas.itemcget(self._rects[0], 'fill')
    self._canvas.pack(side = tk.LEFT)
  def _change_cell_selection(self, i: Optional[int], b: bool):
    if not i is None:
      f = 'yellow' if b else self._default_fill
      self._canvas.itemconfigure(self._rects[i], fill = f)
  def select_cell(self, i: int):
    if self._selected_cell != i:
      self._change_cell_selection(self._selected_cell, False)
      self._change_cell_selection(i, True)
      self._selected_cell = i
  def draw_position(self, pos: Position):
    for i, (old, new) in enumerate(zip(self._board, pos.board)):
      if old == new:
        continue
      if old != shogi.piece.FREE:
        self._canvas.delete(f'cell{i}')
      if new != shogi.piece.FREE:
        p = self._p.images.get(new)
        x1, y1 = self._cell_coords(i)
        self._canvas.create_image(x1 + 1, y1 + 1, anchor = tk.N + tk.W, image = p, tag = f'cell{i}')
      self._board[i] = new

class _Hand:
  def __init__(self, tk_position: TksPosition, side: int):
    self._p = tk_position
    self._side = side
    self._side_name = 'sente' if side > 0 else 'gote'
    self._pocket = [0] * shogi.piece.ROOK
    self._canvas = tk.Canvas(tk_position.parent_window, height = tk_position.height, width = tk_position.cell_width, bg = '#000')
    self._canvas.pack(side = tk.LEFT)
  def draw_position(self, pos: Position):
    c = pos.sente_pieces if self._side > 0 else pos.gote_pieces
    for i, (old, new) in enumerate(zip(self._pocket, c)):
      if old == new:
        continue
      t = f'{self._side_name}{i}'
      img_name = 'i' + t
      text_name = 't' + t
      if old > 0:
        self._canvas.delete(img_name)
        self._canvas.delete(text_name)
      if new > 0:
        if self._side > 0:
          y = self._p.height - (i + 1) * (self._p.cell_width + 1)
          yt = y
          a = tk.N
        else:
          y = i * (self._p.cell_width + 1)
          yt = y + (self._p.cell_width + 1)
          a = tk.S
        p = self._p.images.get(self._side * (i + 1))
        assert not p is None
        self._canvas.create_image(0, y, anchor = tk.N + tk.W, image = p, tag = img_name)
        self._canvas.create_text(self._p.cell_width, yt, anchor = a + tk.E, font = self._p.font, tag = text_name, text = str(new), fill = '#fff')
      self._pocket[i] = new
