# -*- coding: UTF8 -*-

import logging
import tkinter as tk
from tkinter import ttk

class Table:
  def __init__(self, parent, style_prefix, columns, font, selectmode, headings = False):
    #self.parent = parent
    self.font = font
    self._headings = headings
    self.columns = columns
    font_size = font.cget('size')
    style = ttk.Style()
    style_name = style_prefix + '.Treeview'
    rowheight = round(font_size * 1.5)
    logging.debug('font_size = %d, rowheight = %d', font_size, rowheight)
    style.configure(style_name, font = font, rowheight = rowheight)
    show = []
    if headings:
      show.append('headings')
    self.tree = ttk.Treeview(parent, style = style_name, columns = columns, selectmode = selectmode, show = show)
    if headings:
      for c in columns:
        self.tree.heading(c, text = c)
    self.tree.column('#0', width = 0, stretch = tk.NO)
    self.rows = []
    '''
    for i, m in enumerate(game.moves):
      t = (str(i + 1), m.kifu, _timedelta_to_str(m.time), _timedelta_to_str(m.cum_time))
      logging.debug("Insert %s", t)
      self._tree.insert(parent = '', index = tk.END, iid = i, text = '', values = t)
    for c in self._tree['columns']:
      self._tree.column(c, anchor = tk.CENTER, width = -1)
    self._tree.pack(side = tk.LEFT, expand = True, fill = tk.Y)
    '''
  def make_columns_width(self):
    if self._headings:
      return [self.font.measure(c) for c in self.columns]
    return [0] * len(self.columns)
  def adjust_columns_width(self, columns_width):
    for name, w in zip(self.columns, columns_width):
      #self.tree.column(name, anchor = tk.CENTER, minwidth = round(w * 1.1), width = round(w * 1.3), stretch = tk.NO)
      self.tree.column(name, anchor = tk.CENTER, minwidth = round(w * 1.1), width = round(w * 1.3))
  def insert_row(self, t, columns_width: list[int]):
    self.rows.append(self.tree.insert(parent = '', index = tk.END, iid = len(self.rows), text = '', values = t))
    for j in range(len(self.columns)):
      columns_width[j] = max(columns_width[j], self.font.measure(t[j]))
  def delete_items(self):
    logging.debug('Remove table rows: %s', self.rows)
    for row in self.rows:
      self.tree.delete(row)
    self.rows = []
