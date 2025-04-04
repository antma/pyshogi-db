# -*- coding: UTF8 -*-

import itertools
import json
import logging
import math
import os
import subprocess
from shutil import copyfile
from typing import Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

import requests
from PIL import Image, ImageSequence, ImageDraw, ImageFont

from shogi import cell, evaluation, piece
from shogi.game import Game
from shogi.move import Move
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
  r = requests.post(url, data = data, timeout = 1.0)
  if r.status_code == 200:
    with open(output_gif_filename, 'wb') as f:
      f.write(r.content)

def matplotlib_graph(title, e, width, height, output_filename):
  a = list(e.items())
  a.sort()
  x, y = [], []
  for u, v in a:
    x.append(u)
    y.append(v[0] * 100.0)
  px = 1/plt.rcParams['figure.dpi']  # pixel in inches
  _, ax = plt.subplots(figsize=(width*px, height*px))
  plt.plot(x, y)
  plt.title(title)
  ax.set_xlabel('moves')
  ax.set_ylabel('percent')
  ax.set_ylim(ymin = 0, ymax = 101)
  ax.set_yticks(np.arange(0, 110, 10))
  #ax.spines['top'].set_visible(False)
  #ax.spines['right'].set_visible(False)
  #ax.spines['bottom'].set_visible(False)
  #ax.spines['left'].set_visible(False)
  plt.savefig(output_filename)

class _Frames:
  def __init__(self, working_dir: str):
    self._working_dir = working_dir
    self._index = 0
  def next_frame_filename(self) -> str:
    self._index += 1
    return os.path.join(self._working_dir, f'frame{self._index:04d}.png')
  def save(self, frame, exif_data = None):
    fn = self.next_frame_filename()
    if exif_data is None:
      frame.save(fn)
    else:
      frame.save(fn, exif = exif_data)
  def copy_last(self):
    self._index -= 1
    old = self.next_frame_filename()
    new = self.next_frame_filename()
    copyfile(old, new)

def _scan_column(frame, col: int):
  x = 0
  a = []
  for color, g in itertools.groupby([frame.getpixel((col, row)) for row in range(frame.height)]):
    l = len(list(g))
    a.append((x, l, color))
    x += l
  return a

def _scan_row(frame, row: int):
  x = 0
  a = []
  for color, g in itertools.groupby([frame.getpixel((col, row)) for col in range(frame.width)]):
    l = len(list(g))
    a.append((x, l, color))
    x += l
  return a

def _draw_arrow(draw, src: Tuple[int, int], dest: Tuple[int, int], r: float, alpha: float, color = (255, 0, 0), width = 2):
  draw.line([src, dest], fill = color, width = width)
  alpha = math.radians(alpha)
  sa = math.sin(alpha)
  ca = math.cos(alpha)
  dx = src[0] - dest[0]
  dy = src[1] - dest[1]
  inv = r / math.hypot(dx, dy)
  dx *= inv
  dy *= inv
  a = [dest]
  cb = ca
  for sign in [-1, 1]:
    sb = sign * sa
    x = cb * dx - sb * dy + dest[0]
    y = sb * dx + cb * dy + dest[1]
    a.append((round(x), round(y)))
  draw.polygon(a, fill = color)

