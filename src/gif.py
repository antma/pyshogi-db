# -*- coding: UTF8 -*-

import json
import logging
import requests
from typing import Optional
from shogi.game import Game
from shogi.position import Position

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
    frames.append({"sfen": pos.sfen(), "lastMove": m.usi_str()})
  d['frames'] = frames
  res = json.dumps(d)
  logging.debug("%s", res)
  return res

def lishogi_gif(server: Optional[str], game: Game, flip_orientation: bool, delay: int, output_gif_filename: str):
  if server is None:
    server = '127.0.0.1:6175'
  data = game_to_lishogi_gif_post_query(game, flip_orientation, delay)
  url = 'http://' + server + '/game.gif'
  r = requests.post(url, data = data)
  if r.status_code == 200:
    with open(output_gif_filename, 'wb') as f:
      f.write(r.content)
