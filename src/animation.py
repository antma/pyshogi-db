# -*- coding: UTF8 -*-

import itertools
import json
import logging
import os
import subprocess
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from shutil import copyfile

import requests
from PIL import Image, ImageSequence, ImageDraw

from shogi import cell, evaluation
from shogi.game import Game
from shogi.position import Position
from usi import game_win_rates

def game_to_lishogi_gif_post_query(game: Game, flip_orientation: bool, delay: int) -> str:
  d = {}
  sente = game.player_with_rating(1)
  if sente:
    d['black'] = sente
  gote = game.player_with_rating(-1)
  if gote:
    d['white'] = gote
  if flip_orientation:
    d['orientation'] = 'white'
  d['delay'] = delay
  start_pos = game.start_pos
  if start_pos is None:
    pos = Position(None)
    start_pos = pos.sfen()
  else:
    pos = Position(start_pos)
  frames = [ {"sfen": start_pos}]
  for m in game.moves:
    pos.do_move(m)
    fd = {"sfen": pos.sfen(), "lastMove": m.usi_str()}
    if pos.is_check():
      fd['check'] = cell.usi_str(pos.find_king(pos.side_to_move))
    frames.append(fd)
  d['frames'] = frames
  res = json.dumps(d)
  logging.debug("%s", res)
  return res

def lishogi_gif(game: Game, flip_orientation: bool, delay: int, output_gif_filename: str, server: Optional[str] = None):
  if server is None:
    server = '127.0.0.1:6175'
  data = game_to_lishogi_gif_post_query(game, flip_orientation, delay)
  url = 'http://' + server + '/game.gif'
  r = requests.post(url, data = data)
  if r.status_code == 200:
    with open(output_gif_filename, 'wb') as f:
      f.write(r.content)

def matplotlib_graph(e, width, height, output_filename):
  a = list(e.items())
  a.sort()
  x, y = [], []
  for u, v in a:
    x.append(u)
    y.append(v[0] * 100.0)
  px = 1/plt.rcParams['figure.dpi']  # pixel in inches
  f, ax = plt.subplots(figsize=(width*px, height*px))
  plt.plot(x,y)
  ax.set_xlabel('moves')
  ax.set_ylabel('percent')
  ax.set_ylim(ymin = 0, ymax = 101)
  ax.set_yticks(np.arange(0, 110, 10))
  #ax.spines['top'].set_visible(False)
  #ax.spines['right'].set_visible(False)
  #ax.spines['bottom'].set_visible(False)
  #ax.spines['left'].set_visible(False)
  plt.savefig(output_filename)

def _frame(working_dir: str, index: int) -> str:
  return os.path.join(working_dir, f'frame{index:04d}.png')

def _scan_column(frame, col: int):
  h, w = frame.height, frame.width
  x = 0
  a = []
  for color, g in itertools.groupby([frame.getpixel((col, row)) for row in range(h)]):
    l = len(list(g))
    a.append((x, l, color))
    x += l
  return a

class _FrameLayout:
  def __init__(self, frame, flip_orientation: bool, bar_width: int = 16):
    h, w = frame.height, frame.width
    self.figure_height = h
    self.figure_width = w
    self.bar_width = bar_width
    self.flip_orientation = flip_orientation
    grey = 15
    lc = _scan_column(frame, w-1)
    assert ([t[2] for t in lc] == [2, grey, 2])
    self.bar_ytop, self.bar_height, _ = lc[1]
    for x in range(w - 1, -1, -1):
      if frame.getpixel((x, self.bar_ytop)) != grey:
        bar_xleft = x
        break
    self.bar_xleft = bar_xleft
    center = lambda t: t[0] + (t[1] // 2)
    self.top_row_center = center(lc[0])
    self.bottom_row_center = center(lc[2])
  def draw_bar(self, im, win_rate: float):
    draw = ImageDraw.Draw(im)
    draw.rectangle((self.bar_xleft, self.bar_ytop, self.bar_xleft + self.bar_width - 1, self.bar_ytop + self.bar_height - 1), fill = ((255,255,255)))
    black_height = round(win_rate * self.bar_height)
    if black_height > 0:
      if self.flip_orientation:
        t = (0, black_height - 1)
      else:
        t = (self.bar_height - black_height, self.bar_height - 1)
      assert t[0] <= t[1]
      draw.rectangle((self.bar_xleft, self.bar_ytop + t[0], self.bar_xleft + self.bar_width - 1, self.bar_ytop + t[1]), fill = ((0,1,0)))

def game_to_mp4(game: Game, flip_orientation: bool, delay: int, working_dir: str, output_mp4_filename: str, preset: str, ttf: str, lishogi_gif_server: Optional[str] = None):
  gif_filename = os.path.join(working_dir, 'game.gif')
  lishogi_gif(game, flip_orientation, delay, gif_filename, lishogi_gif_server)
  layout = None
  e = game_win_rates(game)
  last_index = None
  dft = (0.5, None)
  with Image.open(gif_filename) as im:
    for index, frame in enumerate(ImageSequence.Iterator(im)):
      move_no = index + game.start_move_no
      if move_no > game.pos.move_no:
        break
      frame_filename = _frame(working_dir, index)
      #h, w = frame.height, frame.width
      im = frame.copy()
      if layout is None:
        layout = _FrameLayout(im, flip_orientation)
      wr, _ = e.get(move_no, dft)
      old_wr, bm = e.get(move_no - 1, dft)
      side = game.move_no_to_side_to_move(move_no)
      msg = evaluation.mistake_str(side, old_wr, wr, bm)
      if not msg is None:
        logging.info(msg)
      layout.draw_bar(im, wr)
      im.save(frame_filename)
      last_index = index
  copyfile(_frame(working_dir, last_index), _frame(working_dir, last_index+1))
  last_index += 2
  matplotlib_graph(e, layout.figure_width, layout.figure_height, _frame(working_dir, last_index))
  command = ['ffmpeg', '-r', f'1000/{delay}', '-i', os.path.join(working_dir, 'frame%04d.png'), '-c:v', 'libx264', '-preset', preset, '-vf', 'fps=25', '-pix_fmt', 'yuv420p', os.path.join(working_dir, 'out.mp4')]
  subprocess.run(command, check = True, shell = False)
