# -*- coding: UTF8 -*-

import logging
import tkinter as tk
from typing import Optional

import kdb
from shogi.kifu import Game, kifu_move
from shogi.move import Move
from shogi.position import Position
from . import table

class _Filter:
  def __init__(self, player_name: str, player_side: int, time_control: Optional[int]):
    self.player = (player_name, player_side)
    self.time_control = time_control
  @staticmethod
  def make(db: kdb.KifuDB, game: Game):
    player = db.player_with_most_games()
    if player is None:
      return None
    time_control = game.get_header_value('time_control')
    if not time_control is None:
      time_control = db.get_time_countrol_rowid(time_control, force = False)
    if player == game.get_header_value('sente'):
      return _Filter(player, 1, time_control)
    if player == game.get_header_value('gote'):
      return _Filter(player, -1, time_control)
    return None
  def moves_with_stats(self, db: kdb.KifuDB, pos: Position) -> list[kdb.MoveGameStat]:
    return db.moves_with_stats(pos, self.player, self.time_control)

class TableMovesWithStat:
  def __init__(self, game_window):
    parent = game_window.frame2
    game = game_window.game
    self._game_window = game_window
    self._filter = game_window.db.make_player_and_tc_filter(game)
    columns = ('move', 'games', 'percent', 'perf')
    self.table = table.Table(parent, 'TableMovesWithStat', columns, game_window.table_font, tk.NONE, headings = True)
    self.active = False
    #self.table.state(ttk.DISABLED)
  def pack(self):
    if not self._filter is None:
      self.table.tree.pack(side = tk.BOTTOM, anchor = tk.S + tk.W, expand = tk.YES, fill = tk.X)
      self.active = True
  def pack_forget(self):
    if self.active:
      self.table.tree.pack_forget()
      self.active = False
  def delete_items(self):
    return self.table.delete_items()
  def draw_position(self, pos: Position):
    if self._filter is None:
      return
    moves = self._game_window.db.moves_with_stats(pos, self._filter)
    total_games = sum(m.games for m in moves)
    self.pack_forget()
    self.delete_items()
    if total_games < 3:
      #self.table.state(ttk.DISABLED)
      logging.debug('Too few games (%d) to show stats', total_games)
      return
    #self.table.state(ttk.READONLY)
    game = self._game_window.game
    move_no = pos.move_no - 1
    prev_move = None
    if move_no > 0:
      try:
        prev_move = game.parsed_moves[move_no - 1]
      except IndexError:
        pass
    columns_width = self.table.make_columns_width()
    for m in moves:
      mv = Move.unpack_from_int(m.packed_move, pos.side_to_move)
      p = m.percent
      perf = round(m.performance())
      t = (kifu_move(mv, prev_move), str(m.games), f'{p:.01f}%', str(perf))
      self.table.insert_row(t, columns_width)
    self.table.adjust_columns_width(columns_width)
    self.table.tree['height'] = len(moves)
    self.pack()