def _center(t):
  return t[0] + (t[1] // 2)

class _FrameLayout:
  def __init__(self, frame, flip_orientation: bool, ttf: Tuple[str,int], bar_width: int = 16):
    h, w = frame.height, frame.width
    self.font = ImageFont.truetype(ttf[0], ttf[1])
    self.figure_height = h
    self.figure_width = w
    self.bar_width = bar_width
    self.flip_orientation = flip_orientation
    grey = 15
    lc = _scan_column(frame, w-1)
    assert [t[2] for t in lc] == [2, grey, 2], f"lc = {lc}"
    self.bar_ytop, self.bar_height, _ = lc[1]
    for x in range(w - 1, -1, -1):
      if frame.getpixel((x, self.bar_ytop)) != grey:
        bar_xleft = x
        break
    self.bar_xleft = bar_xleft
    self.top_row_center = _center(lc[0])
    self.bottom_row_center = _center(lc[2])
    lr = _scan_row(frame, self.bar_ytop)
    logging.debug('lr = %s', lr)
    assert ([t[2] for t in lr] == [15, 0, 15])
    self.cell_xleft = lr[1][0] + 1
    self.cell_width = (lr[1][1] - 2) // 9
    self.cell_ytop = self.bar_ytop + 1
    self.cell_height = (self.bar_height - 2) // 9
    logging.debug('cell sizes = %dx%d', self.cell_width, self.cell_height)
    self.sente_xcenter = _center(lr[2])
    self.gote_xcenter = _center(lr[0])
    self.vl_width = ((lr[1][1] + 8) // 9) * 9
    self.vl_height = (self.vl_width // 9) * 16
    #(left, upper, right, lower)
    self.vl_board_crop_box = (self.cell_xleft - 1, self.bar_ytop, self.cell_xleft - 1 + lr[1][1], self.bar_ytop + self.bar_height)
    self.right_pieces = lr[2]
    self.left_pieces = lr[0]
  def draw_bar(self, draw, win_rate: float):
    draw.rectangle((self.bar_xleft, self.bar_ytop, self.bar_xleft + self.bar_width - 1, self.bar_ytop + self.bar_height - 1), fill = ((255,255,255)))
    black_height = round(win_rate * self.bar_height)
    if black_height > 0:
      if self.flip_orientation:
        t = (0, black_height - 1)
      else:
        t = (self.bar_height - black_height, self.bar_height - 1)
      assert t[0] <= t[1]
      draw.rectangle((self.bar_xleft, self.bar_ytop + t[0], self.bar_xleft + self.bar_width - 1, self.bar_ytop + t[1]), fill = ((0,1,0)))
  def draw_text(self, draw, side: int, msg: str, color):
    sente = (side > 0) ^ self.flip_orientation
    y = self.bottom_row_center if sente else self.top_row_center
    draw.text((self.bar_xleft - 1, y), msg, font = self.font, fill = color, anchor = 'rm')
  def cell_coords(self, c: int) -> Tuple[int, int]:
    row, col = divmod(c, 9)
    col = 8 - col
    if self.flip_orientation:
      row, col = 8 - row, 8 - col
    return (self.cell_xleft + round((col + 0.5) * self.cell_width), self.cell_ytop + round((row + 0.5) * self.cell_height))
  def draw_move(self, draw, m: Move):
    dest = self.cell_coords(m.to_cell)
    if m.is_drop():
      p = round(((piece.ROOK - abs(m.to_piece)) + 0.5) * self.cell_height)
      if (m.to_piece > 0) != self.flip_orientation:
        src = (self.sente_xcenter, self.bar_ytop + self.bar_height - 2 - p)
      else:
        src = (self.gote_xcenter, self.bar_ytop + p)
    else:
      src = self.cell_coords(m.from_cell)
    _draw_arrow(draw, src, dest, self.cell_width * 0.2, 30.0)
  def draw_vertical_frame(self, frame, countdown: Optional[int] = None):
    im = Image.new('RGB', (self.vl_width, self.vl_height), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    board = frame.crop(self.vl_board_crop_box)
    x, y = 0, self.cell_height
    board_dest_rect = (x, y, x + board.width, y + board.height)
    im.paste(board, board_dest_rect)
    z = board.width
    draw.rectangle([(0, 0), (z - 1, self.cell_height - 1)], fill = (105,107,104))
    y = board.height + self.cell_height
    diagram_height = board.height + 2 * self.cell_height
    draw.rectangle([(0, y), (z - 1, diagram_height - 1)], fill = (105,107,104))
    for p in reversed(range(piece.PAWN, piece.ROOK + 1)):
      x = self.right_pieces[0]
      y = self.bar_ytop + 1 + (p + 1) * self.cell_height + 8
      l = self.right_pieces[1]
      dl = round(l * 0.1)
      x += dl
      l -= 2 * dl
      rp = frame.crop((x, y, x + l, y + self.cell_height))
      x = self.left_pieces[0]
      y = self.bar_ytop + 1 + (piece.ROOK - p) * self.cell_height + 8
      l = self.left_pieces[1]
      dl = round(l * 0.1)
      x += dl
      l -= 2 * dl
      lp = frame.crop((x, y, x + l, y + self.cell_height))
      y = self.cell_height + board.height + 1
      im.paste(rp, (z - rp.width, y, z, y + rp.height))
      y = 0
      im.paste(lp, (z - lp.width, y, z, y + lp.height))
      z -= max(rp.width, lp.width)
      #break
      #im.paste(lp, (z - rp.width, 0, z, rp.height))
    if countdown:
      x = im.width // 2
      y = (diagram_height + im.height) // 2
      draw.text((x, y), str(countdown), font = self.font, fill = (0, 255, 255), anchor = 'mm')
    return im

def game_to_mp4(game: Game, flip_orientation: bool, delay: int, working_dir: str, output_mp4_filename: str, preset: str, ttf: Tuple[str,int], countdown: int = 0, vertical_layout: bool = False, lishogi_gif_server: Optional[str] = None):
  gif_filename = os.path.join(working_dir, 'game.gif')
  for key in ['sente', 'gote']:
    if game.get_tag(key) is None:
      game.set_tag(key, ' ')
  lishogi_gif(game, flip_orientation, delay, gif_filename, lishogi_gif_server)
  layout = None
  positions = game.positions()
  e = game_win_rates(game, 3)
  dft = (0.5, [])
  has_evals = len(e) > 0
  frames = _Frames(working_dir)
  with Image.open(gif_filename) as im:
    for index, frame in enumerate(ImageSequence.Iterator(im)):
      move_no = index + game.start_move_no
      if move_no > game.pos.move_no:
        break
      if layout is None:
        layout = _FrameLayout(frame, flip_orientation, ttf)
      if vertical_layout:
        while countdown > 0:
          im = layout.draw_vertical_frame(frame, countdown)
          frames.save(im)
          countdown -= 1
        im = layout.draw_vertical_frame(frame, None)
        frames.save(im)
      elif has_evals:
        im = frame.copy()
        exif_data = im.getexif()
        exif_data[270] = positions[move_no]
        wr, curm = e.get(move_no + 1, dft)
        old_wr, bm = e.get(move_no, dft)
        side = -game.move_no_to_side_to_move(move_no + 1)
        msg = None
        try:
          if not (bm[0][0] == game.moves[index]):
            msg = evaluation.mistake_str(side, old_wr, wr, ' '.join(s[1] for s in bm))
        except IndexError:
          pass
        draw = ImageDraw.Draw(im)
        layout.draw_bar(draw, old_wr)
        if (not msg is None) and curm:
          layout.draw_text(draw, side, msg, (255, 255, 255))
          logging.info("%s. %s (side = %d)", move_no, msg, side)
          layout.draw_move(draw, bm[0][0])
        frames.save(im, exif_data)
      else:
        if countdown > 0:
          side = game.move_no_to_side_to_move(move_no)
          for t in reversed(range(countdown + 1)):
            im = frame.copy()
            draw = ImageDraw.Draw(im)
            layout.draw_text(draw, side, str(t), (0, 255, 255))
            frames.save(im)
          countdown = 0
        else:
          frames.save(frame)
  frames.copy_last()
  if (has_evals) and (not vertical_layout):
    sente = game.player_with_rating(1)
    gote = game.player_with_rating(-1)
    title = sente + ' vs ' + gote
    matplotlib_graph(title, e, layout.figure_width, layout.figure_height, frames.next_frame_filename())
  command = ['ffmpeg', '-r', f'1000/{delay}', '-i', os.path.join(working_dir, 'frame%04d.png'), '-c:v', 'libx264', '-preset', preset, '-vf', 'fps=25', '-pix_fmt', 'yuv420p', os.path.join(working_dir, output_mp4_filename)]
  subprocess.run(command, check = True, shell = False)
