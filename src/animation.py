# -*- coding: UTF8 -*-

import json
import logging
import os
import subprocess
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt

import requests
from PIL import Image, ImageSequence, ImageDraw

from shogi import cell
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
    y.append(v * 100.0)
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

def game_to_mp4(game: Game, flip_orientation: bool, delay: int, working_dir: str, output_mp4_filename: str, preset: str, lishogi_gif_server: Optional[str] = None):
  gif_filename = os.path.join(working_dir, 'game.gif')
  lishogi_gif(game, flip_orientation, delay, gif_filename, lishogi_gif_server)
  bar_width = 16
  bar_xleft = None
  bar_ytop = None
  bar_height = None
  figure_width = None
  figure_height = None
  grey = 15
  e = game_win_rates(game)
  last_index = None
  with Image.open(gif_filename) as im:
    for index, frame in enumerate(ImageSequence.Iterator(im)):
      move_no = index + game.start_move_no
      if move_no > game.pos.move_no:
        break
      wr = e.get(move_no, 0.5)
      frame_filename = os.path.join(working_dir, f"frame{index:04d}.png")
      h, w = frame.height, frame.width
      im = frame.copy()
      if bar_xleft is None:
        figure_width = w
        figure_height = h
        for y in range(h):
          s = 0
          for x in range(w - 1, -1, -1):
            p = im.getpixel((x, y)) 
            if (s == 0) and (p == grey):
              s += 1
            elif (s == 1) and (p != grey):
              s += 1 
              bar_ytop = y
              bar_xleft = x
              break
          if s == 2:
            break
        for y in range(bar_ytop + 1, h):
          if im.getpixel((bar_xleft, y)) != 2:
            bar_height = y - bar_ytop
        logging.debug('bar_xleft = %d, bar_ytop = %d, bar_height = %d', bar_xleft, bar_ytop, bar_height)
      draw = ImageDraw.Draw(im)
      draw.rectangle((bar_xleft, bar_ytop, bar_xleft + bar_width - 1, bar_ytop + bar_height - 1), fill = ((255,255,255)))
      black_height = round(wr * bar_height)
      logging.debug('Frame %d: wr = %s, black_h = %d, bar_h = %d', index, wr, black_height, bar_height)
      if black_height > 0:
        if flip_orientation:
          t = (0, black_height - 1)
        else:
          t = (bar_height - black_height, bar_height - 1)
        assert t[0] <= t[1]
        draw.rectangle((bar_xleft, bar_ytop + t[0], bar_xleft + bar_width - 1, bar_ytop + t[1]), fill = ((0,1,0)))
      im.save(frame_filename)
      last_index = index
  last_index += 1
  matplotlib_graph(e, figure_width, figure_height, os.path.join(working_dir, f'frame{last_index:04d}.png'))
  command = ['ffmpeg', '-r', f'1000/{delay}', '-i', os.path.join(working_dir, 'frame%04d.png'), '-c:v', 'libx264', '-preset', preset, '-vf', 'fps=25', '-pix_fmt', 'yuv420p', os.path.join(working_dir, 'out.mp4')]
  subprocess.run(command, check = True, shell = False)
