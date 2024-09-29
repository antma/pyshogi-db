# -*- coding: UTF8 -*-

import logging
import tkinter as tk
from typing import Optional

import usi
from shogi.move import Move
from shogi.position import Position
from . import pieces
from . import tks_pos

class USIGameWindow:
  def __init__(self, parent, images: pieces.ShogiPiecesImages, usi_game: usi.USIGame, sleep_ms: int = 50):
    self.frame = tk.Frame(parent)
    self._sleep_ms = sleep_ms
    self.usi_game = usi_game
    self.board = tks_pos.TksPosition(self.frame, images)
    self.frame.pack(side = tk.LEFT)
    self.frame.after(0, self.step)
  def step(self):
    if self.usi_game.is_idle():
      g = self.usi_game.game
      self.draw_position(g.pos)
      self.set_last_move(g.last_move())
    self.usi_game.step()
    self.frame.after(self._sleep_ms, self.step)
  def draw_position(self, pos: Position):
    logging.debug('GameWindow.draw_position: %s', pos.sfen())
    self.board.draw_position(pos)
  def set_last_move(self, m: Optional[Move]):
    self.board.select_cell(m and m.to_cell)
